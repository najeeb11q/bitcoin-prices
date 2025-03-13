import os
import json
import time
import requests
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
from openai import OpenAI  # Updated import for OpenAI API >=1.0.0

# Load environment variables from .env file
load_dotenv()

class InfoAgent:
    def __init__(self):
        """
        Initialize the InfoAgent with necessary API keys from environment variables
        """
        # Load API keys from environment variables
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        # Verify that necessary API keys and Supabase credentials are available
        if not self.brave_api_key or not self.openai_api_key:
            raise ValueError("API keys for Brave or OpenAI not found in environment variables")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        
        # Initialize OpenAI client and Supabase client
        self.openai_client = OpenAI(api_key=self.openai_api_key)  # Updated for new OpenAI API
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    def generate_search_query(self, prompt="Generate a finance-related search query for the latest news"):
        """
        Use OpenAI to generate a dynamic search query based on a prompt
        
        Args:
            prompt: The prompt to send to OpenAI for generating a search query
        
        Returns:
            A generated search query
        """
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",  # You can also use "gpt-3.5-turbo" if preferred
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating finance-related search queries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()

    def search_brave(self, query, count=10):
        """
        Search financial news using Brave Search API
        
        Args:
            query: Search query string
            count: Number of results to return
            
        Returns:
            List of search results
        """
        url = "https://api.search.brave.com/res/v1/web/search"
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        
        params = {
            "q": query,
            "count": count,
            "search_lang": "en",
            "freshness": "past_week"  # Get recent news
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("web", {}).get("results", [])
        else:
            print(f"Error searching Brave: {response.status_code}")
            return []
            
    def extract_news_info(self, search_results):
        """
        Extract relevant news information from search results
        
        Args:
            search_results: List of search result items from Brave
            
        Returns:
            List of formatted news items
        """
        news_items = []
        
        for item in search_results:
            news_item = {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "published": item.get("published", ""),
                "source": item.get("source", "")
            }
            
            # Format the news item for database storage
            formatted_text = f"Title: {news_item['title']}\n"
            formatted_text += f"Description: {news_item['description']}\n"
            formatted_text += f"URL: {news_item['url']}\n"
            formatted_text += f"Source: {news_item['source']}\n"
            formatted_text += f"Published: {news_item['published']}"
            
            news_items.append(formatted_text)
            
        return news_items
        
    def store_in_supabase(self, news_items):
        """
        Store news items in Supabase database
        
        Args:
            news_items: List of formatted news items
            
        Returns:
            Number of items successfully stored
        """
        success_count = 0
        
        for item in news_items:
            current_time = datetime.now().isoformat()
            
            data = {
                "timestamp": current_time,
                "finance_info": item
            }
            
            result = self.supabase.table("eco_info").insert(data).execute()
            
            if hasattr(result, 'data') and result.data:
                success_count += 1
            else:
                print(f"Error storing item: {result}")
                
        return success_count
        
    def fetch_financial_news(self, num_queries=3):
        """
        Main function to fetch and store financial news
        
        Args:
            num_queries: Number of queries to generate via OpenAI and search for
            
        Returns:
            Total number of news items stored
        """
        total_stored = 0
        
        for i in range(num_queries):
            # Generate a search query using OpenAI
            query = self.generate_search_query(f"Generate a finance-related search query for the latest news ({i+1}/{num_queries})")
            print(f"Searching for: {query}")
            
            # Search for the generated query in Brave Search
            search_results = self.search_brave(query)
            news_items = self.extract_news_info(search_results)
            stored_count = self.store_in_supabase(news_items)
            
            total_stored += stored_count
            print(f"Stored {stored_count} items for query: {query}")
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
        return total_stored

# Example usage
if __name__ == "__main__":
    try:
        agent = InfoAgent()
        total = agent.fetch_financial_news()
        print(f"Total news items stored: {total}")
    except Exception as e:
        print(f"Error: {e}")