import json
from transformers import pipeline
import sys

# Fix Windows encoding issue
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def test_small_model(news_text=None):
    """
    Run a small summarization model and return results as a dictionary (JSON-like).
    """

    try:
        summarizer = pipeline(
            "summarization", 
            model="facebook/bart-large-cnn",
            device=-1  # Use CPU
        )

        # Default test input if none provided
        if not news_text:
            news_text = """
            Training camp practice number six for the New York Giants is underway and it unfortunately comes with some bad news as Malik Neighbors had to leave practice with an apparent shoulder injury and we're going to react to that as we got some new information from Ian Rapaort. First though, send Malik Neighbors the good vibes. If there's any player on this team that they can't afford to get hurt, it's him, Dexter Lawrence, and Andrew Thomas. So, send leak some good vibes. Hit that thumbs up icon right now. [Music] Welcome in to New York Giants now by chat sports. I am your host Marshall Green. Let's dive into it. On Tuesday's practice, Malik Neighbors had to leave early due to a shoulder injury. At this moment, we are unsure how severe the injury is, but let's just tell you what we know. Jordan tweeting this out saying Muik Neighbors banged up on a run play on the ground for a few seconds, grabbed at his shoulder as he walked off. Something to monitor. He then followed that up by saying Malik Neighbors went into the fieldhouse with the Giants head trainer Ronnie Barnes. And then Ronnie came out outside and gave head coach Brian Dable an update.  
            """

        summary_result = summarizer(
            news_text, 
            max_length=100, 
            min_length=30, 
            do_sample=False
        )

        summary = summary_result[0]['summary_text']

        return {
            "status": "success",
            "original_text": news_text.strip(),
            "summary": summary,
            "timestamp": "2025-01-26",
            
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "timestamp": "2025-01-26"
        }


# Example usage:
if __name__ == "__main__":
    result = test_small_model()
    print(json.dumps(result, indent=2, ensure_ascii=False))  # You can remove this too if it's being imported elsewhere
    