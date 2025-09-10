# enhanced_news_filter.py
import re
import requests
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import isodate
import os
import time
import random
from pymongo import MongoClient
from urllib.parse import urlparse
import hashlib
from dotenv import load_dotenv

load_dotenv()

class EnhancedNewsFilter:
    def __init__(self):
        # Music indicators in transcripts
        self.music_indicators = [
            '[Music]', '[music]', '[MUSIC]',
            '[Applause]', '[applause]', '[APPLAUSE]',
            '[Laughter]', '[laughter]', '[LAUGHTER]',
            '[Background Music]', '[background music]',
            '[Instrumental]', '[instrumental]',
            '[Sound]', '[sound]', '[SOUND]',
            '[Beat]', '[beat]', '[BEAT]'
        ]
        
        # Live news indicators in titles
        self.live_indicators = [
            'live', 'LIVE', 'Live',
            'breaking', 'BREAKING', 'Breaking',
            'streaming', 'STREAMING', 'Streaming',
            'पत्रकार सम्मेलन', 'प्रेस कॉन्फ्रेंस',  # Hindi for press conference
            'सीधा प्रसारण',  # Hindi for live broadcast
        ]
    
    def clean_transcript_text(self, transcript_text):
        """Clean transcript by removing music/sound markers"""
        if not transcript_text:
            return ""
        
        cleaned_text = transcript_text
        
        # Remove music indicators
        for indicator in self.music_indicators:
            cleaned_text = cleaned_text.replace(indicator, " ")
        
        # Remove repeated words (like "Heat Heat Heat")
        cleaned_text = re.sub(r'\b(\w+)(\s+\1)+\b', r'\1', cleaned_text, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
    
    def is_meaningful_transcript(self, transcript_text, min_words=10, min_unique_words=5):
        """Check if transcript contains meaningful content"""
        if not transcript_text:
            return False
        
        # Clean the transcript first
        cleaned_text = self.clean_transcript_text(transcript_text)
        
        if not cleaned_text or len(cleaned_text.strip()) < 20:
            return False
        
        # Split into words and filter out short/meaningless words
        words = [word.strip('.,!?;:') for word in cleaned_text.split() 
                if len(word.strip('.,!?;:')) > 2]
        
        # Check if we have enough words
        if len(words) < min_words:
            return False
        
        # Check for unique words (avoid repetitive content)
        unique_words = set(word.lower() for word in words)
        if len(unique_words) < min_unique_words:
            return False
        
        # Check if it's mostly music/sound effects
        music_word_count = sum(1 for word in words if any(
            indicator.lower().replace('[', '').replace(']', '') in word.lower() 
            for indicator in self.music_indicators
        ))
        
        # If more than 30% of words are music-related, reject
        if music_word_count / len(words) > 0.3:
            return False
        
        # Check for repetitive patterns (like "Heat Heat Heat")
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # If any single word appears more than 40% of the time, it's likely repetitive
        max_word_frequency = max(word_counts.values()) if word_counts else 0
        if max_word_frequency / len(words) > 0.4:
            return False
        
        return True
    
    def is_live_news(self, title, description=""):
        """Check if video is live news/streaming"""
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Check for live indicators in title
        for indicator in self.live_indicators:
            if indicator.lower() in title_lower:
                return True
        
        # Additional patterns for live content
        live_patterns = [
            r'\blive\b',
            r'\bstreaming\b',
            r'\bpress conference\b',
            r'\bpress meet\b',
            r'\bसीधा\b.*?प्रसारण',
            r'\bलाइव\b',
        ]
        
        for pattern in live_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True
            if description and re.search(pattern, description_lower, re.IGNORECASE):
                return True
        
        return False


class EnhancedNewsTranscriptCacher:
    def __init__(self, 
                 mongo_uri=os.getenv("MONGO_URI"), 
                 database_name="NewsByte_AI", 
                 collection_name="news"):
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.request_count = 0
        self.last_request_time = 0
        self.content_filter = EnhancedNewsFilter()  # Initialize filter
        
        # Create indexes for better performance
        self.collection.create_index("video_url")
        self.collection.create_index("cached_at")
        self.collection.create_index("title")
        self.collection.create_index([("cached_at", -1), ("genre", 1)])
        
        print(f"Connected to MongoDB: {database_name}.{collection_name}")
    
    def detect_genre(self, text):
        text = text.lower()
        if any(word in text for word in ['election', 'minister', 'bjp', 'congress', 'parliament','cm','pm']):
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
            return 'general'
    
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
        """Enhanced transcript fetching with music/live filtering"""
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
            transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
            
            # Check if transcript is meaningful
            if self.content_filter.is_meaningful_transcript(transcript_text):
                cleaned_text = self.content_filter.clean_transcript_text(transcript_text)
                return transcript_data, 'en', cleaned_text
            else:
                print(f"[skip] Transcript mostly music/repetitive: {video_id}")
                return None, None, None
                
        # except NoTranscriptFound:
        #     try:
        #         # # Try Hindi
        #         # transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
        #         # transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
                
        #         # if self.content_filter.is_meaningful_transcript(transcript_text):
        #         #     cleaned_text = self.content_filter.clean_transcript_text(transcript_text)
        #         #     return transcript_data, 'hi', cleaned_text
        #         # else:
        #         #     print(f"[skip] Hindi transcript mostly music/repetitive: {video_id}")
        #         #     return None, None, None
                    
        #     except:
        #         pass
            
            # Try any available language
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    try:
                        transcript_data = transcript.fetch()
                        transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
                        
                        if self.content_filter.is_meaningful_transcript(transcript_text):
                            cleaned_text = self.content_filter.clean_transcript_text(transcript_text)
                            return transcript_data, transcript.language_code, cleaned_text
                    except:
                        continue
                        
                # Try translation to English
                for transcript in transcript_list:
                    try:
                        if transcript.is_translatable:
                            translated = transcript.translate('en')
                            transcript_data = translated.fetch()
                            transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
                            
                            if self.content_filter.is_meaningful_transcript(transcript_text):
                                cleaned_text = self.content_filter.clean_transcript_text(transcript_text)
                                return transcript_data, f'{transcript.language_code}-to-en', cleaned_text
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
        
        return None, None, None
    
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
                                   cache_hours: int = 6,
                                   exclude_live: bool = True,
                                   min_transcript_words: int = 10):
        """
        Enhanced main function with music and live news filtering
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
            "maxResults": 50,  # Fetch more since we'll filter many out
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
            return self.get_cached_news(hours_old=24, limit=num_videos_to_fetch)

        data = resp.json()
        items = data.get("items", [])
        new_results = []
        processed_count = 0
        api_calls_made = 0
        skipped_live = 0
        skipped_music = 0

        for item in items:
            if len(new_results) >= num_videos_to_fetch:
                break
                
            vid_info = item.get("id", {})
            video_id = vid_info.get("videoId")
            if not video_id:
                continue

            processed_count += 1
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            print(f"Processing {processed_count}: {title[:50]}...")

            # Check if already cached and fresh
            is_fresh, cached_data = self.is_cached_and_fresh(video_url, cache_hours)
            
            if is_fresh:
                print(f"[cache] Using cached data for {video_id}")
                new_results.append(cached_data)
                continue

            # Filter out live news if requested
            if exclude_live and self.content_filter.is_live_news(title, description):
                print(f"[skip] Live news detected: {video_id}")
                skipped_live += 1
                continue

            # Skip shorts
            if self.is_short(video_id, API_KEY):
                print(f"[skip] Short video: {video_id}")
                continue

            # Fetch transcript with enhanced filtering
            transcript_data, language, cleaned_transcript = self.get_transcript_with_fallbacks(video_id)
            api_calls_made += 1
            
            if not transcript_data or not cleaned_transcript:
                print(f"[skip] No meaningful transcript: {video_id}")
                skipped_music += 1
                continue

            # Final word count check
            word_count = len(cleaned_transcript.split())
            if word_count < min_transcript_words:
                print(f"[skip] Transcript too short ({word_count} words): {video_id}")
                continue

            genre = self.detect_genre(cleaned_transcript)
            
            # Create result object with cleaned transcript
            result = {
                "title": title,
                "genre": genre,
                "video_url": video_url,
                "thumbnail": thumbnail,
                "transcript": cleaned_transcript,  # Use cleaned transcript
                "transcript_language": language,
                "video_id": video_id,
                "word_count": word_count
            }
            
            # Cache the result
            if self.cache_video_data(result):
                new_results.append(result)
                print(f"[success] Cached {video_id} ({language}, {word_count} words) - Total: {len(new_results)}")
            
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

        print(f"\n=== ENHANCED FILTERING SUMMARY ===")
        print(f"✅ Total results: {len(new_results)}")
        print(f"🆕 New API calls made: {api_calls_made}")
        print(f"💾 Used cached data: {len(new_results) - api_calls_made}")
        print(f"🎵 Skipped music/repetitive: {skipped_music}")
        print(f"📡 Skipped live news: {skipped_live}")
        print(f"🎯 Cache efficiency: {((len(new_results) - api_calls_made) / max(len(new_results), 1) * 100):.1f}%")
        
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


# Test function
def test_enhanced_filter():
    """Test the enhanced filtering system"""
    
    # Test the filter class directly
    filter_obj = EnhancedNewsFilter()
    
    # Test 1: Clean transcript text
    dirty_transcript = "[Music] Heat Heat Heat [Music] This is actual news content about politics [Applause] More content here [Music]"
    clean_transcript = filter_obj.clean_transcript_text(dirty_transcript)
    print(f"Original: {dirty_transcript}")
    print(f"Cleaned: {clean_transcript}")
    print()
    
    # Test 2: Check if transcript is meaningful
    is_meaningful = filter_obj.is_meaningful_transcript(clean_transcript)
    print(f"Is meaningful: {is_meaningful}")
    print()
    
    # Test 3: Test music-only transcript
    music_only = "[Music] Heat Heat Heat Heat Beat Beat [Music] [Applause]"
    is_music_meaningful = filter_obj.is_meaningful_transcript(music_only)
    print(f"Music-only meaningful: {is_music_meaningful}")  # Should be False
    print()
    
    # Test 4: Live news detection
    live_titles = [
        "LIVE: Breaking News Conference",
        "NDTV पत्रकार सम्मेलन LIVE",
        "Regular news video",
        "Press conference streaming now"
    ]
    
    for title in live_titles:
        is_live = filter_obj.is_live_news(title)
        print(f"'{title}' -> Live: {is_live}")


# Usage example
if __name__ == "__main__":
    # Test the filter
    print("🧪 Testing Enhanced Filter...")
    test_enhanced_filter()
    
    print("\n" + "="*50)
    print("🚀 Using Enhanced Cacher")
    
    # Use the enhanced cacher
    try:
        enhanced_cacher = EnhancedNewsTranscriptCacher()
        
        # Get enhanced news with filtering
        results = enhanced_cacher.get_latest_news_with_caching(
            query='NDTV latest news',
            num_videos_to_fetch=5,
            exclude_live=True,          # Filter out live content
            min_transcript_words=15,    # Minimum words required
            cache_hours=6
        )
        
        print(f"\n📊 Final Results: {len(results)} videos")
        
        # Display first result as example
        if results:
            first_result = results[0]
            print(f"\n📰 Sample result:")
            print(f"Title: {first_result.get('title', '')[:100]}...")
            print(f"Genre: {first_result.get('genre', 'Unknown')}")
            print(f"Words: {first_result.get('word_count', 0)}")
            print(f"Language: {first_result.get('transcript_language', 'Unknown')}")
            print(f"Transcript preview: {first_result.get('transcript', '')[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your .env file has MONGO_URI and YOUTUBE_API_KEY")