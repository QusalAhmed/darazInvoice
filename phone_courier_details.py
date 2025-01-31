import os
import dotenv
import requests
import sqlite3
from colors import *

# Load environment variables from .env file
dotenv.load_dotenv()

# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()

def check_courier(phone_number):
    url = f"https://bdcourier.com/api/courier-check?phone={phone_number}"
    headers = {
        "Authorization": F"Bearer {os.getenv('BD_COURIER_TOKEN')}"
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        # Print the response data key-value pairs
        for key, value in data['courierData'].items():
            print(f"{key}: {value}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    cursor.execute('SELECT phone_number, order_id FROM outside_delivery')
    for row in cursor.fetchall():
        phone, order_id = row
        cursor.execute('SELECT shop_name FROM open_order WHERE order_id = ?', (order_id,))
        shop_name = cursor.fetchone()[0]
        print(YELLOW + f"Checking courier for {order_id} from {shop_name}" + RESET)
        check_courier(phone)