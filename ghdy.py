
from dotenv import load_dotenv
import os

# Specify the full path to the .env file
load_dotenv(dotenv_path="C:/Users/NAJEEB AHMED/PycharmProjects/open cv python/.env")

# Debugging: Print all environment variables to see if they are loaded
print("Environment variables:", os.environ)

# Get the values of SUPABASE_URL and SUPABASE_KEY
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Debugging: Print the values of SUPABASE_URL and SUPABASE_KEY
print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key: {supabase_key}")

# Initialize the Supabase client only if the URL and key are valid
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL or Key not found in environment variables!")

from supabase import create_client
supabase = create_client(supabase_url, supabase_key)



from datetime import datetime, timedelta
import requests
import pandas as pd
from supabase import create_client
import time
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

from datetime import datetime
from supabase import create_client

timestamp_str = datetime.now().isoformat()

# Supabase configuration
SUPABASE_URL = os.getenv('https://kaepzhzmpldpnsfqhdbs.supabase.co')
SUPABASE_KEY = os.getenv('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImthZXB6aHptcGxkcG5zZnFoZGJzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcyNzgxODEsImV4cCI6MjA1Mjg1NDE4MX0.11he9YDEQ2Cy7pyLjUwkoh5o3bBnoq0nZx_EPCx6DSg')


supabase = create_client(supabase_url, supabase_key)


def fetch_bitcoin_price():
    """
    Fetch current Bitcoin price from CoinGecko API
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'usd'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['bitcoin']['usd']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price: {e}")
        return None


def save_to_supabase(price_data):
    try:
        # Ensure numeric price
        price_usd = float(price_data['price_usd'])
        current_time = datetime.now()

        data = {
            'timestamp': int(current_time.timestamp()),
            'readable_timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'price_usd': price_usd
        }

        supabase.table('bitcoin_prices').insert(data).execute()
        print("Data saved successfully!")
    except Exception as e:
        print(f"Error saving to Supabase: {e}")


def fetch_recent_prices():
    """
    Fetch recent prices from Supabase
    """
    try:
        response = supabase.table('bitcoin_prices') \
            .select('*') \
            .order('timestamp', desc=True) \
            .limit(24) \
            .execute()

        return pd.DataFrame(response.data)
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return None


def main():
    print("Bitcoin Price Logger Started")
    print("---------------------------")

    while True:
        try:
            # Get current price
            current_price = fetch_bitcoin_price()

            if current_price:
                # Prepare data for Supabase
                price_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'price_usd': current_price
                }

                # Save to Supabase
                save_to_supabase(price_data)

                # Fetch and display recent prices
                recent_prices = fetch_recent_prices()
                if recent_prices is not None:
                    print("\nRecent Bitcoin Prices:")
                    print(recent_prices[['timestamp', 'price_usd']].to_string())

            # Wait for an hour before next update
            print("\nWaiting for next update...")
            time.sleep(3600)  # 1 hour

        except KeyboardInterrupt:
            print("\nLogging stopped by user")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    main()