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
    


def is_short(video_id,API_KEY):
    video_url = (
        f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails"
        f"&id={video_id}&key={API_KEY}"
    )
    res = requests.get(video_url)
    if res.status_code != 200:
        return True

    items = res.json().get("items", [])
    if not items:
        return True

    duration = items[0]["contentDetails"].get("duration", "")
    try:
        parsed_duration = isodate.parse_duration(duration)
        return parsed_duration.total_seconds() < 60
    except:
        return True
    

def get_latest_news_transcript_cleaned(query = 'NDTV Sports latest news',num_videos_to_fetch = 10,minutes_ago = 1440,channel_id= "UCZFMm1mMw0F81Z37aaEzTUA"):
    API_KEY = 'AIzaSyC4DYeF37H6WGWP9ISVsnWjoaWgrgLHXSc'

    time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    published_after = time_threshold.isoformat(timespec="seconds").replace("+00:00", "Z")

    search_url = (
        f'https://www.googleapis.com/youtube/v3/search?part=snippet'
        f'&q={query}&type=video&maxResults={num_videos_to_fetch}'
        f'&order=date&safeSearch=strict&publishedAfter={published_after}&key={API_KEY}'
    )
    if channel_id:
        base += f"&channelId={channel_id}"

    response = requests.get(search_url)
    if response.status_code != 200:
        return f"Error: Failed to fetch videos. Status Code: {response.status_code}"

    data = response.json()
    items = data.get('items', [])
    results = []
    for item in items:
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        thumbnail = item['snippet']['thumbnails']['high']['url']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        if is_short(video_id,API_KEY):
            continue

        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            if not transcript_data:
                continue

            transcript_text = " ".join([segment.get('text', '') for segment in transcript_data])
            if not transcript_text.strip():
                continue
            genre = detect_genre(transcript_text)
            result = {
                "title":title,
                "genre":genre,
                "video_url":video_url,
                "thumbnail":thumbnail,
                "transcript":transcript_text.strip()
            }
            results.append(result)

            if len(results) >= num_videos_to_fetch:
                break
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            continue
        except Exception:
            continue
    return results

# if __name__== "__main__":
#     news_output = get_latest_news_transcript_cleaned()
#     print(news_output)

