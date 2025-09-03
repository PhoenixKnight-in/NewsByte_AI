import requests
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import isodate
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

def detect_genre(text):
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

def is_short(video_id, API_KEY):
    video_url = (
        f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails"
        f"&id={video_id}&key={API_KEY}"
    )
    res = requests.get(video_url)
    if res.status_code != 200:
        print(f"[is_short] failed to fetch contentDetails for {video_id}, status {res.status_code}")
        return True

    items = res.json().get("items", [])
    if not items:
        print(f"[is_short] no contentDetails item for {video_id}")
        return True

    duration = items[0]["contentDetails"].get("duration", "")
    try:
        parsed_duration = isodate.parse_duration(duration)
        return parsed_duration.total_seconds() < 60
    except Exception as e:
        print(f"[is_short] parse error for {video_id}: {e}")
        return True

class ImprovedTranscriptFetcher:
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
        
    def get_transcript_with_fallbacks(self, video_id, delay=2):
        """Enhanced transcript fetching with multiple fallback strategies"""
        
        # Rate limiting: ensure minimum delay between requests
        current_time = time.time()
        if current_time - self.last_request_time < delay:
            sleep_time = delay - (current_time - self.last_request_time)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Add random delay to avoid pattern detection
        time.sleep(random.uniform(0.5, 1.5))
        
        try:
            # Strategy 1: Try English first (your original approach)
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            return transcript_data, 'en'
            
        except NoTranscriptFound:
            # Strategy 2: Try Hindi (common in Indian news channels)
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
                return transcript_data, 'hi'
            except:
                pass
            
            # Strategy 3: Try any available language
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    try:
                        transcript_data = transcript.fetch()
                        return transcript_data, transcript.language_code
                    except:
                        continue
                        
                # Strategy 4: Try translation to English
                for transcript in transcript_list:
                    try:
                        if transcript.is_translatable:
                            translated = transcript.translate('en')
                            transcript_data = translated.fetch()
                            return transcript_data, f'{transcript.language_code}-to-en'
                    except:
                        continue
                        
            except Exception as e:
                print(f"[transcript-fallback] Could not list transcripts for {video_id}: {e}")
        
        except TranscriptsDisabled:
            print(f"[transcript] disabled for {video_id}")
            
        except VideoUnavailable:
            print(f"[transcript] video unavailable: {video_id}")
            
        except Exception as e:
            if "blocked" in str(e).lower() or "ip" in str(e).lower():
                print(f"[transcript] IP blocked for {video_id}, adding longer delay")
                time.sleep(random.uniform(10, 20))
            else:
                print(f"[transcript] unexpected error on {video_id}: {e}")
        
        return None, None

def get_latest_news_transcript_cleaned(
    query: str = 'NDTV Sports latest news',
    num_videos_to_fetch: int = 10,
    minutes_ago: int = 500,
    channel_id: str = "UCZFMm1mMw0F81Z37aaEzTUA"
):
    
    API_KEY = os.getenv("YOUTUBE_API_KEY")
    if not API_KEY:
        raise ValueError("Missing YouTube API Key. Check your .env file.")
    
    # Initialize the improved transcript fetcher
    transcript_fetcher = ImprovedTranscriptFetcher()
    
    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    published_after = time_threshold.isoformat(timespec="seconds").replace("+00:00", "Z")

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 20,  # Fetch more to account for failures
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
        print(f"[search] failed: {resp.status_code} {resp.text}")
        return []

    data = resp.json()
    items = data.get("items", [])
    results = []
    processed_count = 0

    for item in items:
        if len(results) >= num_videos_to_fetch:
            break
            
        vid_info = item.get("id", {})
        video_id = vid_info.get("videoId")
        if not video_id:
            continue

        processed_count += 1
        print(f"Processing video {processed_count}: {video_id}")

        title = item.get("snippet", {}).get("title", "")
        thumbnail = item.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", "")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Skip shorts
        if is_short(video_id, API_KEY):
            print(f"[skip] {video_id} is a short video")
            continue

        # Use improved transcript fetching
        transcript_data, language = transcript_fetcher.get_transcript_with_fallbacks(video_id)
        
        if not transcript_data:
            print(f"[skip] No transcript available for {video_id}")
            continue

        transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
        if not transcript_text:
            print(f"[skip] Empty transcript for {video_id}")
            continue

        genre = detect_genre(transcript_text)
        result = {
            "title": title,
            "genre": genre,
            "video_url": video_url,
            "thumbnail": thumbnail,
            "transcript": transcript_text,
            "transcript_language": language  # Track what language we got
        }
        results.append(result)
        
        print(f"[success] Added {video_id} ({language}) - Total: {len(results)}")
        
        # Add delay between successful fetches to be respectful
        if len(results) < num_videos_to_fetch:
            time.sleep(random.uniform(2, 4))

    print(f"\n=== SUMMARY ===")
    print(f"✅ Successfully fetched: {len(results)}/{processed_count} videos")
    print(f"📊 Languages found: {set(r.get('transcript_language', 'unknown') for r in results)}")
    
    return results

# Alternative function for debugging specific video IDs
def debug_specific_videos(video_ids):
    """
    Test transcript fetching for specific problematic video IDs
    """
    fetcher = ImprovedTranscriptFetcher()
    
    for video_id in video_ids:
        print(f"\n--- Testing {video_id} ---")
        transcript_data, language = fetcher.get_transcript_with_fallbacks(video_id, delay=3)
        
        if transcript_data:
            preview = " ".join(segment.get("text", "") for segment in transcript_data[:3])
            print(f"✅ Success ({language}): {preview}...")
        else:
            print(f"❌ Failed: {video_id}")

# if __name__ == "__main__":
#     # Test with your problematic video IDs first
#     problematic_videos = [
#         'p8zs_qfWP5s', 'Bi_G52xBaN8', 'b-b0drFzf9E', 
#         'uMP0UgVpckg', '1ntoF44JUHg', '-RwocJPRtN4'
#     ]
    
#     print("=== TESTING PROBLEMATIC VIDEOS ===")
#     debug_specific_videos(problematic_videos)
    
#     print("\n=== RUNNING MAIN FUNCTION ===")
#     # Run your main function
#     results = get_latest_news_transcript_cleaned(
#         query='NDTV latest news',
#         num_videos_to_fetch=5,
#         minutes_ago=2000
#     )
    
#     print(f"Final results: {len(results)} videos processed successfully")