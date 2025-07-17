from pydantic import BaseModel
from datetime import date
class video(BaseModel):
    title:str
    link: str
    desc: str
    thumbnail: str  
    duration: str
    upload_date: date
    transcript: str