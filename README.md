# NewsByte_AI App - News Summary App
## "Breaking news, summarized in seconds."

A **Flutter + FastAPI-based application** that fetches the latest YouTube videos from a News channel, retrieves transcripts, generates summaries, and displays them with thumbnails.  
The app uses **YouTube Data API**, **YouTube Transcript API**, **GNews.io API** for homepage articles, and an **AI summarization backend**.

🌐 Hosted at: https://newsbyte-ai.onrender.com
---

### 👥 Team AINEWSUM
- **Parthiban M** (Team Lead) – Integration of frontend, backend, database, and deployment, AI Summarization ,Mongodb (database creation),cache system created
- **Poojikasri** – Frontend Developer
- **Udiksha Agarwal** – YouTube API & Transcript Retrieval
- **laya** - Authentication
- **Tanay** - Database creation 
---

## Project Preview
![WhatsApp Image 2025-09-12 at 23 40 15_368f9b82](https://github.com/user-attachments/assets/89358918-b290-419d-9a88-7295f9c14740)
![WhatsApp Image 2025-09-12 at 23 40 16_9238f1b7](https://github.com/user-attachments/assets/8d54834a-b808-48f0-a114-2e5aa226250e)
![WhatsApp Image 2025-09-12 at 23 40 16_ddddba0f](https://github.com/user-attachments/assets/1a881fce-f866-41a3-bf94-49c5851f75cb)



---

## ✨ Features
- 📡 Fetch latest videos from YouTube channels

- 🖼 Display video thumbnails, titles, and publish time

- 🧠 Generate and view AI summaries for each video

- 💾 Store generated summaries in a database for later retrieval

- ⚡ Backend powered by FastAPI & Python

- ⏱ Real-time transcript fetching & summarization

- 📄 Homepage news articles via GNews.io API

- 🔒 Local data caching using SharedPreferences 

---

## 🛠 Backend Setup (FastAPI)

1. **Clone the repository**
```
git clone https://github.com/<your_username>/NewsByte_AI
cd NewsByte_AI/backend2
```

2. **Create a virtual environment**
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. **Install dependencies**
```
pip install -r requirements.txt
```
4. **Add environment variables**
- Create a .env file inside backend/:
```
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
```
5. **Run the backend**
```
uvicorn main:app --reload
```
6. **Backend will start at:**

http://127.0.0.1:8000

## 📱 Frontend Setup (Flutter)

1. **Navigate to the frontend folder**
```
cd ../frontend
```
2. **Install dependencies**
```
flutter pub get
```
3. **Update API base URL**
In api_service.dart:

const String serverUrl = "http://127.0.0.1:8000";

4. **Run the Flutter app**
```
flutter run
```
## 💻 Technologies Used
Backend:

- Python, FastAPI

- YouTube Data API

- YouTube Transcript API

- OpenAI API (text summarization)

- Hugging Face BART-Large-CNN model

Frontend:

- Flutter, Dart

- SharedPreferences for local storage

Database:

- MongoDB (for storing generated summaries)

Others:

- REST API communication

- Render hosting for backend

## 🚀 How It Works

- Home page displays news articles via GNews.io API.

- User selects a preferred news channel from Explore Channels.

- Frontend requests the latest videos from the backend.

- Backend fetches video details via YouTube Data API.

- Backend retrieves transcripts using YouTube Transcript API.

- Summarization is done using OpenAI API and Hugging Face BART-Large-CNN model.

- Generated summary is stored in the database.

- Frontend displays video + summary, with offline caching via SharedPreferences.

## 🌐 Deployment on Render

### Create a new Web Service on Render

- Connect your GitHub repository.

- Set Root Directory to backend2.

- Add a Procfile in backend2/:

web:
```
uvicorn main:app --host 0.0.0.0 --port 10000
```
- Ensure requirements.txt exists in backend2/.

Set environment variables in Render Dashboard → Environment:
```
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
HF_API_KEY=your_huggingface_api_key
```

Deploy → Render will automatically build and host your FastAPI backend.

Backend will be accessible at:

https://your-app-name.onrender.com

## ⚡ NewsByte_AI – Stay informed, faster!
