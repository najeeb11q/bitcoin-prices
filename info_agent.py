import os
import json
import time
import requests
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables from .env file
load_dotenv()

class BitcoinNewsAgent:
    def __init__(self):
        """
        Initialize the BitcoinNewsAgent with necessary API keys from environment variables
        """
        # Load API keys from environment variables
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.hf_api_key = os.getenv("HF_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        # Verify that necessary API keys and Supabase credentials are available
        if not self.brave_api_key:
            raise ValueError("API key for Brave not found in environment variables")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        
        # Initialize Hugging Face client
        self.hf_client = InferenceClient(token=self.hf_api_key)
        
        # Initialize Supabase client
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    def generate_bitcoin_query(self):
        """
        Generate a search query related to Bitcoin and finance
        
        Returns:
            A generated search query
        """
        # List of predefined Bitcoin and finance related queries
        bitcoin_queries = [
            "latest Bitcoin price analysis",
            "Bitcoin market trends this week",
            "cryptocurrency finance news Bitcoin",
            "Bitcoin investment strategies",
            "Bitcoin and traditional finance integration",
            "Bitcoin ETF performance",
            "Bitcoin mining profitability",
            "Bitcoin regulatory news",
            "Bitcoin institutional adoption"
        ]
        
        # If HF API key is available, use AI to generate query
        if self.hf_api_key:
            try:
                system_prompt = "You are a helpful assistant for generating Bitcoin and finance-related search queries."
                user_prompt = "Generate a specific search query about recent Bitcoin price movements, market trends, or financial integration."
                full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
                
                response = self.hf_client.text_generation(
                    prompt=full_prompt,
                    model="mistralai/Mistral-7B-Instruct-v0.2",
                    max_new_tokens=50,
                    temperature=0.7
                )
                
                # Remove quotes if present
                query = response.strip().strip('"\'')
                return query
            except Exception as e:
                print(f"Error generating query with AI: {e}")
                # Fall back to random query from list
                import random
                return random.choice(bitcoin_queries)
        else:
            # Use a random query from the predefined list if no API key
            import random
            return random.choice(bitcoin_queries)

    def search_brave(self, query, count=5):
        """
        Search Bitcoin and finance news using Brave Search API
        
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
            
    def summarize_article(self, article):
        """
        Summarize a news article using Hugging Face API
        
        Args:
            article: Article data with title and description
            
        Returns:
            A summarized version of the article
        """
        if not self.hf_api_key:
            # If no API key, just return the original description
            return article.get("description", "No description available")
        
        try:
            title = article.get("title", "")
            description = article.get("description", "")
            
            prompt = f"""Summarize this financial news article about Bitcoin in 2-3 sentences:
            Title: {title}
            Description: {description}
            
            Summary:"""
            
            summary = self.hf_client.text_generation(
                prompt=prompt,
                model="mistralai/Mistral-7B-Instruct-v0.2",
                max_new_tokens=100,
                temperature=0.3
            )
            
            return summary.strip()
        except Exception as e:
            print(f"Error summarizing article: {e}")
            return article.get("description", "No description available")
            
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
            
            # Simple data structure without user_id since RLS is disabled
            data = {
                "timestamp": current_time,
                "finance_info": item
            }
            
            try:
                result = self.supabase.table("eco_info").insert(data).execute()
                
                if hasattr(result, 'data') and result.data:
                    success_count += 1
                else:
                    print(f"Error storing item: {result}")
            except Exception as e:
                print(f"Supabase error: {e}")
                
        return success_count
        
    def fetch_bitcoin_news(self, num_queries=3):
        """
        Main function to fetch and store Bitcoin financial news
        
        Args:
            num_queries: Number of queries to generate and search for
            
        Returns:
            Total number of news items stored
        """
        total_stored = 0
        
        for i in range(num_queries):
            # Generate a Bitcoin and finance related query
            query = self.generate_bitcoin_query()
            print(f"Searching for: {query}")
            
            # Search for the generated query in Brave Search
            search_results = self.search_brave(query)
            
            news_items = []
            for item in search_results:
                # Summarize each article
                summary = self.summarize_article(item)
                
                # Format the news item for database storage
                formatted_text = f"Query: {query}\n"
                formatted_text += f"Title: {item.get('title', '')}\n"
                formatted_text += f"Summary: {summary}\n"
                formatted_text += f"URL: {item.get('url', '')}\n"
                formatted_text += f"Source: {item.get('source', '')}\n"
                formatted_text += f"Published: {item.get('published', '')}"
                
                news_items.append(formatted_text)
            
            # Store the summarized news items
            stored_count = self.store_in_supabase(news_items)
            
            total_stored += stored_count
            print(f"Stored {stored_count} items for query: {query}")
            
            # Add a small delay to avoid rate limiting
            time.sleep(2)
            
        return total_stored

# Example usage
if __name__ == "__main__":
    try:
        agent = BitcoinNewsAgent()
        total = agent.fetch_bitcoin_news()
        print(f"Total news items stored: {total}")
    except Exception as e:
        print(f"Error: {e}")