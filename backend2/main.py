import os
import sys
from fastapi import Query
from dotenv import load_dotenv
from Transcripts.final_youtube_retrieval import get_latest_news_with_caching
from models.youtubevid import NewsItem
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
from typing import Dict, Any
import requests


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
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI App
app = FastAPI()

# Security & Models
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# Initialize with external API configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGING_FACE")  # Add this to Render env vars
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Alternative

# Simple text-based summarization fallback
def simple_extractive_summary(text: str, max_sentences: int = 3) -> str:
    """
    Simple extractive summarization without ML models
    """
    sentences = text.split('. ')
    if len(sentences) <= max_sentences:
        return text
    
    # Take first sentence, middle sentence, and last sentence
    if len(sentences) >= 3:
        indices = [0, len(sentences)//2, -1]
        summary_sentences = [sentences[i] for i in indices]
        return '. '.join(summary_sentences) + '.'
    else:
        return '. '.join(sentences[:max_sentences]) + '.'

def huggingface_api_summary(text: str, api_key: str) -> Dict[str, Any]:
    """
    Use Hugging Face Inference API for summarization
    """
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": text[:1000]},  # Limit input length
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return {
                    "status": "success",
                    "summary": result[0].get("summary_text", ""),
                    "method": "huggingface_api"
                }
        
        return {
            "status": "error",
            "error_message": f"API error: {response.status_code}",
            "method": "huggingface_api"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "method": "huggingface_api"
        }

def openai_summary(text: str, api_key: str) -> Dict[str, Any]:
    """
    Use OpenAI API for summarization
    """
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Summarize the following news transcript in 2-3 sentences."},
                {"role": "user", "content": text[:2000]}
            ],
            "max_tokens": 150,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"]
            return {
                "status": "success",
                "summary": summary,
                "method": "openai_api"
            }
        
        return {
            "status": "error",
            "error_message": f"OpenAI API error: {response.status_code}",
            "method": "openai_api"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "method": "openai_api"
        }

def Phoenix_Sum(news_text: str = None) -> Dict[str, Any]:
    """
    Memory-efficient summarization using external APIs or simple extraction
    """
    try:
        if not news_text or len(news_text.strip()) < 50:
            return {
                "status": "error",
                "error_message": "Text too short for meaningful summarization",
                "timestamp": datetime.utcnow().isoformat()
            }

        original_length = len(news_text)
        news_text = news_text.strip()

        # Try external APIs first
        if HUGGINGFACE_API_KEY:
            logger.info("Attempting Hugging Face API summarization")
            result = huggingface_api_summary(news_text, HUGGINGFACE_API_KEY)
            if result["status"] == "success":
                result.update({
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {
                        "original_length": original_length,
                        "summary_length": len(result["summary"]),
                        "compression_ratio": len(result["summary"]) / original_length
                    }
                })
                return result

        if OPENAI_API_KEY:
            logger.info("Attempting OpenAI API summarization")
            result = openai_summary(news_text, OPENAI_API_KEY)
            if result["status"] == "success":
                result.update({
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {
                        "original_length": original_length,
                        "summary_length": len(result["summary"]),
                        "compression_ratio": len(result["summary"]) / original_length
                    }
                })
                return result

        # Fallback to simple extractive summary
        logger.info("Using simple extractive summarization as fallback")
        simple_summary = simple_extractive_summary(news_text)
        
        return {
            "status": "success",
            "summary": simple_summary,
            "method": "extractive_fallback",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "original_length": original_length,
                "summary_length": len(simple_summary),
                "compression_ratio": len(simple_summary) / original_length
            }
        }

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Remove all the heavy model initialization code
# No more global model loading, just simple functions

def batch_summarize(text_list):
    """
    Lightweight batch summarization without memory issues
    """
    try:
        results = []
        for i, text in enumerate(text_list):
            logger.info(f"Processing item {i+1}/{len(text_list)}")
            result = Phoenix_Sum(text)
            results.append(result)

        return {
            "batch_results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"])
        }
        
    except Exception as e:
        return {"error": str(e)}

# Remove the test_summarization_quality function or simplify it
# def test_summarization_quality():
#     """Simple test without models"""
#     test_text = "Training camp practice number six for the New York Giants is underway."
#     result = Phoenix_Sum(test_text)
#     return result


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

# Helper function to get cached news from MongoDB with STRICT channel_id filtering
def get_cached_news_from_db(channel_id: str = None, query: str = None, limit: int = 50, hours_back: int = 24) -> List[dict]:
    """Retrieve cached news from MongoDB with STRICT channel_id filtering"""
    try:
        filter_query = {}
        
        # STRICT Channel ID filtering - this is the key fix
        if channel_id:
            # Make sure we're filtering exactly by channel_id
            filter_query["channel_id"] = {"$eq": channel_id}  # Exact match
            logger.info(f"STRICT filtering by channel_id: {channel_id}")
        
        # Time-based filter
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        time_filter = {"cached_at": {"$gte": cutoff_time}}
        
        # Secondary text search (only if channel_id filter is applied)
        if query and channel_id:
            filter_query = {
                "$and": [
                    {"channel_id": {"$eq": channel_id}},
                    {"cached_at": {"$gte": cutoff_time}},
                    {
                        "$or": [
                            {"title": {"$regex": query, "$options": "i"}},
                            {"description": {"$regex": query, "$options": "i"}}
                        ]
                    }
                ]
            }
        elif query and not channel_id:
            # If only query provided (no channel_id), search across all channels
            filter_query = {
                "$and": [
                    {"cached_at": {"$gte": cutoff_time}},
                    {
                        "$or": [
                            {"title": {"$regex": query, "$options": "i"}},
                            {"description": {"$regex": query, "$options": "i"}},
                            {"channel_name": {"$regex": query, "$options": "i"}}
                        ]
                    }
                ]
            }
        elif channel_id and not query:
            # Channel ID only
            filter_query = {
                "$and": [
                    {"channel_id": {"$eq": channel_id}},
                    {"cached_at": {"$gte": cutoff_time}}
                ]
            }
        else:
            # Neither channel_id nor query provided
            filter_query = time_filter
        
        # Execute query
        cursor = db.news.find(filter_query).sort("cached_at", -1).limit(limit)
        results = list(cursor)
        
        # Debug logging
        logger.info(f"Filter query used: {filter_query}")
        logger.info(f"Found {len(results)} items")
        
        # Log what channels we actually got
        channels_found = set()
        for item in results:
            if 'channel_id' in item:
                channels_found.add(item['channel_id'])
            item.pop('_id', None)
        
        logger.info(f"Channels in results: {channels_found}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving cached news from DB: {e}")
        return []

# Helper function to get unique channels from cache
def get_cached_channels() -> List[dict]:
    """Get list of unique channels available in cache"""
    try:
        # Aggregate unique channels with their info
        pipeline = [
            {"$match": {"cached_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}}},
            {
                "$group": {
                    "_id": "$channel_id",
                    "channel_name": {"$first": "$channel_name"},
                    "channel_url": {"$first": "$channel_url"},
                    "video_count": {"$sum": 1},
                    "latest_video": {"$max": "$cached_at"}
                }
            },
            {"$sort": {"video_count": -1}}
        ]
        
        results = list(db.news.aggregate(pipeline))
        
        # Format results
        channels = []
        for result in results:
            channels.append({
                "channel_id": result["_id"],
                "channel_name": result["channel_name"],
                "channel_url": result["channel_url"],
                "video_count": result["video_count"],
                "latest_video": result["latest_video"]
            })
        
        logger.info(f"Found {len(channels)} unique channels in cache")
        return channels
        
    except Exception as e:
        logger.error(f"Error retrieving cached channels: {e}")
        return []

# Function to clean up mixed channel data (run once)
def cleanup_mixed_channel_cache():
    """One-time cleanup function to identify and fix mixed channel data"""
    try:
        # Find all items without proper channel_id
        count_without_channel = db.news.count_documents({"channel_id": {"$exists": False}})
        logger.info(f"Found {count_without_channel} items without channel_id")
        
        # Find all unique channels currently in cache
        pipeline = [
            {"$group": {"_id": "$channel_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        channel_stats = list(db.news.aggregate(pipeline))
        logger.info("Current channel distribution in cache:")
        for stat in channel_stats:
            logger.info(f"  Channel: {stat['_id']} - Count: {stat['count']}")
        
        return channel_stats
        
    except Exception as e:
        logger.error(f"Error in cleanup function: {e}")
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

# NEW SUMMARIZATION ENDPOINTS
# Add logging middleware to handle errors gracefully
@app.middleware("http")
async def safe_logging_middleware(request, call_next):
    start_time = datetime.now()
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Safe logging
        try:
            logger.info(f"{request.client.host} - {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        except Exception:
            # If logging fails, continue without logging
            pass
            
        return response
    except Exception as e:
        # Safe error logging
        try:
            logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")
        except Exception:
            # If logging fails, print to stderr as fallback
            print(f"Request failed: {request.method} {request.url.path} - {str(e)}", file=sys.stderr)
        raise


@app.post("/summarize_news/{video_id}")
async def summarize_news_by_video_id(
    video_id: str,
    force_regenerate: bool = Query(False, description="Force regenerate even if summary exists")
):
    """
    Generate and store summary for a specific video using its video_id
    """
    try:
        # Find the news item by video_id
        news_item = db.news.find_one({"video_id": video_id})
        
        if not news_item:
            raise HTTPException(
                status_code=404, 
                detail=f"No news item found with video_id: {video_id}"
            )
        
        # Check if summary already exists (unless force_regenerate is True)
        existing_summary = news_item.get("summary")
        if existing_summary and not force_regenerate:
            return {
                "message": "Summary already exists",
                "video_id": video_id,
                "summary": existing_summary,
                "summary_created_at": news_item.get("summary_created_at"),
                "regenerated": False
            }
        # Check if transcript exists
        transcript = news_item.get("transcript", "")
        if not transcript or len(transcript.strip()) < 50:
            # Try description as fallback
            transcript = news_item.get("description", "")
            if not transcript or len(transcript.strip()) < 50:
                raise HTTPException(
                    status_code=400, 
                    detail="No transcript or description available for summarization"
                )
        
        # Check if summary already exists
        if news_item.get("summary"):
            return {
                "message": "Summary already exists",
                "video_id": video_id,
                "existing_summary": news_item["summary"],
                "summary_created_at": news_item.get("summary_created_at"),
                "regenerated": False
            }
        
        # Generate summary
        logger.info(f"Generating summary for video_id: {video_id}")
        summary_result = Phoenix_Sum(transcript)
        
        if summary_result["status"] != "success":
            raise HTTPException(
                status_code=500, 
                detail=f"Summarization failed: {summary_result.get('error_message', 'Unknown error')}"
            )
        
        # Store summary back in database (without user info since no auth)
        update_result = db.news.update_one(
            {"video_id": video_id},
            {
                "$set": {
                    "summary": summary_result["summary"],
                    "summary_created_at": datetime.utcnow(),
                    "summary_created_by": "anonymous",  # Since no user authentication
                    "summary_status": "completed"
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=500, 
                detail="Failed to update news item with summary"
            )
        
        logger.info(f"Summary generated and stored for video_id: {video_id}")
        
        return {
            "message": "Summary generated successfully",
            "video_id": video_id,
            "title": news_item.get("title", ""),
            "summary": summary_result["summary"],
            "summary_created_at": datetime.utcnow(),
            "summary_created_by": "anonymous",
            "regenerated": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in summarization endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@app.post("/regenerate_summary/{video_id}")
async def regenerate_summary(video_id: str):
    """
    Regenerate summary for a specific video (overwrites existing summary) - NO AUTH REQUIRED
    """
    try:
        # Find the news item by video_id
        news_item = db.news.find_one({"video_id": video_id})
        
        if not news_item:
            raise HTTPException(
                status_code=404, 
                detail=f"No news item found with video_id: {video_id}"
            )
            
        # Get transcript
        transcript = news_item.get("transcript", "")
        if not transcript or len(transcript.strip()) < 50:
            # Try description as fallback
            transcript = news_item.get("description", "")
            if not transcript or len(transcript.strip()) < 50:
                raise HTTPException(
                    status_code=400, 
                    detail="No transcript or description available for summarization"
                )
        
        # Generate new summary
        logger.info(f"Regenerating summary for video_id: {video_id}")
        summary_result = Phoenix_Sum(transcript)
        
        if summary_result["status"] != "success":
            raise HTTPException(
                status_code=500, 
                detail=f"Summarization failed: {summary_result.get('error_message', 'Unknown error')}"
            )
        
        # Store new summary (overwrite existing)
        update_result = db.news.update_one(
            {"video_id": video_id},
            {
                "$set": {
                    "summary": summary_result["summary"],
                    "summary_created_at": datetime.utcnow(),
                    "summary_created_by": "anonymous",
                    "summary_status": "regenerated",
                    "previous_summary_backup": news_item.get("summary", "")
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=500, 
                detail="Failed to update news item with new summary"
            )
        
        logger.info(f"Summary regenerated for video_id: {video_id}")
        
        return {
            "message": "Summary regenerated successfully",
            "video_id": video_id,
            "title": news_item.get("title", ""),
            "new_summary": summary_result["summary"],
            "summary_created_at": datetime.utcnow(),
            "summary_created_by": "anonymous",
            "regenerated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in regenerate summary endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/batch_summarize")
async def batch_summarize_news(
    channel_id: str = Query(None, description="Summarize all news from specific channel"),
    limit: int = Query(10, description="Maximum number of items to summarize"),
    skip_existing: bool = Query(True, description="Skip items that already have summaries")
):
    """
    Batch summarize multiple news items - NO AUTH REQUIRED
    """
    try:
        # Build filter query
        filter_query = {}
        if channel_id:
            filter_query["channel_id"] = {"$eq": channel_id}
        
        if skip_existing:
            filter_query["summary"] = {"$exists": False}
        
        # Get items to summarize
        cursor = db.news.find(filter_query).limit(limit)
        items = list(cursor)
        
        if not items:
            return {
                "message": "No items found to summarize",
                "filter_applied": filter_query,
                "processed": 0,
                "successful": 0,
                "failed": 0
            }
        
        successful = 0
        failed = 0
        failed_items = []
        
        for item in items:
            try:
                video_id = item.get("video_id")
                if not video_id:
                    failed += 1
                    failed_items.append({"item": str(item.get("_id", "unknown")), "reason": "No video_id"})
                    continue
                
                # Get transcript
                transcript = item.get("transcript", "")
                if not transcript or len(transcript.strip()) < 50:
                    transcript = item.get("description", "")
                    if not transcript or len(transcript.strip()) < 50:
                        failed += 1
                        failed_items.append({"video_id": video_id, "reason": "No transcript or description"})
                        continue
                
                # Generate summary
                summary_result = Phoenix_Sum(transcript)
                
                if summary_result["status"] != "success":
                    failed += 1
                    failed_items.append({"video_id": video_id, "reason": summary_result.get("error_message", "Summarization failed")})
                    continue
                
                # Update database
                update_result = db.news.update_one(
                    {"video_id": video_id},
                    {
                        "$set": {
                            "summary": summary_result["summary"],
                            "summary_created_at": datetime.utcnow(),
                            "summary_created_by": "anonymous",
                            "summary_status": "batch_generated"
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    successful += 1
                else:
                    failed += 1
                    failed_items.append({"video_id": video_id, "reason": "Database update failed"})
                
            except Exception as e:
                failed += 1
                failed_items.append({"video_id": item.get("video_id", "unknown"), "reason": str(e)})
        
        return {
            "message": "Batch summarization completed",
            "processed": len(items),
            "successful": successful,
            "failed": failed,
            "failed_items": failed_items[:5] if failed_items else [],
            "filter_applied": filter_query
        }
        
    except Exception as e:
        logger.error(f"Error in batch summarization: {e}")
        raise HTTPException(status_code=500, detail=f"Batch summarization failed: {str(e)}")


@app.get("/get_summary/{video_id}")
async def get_summary_by_video_id(video_id: str):
    """
    Get existing summary for a specific video by video_id
    """
    try:
        # Find the news item by video_id
        news_item = db.news.find_one({"video_id": video_id})
        
        if not news_item:
            raise HTTPException(
                status_code=404, 
                detail=f"No news item found with video_id: {video_id}"
            )
        
        # Check if summary exists
        if not news_item.get("summary"):
            return {
                "video_id": video_id,
                "title": news_item.get("title", ""),
                "has_summary": False,
                "summary": None,
                "message": "No summary available for this video"
            }
        
        return {
            "video_id": video_id,
            "title": news_item.get("title", ""),
            "has_summary": True,
            "summary": news_item["summary"],
            "summary_created_at": news_item.get("summary_created_at"),
            "summary_created_by": news_item.get("summary_created_by", "unknown")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving summary for video_id {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/get_video_details/{video_id}")
async def get_video_details(video_id: str):
    """
    Get complete video details including summary status
    """
    try:
        news_item = db.news.find_one({"video_id": video_id})
        
        if not news_item:
            raise HTTPException(
                status_code=404, 
                detail=f"No video found with video_id: {video_id}"
            )
        
        # Remove MongoDB ObjectId
        news_item.pop('_id', None)
        
        # Add summary status
        news_item["has_summary"] = bool(news_item.get("summary"))
        news_item["has_transcript"] = bool(news_item.get("transcript"))
        
        return news_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving video details for {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
# YouTube retrieval with proper error handling and channel_id focus
@app.get("/get_latest_news", response_model=List[NewsItem])
async def get_latest_news(
    channel_id: str | None = None,
    query: str = "Sports latest news", 
    num_videos: int = 3, 
    minutes_ago: int = 1440
):
    try:
        logger.info(f"Attempting to fetch latest news: channel_id='{channel_id}', query='{query}', num_videos={num_videos}")
        
        # FORCE FRESH FETCH when channel_id is provided to avoid cross-channel contamination
        force_refresh = bool(channel_id)  # Always force refresh for specific channels
        
        # Try to get fresh news first
        results = get_latest_news_with_caching(
            query=query,
            num_videos_to_fetch=num_videos,
            minutes_ago=minutes_ago,
            channel_id=channel_id,
            force_refresh=force_refresh,  # Use force_refresh based on channel_id
            cache_hours=6
        )
        
        if results and len(results) > 0:
            logger.info(f"Successfully fetched {len(results)} fresh news items")
            
            # Validate that all results match the requested channel_id
            if channel_id:
                validated_results = []
                for item in results:
                    if isinstance(item, dict) and item.get('channel_id') == channel_id:
                        item["cached_at"] = datetime.utcnow()
                        item["source"] = "fresh"
                        validated_results.append(item)
                    else:
                        logger.warning(f"Filtered out item from wrong channel: got {item.get('channel_id')}, expected {channel_id}")
                
                results = validated_results
            else:
                # No channel_id specified, accept all results
                for item in results:
                    if isinstance(item, dict):
                        item["cached_at"] = datetime.utcnow()
                        item["source"] = "fresh"
            
            # Save to MongoDB (handle duplicates)
            if results:
                try:
                    db.news.insert_many(results, ordered=False)
                    logger.info(f"Saved {len(results)} items to MongoDB")
                except Exception as save_error:
                    logger.warning(f"Some items may already exist in DB: {save_error}")
            
            return results
        else:
            # If no fresh results, fall back to cached data with STRICT channel_id filtering
            logger.warning("No fresh results found, falling back to cached data")
            if not channel_id:
                raise Exception("No fresh data available and no channel_id for cache lookup")
            
            # Get cached data with STRICT filtering
            cached_results = get_cached_news_from_db(
                channel_id=channel_id, 
                query=None,  # Don't use query for fallback to get more results
                limit=num_videos
            )
            
            if cached_results:
                logger.info(f"Successfully retrieved {len(cached_results)} cached items for channel {channel_id}")
                
                # Mark as cached source and validate channel
                validated_cached = []
                for item in cached_results:
                    if item.get('channel_id') == channel_id:
                        item["source"] = "cached"
                        validated_cached.append(item)
                
                return validated_cached
            else:
                logger.error(f"No cached data available for channel {channel_id}")
                return []
            
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        
        # Final fallback to cached data from MongoDB with STRICT channel_id filtering
        if channel_id:
            logger.info(f"Final fallback to cached news for channel {channel_id}")
            cached_results = get_cached_news_from_db(
                channel_id=channel_id, 
                query=None, 
                limit=num_videos
            )
            
            if cached_results:
                logger.info(f"Final fallback: retrieved {len(cached_results)} cached items")
                
                # Double-check channel validation
                final_results = []
                for item in cached_results:
                    if item.get('channel_id') == channel_id:
                        item["source"] = "cached_fallback"
                        final_results.append(item)
                
                return final_results
        
        logger.error("All fallback attempts failed")
        return []
    
@app.get("/get_saved_news", response_model=List[NewsItem])
async def get_saved_news(
    channel_id: str | None = None,
    limit: int = 50, 
    skip: int = 0
):
    """Get all saved news with pagination, optionally filtered by channel_id"""
    try:
        filter_query = {}
        if channel_id:
            filter_query["channel_id"] = {"$eq": channel_id}  # Strict filtering
        
        news = []
        cursor = db.news.find(filter_query).sort("cached_at", -1).skip(skip).limit(limit)
        
        for item in cursor:
            item.pop('_id', None)
            news.append(item)
            
        logger.info(f"Retrieved {len(news)} saved news items (channel_id: {channel_id})")
        return news
        
    except Exception as e:
        logger.error(f"Error retrieving saved news: {e}")
        return []

# Main endpoint for cached news with STRICT channel_id filtering
@app.get("/get_cached_news", response_model=List[NewsItem])
async def get_cached_news_endpoint(
    channel_id: str | None = Query(None, description="REQUIRED: YouTube Channel ID for specific channel"),
    query: str | None = Query(None, description="Optional: Search text within the channel"),
    limit: int = Query(50, description="Maximum number of results"),
    hours_back: int = Query(24, description="Hours back to search in cache")
):
    """Get cached news - MUST specify channel_id to avoid mixed results"""
    try:
        if not channel_id:
            # Return empty or error if no channel_id specified
            logger.warning("No channel_id provided - returning empty results to avoid mixed content")
            return []
        
        cached_results = get_cached_news_from_db(
            channel_id=channel_id, 
            query=query, 
            limit=limit, 
            hours_back=hours_back
        )
        
        # Additional validation - make sure all results are from the requested channel
        validated_results = []
        for item in cached_results:
            if item.get('channel_id') == channel_id:
                validated_results.append(item)
            else:
                logger.warning(f"Filtered out item from wrong channel: {item.get('channel_id')}")
        
        logger.info(f"Returning {len(validated_results)} validated items for channel {channel_id}")
        return validated_results
        
    except Exception as e:
        logger.error(f"Error in cached news endpoint: {e}")
        return []

# New endpoint to get available channels in cache
@app.get("/get_cached_channels")
async def get_cached_channels_endpoint():
    """Get list of channels available in cache"""
    try:
        channels = get_cached_channels()
        return {
            "channels": channels,
            "total_channels": len(channels),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error retrieving cached channels: {e}")
        return {"channels": [], "total_channels": 0, "error": str(e)}

# New endpoint to get news by specific channel with detailed stats
@app.get("/get_news_by_channel/{channel_id}", response_model=List[NewsItem])
async def get_news_by_channel(
    channel_id: str,
    limit: int = Query(50, description="Maximum number of results"),
    hours_back: int = Query(24, description="Hours back to search")
):
    """Get all news from a specific channel"""
    try:
        results = get_cached_news_from_db(
            channel_id=channel_id,
            limit=limit,
            hours_back=hours_back
        )
        
        if not results:
            raise HTTPException(
                status_code=404, 
                detail=f"No cached news found for channel_id: {channel_id}"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving news for channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# New endpoint to debug cache contents
@app.get("/debug_cache")
async def debug_cache_contents():
    """Debug endpoint to see what's actually in your cache"""
    try:
        # Get channel distribution
        pipeline = [
            {"$group": {
                "_id": "$channel_id", 
                "count": {"$sum": 1},
                "channel_name": {"$first": "$channel_name"},
                "sample_titles": {"$push": "$title"},
                "has_summaries": {"$sum": {"$cond": [{"$ne": ["$summary", None]}, 1, 0]}},
                "has_transcripts": {"$sum": {"$cond": [{"$ne": ["$transcript", None]}, 1, 0]}}
            }},
            {"$sort": {"count": -1}}
        ]
        
        channel_stats = list(db.news.aggregate(pipeline))
        
        # Limit sample titles to first 3
        for stat in channel_stats:
            if stat["sample_titles"]:
                stat["sample_titles"] = stat["sample_titles"][:3]
        
        # Get summary statistics
        total_items = db.news.count_documents({})
        items_with_summaries = db.news.count_documents({"summary": {"$exists": True, "$ne": None}})
        items_with_transcripts = db.news.count_documents({"transcript": {"$exists": True, "$ne": None}})
        
        return {
            "total_items": total_items,
            "items_with_summaries": items_with_summaries,
            "items_with_transcripts": items_with_transcripts,
            "summary_coverage": f"{(items_with_summaries/total_items*100):.1f}%" if total_items > 0 else "0%",
            "transcript_coverage": f"{(items_with_transcripts/total_items*100):.1f}%" if total_items > 0 else "0%",
            "channels": channel_stats,
            "recent_items": db.news.count_documents({
                "cached_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            })
        }
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return {"error": str(e)}

# Add endpoint to get summary statistics
@app.get("/summary_stats")
async def get_summary_statistics():
    """Get statistics about summaries in the database"""
    try:
        # Aggregate summary statistics
        pipeline = [
            {
                "$group": {
                    "_id": "$channel_id",
                    "channel_name": {"$first": "$channel_name"},
                    "total_items": {"$sum": 1},
                    "items_with_summaries": {
                        "$sum": {"$cond": [{"$ne": ["$summary", None]}, 1, 0]}
                    },
                    "items_with_transcripts": {
                        "$sum": {"$cond": [{"$ne": ["$transcript", None]}, 1, 0]}
                    },
                    "latest_summary": {"$max": "$summary_created_at"}
                }
            },
            {"$sort": {"total_items": -1}}
        ]
        
        channel_summary_stats = list(db.news.aggregate(pipeline))
        
        # Calculate coverage percentages
        for stat in channel_summary_stats:
            total = stat["total_items"]
            stat["summary_coverage"] = f"{(stat['items_with_summaries']/total*100):.1f}%" if total > 0 else "0%"
            stat["transcript_coverage"] = f"{(stat['items_with_transcripts']/total*100):.1f}%" if total > 0 else "0%"
        
        # Overall statistics
        total_items = db.news.count_documents({})
        total_summaries = db.news.count_documents({"summary": {"$exists": True, "$ne": None}})
        total_transcripts = db.news.count_documents({"transcript": {"$exists": True, "$ne": None}})
        
        # Recent activity
        recent_summaries = db.news.count_documents({
            "summary_created_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        })
        
        return {
            "overall_stats": {
                "total_items": total_items,
                "total_summaries": total_summaries,
                "total_transcripts": total_transcripts,
                "overall_summary_coverage": f"{(total_summaries/total_items*100):.1f}%" if total_items > 0 else "0%",
                "overall_transcript_coverage": f"{(total_transcripts/total_items*100):.1f}%" if total_items > 0 else "0%",
                "recent_summaries_24h": recent_summaries
            },
            "by_channel": channel_summary_stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting summary statistics: {e}")
        return {"error": str(e)}

# Add endpoint to clear cache for specific channels
@app.delete("/clear_cache")
async def clear_cache(
    channel_id: str | None = Query(None, description="Clear cache for specific channel, or leave empty for all"),
    confirm: bool = Query(False, description="Must be True to actually delete")
):
    """Clear cached data"""
    if not confirm:
        return {
            "message": "Add ?confirm=true to actually delete data",
            "warning": "This action cannot be undone"
        }
    
    try:
        if channel_id:
            # Clear specific channel
            result = db.news.delete_many({"channel_id": {"$eq": channel_id}})
            return {
                "message": f"Cleared {result.deleted_count} items for channel {channel_id}",
                "channel_id": channel_id
            }
        else:
            # Clear all cache
            result = db.news.delete_many({})
            return {
                "message": f"Cleared all {result.deleted_count} cached items",
                "warning": "All cache cleared"
            }
            
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {e}")

# Add endpoint to clear only summaries (keep news items but remove summaries)
@app.delete("/clear_summaries")
async def clear_summaries(
    channel_id: str | None = Query(None, description="Clear summaries for specific channel, or leave empty for all"),
    confirm: bool = Query(False, description="Must be True to actually delete summaries")
):
    """Clear only summaries from cached data (keeps news items)"""
    if not confirm:
        return {
            "message": "Add ?confirm=true to actually delete summaries",
            "warning": "This action cannot be undone"
        }
    
    try:
        filter_query = {}
        if channel_id:
            filter_query["channel_id"] = {"$eq": channel_id}
        
        # Remove summary fields but keep the news items
        result = db.news.update_many(
            filter_query,
            {
                "$unset": {
                    "summary": "",
                    "summary_created_at": "",
                    "summary_created_by": "",
                    "summary_status": "",
                    "previous_summary_backup": ""
                }
            }
        )
        
        return {
            "message": f"Cleared summaries from {result.modified_count} items",
            "channel_id": channel_id if channel_id else "all channels",
            "items_modified": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing summaries: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing summaries: {e}")


# Health check endpoint (enhanced with summarization model status)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.command('ping')
        
        # Get cache statistics
        total_cached = db.news.count_documents({})
        recent_cached = db.news.count_documents({
            "cached_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        })
        
        # Get summary statistics
        total_summaries = db.news.count_documents({"summary": {"$exists": True, "$ne": None}})
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "connected",
            "summarization_model": "loaded" if summarizer else "failed",
            "cache_stats": {
                "total_cached_items": total_cached,
                "recent_cached_items": recent_cached,
                "total_summaries": total_summaries,
                "summary_coverage": f"{(total_summaries/total_cached*100):.1f}%" if total_cached > 0 else "0%"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.get("/")
def root():
    return {
        "message": "FastAPI NewsByte AI with Summarization is running!",
        "features": [
            "User Authentication",
            "YouTube News Caching",
            "AI-Powered Summarization", 
            "Channel-specific Filtering",
            "Batch Processing"
        ],
        "endpoints": {
            "auth": ["/signup", "/login", "/users/me"],
            "news": ["/get_latest_news", "/get_cached_news", "/get_news_by_channel/{channel_id}"],
            "summarization": ["/summarize_news/{video_id}", "/get_summary/{video_id}", "/batch_summarize"],
            "admin": ["/debug_cache", "/summary_stats", "/clear_cache", "/clear_summaries"]
        }
    }