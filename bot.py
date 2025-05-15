import logging
import os
from telethon import TelegramClient, events
from telethon.tl.types import User

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Client API credentials
api_id = 20284828
api_hash = "a980ba25306901d5c9b899414d6a9ab7"
bot_token = os.getenv("7593658145:AAHhK4VKAFDrrteIgm-d7ZE4PAQ7XL3QdYE")

# Initialize Telethon client
client = TelegramClient('bot', api_id, api_hash)

# Command handler for /start
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        "Hello! I'm a group stats bot. Use /stats in a group to get member statistics. Make sure I'm an admin!"
    )

# Command handler for /help
@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.reply(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/stats - Get group member statistics\n"
        "/details - Get detailed group stats\n"
        "/refresh - Refresh group stats\n"
        "/help - Show this help message"
    )

# Command handler for /stats
@client.on(events.NewMessage(pattern='/stats'))
async def stats(event):
    if not event.is_group:
        await event.reply("This command can only be used in a group or supergroup.")
        return

    chat = await event.get_chat()
    chat_id = chat.id

    # Check if the bot has admin privileges
    try:
        admins = await client.get_participants(chat, filter=client.get_filter('ChatAdministrators'))
        bot_id = (await client.get_me()).id
        if not any(admin.id == bot_id for admin in admins):
            await event.reply("I need to be an admin to fetch member details!")
            return
    except Exception as e:
        await event.reply(f"Error checking admin status: {e}")
        return

    try:
        # Initialize counters
        deleted_count = 0
        premium_count = 0
        normal_count = 0
        total_count = 0

        # Fetch all members
        async for user in client.iter_participants(chat):
            total_count += 1
            if user.is_deleted:
                deleted_count += 1
            elif getattr(user, 'is_premium', False):
                premium_count += 1
            else:
                normal_count += 1

        response = (
            f"📊 Group Member Statistics 📊\n"
            f"Total Members: {total_count}\n"
            f"Deleted Accounts: {deleted_count}\n"
            f"Premium Members: {premium_count}\n"
            f"Normal Members: {normal_count}"
        )
        await event.reply(response)

    except Exception as e:
        await event.reply(f"Error fetching member stats: {e}")

# Command handler for /details
@client.on(events.NewMessage(pattern='/details'))
async def details(event):
    if not event.is_group:
        await event.reply("This command can only be used in a group or supergroup.")
        return

    chat = await event.get_chat()
    chat_id = chat.id

    # Check if the bot has admin privileges
    try:
        admins = await client.get_participants(chat, filter=client.get_filter('ChatAdministrators'))
        bot_id = (await client.get_me()).id
        if not any(admin.id == bot_id for admin in admins):
            await event.reply("I need to be an admin to fetch member details!")
            return
    except Exception as e:
        await event.reply(f"Error checking admin status: {e}")
        return

    try:
        # Initialize lists and counters
        premium_users = []
        deleted_count = 0

        # Fetch all members
        async for user in client.iter_participants(chat):
            if getattr(user, 'is_premium', False):
                premium_users.append(f"@{user.username}" if user.username else f"ID:{user.id}")
            if user.is_deleted:
                deleted_count += 1

        response = (
            f"📋 Detailed Group Stats 📋\n"
            f"Premium Members: {', '.join(premium_users) or 'None'}\n"
            f"Deleted Accounts: {deleted_count}"
        )
        await event.reply(response)

    except Exception as e:
        await event.reply(f"Error fetching detailed stats: {e}")

# Command handler for /refresh
@client.on(events.NewMessage(pattern='/refresh'))
async def refresh(event):
    if not event.is_group:
        await event.reply("This command can only be used in a group or supergroup.")
        return
    await stats(event)
    await event.reply("Stats refreshed!")

# Start the client
async def main():
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set. Please set it in Heroku config vars.")
        raise ValueError("BOT_TOKEN is not set")
    try:
        await client.start(bot_token=bot_token)
        logger.info("Bot started successfully")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
