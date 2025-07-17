#  NewsByte AI – Real-Time AI-Powered News Summarizer

**NewsByte AI** is a mobile app that delivers real-time, concise news summaries from YouTube news channels and online articles using cutting-edge AI technologies like Whisper and GPT. Stay informed without the noise — just the essence of breaking news.

---

## Features

- 🎥 **YouTube News Integration**: Fetch and play the latest news videos from trusted sources like NDTV, BBC, and more.
- 📄 **Article Aggregation**: Pull breaking news from RSS feeds and public news websites.
- 🧠 **AI-Powered Summaries**:
  - **Transcription** with Whisper (video → text)
  - **Summarization** with GPT-4o (text → short digest)
- 📰 **Headline Generator**: AI-crafted titles for fast scanning

---

## 📱 Tech Stack

| Layer            | Technology               |
|------------------|---------------------------|
| Frontend         | Flutter                   |
| Video Playback   | youtube_player_flutter    |
| Backend API      | FastAPI (Python)          |
| Transcription    | OpenAI Whisper / whisper.cpp |
| Summarization    | OpenAI GPT-4o             |
| News Parsing     | YouTube Data API, RSS, newspaper3k |
| Database         | MongoDB (MongoDB Atlas)   |
| Hosting          | Render / Railway / Firebase |
| Push Notifications (Optional) | Firebase Cloud Messaging |

---

## 🛠️ Installation Guide

### 🔹 Prerequisites
- Python 3.9+
- Flutter SDK
- MongoDB Atlas account
- OpenAI API key
- YouTube Data API key
- 
```bash
git clone https://github.com/yourusername/newsbyte-ai.git
pip install -r requirements.txt
