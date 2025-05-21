from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    MessageHandler,
)
from app.controllers.adding_jokes import AddingJokes
from app.controllers.chat_controller import ChatController
from app.controllers.controller import Controller
from app.controllers.setting_controller import SettingController
from app.controllers.user_controller import UserController
from bot_token import BOT_TOKEN
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(funcName)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


# Initialize the bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Initialize controllers
controller = Controller()
controller.application = application
chat_controller = ChatController()
setting_controller = SettingController()
adding_jokes = AddingJokes()

# Schedule the periodic task using JobQueue
application.job_queue.run_repeating(
    callback=chat_controller.sending_jokes_to_active_chats,
    interval=303,  # Run every 5 minutes (303 seconds)
    first=30,  # Start after 30 seconds
)


adding_jokes.application = application
adding_jokes.setup_handler()

chat_controller.application = application
chat_controller.setup_handler()

setting_controller.application = application
setting_controller.setup_handler()


if __name__ == "__main__":
    logger.info("Starting the bot...")
    application.run_polling()
