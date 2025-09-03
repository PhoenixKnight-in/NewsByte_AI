import os
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from Transcripts.final_youtube_retrieval import get_latest_news_with_caching
from models.youtubevid import NewsItem
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from bson.objectid import ObjectId
from models.token import Token
from models.token_data import TokenData
from models.user import User, UserInDB
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
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

# Helper function to get cached news from MongoDB
def get_cached_news_from_db(query: str = None, limit: int = 50) -> List[dict]:
    """Retrieve cached news from MongoDB"""
    try:
        # Build query filter
        filter_query = {}
        if query:
            filter_query["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        
        # Get recent cached news (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        filter_query["cached_at"] = {"$gte": cutoff_time}
        
        cursor = db.news.find(filter_query).sort("cached_at", -1).limit(limit)
        results = list(cursor)
        
        # Remove MongoDB _id field
        for item in results:
            item.pop('_id', None)
            
        logger.info(f"Retrieved {len(results)} cached news items from DB")
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving cached news from DB: {e}")
        return []

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

# YouTube retrieval with proper error handling
@app.get("/get_latest_news", response_model=List[NewsItem])
async def get_latest_news(
    query: str = "Sports latest news", 
    num_videos: int = 3, 
    minutes_ago: int = 1440,
    channel_id: str | None = None
):
    try:
        logger.info(f"Attempting to fetch latest news: query='{query}', num_videos={num_videos}")
        
        # Try to get fresh news first
        results = get_latest_news_with_caching(
            query=query,
            num_videos_to_fetch=num_videos,
            minutes_ago=minutes_ago,
            channel_id=channel_id,
            force_refresh=False,
            cache_hours=6
        )
        
        if results and len(results) > 0:
            logger.info(f"Successfully fetched {len(results)} fresh news items")
            
            # Add timestamp for caching
            for item in results:
                if isinstance(item, dict):
                    item["cached_at"] = datetime.utcnow()
                    item["source"] = "fresh"
            
            # Save to MongoDB (handle duplicates)
            try:
                db.news.insert_many(results, ordered=False)
                logger.info(f"Saved {len(results)} items to MongoDB")
            except Exception as save_error:
                logger.warning(f"Some items may already exist in DB: {save_error}")
            
            return results
        else:
            # If no fresh results, fall back to cached data
            logger.warning("No fresh results found, falling back to cached data")
            raise Exception("No fresh data available")
            
    except Exception as e:
        logger.error(f"Error fetching fresh news: {e}")
        
        # Fallback to cached data from MongoDB
        logger.info("Falling back to cached news from database")
        cached_results = get_cached_news_from_db(query, num_videos)
        
        if cached_results:
            logger.info(f"Successfully retrieved {len(cached_results)} cached items")
            
            # Mark as cached source
            for item in cached_results:
                item["source"] = "cached"
                
            return cached_results
        else:
            logger.error("No cached data available either")
            # Return empty list instead of raising HTTP exception
            return []

@app.get("/get_saved_news", response_model=List[NewsItem])
async def get_saved_news(limit: int = 50, skip: int = 0):
    """Get all saved news with pagination"""
    try:
        news = []
        cursor = db.news.find().sort("cached_at", -1).skip(skip).limit(limit)
        
        for item in cursor:
            item.pop('_id', None)
            news.append(item)
            
        logger.info(f"Retrieved {len(news)} saved news items")
        return news
        
    except Exception as e:
        logger.error(f"Error retrieving saved news: {e}")
        return []

# New endpoint specifically for cached news
@app.get("/get_cached_news", response_model=List[NewsItem])
async def get_cached_news_endpoint(
    query: str | None = None,
    limit: int = 50
):
    """Get cached news from database"""
    try:
        cached_results = get_cached_news_from_db(query, limit)
        return cached_results
    except Exception as e:
        logger.error(f"Error in cached news endpoint: {e}")
        return []

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.command('ping')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.get("/")
def root():
    return {"message": "Your FastAPI app with MongoDB Auth is running!"}