import json
from transformers import pipeline
import sys

# Fix Windows encoding issue
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def test_small_model():
    """
    Test with smaller model for quick testing
    Returns output in JSON format as requested
    """
    
    print("Loading Small Summarization Model...")
    print("="*50)
    
    try:
        # Use pre-trained summarization pipeline (much smaller - ~500MB)
        summarizer = pipeline(
            "summarization", 
            model="facebook/bart-large-cnn",
            device=-1  # Use CPU
        )
        
        print("Model loaded successfully!")
        
        # Test news text for summarization
        news_text = """
        The Indian government announced new policies for renewable energy sector today. 
        The policy includes subsidies for solar panel installations and wind energy projects. 
        This initiative is expected to create thousands of jobs and reduce carbon emissions significantly. 
        The Prime Minister said this move will help India achieve its climate goals by 2030. 
        Industry experts believe this could revolutionize India's energy landscape and attract 
        foreign investments in the green energy sector.
        """
        
        print("Generating summary...")
        
        # Generate summary
        summary_result = summarizer(
            news_text, 
            max_length=100, 
            min_length=30, 
            do_sample=False
        )
        
        # Extract summary text
        summary = summary_result[0]['summary_text']
        
        # Return in JSON format as requested
        result = {
            "status": "success",
            "model_used": "facebook/bart-large-cnn",
            "original_text": news_text.strip(),
            "summary": summary,
            "timestamp": "2025-01-26",
            "model_type": "BART (Facebook)"
        }
        
        print("Summary generated successfully!")
        print("\n" + "="*60)
        print("FINAL OUTPUT (JSON FORMAT):")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error_message": str(e),
            "timestamp": "2025-01-26"
        }
        print(f"Error: {e}")
        print(json.dumps(error_result, indent=2))
        return error_result

if __name__ == "__main__":
    print("Testing Small Model for News Summarization")
    print("This will download ~500MB instead of 14GB")
    print("="*50)
    test_small_model()