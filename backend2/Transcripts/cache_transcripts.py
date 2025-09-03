import requests
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import isodate
import os
import time
import random
from dotenv import load_dotenv
from pymongo import MongoClient
from urllib.parse import urlparse
import hashlib
import os
from dotenv import load_dotenv
load_dotenv()

class NewsTranscriptCacher:
    def __init__(self, 
                 mongo_uri=os.getenv("MONGO_URI"), 
                 database_name="NewsByte_AI", 
                 collection_name="news"):
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.request_count = 0
        self.last_request_time = 0
        
        # Create indexes for better performance
        self.collection.create_index("video_url")
        self.collection.create_index("cached_at")
        self.collection.create_index("title")
        self.collection.create_index([("cached_at", -1), ("genre", 1)])
        
        print(f"Connected to MongoDB: {database_name}.{collection_name}")
    
    def detect_genre(self, text):
        text = text.lower()
        if any(word in text for word in ['election', 'minister', 'bjp', 'congress', 'parliament']):
            return 'politics'
        elif any(word in text for word in ['match', 'team', 'player', 'tournament']):
            return 'sports'
        elif any(word in text for word in ['ai', 'technology', 'smartphone', 'internet']):
            return 'technology'
        elif any(word in text for word in ['movie', 'film', 'actor', 'celebrity', 'music']):
            return 'entertainment'
        elif any(word in text for word in ['attack', 'murder', 'crime', 'terror', 'raid']):
            return 'crime'
        else:
            return 'default'
    
    def is_short(self, video_id, API_KEY):
        video_url = (
            f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails"
            f"&id={video_id}&key={API_KEY}"
        )
        res = requests.get(video_url)
        if res.status_code != 200:
            print(f"[is_short] failed to fetch contentDetails for {video_id}")
            return True

        items = res.json().get("items", [])
        if not items:
            return True

        duration = items[0]["contentDetails"].get("duration", "")
        try:
            parsed_duration = isodate.parse_duration(duration)
            return parsed_duration.total_seconds() < 60
        except Exception as e:
            return True
    
    def get_video_id_from_url(self, video_url):
        """Extract video ID from YouTube URL"""
        if "watch?v=" in video_url:
            return video_url.split("watch?v=")[1].split("&")[0]
        return None
    
    def is_cached_and_fresh(self, video_url, cache_hours=24):
        """Check if video is already cached and still fresh"""
        video_id = self.get_video_id_from_url(video_url)
        if not video_id:
            return False, None
            
        # Check if we have this video in cache
        cached_doc = self.collection.find_one({"video_url": video_url})
        
        if not cached_doc:
            return False, None
        
        # Check if cache is still fresh
        cached_at = cached_doc.get("cached_at")
        if not cached_at:
            return False, cached_doc
            
        cache_age = datetime.now(timezone.utc) - cached_at
        if cache_age.total_seconds() > (cache_hours * 3600):
            return False, cached_doc
            
        return True, cached_doc
    
    def get_transcript_with_fallbacks(self, video_id, delay=2):
        """Enhanced transcript fetching with rate limiting"""
        current_time = time.time()
        if current_time - self.last_request_time < delay:
            sleep_time = delay - (current_time - self.last_request_time)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        time.sleep(random.uniform(0.5, 1.5))
        
        try:
            # Try English first
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            return transcript_data, 'en'
            
        except NoTranscriptFound:
            try:
                # Try Hindi
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
                return transcript_data, 'hi'
            except:
                pass
            
            # Try any available language
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    try:
                        transcript_data = transcript.fetch()
                        return transcript_data, transcript.language_code
                    except:
                        continue
                        
                # Try translation to English
                for transcript in transcript_list:
                    try:
                        if transcript.is_translatable:
                            translated = transcript.translate('en')
                            transcript_data = translated.fetch()
                            return transcript_data, f'{transcript.language_code}-to-en'
                    except:
                        continue
            except:
                pass
        
        except Exception as e:
            if "blocked" in str(e).lower():
                print(f"[transcript] IP blocked for {video_id}")
                time.sleep(random.uniform(10, 20))
            else:
                print(f"[transcript] error on {video_id}: {e}")
        
        return None, None
    
    def cache_video_data(self, video_data):
        """Store or update video data in MongoDB"""
        try:
            # Use video_url as unique identifier
            filter_query = {"video_url": video_data["video_url"]}
            
            # Add caching metadata
            video_data["cached_at"] = datetime.now(timezone.utc)
            video_data["cache_version"] = "1.0"
            
            # Upsert (update if exists, insert if not)
            result = self.collection.replace_one(
                filter_query, 
                video_data, 
                upsert=True
            )
            
            action = "updated" if result.matched_count > 0 else "inserted"
            print(f"[cache] {action} video: {video_data.get('title', 'Unknown')[:50]}...")
            
            return True
        except Exception as e:
            print(f"[cache] error storing video data: {e}")
            return False
    
    def get_cached_news(self, 
                       hours_old=24, 
                       genres=None, 
                       limit=50):
        """Retrieve cached news from MongoDB"""
        
        # Build query
        query = {}
        
        # Only get fresh cache entries
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_old)
        query["cached_at"] = {"$gte": cutoff_time}
        
        # Filter by genres if specified
        if genres:
            query["genre"] = {"$in": genres}
        
        try:
            cursor = self.collection.find(query).sort("cached_at", -1).limit(limit)
            results = list(cursor)
            
            print(f"[cache] Retrieved {len(results)} cached news items")
            return results
            
        except Exception as e:
            print(f"[cache] error retrieving cached data: {e}")
            return []
    
    def get_latest_news_with_caching(self,
                                   query: str = 'NDTV latest news',
                                   num_videos_to_fetch: int = 10,
                                   minutes_ago: int = 500,
                                   channel_id: str = "UCZFMm1mMw0F81Z37aaEzTUA",
                                   force_refresh: bool = False,
                                   cache_hours: int = 6):
        """
        Main function that uses caching intelligently
        """
        
        API_KEY = os.getenv("YOUTUBE_API_KEY")
        if not API_KEY:
            raise ValueError("Missing YouTube API Key. Check your .env file.")
        
        # If not forcing refresh, try to get cached data first
        if not force_refresh:
            cached_results = self.get_cached_news(hours_old=cache_hours, limit=num_videos_to_fetch)
            if len(cached_results) >= num_videos_to_fetch:
                print(f"[cache] Using {len(cached_results)} cached results")
                return cached_results
            else:
                print(f"[cache] Only found {len(cached_results)} cached items, fetching fresh data")
        
        # Search for new videos
        time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        published_after = time_threshold.isoformat(timespec="seconds").replace("+00:00", "Z")

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 30,  # Fetch more to account for failures and shorts
            "order": "date",
            "safeSearch": "strict",
            "publishedAfter": published_after,
            "key": API_KEY,
        }
        if channel_id:
            params["channelId"] = channel_id

        search_url = "https://www.googleapis.com/youtube/v3/search"
        resp = requests.get(search_url, params=params)
        if resp.status_code != 200:
            print(f"[search] failed: {resp.status_code}")
            # Return cached data as fallback
            return self.get_cached_news(hours_old=24, limit=num_videos_to_fetch)

        data = resp.json()
        items = data.get("items", [])
        new_results = []
        processed_count = 0
        api_calls_made = 0

        for item in items:
            if len(new_results) >= num_videos_to_fetch:
                break
                
            vid_info = item.get("id", {})
            video_id = vid_info.get("videoId")
            if not video_id:
                continue

            processed_count += 1
            title = item.get("snippet", {}).get("title", "")
            thumbnail = item.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", "")
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            print(f"Processing {processed_count}: {title[:50]}...")

            # Check if already cached and fresh
            is_fresh, cached_data = self.is_cached_and_fresh(video_url, cache_hours)
            
            if is_fresh:
                print(f"[cache] Using cached data for {video_id}")
                new_results.append(cached_data)
                continue

            # Skip shorts
            if self.is_short(video_id, API_KEY):
                print(f"[skip] Short video: {video_id}")
                continue

            # Fetch transcript (this is the expensive operation)
            transcript_data, language = self.get_transcript_with_fallbacks(video_id)
            api_calls_made += 1
            
            if not transcript_data:
                print(f"[skip] No transcript: {video_id}")
                continue

            transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
            if not transcript_text:
                continue

            genre = self.detect_genre(transcript_text)
            
            # Create result object
            result = {
                "title": title,
                "genre": genre,
                "video_url": video_url,
                "thumbnail": thumbnail,
                "transcript": transcript_text,
                "transcript_language": language,
                "video_id": video_id
            }
            
            # Cache the result
            if self.cache_video_data(result):
                new_results.append(result)
                print(f"[success] Cached {video_id} ({language}) - Total: {len(new_results)}")
            
            # Rate limiting
            time.sleep(random.uniform(2, 4))

        # Combine with existing cache if needed
        if len(new_results) < num_videos_to_fetch:
            additional_cached = self.get_cached_news(
                hours_old=24, 
                limit=num_videos_to_fetch - len(new_results)
            )
            # Avoid duplicates
            existing_urls = {r.get("video_url") for r in new_results}
            for cached_item in additional_cached:
                if cached_item.get("video_url") not in existing_urls:
                    new_results.append(cached_item)

        print(f"\n=== SUMMARY ===")
        print(f"✅ Total results: {len(new_results)}")
        print(f"🆕 New API calls made: {api_calls_made}")
        print(f"💾 Used cached data: {len(new_results) - api_calls_made}")
        print(f"🎯 Cache efficiency: {((len(new_results) - api_calls_made) / len(new_results) * 100):.1f}%")
        
        return new_results[:num_videos_to_fetch]
    
    def cleanup_old_cache(self, days_old=7):
        """Remove old cached entries to keep database clean"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        result = self.collection.delete_many({
            "cached_at": {"$lt": cutoff_time}
        })
        
        print(f"[cleanup] Removed {result.deleted_count} old cache entries")
        return result.deleted_count
    
    def get_cache_stats(self):
        """Get statistics about cached data"""
        try:
            total_docs = self.collection.count_documents({})
            
            # Count by genre
            pipeline = [
                {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            genre_stats = list(self.collection.aggregate(pipeline))
            
            # Recent cache entries (last 24 hours)
            recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_count = self.collection.count_documents({
                "cached_at": {"$gte": recent_cutoff}
            })
            
            stats = {
                "total_cached_videos": total_docs,
                "recent_cache_entries": recent_count,
                "genre_distribution": {item["_id"]: item["count"] for item in genre_stats}
            }
            
            print(f"=== CACHE STATS ===")
            print(f"Total cached videos: {stats['total_cached_videos']}")
            print(f"Recent entries (24h): {stats['recent_cache_entries']}")
            print(f"Genre distribution: {stats['genre_distribution']}")
            
            return stats
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}

# # Usage Examples
# if __name__ == "__main__":
#     # Initialize the cacher
#     cacher = NewsTranscriptCacher()
    
#     # Get cache statistics
#     cacher.get_cache_stats()
    
#     # Get latest news (will use cache when possible)
#     print("\n=== FETCHING LATEST NEWS ===")
#     results = cacher.get_latest_news_with_caching(
#         query='NDTV latest news',
#         num_videos_to_fetch=10,
#         minutes_ago=2000,
#         cache_hours=6  # Use cache if data is less than 6 hours old
#     )
    
#     print(f"\nFinal results: {len(results)} videos")
    
#     # Clean up old cache (optional)
#     # cacher.cleanup_old_cache(days_old=7)