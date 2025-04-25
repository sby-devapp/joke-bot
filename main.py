from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, filters, MessageHandler

# Import controllers
from app.controllers.chat_controller import ChatController
from app.controllers.setting_controller import SettingController
from app.controllers.user_controller import UserController
from bot_token import BOT_TOKEN
import asyncio

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(funcName)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)

# Initialize controllers
chat_controller = ChatController()
setting_controller = SettingController()
user_controller = UserController()

# Initialize the bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Schedule the periodic task using JobQueue
application.job_queue.run_repeating(
    callback=chat_controller.sending_jokes_to_active_chats,
    interval=120,  # Run every 2 minutes (120 seconds)
    first=5  # Start after 5 seconds
)





# Register command handlers
application.add_handler(CommandHandler("profile", chat_controller.user_profile))
application.add_handler(CommandHandler("help", chat_controller.help))
application.add_handler(CommandHandler("start", chat_controller.start))
application.add_handler(CommandHandler("joke", chat_controller.send_joke))
application.add_handler(CommandHandler("stop", chat_controller.stop))

# Register settings-related command handlers
application.add_handler(CommandHandler("settings", setting_controller.handle_settings_command))


# Handle settings callbacks
async def handle_callback_query(update, context):
    """
    Handles all callback queries related to settings.
    """
    if not await chat_controller.is_user_admin_or_owner(update, context):
           await update.callback_query.answer("You are not authorized to change settings.\n only admins or owners can do this.")
           return
    
    query = update.callback_query
    await setting_controller.handle_callback_query(update, context)

application.add_handler(CallbackQueryHandler(handle_callback_query))

# Start the bot
if __name__ == "__main__":
    logger.info("Starting the bot...")
    application.run_polling()