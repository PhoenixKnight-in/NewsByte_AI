# NewsByte_AI App - News Summary App
## "Breaking news, summarized in seconds."

A **Flutter + FastAPI-based application** that fetches the latest YouTube videos from a News channel, retrieves transcripts, generates summaries, and displays them with thumbnails.  
The app uses **YouTube Data API**, **YouTube Transcript API**, **GNews.io API** for homepage articles, and an **AI summarization backend**.

---

### 👥 Team AINEWSUM
- **Parthiban M** (Team Lead) – Integration of frontend, backend, database, and deployment  
- **Poojikasri** – Frontend Developer  
- **Udiksha Agarwal** – YouTube API & Transcript Retrieval  
- **Yashvendra** – Falcon AI LLM Summarization  
- **Tanay** – Database Creation  

---

## Project Preview
![WhatsApp Image 2025-08-11 at 18 44 58_a8a245b4](https://github.com/user-attachments/assets/69788e41-5d54-45a8-b3a6-069301ac0846)

![WhatsApp Image 2025-08-11 at 18 44 58_dc8c6fd6](https://github.com/user-attachments/assets/fc59a10b-c514-40a1-b23a-a6d280566070)

![WhatsApp Image 2025-08-11 at 18 44 59_86d14a1b](https://github.com/user-attachments/assets/3051f142-c0eb-42fd-8cac-b6bff9bb00f5)


---

## ✨ Features
- 📡 Fetch latest videos from a YouTube channel  
- 🖼 Display video thumbnails and titles  
- 🧠 View AI-generated summaries for each video  
- 💾 Local data caching using SharedPreferences  
- ⚡ Backend powered by **FastAPI & Python**  
- ⏱ Real-time transcript fetching and summarization  

---

## 🛠 Backend Setup (FastAPI)

1. **Clone the repository**
git clone https://github.com/<your_username>/NewsByte_AI
cd NewsByte_AI/backend2

Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

pip install -r requirements.txt
Add environment variables
Create a .env file inside backend/:

YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
Run the backend

bash
Copy
Edit
uvicorn main:app --reload
Backend will start at:

http://127.0.0.1:8000
📱 Frontend Setup (Flutter)
Navigate to the frontend folder

cd ../frontend
Install dependencies

flutter pub get
Update API base URL
In api_service.dart:

const String serverUrl = "http://127.0.0.1:8000";
Run the Flutter app

flutter run
🔗 API Endpoints
1️⃣ Get Latest Videos
GET /videos?channel_id=CHANNEL_ID
Params:

channel_id – YouTube channel ID

channel_id_TIMES_NOW=UC6RJ7-PaXg6TIH2BzZfTV7w

channel_id_NDTV=UCZFMm1mMw0F81Z37aaEzTUA

Response:

json
[
  {
    "video_id": "abc123",
    "title": "Latest News",
    "thumbnail_url": "https://...",
    "published_at": "2025-08-10T12:00:00Z"
  }
]
2️⃣ Get Video Summary
GET /summary?video_id=VIDEO_ID
Params:

video_id – YouTube video ID

Response:

{
  "video_id": "abc123",
  "summary": "This video talks about..."
}
💻 Technologies Used
Backend: Python, FastAPI, YouTube Data API, YouTube Transcript API, OpenAI API
Frontend: Flutter, Dart, SharedPreferences
Database: Local storage (SharedPreferences)
Others: REST API communication

🚀 How It Works
Home page displays news articles via GNews.io API.

User selects a preferred news channel from "Explore Channels".

Frontend requests the latest videos from the backend.

Backend fetches video details via YouTube Data API.

Backend retrieves transcripts using YouTube Transcript API.

Summarization is done using Falcon AI (Hugging Face).

Frontend displays the video list with summaries.

SharedPreferences caches data locally for offline usage.
