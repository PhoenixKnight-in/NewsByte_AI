"""
AI News Summary App - Main Entry Point
Team Project: AiNewsSummary
Description: Command-line interface for AI news summarization
"""

import argparse
import sys
import os
from datetime import datetime
from news_summarizer import AINewsSummarizer

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🤖 AI NEWS SUMMARIZER 📰                   ║
    ║                     Team Project Version                     ║
    ║              Powered by Tavily API & Python                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def interactive_mode():
    """Run the app in interactive mode"""
    print_banner()
    print("🎯 Welcome to Interactive Mode!")
    print("Choose an option:")
    print("1. Generate comprehensive report")
    print("2. Search specific category")
    print("3. Custom topic search")
    print("4. Get trending topics")
    print("5. Exit")
    
    summarizer = AINewsSummarizer()
    
    while True:
        try:
            choice = input("\n👉 Enter your choice (1-5): ").strip()
            
            if choice == '1':
                print("\n🚀 Generating comprehensive report...")
                categories = input("Enter categories (comma-separated) or press Enter for default [ai,tech,business]: ").strip()
                
                if categories:
                    cat_list = [cat.strip() for cat in categories.split(',')]
                else:
                    cat_list = ['ai', 'tech', 'business']
                
                days = input("Enter number of days to look back (default: 7): ").strip()
                days = int(days) if days.isdigit() else 7
                
                report = summarizer.generate_comprehensive_report(cat_list, max_results=3, days=days)
                print(report)
                
                save = input("Save report to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = summarizer.save_report(report)
                    print(f"✅ Report saved: {filename}")
            
            elif choice == '2':
                print("\nAvailable categories:")
                for cat in summarizer.categories.keys():
                    print(f"  - {cat}")
                
                category = input("Enter category: ").strip()
                max_results = input("Max results (default: 5): ").strip()
                max_results = int(max_results) if max_results.isdigit() else 5
                
                report = summarizer.generate_category_report(category, max_results)
                print(report)
            
            elif choice == '3':
                topic = input("Enter custom topic: ").strip()
                max_results = input("Max results (default: 5): ").strip()
                max_results = int(max_results) if max_results.isdigit() else 5
                
                articles = summarizer.search_news(topic, max_results)
                if articles:
                    for i, article in enumerate(articles, 1):
                        print(summarizer.format_article(article, i))
                else:
                    print("❌ No articles found for this topic")
            
            elif choice == '4':
                print("🔥 Fetching trending topics...")
                trending = summarizer.get_trending_topics(max_results=5)
                if trending:
                    print("\n📈 TRENDING TECHNOLOGY TOPICS")
                    print("=" * 50)
                    for i, article in enumerate(trending, 1):
                        print(summarizer.format_article(article, i))
                else:
                    print("❌ No trending topics found")
            
            elif choice == '5':
                print("👋 Thank you for using AI News Summarizer!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def command_line_mode(args):
    """Run the app in command-line mode"""
    print_banner()
    
    try:
        summarizer = AINewsSummarizer()
        
        if args.category:
            print(f"🔍 Generating {args.category} news report...")
            report = summarizer.generate_category_report(
                args.category, 
                args.max_results, 
                args.days
            )
            print(report)
            
            if args.save:
                summarizer.save_report(report)
                
        elif args.topic:
            print(f"🔍 Searching for: {args.topic}")
            articles = summarizer.search_news(args.topic, args.max_results, args.days)
            
            if articles:
                for i, article in enumerate(articles, 1):
                    print(summarizer.format_article(article, i))
            else:
                print("❌ No articles found")
                
        elif args.comprehensive:
            categories = args.categories.split(',') if args.categories else ['ai', 'tech', 'business']
            print(f"🚀 Generating comprehensive report for: {', '.join(categories)}")
            
            report = summarizer.generate_comprehensive_report(
                categories, 
                args.max_results, 
                args.days
            )
            print(report)
            
            if args.save:
                summarizer.save_report(report)
                
        elif args.trending:
            print("🔥 Fetching trending topics...")
            trending = summarizer.get_trending_topics(args.max_results)
            
            if trending:
                print("\n📈 TRENDING TECHNOLOGY TOPICS")
                print("=" * 50)
                for i, article in enumerate(trending, 1):
                    print(summarizer.format_article(article, i))
            else:
                print("❌ No trending topics found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="AI News Summarizer - Get latest tech news summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -i                           # Interactive mode
  python main.py -c ai --save                 # AI news category
  python main.py -t "OpenAI ChatGPT" -r 5     # Custom topic search
  python main.py --comprehensive --save       # Full report
  python main.py --trending -r 10             # Trending topics
        """
    )
    
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('-c', '--category', type=str,
                       help='News category (ai, tech, business, crypto, etc.)')
    parser.add_argument('-t', '--topic', type=str,
                       help='Custom topic to search')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Generate comprehensive multi-category report')
    parser.add_argument('--trending', action='store_true',
                       help='Get trending technology topics')
    parser.add_argument('--categories', type=str,
                       help='Comma-separated list of categories for comprehensive report')
    parser.add_argument('-r', '--max-results', type=int, default=5,
                       help='Maximum number of results per category (default: 5)')
    parser.add_argument('-d', '--days', type=int, default=7,
                       help='Number of days to look back (default: 7)')
    parser.add_argument('--save', action='store_true',
                       help='Save report to file')
    
    args = parser.parse_args()
    
    # If no arguments provided, run interactive mode
    if not any([args.category, args.topic, args.comprehensive, args.trending, args.interactive]):
        interactive_mode()
    elif args.interactive:
        interactive_mode()
    else:
        command_line_mode(args)

if __name__ == "__main__":
    main()