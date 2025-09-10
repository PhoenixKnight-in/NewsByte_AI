import json
from transformers import pipeline
import sys
import logging
from datetime import datetime
from huggingface_hub import login
from dotenv import load_dotenv
import os
load_dotenv()
# Fix Windows encoding issue
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# login to hugging face
login(token =os.getenv("HUGGING_FACE"))


# Initialize the best model for news summarization
try:
    # # Option 1: Pegasus (best for news) - Use this for production
    # summarizer = pipeline(
    #     "summarization", 
    #     model="google/pegasus-cnn_dailymail",  # Specifically trained on news
    #     device=-1,  # CPU
    #     framework="pt"
    # )
    # model_name = "Pegasus CNN/DailyMail"
    
    #Option 2: If you want faster inference, use DistilBART instead:
    summarizer = pipeline(
        "summarization", 
        model="sshleifer/distilbart-cnn-12-6",
        device=-1
    )
    model_name = "DistilBART"
    
    # #Option 3: For very long transcripts (>1024 tokens), use LED:
    # summarizer = pipeline(
    #     "summarization",
    #     model="allenai/led-base-16384",
    #     device=-1
    # )
    # model_name = "LED-base"
    
    logger.info(f"Summarization model '{model_name}' loaded successfully")
    
except Exception as e:
    logger.error(f"Failed to load summarization model: {e}")
    summarizer = None
    model_name = "None"

def Falcon_Sum(news_text=None):
    """
    Run an improved summarization model optimized for news content.
    Returns abstractive summaries that capture core content, not just paraphrasing.
    """
    try:
        if not summarizer:
            return {
                "status": "error",
                "error_message": "Summarization model not available",
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": model_name
            }

        # Validate input
        if not news_text or len(news_text.strip()) < 50:
            return {
                "status": "error",
                "error_message": "Text too short for meaningful summarization (minimum 50 characters)",
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": model_name
            }

        # Clean and prepare text
        news_text = news_text.strip()
        original_length = len(news_text)
        
        # Handle long texts intelligently
        max_input_length = 1024  # BART/Pegasus token limit
        if len(news_text) > max_input_length:
            # Try to find a good breaking point (sentence boundary)
            truncated_text = news_text[:max_input_length]
            last_sentence = truncated_text.rfind('.')
            if last_sentence > 500:  # If we find a reasonable sentence boundary
                news_text = truncated_text[:last_sentence + 1]
            else:
                news_text = truncated_text + "..."
        
        # Determine optimal summary length based on input length
        if len(news_text) < 200:
            max_length, min_length = 50, 20
        elif len(news_text) < 500:
            max_length, min_length = 80, 30
        elif len(news_text) < 1000:
            max_length, min_length = 120, 40
        else:
            max_length, min_length = 150, 50

        # Generate summary with optimized parameters
        summary_result = summarizer(
            news_text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False,  # Deterministic output
            early_stopping=True,
            no_repeat_ngram_size=3,  # Avoid repetition
            num_beams=4  # Better quality with beam search
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
            "model_used": model_name
        }

def batch_summarize(text_list):
    """
    Efficiently summarize multiple texts in batch
    """
    if not summarizer:
        return {"error": "Model not available"}
    
    try:
        results = []
        for i, text in enumerate(text_list):
            logger.info(f"Processing item {i+1}/{len(text_list)}")
            result = Falcon_Sum(text)
            results.append(result)
        
        return {
            "batch_results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"])
        }
        
    except Exception as e:
        return {"error": str(e)}

# Test function to compare models
def test_summarization_quality():
    """
    Test function to evaluate summarization quality
    """
    test_text = """
    Training camp practice number six for the New York Giants is underway and it unfortunately comes with some bad news as Malik Neighbors had to leave practice with an apparent shoulder injury and we're going to react to that as we got some new information from Ian Rapaort. First though, send Malik Neighbors the good vibes. If there's any player on this team that they can't afford to get hurt, it's him, Dexter Lawrence, and Andrew Thomas. So, send leak some good vibes. Hit that thumbs up icon right now. Welcome in to New York Giants now by chat sports. I am your host Marshall Green. Let's dive into it. On Tuesday's practice, Malik Neighbors had to leave early due to a shoulder injury. At this moment, we are unsure how severe the injury is, but let's just tell you what we know. Jordan tweeting this out saying Muik Neighbors banged up on a run play on the ground for a few seconds, grabbed at his shoulder as he walked off. Something to monitor. He then followed that up by saying Malik Neighbors went into the fieldhouse with the Giants head trainer Ronnie Barnes. And then Ronnie came out outside and gave head coach Brian Dable an update.
    """
    
    result = Falcon_Sum(test_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

# Example usage and model comparison
if __name__ == "__main__":
    # Test the improved model
    result = test_summarization_quality()
    
    print(f"\nModel: {model_name}")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Summary: {result['summary']}")
        print(f"Compression: {result['metrics']['compression_ratio']}")