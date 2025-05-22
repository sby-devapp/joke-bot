from telegram.ext import ApplicationBuilder

from app.controllers.adding_jokes import AddingJokes
from app.controllers.chat_controller import ChatController
from app.controllers.controller import Controller
from app.controllers.setting_controller import SettingController
from bot_token import BOT_TOKEN

# Set logging to WARNING to hide info logs globally
import logging

logging.basicConfig(level=logging.WARNING)
# Suppress httpx info logs
logging.getLogger("httpx").setLevel(logging.WARNING)
# Suppress apscheduler info logs
logging.getLogger("apscheduler").setLevel(logging.WARNING)
# Suppress telegram.ext info logs (optional)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)


# Initialize the bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Initialize controllers
controller = Controller()
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
    print("The bot is starting ...")
    application.run_polling()
