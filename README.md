<<<<<<< HEAD
# frontend

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
=======
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
>>>>>>> 6344990e4e90c3fdcaba16aeb3c158b11f9b4b5f
