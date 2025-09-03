import requests
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import isodate
import os
import time
import random
from Transcripts.cache_transcripts import NewsTranscriptCacher
from dotenv import load_dotenv

load_dotenv()

# Initialize with proper error handling
def initialize_cacher():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        # Fallback to default local MongoDB
        mongo_uri = os.getenv("MONGO_URI")
        print("Warning: MONGO_URI not found, using default localhost")
    
    try:
        cacher = NewsTranscriptCacher(
            mongo_uri=mongo_uri,
            database_name="NewsByte_AI", 
            collection_name="news"
        )
        print("✅ Cache system initialized successfully")
        return cacher
    except Exception as e:
        print(f"❌ Failed to initialize cache: {e}")
        return None

# Global cacher instance
cacher = initialize_cacher()

def get_latest_news_with_caching(
    query: str = 'NDTV latest news',
    num_videos_to_fetch: int = 10,
    minutes_ago: int = 500,
    channel_id: str = "UCZFMm1mMw0F81Z37aaEzTUA",
    force_refresh: bool = False,
    cache_hours: int = 6
):
    """
    Main function that uses the caching system properly
    """
    
    if not cacher:
        print("❌ Cache system not available, falling back to direct fetch")
        return get_latest_news_direct(query, num_videos_to_fetch, minutes_ago, channel_id)
    
    try:
        # Use the cacher's method which handles all the caching logic
        results = cacher.get_latest_news_with_caching(
            query=query,
            num_videos_to_fetch=num_videos_to_fetch,
            minutes_ago=minutes_ago,
            channel_id=channel_id,
            force_refresh=force_refresh,
            cache_hours=cache_hours
        )
        
        return results
        
    except Exception as e:
        print(f"❌ Cache system failed: {e}")
        print("Falling back to direct fetch...")
        return get_latest_news_direct(query, num_videos_to_fetch, minutes_ago, channel_id)

def get_latest_news_direct(
    query: str = 'NDTV latest news',
    num_videos_to_fetch: int = 10,
    minutes_ago: int = 500,
    channel_id: str = "UCZFMm1mMw0F81Z37aaEzTUA"
):
    """
    Fallback function for when cache is not available
    This is your original function, simplified
    """
    
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    if not API_KEY:
        raise ValueError("Missing YouTube API Key. Check your .env file.")
    
    print("🔄 Using direct fetch (no caching)")
    
    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    published_after = time_threshold.isoformat(timespec="seconds").replace("+00:00", "Z")

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 20,
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
        return []

    data = resp.json()
    items = data.get("items", [])
    results = []

    for item in items[:num_videos_to_fetch]:  # Limit processing
        vid_info = item.get("id", {})
        video_id = vid_info.get("videoId")
        if not video_id:
            continue

        title = item.get("snippet", {}).get("title", "")
        thumbnail = item.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", "")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Basic result without transcript (fallback mode)
        result = {
            "title": title,
            "genre": "default",
            "video_url": video_url,
            "thumbnail": thumbnail,
            "transcript": "Transcript not available (direct mode)",
            "transcript_language": "none"
        }
        results.append(result)

    return results

def get_cache_stats():
    """Get cache statistics"""
    if not cacher:
        return {"error": "Cache not available"}
    
    try:
        return cacher.get_cache_stats()
    except Exception as e:
        return {"error": f"Failed to get stats: {e}"}

def cleanup_cache(days_old=7):
    """Clean up old cache entries"""
    if not cacher:
        print("Cache not available for cleanup")
        return 0
    
    try:
        return cacher.cleanup_old_cache(days_old=days_old)
    except Exception as e:
        print(f"Cache cleanup failed: {e}")
        return 0

def force_refresh_cache(query="NDTV latest news", num_videos=5):
    """Force refresh cache for testing"""
    return get_latest_news_with_caching(
        query=query,
        num_videos_to_fetch=num_videos,
        force_refresh=True,
        cache_hours=0  # Ignore all cache
    )

# Test the system
def test_cache_system():
    """Test if cache system is working properly"""
    print("🧪 Testing cache system...")
    
    # Test 1: Check cache connection
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # Test 2: Fetch some news (should use cache if available)
    print("\n📰 Fetching news (cache-first)...")
    results = get_latest_news_with_caching(
        query="NDTV sports",
        num_videos_to_fetch=3,
        cache_hours=1  # Very fresh cache
    )
    
    print(f"Got {len(results)} results")
    if results:
        print(f"First result: {results[0].get('title', 'No title')[:50]}...")
    
    # Test 3: Force refresh
    print("\n🔄 Testing force refresh...")
    fresh_results = force_refresh_cache("NDTV politics", 2)
    print(f"Fresh results: {len(fresh_results)}")
    
    return len(results), len(fresh_results)

# if __name__ == "__main__":
#     # Run tests
#     test_cache_system()
    
#     # Your main usage
#     print("\n" + "="*50)
#     print("🚀 MAIN EXECUTION")
    
#     # This is how you should call it:
#     results = get_latest_news_with_cache(
#         query='NDTV latest news',
#         num_videos_to_fetch=10,
#         cache_hours=6  # Use cache if less than 6 hours old
#     )
    
#     print(f"📊 Final results: {len(results)} videos")
    
#     # Show cache efficiency if available
#     if cacher:
#         stats = get_cache_stats()
#         if 'total_cached_videos' in stats:
#             print(f"💾 Total cached: {stats['total_cached_videos']}")
#             print(f"🆕 Recent (24h): {stats.get('recent_cache_entries', 0)}")