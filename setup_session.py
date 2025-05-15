import os
from telethon.sync import TelegramClient

print("⚠️ Run this ONLY ONCE on your local machine (not Heroku) ⚠️")

api_id = input("Enter API_ID: ") or os.getenv('TELEGRAM_API_ID')
api_hash = input("Enter API_HASH: ") or os.getenv('TELEGRAM_API_HASH')
phone = input("Enter phone (+countrycode): ") or os.getenv('TELEGRAM_PHONE')

with TelegramClient('telethon_session', api_id, api_hash) as client:
    client.start(phone=phone)
    print("\n✅ Login successful! 'telethon_session.session' created")
    print("1. Add this file to .gitignore")
    print("2. Convert to Heroku config with:")
    print("   heroku config:set TELEGRAM_SESSION=\"$(base64 telethon_session.session)\"")
