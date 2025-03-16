import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables from .env file
load_dotenv()

class FinanceEmailAgent:
    def __init__(self):
        """
        Initialize the FinanceEmailAgent with necessary API keys from environment variables
        """
        # Load API keys from environment variables
        self.hf_api_key = os.getenv("HF_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        self.recipient_email = "s.hamza.zar@gmail.com"
        
        # Verify that necessary API keys and credentials are available
        if not self.hf_api_key:
            raise ValueError("HF_API_KEY not found in environment variables")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
            
        if not self.gmail_user or not self.gmail_password:
            raise ValueError("GMAIL_USER or GMAIL_APP_PASSWORD not found in environment variables")
        
        # Initialize Hugging Face client
        self.hf_client = InferenceClient(token=self.hf_api_key)
        
        # Initialize Supabase client
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
    def get_recent_eco_info(self, days=7):
        """
        Retrieve recent economic information from the eco_info table
        
        Args:
            days: Number of past days to retrieve data for
            
        Returns:
            List of economic information entries
        """
        try:
            # Calculate the date threshold
            threshold_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Query Supabase for recent entries
            response = self.supabase.table("eco_info") \
                .select("*") \
                .gte("timestamp", threshold_date) \
                .order("timestamp", desc=True) \
                .execute()
                
            if hasattr(response, 'data'):
                print(f"Retrieved {len(response.data)} eco_info records")
                return response.data
            else:
                print("No data attribute in response")
                return []
                
        except Exception as e:
            print(f"Error retrieving eco_info data: {e}")
            return []
            
    def get_recent_btc_prices(self, days=7):
        """
        Retrieve recent Bitcoin price data from the btc_prices table
        
        Args:
            days: Number of past days to retrieve data for
            
        Returns:
            List of Bitcoin price entries
        """
        try:
            # Calculate the date threshold
            threshold_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Query Supabase for recent entries
            response = self.supabase.table("btc_prices") \
                .select("*") \
                .gte("timestamp", threshold_date) \
                .order("timestamp", desc=True) \
                .execute()
                
            if hasattr(response, 'data'):
                print(f"Retrieved {len(response.data)} btc_prices records")
                return response.data
            else:
                print("No data attribute in response")
                return []
                
        except Exception as e:
            print(f"Error retrieving btc_prices data: {e}")
            return []
    
    def prepare_context(self, eco_info, btc_prices):
        """
        Prepare context from the retrieved data for the AI analysis
        
        Args:
            eco_info: List of economic information entries
            btc_prices: List of Bitcoin price entries
            
        Returns:
            Formatted context string
        """
        context = "RECENT BITCOIN NEWS:\n\n"
        
        # Format economic information
        for item in eco_info[:10]:  # Limit to 10 most recent items
            if 'finance_info' in item:
                context += f"{item['finance_info']}\n\n"
        
        context += "\nRECENT BITCOIN PRICE DATA:\n\n"
        
        # Format Bitcoin price data
        for item in btc_prices[:10]:  # Limit to 10 most recent price points
            # Format depends on your btc_prices table structure
            # Assuming it has price, timestamp, volume fields
            if all(k in item for k in ['price', 'timestamp']):
                date_str = item['timestamp'].split('T')[0] if isinstance(item['timestamp'], str) else "Unknown date"
                context += f"Date: {date_str}, Price: ${item['price']}"
                if 'volume' in item:
                    context += f", Volume: {item['volume']}"
                context += "\n"
        
        return context
    
    def generate_analysis(self, context):
        """
        Generate concise financial analysis using HuggingFace API
        
        Args:
            context: Context data containing Bitcoin news and price information
            
        Returns:
            Concise professional analysis
        """
        try:
            # Create the prompt for analysis
            system_prompt = """You are a professional financial analyst specializing in cryptocurrency markets, particularly Bitcoin.
You write extremely concise, insightful analysis that identifies important correlations between news and price movements.
Your analysis should be brief (maximum 5 short paragraphs), professionally written, and highly informative."""
            
            user_prompt = f"""Based on the following information about Bitcoin news and recent price movements, 
create a VERY short, concise, professional analysis email identifying key correlations and insights.
Focus only on the most significant patterns and actionable information.
Be direct and to the point.

CONTEXT DATA:
{context}

Please format your response as a professional email to Hamza."""
            
            full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
            
            # Generate the analysis
            response = self.hf_client.text_generation(
                prompt=full_prompt,
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                max_new_tokens=600,
                temperature=0.3
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating analysis: {e}")
            return "Error generating Bitcoin market analysis. Please check the system logs."
    
    def send_email(self, analysis):
        """
        Send the analysis email using Gmail SMTP
        
        Args:
            analysis: The analysis text to send
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Prepare email content
            subject = f"Bitcoin Market Analysis - {today}"
            
            # If the analysis doesn't already have a salutation, add one
            if not analysis.startswith("Dear Hamza") and not analysis.startswith("Hi Hamza"):
                analysis = f"Dear Hamza,\n\n{analysis}"
                
            # If the analysis doesn't have a signature, add one
            if not "Regards" in analysis and not "Sincerely" in analysis:
                analysis += "\n\nRegards,\nYour Finance Agent"
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            # Attach text body
            msg.attach(MIMEText(analysis, 'plain'))
            
            # Connect to Gmail server and send
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Email sent successfully to {self.recipient_email}")
            return True
                
        except Exception as e:
            print(f"Exception when sending email: {e}")
            return False
    
    def run(self, test_mode=False):
        """
        Main function to execute the finance email agent workflow
        
        Args:
            test_mode: If True, will generate a test email even without data
            
        Returns:
            Boolean indicating success or failure of the entire process
        """
        try:
            # Step 1: Get recent data from both tables
            eco_info = self.get_recent_eco_info()
            btc_prices = self.get_recent_btc_prices()
            
            if not eco_info or not btc_prices:
                print("Insufficient data to generate analysis")
                if test_mode:
                    # Generate a test email instead
                    test_analysis = "Dear Hamza,\n\nThis is a test email from your Finance Email Agent. The system is functioning correctly but couldn't find sufficient recent data in the database. Please ensure your data collection agents are running properly.\n\nRegards,\nYour Finance Agent"
                    return self.send_email(test_analysis)
                return False
                
            # Step 2: Prepare context for analysis
            context = self.prepare_context(eco_info, btc_prices)
            
            # Step 3: Generate professional analysis
            analysis = self.generate_analysis(context)
            
            # Step 4: Send email with analysis
            return self.send_email(analysis)
            
        except Exception as e:
            print(f"Error in finance email agent workflow: {e}")
            return False

# Example usage
if __name__ == "__main__":
    try:
        agent = FinanceEmailAgent()
        # Use test_mode=True to send a test email even if there's no data
        success = agent.run(test_mode=True)
        print(f"Finance email agent completed with success: {success}")
    except Exception as e:
        print(f"Error: {e}")