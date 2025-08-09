from pydantic import BaseModel

class NewsItem(BaseModel):
    title: str
    genre: str
    video_url: str
    thumbnail: str
    transcript: str
