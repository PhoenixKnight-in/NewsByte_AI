
                                                               YouTube News Summary App



A Flutter + FastAPI-based application that fetches the latest YouTube videos from a News channel, retrieves transcripts, generates summaries, and displays them with thumbnails.
The app uses YouTube Data API, YouTube Transcript API,Gnew.io API for Homepage articles and an AI summarization backend.



Team AINEWSUM:
Parthiban M (Team lead - Worked in integration of frontend,backend,database and deployment)
Poojikasri (Frontend dev)
Udiksha Agarwal (YOUTUBE Transcript retrieval)
Yashvendra(Falcon AI LLM Summarization)
Tanay(Database Creation)
laya (Authentication)

📌 Features
Fetch latest videos from a YouTube channel.

Display video thumbnails, title.

View AI-generated summaries for each video.

Local data caching using SharedPreferences.

Backend powered by FastAPI and Python.

Real-time transcript fetching and summarization.

Backend Setup (FastAPI)
1. Clone the repository
bash
Copy
Edit
git clone (https://github.com/<your_username>/NewsByte_AI)
cd NewsByte_AI/backend2

3. Create a virtual environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3️⃣ Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
4️⃣ Add your environment variables
Create a .env file in backend/:

ini
Copy
Edit
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
5️⃣ Run the backend
bash
Copy
Edit
uvicorn main:app --reload
Backend will start at:

cpp
Copy
Edit
http://127.0.0.1:8000
📱 Frontend Setup (Flutter)
1️⃣ Navigate to the frontend folder
bash
Copy
Edit
cd ../frontend
2️⃣ Install dependencies
bash
Copy
Edit
flutter pub get
3️⃣ Update API base URL
In api_service.dart, set your backend API URL:

dart
Copy
Edit
const String serverUrl = "http://127.0.0.1:8000";
4️⃣ Run the Flutter app
bash
Copy
Edit
flutter run
🔗 API Endpoints
1. Get latest videos
GET /videos?channel_id=CHANNEL_ID

Params:

channel_id: YouTube channel ID
channel_id_TIMES_NOW=UC6RJ7-PaXg6TIH2BzZfTV7w
channel_id_NDTV=UCZFMm1mMw0F81Z37aaEzTUA

Response:

json
Copy
Edit
[
  {
    "video_id": "abc123",
    "title": "Latest News",
    "thumbnail_url": "https://...",
    "published_at": "2025-08-10T12:00:00Z"
  }
]
2. Get video summary
GET /summary?video_id=VIDEO_ID

Params:

video_id: YouTube video ID

Response:

json
Copy
Edit
{
  "video_id": "abc123",
  "summary": "This video talks about..."
}
🛠 Technologies Used
Backend: Python, FastAPI, YouTube Data API, YouTube Transcript API, OpenAI API

Frontend: Flutter, Dart, SharedPreferences

Database: Local storage (SharedPreferences)

Others: REST API communication

🚀 How It Works
Home page contains News From article using GNews.io API key 
EXPLORE CHANNELS you have to select the prefered channel
Frontend requests the latest videos from a YouTube channel via backend.

Backend uses YouTube Data API to fetch video details.

Backend retrieves transcripts using YouTube Transcript API.

Summarization is done via AI model (e.g.,Falcon AI from Hugging face).

Frontend displays the video list with summaries.

SharedPreferences caches data locally for offline use.
