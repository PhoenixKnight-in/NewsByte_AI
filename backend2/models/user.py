from typing import Optional
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserInDB(User):
    hashed_password: str