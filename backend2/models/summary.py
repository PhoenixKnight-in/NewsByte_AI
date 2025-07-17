from pydantic import BaseModel

class User(BaseModel):
    id_of_video: str
    summary: str
    AI_used: str #chatgpt or whichever model used
    