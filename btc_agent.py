import requests
import os
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fetch_btc_price_and_store():
    """
    Fetches the current Bitcoin price in USD using the CoinGecko API,
    prints it to the console, and stores it in Supabase database.
    """
    try:
        # CoinGecko API endpoint for Bitcoin price
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        
        # Send GET request to the API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract the Bitcoin price in USD
            btc_price = data['bitcoin']['usd']
            
            # Print the price
            print(f"Current Bitcoin price: ${btc_price:,.2f} USD")
            
            # Store in Supabase
            store_in_supabase(btc_price)
            
            return btc_price
        else:
            print(f"Error fetching data: HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def store_in_supabase(price):
    """
    Stores the Bitcoin price in a Supabase database.
    """
    try:
        # Get Supabase credentials from environment variables
        # You should set these in your environment or use a .env file
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        # Ensure credentials are available
        if not supabase_url or not supabase_key:
            print("Error: Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
            return False
        
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Prepare data to insert
        current_time = datetime.now().isoformat()
        data = {
            "price": price,
            "currency": "USD",
            "timestamp": current_time
        }
        
        # Insert data into your table (replace 'bitcoin_prices' with your actual table name)
        response = supabase.table('btc_prices').insert(data).execute()
        
        # Check if insertion was successful
        if len(response.data) > 0:
            print(f"Successfully stored Bitcoin price in Supabase at {current_time}")
            return True
        else:
            print("Error: No data returned from Supabase after insertion")
            return False
            
    except Exception as e:
        print(f"Error storing data in Supabase: {e}")
        return False

# Execute the function if run directly
if __name__ == "__main__":
    fetch_btc_price_and_store()