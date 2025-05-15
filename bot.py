import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from telethon.sync import TelegramClient
from telethon.tl.types import ChannelParticipantsSearch
from telethon.errors import FloodWaitError
import asyncio
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache setup
stats_cache = {}
CACHE_EXPIRY = timedelta(hours=6)

# Telethon client setup
def get_telethon_client():
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    session_name = 'group_stats_bot'
    
    if not all([api_id, api_hash, phone]):
        logger.error("Missing Telethon environment variables")
        return None
    
    return TelegramClient(session_name, int(api_id), api_hash)

async def get_detailed_stats(chat_id):
    client = get_telethon_client()
    if not client:
        return None
    
    try:
        await client.start(phone=os.getenv('TELEGRAM_PHONE'))
        
        deleted_count = 0
        premium_count = 0
        total_count = 0
        bot_count = 0
        
        async for user in client.iter_participants(chat_id):
            total_count += 1
            if user.deleted:
                deleted_count += 1
            elif user.bot:
                bot_count += 1
            elif getattr(user, 'premium', False):
                premium_count += 1
                
        return {
            'total': total_count,
            'deleted': deleted_count,
            'premium': premium_count,
            'bots': bot_count,
            'active': total_count - deleted_count - bot_count
        }
    except FloodWaitError as e:
        logger.error(f"Flood wait: {e}")
        return None
    except Exception as e:
        logger.error(f"Telethon error: {e}")
        return None
    finally:
        await client.disconnect()

async def get_cached_stats(chat_id):
    now = datetime.now()
    if chat_id in stats_cache and now - stats_cache[chat_id]['timestamp'] < CACHE_EXPIRY:
        return stats_cache[chat_id]['data']
    
    data = await get_detailed_stats(chat_id)
    if data:
        stats_cache[chat_id] = {
            'data': data,
            'timestamp': now
        }
    return data

# Command handlers (updated)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm an advanced group stats bot. Use /stats in a group to get detailed member statistics. "
        "Make sure I'm an admin with the right permissions!"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in a group or supergroup.")
        return

    bot_id = context.bot.id
    chat_id = update.effective_chat.id
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if not any(admin.user.id == bot_id for admin in admins):
            await update.message.reply_text("I need to be an admin with member access to fetch detailed stats!")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking admin status: {e}")
        return

    try:
        # Get basic count from Bot API
        total_count = await context.bot.get_chat_member_count(chat_id)
        
        # Get detailed stats from Telethon
        detailed_stats = await get_cached_stats(chat_id)
        
        if not detailed_stats:
            await update.message.reply_text(
                f"📊 Basic Group Stats 📊\n"
                f"Total Members: {total_count}\n"
                f"Detailed stats unavailable right now. Please try again later."
            )
            return
        
        premium_percentage = (detailed_stats['premium'] / detailed_stats['active'] * 100) if detailed_stats['active'] > 0 else 0
        
        response = (
            f"📊 Advanced Group Statistics 📊\n"
            f"👥 Total Members: {total_count}\n"
            f"🟢 Active Users: {detailed_stats['active']}\n"
            f"🧟 Deleted Accounts: {detailed_stats['deleted']}\n"
            f"🤖 Bots: {detailed_stats['bots']}\n"
            f"⭐ Premium Members: {detailed_stats['premium']} ({premium_percentage:.1f}%)\n"
            f"\n"
            f"Last updated: {stats_cache[chat_id]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Use /refresh to update stats"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await update.message.reply_text("An error occurred while fetching stats. Please try again later.")

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in a group or supergroup.")
        return
    
    chat_id = update.effective_chat.id
    if chat_id in stats_cache:
        del stats_cache[chat_id]
    
    await stats(update, context)
    await update.message.reply_text("Stats cache cleared and refreshed!")

# Keep your existing help and details functions
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/stats - Get detailed group member statistics\n"
        "/refresh - Force refresh group stats\n"
        "/help - Show this help message"
    )

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update.effective_message:
        await update.effective_message.reply_text("An error occurred. Please try again later.")

def main() -> None:
    # Check required environment variables
    required_vars = [
        "BOT_TOKEN",
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "TELEGRAM_PHONE"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return

    # Create the Application
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("refresh", refresh))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
