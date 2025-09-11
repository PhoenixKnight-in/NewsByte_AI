import os
import json
import sys
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
# Import the summarization function
from transformers import pipeline


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


# Initialize summarization models (load both at startup)
summarizers = {}
model_info = {}

try:
    #try loading smaller versions
    # Only load one lightweight model at startup
    logger.info("Loading single lightweight model...")
    summarizer = pipeline(
        "summarization", 
        model="sshleifer/distilbart-cnn-6-3",  # Smaller version
        device=-1,
        framework="pt"
    )
    logger.info("Model loaded successfully")
    # Load DistilBART for shorter transcripts (better quality, faster)
    # logger.info("Loading DistilBART model for short transcripts...")
    # summarizers["distilbart"] = pipeline(
    #     "summarization", 
    #     model="sshleifer/distilbart-cnn-12-6",
    #     device=-1
    # )
    # model_info["distilbart"] = {
    #     "name": "DistilBART-CNN",
    #     "max_input_length": 1024,
    #     "optimal_for": "short_to_medium_transcripts",
    #     "quality": "high",
    #     "speed": "fast"
    # }
    # logger.info("DistilBART model loaded successfully")
    
    # # Load LED for longer transcripts (handles longer sequences)
    # logger.info("Loading LED model for long transcripts...")
    # summarizers["led"] = pipeline(
    #     "summarization",
    #     model="allenai/led-base-16384",
    #     device=-1
    # )
    # model_info["led"] = {
    #     "name": "LED-base-16384",
    #     "max_input_length": 16384,
    #     "optimal_for": "long_transcripts",
    #     "quality": "good",
    #     "speed": "moderate"
    # }
    # logger.info("LED model loaded successfully")
    
    # logger.info("Both summarization models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load summarization models: {e}")
    summarizers = {}

# Fix Windows encoding issue
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def select_optimal_model(text_length):
    """
    Select the optimal summarization model based on text length
    
    Args:
        text_length (int): Length of the text in characters
        
    Returns:
        tuple: (model_key, model_pipeline, model_name)
    """
    # Threshold for model selection (roughly 800 words = 4000 characters)
    # LONG_TEXT_THRESHOLD = 4000
    
    # if text_length > LONG_TEXT_THRESHOLD:
    #     # Use LED for longer transcripts
    #     return "led", summarizers.get("led"), model_info["led"]["name"]
    # else:
    #     # Use DistilBART for shorter transcripts
    return "distilbart", summarizers.get("distilbart"), model_info["distilbart"]["name"]

def Phoenix_Sum(news_text=None):
    """
    Run an intelligent summarization system that automatically selects the best model
    based on transcript length for optimal quality and performance.
    """
    try:
        if not summarizers:
            return {
                "status": "error",
                "error_message": "No summarization models available",
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": "none"
            }

        # Validate input
        if not news_text or len(news_text.strip()) < 50:
            return {
                "status": "error",
                "error_message": "Text too short for meaningful summarization (minimum 50 characters)",
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": "none"
            }

        # Clean and prepare text
        news_text = news_text.strip()
        original_length = len(news_text)
        
        # Select optimal model based on text length
        model_key, selected_model, model_name = select_optimal_model(original_length)
        
        if not selected_model:
            return {
                "status": "error",
                "error_message": f"Selected model ({model_key}) not available",
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": model_name
            }
        
        logger.info(f"Selected model: {model_name} for text length: {original_length}")
        
        # Get model-specific parameters
        if model_key == "led":
            max_input_length = 14000  # Conservative limit for LED (allows for tokenization overhead)
            # LED can handle longer sequences, so less aggressive truncation
            if len(news_text) > max_input_length:
                truncated_text = news_text[:max_input_length]
                last_sentence = truncated_text.rfind('.')
                if last_sentence > max_input_length * 0.8:
                    news_text = truncated_text[:last_sentence + 1]
                else:
                    news_text = truncated_text + "..."
        else:  # DistilBART
            max_input_length = 1024  # DistilBART token limit
            if len(news_text) > max_input_length:
                truncated_text = news_text[:max_input_length]
                last_sentence = truncated_text.rfind('.')
                if last_sentence > 500:
                    news_text = truncated_text[:last_sentence + 1]
                else:
                    news_text = truncated_text + "..."
        
        # Determine optimal summary length based on input length and model
        if len(news_text) < 200:
            max_length, min_length = 50, 20
        elif len(news_text) < 500:
            max_length, min_length = 80, 30
        elif len(news_text) < 1000:
            max_length, min_length = 120, 40
        elif len(news_text) < 3000:
            max_length, min_length = 150, 50
        else:
            # For very long texts (LED territory)
            max_length, min_length = 200, 60
        
        # Model-specific parameters
        if model_key == "led":
            # LED-specific parameters for longer sequences
            summary_result = selected_model(
                news_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                early_stopping=True,
                no_repeat_ngram_size=3,
                num_beams=2  # Reduce beams for LED to speed up processing
            )
        else:  # DistilBART
            # DistilBART-specific parameters for better quality on shorter texts
            summary_result = selected_model(
                news_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                early_stopping=True,
                no_repeat_ngram_size=3,
                num_beams=4  # Higher beams for DistilBART for better quality
            )

        summary = summary_result[0]['summary_text']
        
        # Quality metrics
        compression_ratio = len(summary) / len(news_text)
        
        return {
            "status": "success",
            "original_text": news_text,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
            "model_used": model_name,
            "model_key": model_key,
            "model_selection_reason": f"Text length {original_length} chars -> {model_name}",
            "metrics": {
                "original_length": original_length,
                "processed_length": len(news_text),
                "summary_length": len(summary),
                "compression_ratio": round(compression_ratio, 2),
                "was_truncated": original_length > max_input_length
            }
        }

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "model_used": model_name if 'model_name' in locals() else "unknown"
        }

def batch_summarize(text_list):
    """
    Efficiently summarize multiple texts in batch with dynamic model selection
    """
    if not summarizers:
        return {"error": "Models not available"}
    
    try:
        results = []
        model_usage_stats = {"distilbart": 0, "led": 0}
        
        for i, text in enumerate(text_list):
            logger.info(f"Processing item {i+1}/{len(text_list)}")
            result = Phoenix_Sum(text)
            results.append(result)
            
            # Track model usage
            if result["status"] == "success":
                model_key = result.get("model_key", "unknown")
                if model_key in model_usage_stats:
                    model_usage_stats[model_key] += 1
        
        return {
            "batch_results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "model_usage_stats": model_usage_stats
        }
        
    except Exception as e:
        return {"error": str(e)}
    

def test_summarization_quality():
    """
    Test function to evaluate summarization quality with dynamic model selection
    """
    # Short text test
    short_text = """
    Training camp practice number six for the New York Giants is underway and it unfortunately comes with some bad news as Malik Neighbors had to leave practice with an apparent shoulder injury.
    """
    
    # Long text test
    long_text = """
    Training camp practice number six for the New York Giants is underway and it unfortunately comes with some bad news as Malik Neighbors had to leave practice with an apparent shoulder injury and we're going to react to that as we got some new information from Ian Rapaort. First though, send Malik Neighbors the good vibes. If there's any player on this team that they can't afford to get hurt, it's him, Dexter Lawrence, and Andrew Thomas. So, send leak some good vibes. Hit that thumbs up icon right now. Welcome in to New York Giants now by chat sports. I am your host Marshall Green. Let's dive into it. On Tuesday's practice, Malik Neighbors had to leave early due to a shoulder injury. At this moment, we are unsure how severe the injury is, but let's just tell you what we know. Jordan tweeting this out saying Muik Neighbors banged up on a run play on the ground for a few seconds, grabbed at his shoulder as he walked off. Something to monitor. He then followed that up by saying Malik Neighbors went into the fieldhouse with the Giants head trainer Ronnie Barnes. And then Ronnie came out outside and gave head coach Brian Dable an update. The injury occurred during a routine running play where Neighbors was participating in drills with the offensive unit. Witnesses reported that he appeared to land awkwardly after making a catch and immediately signaled to the sidelines. The training staff quickly responded and escorted him off the field for evaluation. This development is particularly concerning for Giants fans as Neighbors has been one of the standout performers during the early stages of training camp. His chemistry with the quarterback has been evident, and losing him for any extended period would be a significant blow to the team's offensive preparations for the upcoming season.
    """ * 3  # Make it longer to trigger LED
    
    print("Testing short text (should use DistilBART):")
    result_short = Phoenix_Sum(short_text)
    print(json.dumps({
        "model_used": result_short.get("model_used"),
        "model_selection_reason": result_short.get("model_selection_reason"),
        "status": result_short.get("status"),
        "text_length": len(short_text)
    }, indent=2))
    
    print("\nTesting long text (should use LED):")
    result_long = Phoenix_Sum(long_text)
    print(json.dumps({
        "model_used": result_long.get("model_used"),
        "model_selection_reason": result_long.get("model_selection_reason"), 
        "status": result_long.get("status"),
        "text_length": len(long_text)
    }, indent=2))
    
    return {"short_test": result_short, "long_test": result_long}

# Example usage and model comparison
if __name__ == "__main__":
    # Test the improved model
    result = test_summarization_quality()
    
    print(f"\nModel: {model_name}")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Summary: {result['summary']}")
        print(f"Compression: {result['metrics']['compression_ratio']}")

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