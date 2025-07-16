import os
import json
import time
import logging
from datetime import date, timedelta
import requests
from access_token import get_access_token
# --- Configuration ---
# It's best practice to load credentials from a .env file or environment variables
# instead of hardcoding them in the script.
# Create a .env file in the same directory with these lines:
# TOAST_CLIENT_ID="your_client_id"
# TOAST_CLIENT_SECRET="your_client_secret"
# TOAST_RESTAURANT_ID="your_restaurant_guid"

from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = "qIfiE1KiedHaqw3TSB0OYTIwoEDgJ9u0"
CLIENT_SECRET = "XEJt_XHR3cix48g_bAd8a-DWC8wP3hSP7w-r3saLxluVTTzhtzc-jwomuZ4zugNi" 
RESTAURANT_ID = "aea8d7f1-0daa-447b-aa43-8d71ee6b6402" 
     # Your specific restaurant's GUID

API_HOSTNAME = "https://ws-api.toasttab.com"
BASE_API_URL = "https://ws-api.toasttab.com"


API_HOSTNAME = "https://ws-api.toasttab.com"
BASE_API_URL = "https://ws-api.toasttab.com"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def fetch_and_save_orders(token: str, business_day: date, restaurant_id: str, output_file: str):
    """
    Fetches all orders for a specific business day and streams them to a JSON file.
    """
    if not all([token, business_day, restaurant_id, output_file]):
        logging.error("Missing required arguments for fetching orders.")
        return False

    orders_url = f"{BASE_API_URL}/orders/v2/ordersBulk"
    headers = {
        "Authorization": f"Bearer {token}",
        "Toast-Restaurant-External-ID": restaurant_id
    }
    params = {
        "businessDate": business_day.strftime('%Y%m%d'),
        "pageSize": 100,
        "page": 1
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write('[')
        first_page = True
        
        while True:
            logging.info(f"Fetching page {params['page']} for business date {params['businessDate']}...")
            try:
                response = session.get(orders_url, params=params, timeout=30)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logging.warning(f"Rate limit hit. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                orders_page = response.json()
                
                if not orders_page:
                    logging.info("No more orders found for this day.")
                    break
                
                for order in orders_page:
                    if not first_page:
                        f.write(',')
                    json.dump(order, f, indent=4)
                    first_page = False
                
                params['page'] += 1
            
            except requests.exceptions.RequestException as err:
                logging.error(f"A request error occurred: {err}")
                if err.response:
                    logging.error(f"Error details: {err.response.text}")
                f.write(']')
                return False

        f.write(']')
        
    logging.info(f"Successfully saved all orders to {output_file}")
    return True

if __name__ == "__main__":
    if not all([CLIENT_ID, CLIENT_SECRET, RESTAURANT_ID]):
        logging.error("Please set TOAST_CLIENT_ID, TOAST_CLIENT_SECRET, and TOAST_RESTAURANT_ID in your .env file.")
    else:
        access_token = get_access_token()
        if access_token:
            # --- Historical Data Pull ---
            start_date = date.today() - timedelta(days=300)
            end_date = date.today() - timedelta(days=1)
            output_directory = "historical_orders"
            
            logging.info(f"Starting historical data pull from {start_date} to {end_date}...")
            
            current_day = start_date
            while current_day <= end_date:
                logging.info(f"--- Processing date: {current_day.strftime('%Y-%m-%d')} ---")
                
                # Correctly create a unique filename for each day in a specific directory
                output_filename = os.path.join(output_directory, f"orders_{current_day.strftime('%Y%m%d')}.json")
                
                success = fetch_and_save_orders(
                    token=access_token,
                    business_day=current_day,
                    restaurant_id=RESTAURANT_ID,
                    output_file=output_filename
                )
                
                if not success:
                    logging.error(f"Failed to fetch data for {current_day}. Stopping process.")
                    break
                
                current_day += timedelta(days=1)
                time.sleep(0.6) # Be a good API citizen
                
            logging.info("Historical data pull complete.")