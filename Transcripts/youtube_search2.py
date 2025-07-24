import requests
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline

# Initialize the summarizer pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

API_KEY = 'AIzaSyC4DYeF37H6WGWP9ISVsnWjoaWgrgLHXSc'
query = 'NDTV latest news'
max_results = 50
minutes_ago = 500

# Calculate time threshold
time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
published_after = time_threshold.isoformat(timespec="seconds").replace("+00:00", "Z")

# Build the search URL
search_url = (
    f'https://www.googleapis.com/youtube/v3/search?part=snippet'
    f'&q={query}&type=video&maxResults={max_results}'
    f'&order=date&publishedAfter={published_after}&key={API_KEY}'
)

# Function to detect YouTube Shorts based on duration
def is_short(video_id):
    video_url = (
        f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails"
        f"&id={video_id}&key={API_KEY}"
    )
    res = requests.get(video_url)
    if res.status_code != 200:
        return True

    details = res.json()
    items = details.get("items", [])
    if not items or "contentDetails" not in items[0]:
        return True

    duration = items[0]["contentDetails"].get("duration", "")
    if not duration:
        return True

    if "H" in duration or "M" in duration:
        return False
    elif "S" in duration:
        try:
            seconds = int(duration.replace("PT", "").replace("S", ""))
            return seconds < 60
        except ValueError:
            return True
    return True

# Function to split long text into manageable chunks
def chunk_text(text, max_chunk_length=1000):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(" ".join(current_chunk + [word])) <= max_chunk_length:
            current_chunk.append(word)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Make the API request to get search results
response = requests.get(search_url)

if response.status_code == 200:
    data = response.json()
    items = data.get('items', [])
    count = 1
    video_count = 0

    for item in items:
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        thumbnail = item['snippet']['thumbnails']['high']['url']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        if is_short(video_id):
            continue

        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            if not transcript_data:
                print(f"No transcript data available for {video_url}")
                continue

            # Combine transcript segments into one text
            transcript_text = " ".join([segment.get('text', '') for segment in transcript_data])

            if transcript_text.strip():
                # Chunk and summarize
                transcript_chunks = chunk_text(transcript_text, max_chunk_length=1000)
                summaries = []

                for chunk in transcript_chunks:
                    try:
                        if len(chunk.split()) < 15:
                            # If the chunk is too small, skip summarization or use it directly
                            summaries.append(chunk)
                        else:
                            summary = summarizer(chunk, max_length=50, min_length=15, do_sample=False)[0]['summary_text']
                            summaries.append(summary)
                    except Exception as e:
                        print(f"Error summarizing chunk: {e}")

                final_summary = " ".join(summaries)

                print(f"\n{count}. Title: {title}")
                print(f" Video Link: {video_url}")
                print(f" Thumbnail: {thumbnail}")
                print(f" Summary: {final_summary}\n")

                count += 1
                video_count += 1
                if video_count >= 10:
                    break
            else:
                print(f"\nSkipped (empty transcript): {video_url}")

        except (TranscriptsDisabled, NoTranscriptFound):
            continue
        except Exception as e:
            print(f"Error processing video {video_url}: {e}")
else:
    print(f"Failed to fetch videos. Status Code: {response.status_code}")
