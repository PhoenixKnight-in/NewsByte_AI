YouTube News Summary App
A Flutter + FastAPI-based application that fetches the latest YouTube videos from a channel, retrieves transcripts, generates summaries, and displays them with thumbnails.
The app uses YouTube Data API, YouTube Transcript API, and an AI summarization backend.

📌 Features
Fetch latest videos from a YouTube channel.

Display video thumbnails, title, and published date.

View AI-generated summaries for each video.

Local data caching using SharedPreferences.

Backend powered by FastAPI and Python.

Real-time transcript fetching and summarization.

🗂 Folder Structure
graphql
Copy
Edit
project_root/
│
├── backend/
│   ├── main.py                # FastAPI backend entry point
│   ├── requirements.txt       # Python dependencies
│   ├── summarizer.py          # AI summarization logic
│   ├── youtube_service.py     # YouTube API + transcript fetching
│
├── frontend/
│   ├── lib/
│   │   ├── video_summary_page.dart   # Video list + summary UI
│   │   ├── shared_pref_service.dart  # SharedPreferences helper
│   │   ├── api_service.dart          # API calls to backend
│
└── README.md
🖥 Backend Setup (FastAPI)
1️⃣ Clone the repository
bash
Copy
Edit
git clone https://github.com/yourusername/youtube-news-summary.git
cd youtube-news-summary/backend
2️⃣ Create a virtual environment
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
const String baseUrl = "http://127.0.0.1:8000";
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
Frontend requests the latest videos from a YouTube channel via backend.

Backend uses YouTube Data API to fetch video details.

Backend retrieves transcripts using YouTube Transcript API.

Summarization is done via AI model (e.g., OpenAI GPT).

Frontend displays the video list with summaries.

SharedPreferences caches data locally for offline use.