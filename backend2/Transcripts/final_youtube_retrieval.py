import requests
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import isodate

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

def get_latest_news_transcript_cleaned(
    query: str = 'NDTV Sports latest news',
    num_videos_to_fetch: int = 10,
    minutes_ago: int = 500,
    channel_id: str = "UCZFMm1mMw0F81Z37aaEzTUA"
):
    API_KEY = 'AIzaSyC4DYeF37H6WGWP9ISVsnWjoaWgrgLHXSc'  # move to env var in production

    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    published_after = time_threshold.isoformat(timespec="seconds").replace("+00:00", "Z")

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 10,
        "order": "date",
        "safeSearch": "strict",
        "publishedAfter": published_after,
        "key": API_KEY,
    }
    if channel_id:
        params["channelId"] = channel_id  # correct param name

    search_url = "https://www.googleapis.com/youtube/v3/search"
    resp = requests.get(search_url, params=params)
    if resp.status_code != 200:
        print(f"[search] failed: {resp.status_code} {resp.text}")
        return []

    data = resp.json()
    items = data.get("items", [])
    results = []

    for item in items:
        vid_info = item.get("id", {})
        video_id = vid_info.get("videoId")
        if not video_id:
            # skip playlists/channels or malformed
            continue

        title = item.get("snippet", {}).get("title", "")
        thumbnail = item.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", "")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        if is_short(video_id, API_KEY):
            continue

        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            if not transcript_data:
                continue

            transcript_text = " ".join(segment.get("text", "") for segment in transcript_data).strip()
            if not transcript_text:
                continue

            genre = detect_genre(transcript_text)
            result = {
                "title": title,
                "genre": genre,
                "video_url": video_url,
                "thumbnail": thumbnail,
                "transcript": transcript_text
            }
            results.append(result)

            if len(results) >= num_videos_to_fetch:
                break
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            print(f"[transcript] unavailable for {video_id}: {e}")
            continue
        except Exception as e:
            print(f"[unexpected] error on {video_id}: {e}")
            continue

    return results
