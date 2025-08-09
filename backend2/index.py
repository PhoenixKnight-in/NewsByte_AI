import os
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from Transcripts.final_youtube_retrieval import get_latest_news_transcript_cleaned
from models.youtubevid import NewsItem
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from bson.objectid import ObjectId
from models.token import Token
from models.token_data import TokenData
from models.user import User, UserInDB


load_dotenv()
# MongoDB Configuration

MONGO_URI = "mongodb+srv://phoenixknight-in:Phoenix18.in@cluster.xopt5jz.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["NewsByte_AI"]
users_collection = db["users"]


# JWT Configuration

SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# FastAPI App

app = FastAPI()

# Security & Models
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    user_dict = users_collection.find_one({"username": username})
    if user_dict:
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "sub": data.get("sub")})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if getattr(current_user, "disabled", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Auth Routes
@app.post("/signup")
async def register_user(user: User = Body(...)):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["disabled"] = False
    users_collection.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": 1, "owner": current_user.username}]

# youtube retrieval
 
@app.get("/get_latest_news", response_model=list[NewsItem])
async def get_latest_news(query: str = "Sports latest news", num_videos: int = 3, minutes_ago: int = 1440,channel_id:str |None = None):
    results = get_latest_news_transcript_cleaned(query, num_videos, minutes_ago,channel_id)
    if not results:
        return []
    # Save to MongoDB
    db.news.insert_many(results)
    return results

@app.get("/get_saved_news", response_model=list[NewsItem])
async def get_saved_news():
    news = []
    for item in db.news.find():
        item.pop('_id', None)
        news.append(item)
    return news 
@app.get("/")
def root():
    return {"message": "Your FastAPI app with MongoDB Auth is running! "}



