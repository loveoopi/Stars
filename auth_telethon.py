from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load values from environment variables
api_id = os.getenv('TELEGRAM_API_ID') or 'YOUR_API_ID'
api_hash = os.getenv('TELEGRAM_API_HASH') or 'YOUR_API_HASH'
phone = os.getenv('TELEGRAM_PHONE') or 'YOUR_PHONE_NUMBER'
password = os.getenv('TELEGRAM_2FA_PASSWORD') or None

# Initialize Telethon client
client = TelegramClient('group_stats_bot', api_id, api_hash)

# Start the client and authenticate
client.start(phone=phone, password=password)
print("Authentication complete. Session file saved as 'group_stats_bot.session'.")
client.disconnect()