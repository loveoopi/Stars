import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello! I'm a group stats bot. Use /stats in a group to get member statistics. Make sure I'm an admin!"
    )

# Command handler for /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/stats - Get group member statistics\n"
        "/details - Get detailed group stats\n"
        "/refresh - Refresh group stats\n"
        "/help - Show this help message"
    )

# Command handler for /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the command is used in a group
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in a group or supergroup.")
        return

    # Check if the bot has admin privileges
    bot_id = context.bot.id
    chat_id = update.effective_chat.id
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if not any(admin.user.id == bot_id for admin in admins):
            await update.message.reply_text("I need to be an admin to fetch member details!")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking admin status: {e}")
        return

    # Initialize counters
    deleted_count = 0
    premium_count = 0
    normal_count = 0
    total_count = 0

    try:
        # Fetch all members (Telegram API limits may apply)
        async for member in context.bot.get_chat_members(chat_id):
            total_count += 1
            user = member.user
            if user.is_deleted:
                deleted_count += 1
            elif user.is_premium:
                premium_count += 1
            else:
                normal_count += 1

        # Prepare response
        response = (
            f"📊 Group Member Statistics 📊\n"
            f"Total Members: {total_count}\n"
            f"Deleted Accounts: {deleted_count}\n"
            f"Premium Members: {premium_count}\n"
            f"Normal Members: {normal_count}"
        )
        await update.message.reply_text(response)

    except Exception as e:
        await update.message.reply_text(f"Error fetching member stats: {e}")

# Command handler for /details
async def details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the command is used in a group
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in a group or supergroup.")
        return

    # Check if the bot has admin privileges
    bot_id = context.bot.id
    chat_id = update.effective_chat.id
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if not any(admin.user.id == bot_id for admin in admins):
            await update.message.reply_text("I need to be an admin to fetch member details!")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking admin status: {e}")
        return

    # Initialize lists and counters
    premium_users = []
    deleted_count = 0

    try:
        # Fetch all members
        async for member in context.bot.get_chat_members(chat_id):
            user = member.user
            if user.is_premium:
                premium_users.append(f"@{user.username}" if user.username else f"ID:{user.id}")
            if user.is_deleted:
                deleted_count += 1

        # Prepare response
        response = (
            f"📋 Detailed Group Stats 📋\n"
            f"Premium Members: {', '.join(premium_users) or 'None'}\n"
            f"Deleted Accounts: {deleted_count}"
        )
        await update.message.reply_text(response)

    except Exception as e:
        await update.message.reply_text(f"Error fetching detailed stats: {e}")

# Command handler for /refresh
async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the command is used in a group
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in a group or supergroup.")
        return
    await stats(update, context)  # Reuse stats function
    await update.message.reply_text("Stats refreshed!")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update.effective_message:
        await update.effective_message.reply_text("An error occurred. Please try again later.")

def main() -> None:
    # Get the bot token from environment variable (for Heroku)
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable not set")
        return

    # Create the Application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("details", details))
    application.add_handler(CommandHandler("refresh", refresh))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
