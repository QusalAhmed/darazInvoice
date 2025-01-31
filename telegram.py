import os
import dotenv
import telebot
import sqlite3

# connect to database
conn = sqlite3.connect('order_details.db')
cursor = conn.cursor()

# Load environment variables from .env file
dotenv.load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('ANISHA_CHAT_ID')

# Create a bot instance
bot = telebot.TeleBot(BOT_TOKEN)

cursor.execute('SELECT phone_number, order_id FROM outside_delivery LIMIT 5')
for row in cursor.fetchall():
    phone, order_id = row
    cursor.execute('SELECT shop_name FROM open_order WHERE order_id = ?', (order_id,))
    shop_name = cursor.fetchone()[0]
    bot.send_message(CHAT_ID, f'+88{phone} from {shop_name} Order ID: {order_id}')
