import requests
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
from time import datetime

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

API_KEY = 'AIzaSyC4DYeF37H6WGWP9ISVsnWjoaWgrgLHXSc' 
query = "Today's latest news India Times Now"
max_results = 10

channel_id = 'UC6RJ7-PaXg6TIH2BzZfTV7w'
today = datetime.utcnow().date().isoformat() + "T00:00:00Z"

# 🔎 Search URL for today's videos from Times Now
search_url = (
    f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}'
    f'&publishedAfter={today}&type=video&maxResults={max_results}&key={API_KEY}'
)
search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&q={query}&type=video&maxResults={max_results}&key={API_KEY}'

#search_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults={max_results}&key={API_KEY}'
response = requests.get(search_url)

if response.status_code == 200:
    data = response.json()
    items = data.get('items', [])

    for i, item in enumerate(items, start=1):
        title = item['snippet']['title']
        video_id = item['id']['videoId']
        thumbnail = item['snippet']['thumbnails']['high']['url']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"\n{i}.  Title: {title}")
        print(f" Video Link: {video_url}")
        print(f" Thumbnail: {thumbnail}")
        proxies = {
            'http': 'http://51.158.68.68:8811',
            'https': 'http://51.158.68.68:8811'
            }

        
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies, languages=['hi', 'en'])
            transcript_text = " ".join([segment['text'] for segment in transcript_data])
            short_text = transcript_text[:2000]  

            
            summary = summarizer(short_text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
            print(f"📝 Summary: {summary}")

        except Exception as e:
            print(f" Could not fetch transcript: {e}")

else:
    print(f" Failed to fetch videos. Status Code: {response.status_code}")
