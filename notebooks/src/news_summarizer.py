"""
AI News Summarizer - Production Version
Author: Your Team
Description: Complete news summarization system using Tavily API
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from tavily import TavilyClient
from dotenv import load_dotenv
import json

class AINewsSummarizer:
    """
    AI-powered news summarization system using Tavily search API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the news summarizer with Tavily API key"""
        load_dotenv()
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        
        if not self.api_key:
            raise ValueError("Tavily API key not found. Please set TAVILY_API_KEY in .env file")
        
        self.client = TavilyClient(api_key=self.api_key)
        self.categories = {
            'ai': 'artificial intelligence AI ChatGPT machine learning generative AI',
            'tech': 'technology latest tech innovations startups software hardware',
            'business': 'business technology companies IPO funding venture capital',
            'crypto': 'cryptocurrency bitcoin blockchain crypto DeFi NFT',
            'cybersecurity': 'cybersecurity data breach hacking security vulnerability',
            'startup': 'startup funding unicorn IPO venture capital new companies'
        }
    
    def search_news(self, query: str, max_results: int = 5, days: int = 7) -> List[Dict]:
        """
        Search for news articles using Tavily API
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results
            days (int): Number of days to look back
            
        Returns:
            List[Dict]: List of news articles
        """
        try:
            results = self.client.search(
                query=query,
                max_results=max_results,
                days=days,
                topic="news"
            )
            return results.get('results', [])
        except Exception as e:
            print(f"❌ Error searching news: {e}")
            return []
    
    def get_news_by_category(self, category: str, max_results: int = 5, days: int = 7) -> List[Dict]:
        """
        Get news articles by predefined category
        
        Args:
            category (str): News category (ai, tech, business, etc.)
            max_results (int): Maximum number of results
            days (int): Number of days to look back
            
        Returns:
            List[Dict]: List of news articles
        """
        query = self.categories.get(category.lower(), f'{category} technology news')
        return self.search_news(query, max_results, days)
    
    def clean_article_content(self, content: str, max_length: int = 400) -> str:
        """
        Clean and format article content
        
        Args:
            content (str): Raw article content
            max_length (int): Maximum length of content
            
        Returns:
            str: Cleaned content
        """
        if not content:
            return "No summary available"
        
        # Remove excessive whitespace and newlines
        clean_content = ' '.join(content.split())
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            'Image:', 'Share:', 'Follow us:', 'Subscribe:', 'Click here:',
            'Read more:', 'Source:', 'Copyright', '©', 'All rights reserved'
        ]
        
        for pattern in unwanted_patterns:
            clean_content = clean_content.replace(pattern, '')
        
        # Truncate if too long (without adding ...)
        if len(clean_content) > max_length:
            # Find the last complete sentence within limit
            truncated = clean_content[:max_length]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            
            # Use the last complete sentence if found
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > max_length * 0.7:  # At least 70% of max length
                clean_content = truncated[:last_sentence_end + 1]
            else:
                clean_content = truncated
        
        return clean_content.strip()
    
    def format_article(self, article: Dict, index: int) -> str:
        """
        Format a single article for display
        
        Args:
            article (Dict): Article data
            index (int): Article index
            
        Returns:
            str: Formatted article string
        """
        title = article.get('title', 'Untitled')
        url = article.get('url', 'No URL')
        content = article.get('content', 'No summary available')
        score = article.get('score', 'N/A')
        
        # Use the enhanced cleaning function
        clean_content = self.clean_article_content(content, max_length=350)
        
        formatted = f"""
{index}. 📌 {title}
   🔗 Source: {url}
   📝 Summary: {clean_content}
   ⭐ Relevance Score: {score}
   {'-' * 80}"""
        
        return formatted
    
    def generate_category_report(self, category: str, max_results: int = 5, days: int = 7) -> str:
        """
        Generate a formatted report for a specific category
        
        Args:
            category (str): News category
            max_results (int): Maximum number of results
            days (int): Number of days to look back
            
        Returns:
            str: Formatted category report
        """
        articles = self.get_news_by_category(category, max_results, days)
        
        if not articles:
            return f"\n❌ No {category.upper()} news found for the last {days} days.\n"
        
        # Header
        report = f"""
{'=' * 80}
📰 {category.upper()} NEWS SUMMARY
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 Found: {len(articles)} articles from last {days} days
{'=' * 80}"""
        
        # Add articles
        for i, article in enumerate(articles, 1):
            report += self.format_article(article, i)
        
        report += "\n" + "=" * 80 + "\n"
        return report
    
    def generate_comprehensive_report(self, categories: List[str] = None, max_results: int = 3, days: int = 7) -> str:
        """
        Generate a comprehensive multi-category news report
        
        Args:
            categories (List[str]): List of categories to include
            max_results (int): Maximum results per category
            days (int): Number of days to look back
            
        Returns:
            str: Complete formatted report
        """
        if categories is None:
            categories = ['ai', 'tech', 'business']
        
        # Report header
        report = f"""
{'#' * 100}
🤖 AI NEWS SUMMARY REPORT
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 Categories: {', '.join(cat.upper() for cat in categories)}
⏰ Time Range: Last {days} days
{'#' * 100}
"""
        
        # Generate each category
        for category in categories:
            print(f"🔍 Fetching {category.upper()} news...")
            category_report = self.generate_category_report(category, max_results, days)
            report += category_report
        
        # Footer
        report += f"""
{'#' * 100}
✅ REPORT GENERATION COMPLETED
📊 Total Categories: {len(categories)}
🤖 Powered by AI News Summarizer
{'#' * 100}
"""
        
        return report
    
    def save_report(self, report: str, filename: str = None) -> str:
        """
        Save report to file
        
        Args:
            report (str): Report content
            filename (str): Optional custom filename
            
        Returns:
            str: Saved filename
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"outputs/ai_news_report_{timestamp}.txt"
        
        try:
            # Ensure outputs directory exists
            os.makedirs('outputs', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(report)
            
            print(f"💾 Report saved successfully: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return ""
    
    def get_trending_topics(self, max_results: int = 10) -> List[Dict]:
        """
        Get trending technology topics
        
        Args:
            max_results (int): Maximum number of results
            
        Returns:
            List[Dict]: List of trending articles
        """
        trending_query = "trending technology news today latest developments"
        return self.search_news(trending_query, max_results, days=1)

# Example usage functions
def main():
    """Main function to demonstrate the news summarizer"""
    try:
        # Initialize summarizer
        summarizer = AINewsSummarizer()
        print("✅ AI News Summarizer initialized successfully!")
        
        # Generate comprehensive report
        print("\n🚀 Generating comprehensive news report...")
        report = summarizer.generate_comprehensive_report(
            categories=['ai', 'tech', 'business'],
            max_results=3,
            days=7
        )
        
        # Display report
        print(report)
        
        # Save report
        filename = summarizer.save_report(report)
        
        print(f"\n🎉 News summary completed! Check {filename}")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")

if __name__ == "__main__":
    main()