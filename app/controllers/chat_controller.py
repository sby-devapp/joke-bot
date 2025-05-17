# File: app/controllers/chat_controller.py

from app.controllers.controller import Controller
import logging
import asyncio
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, CommandHandler
from app.db.entities.chat import Chat
from app.views.joke_view import JokeView

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ChatController(Controller):
    """
    Manages interactions related to chats.
    Inherits shared functionality from the base Controller class.
    """

    def __init__(self):
        super().__init__()  # Call the parent class's constructor
        logger.info("Initializing ChatController...")

    async def send_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /joke command.
        Sends a single random joke to the user.
        """
        chat = self.get_chat(update=update, context=context)
        joke = chat.get_random_joke()
        if joke is None:
            await update.message.reply_text(
                "No jokes available for your preferred tags and language "
            )
            chat.setting.sending_jokes = "off"
            chat.setting.save()
            await update.message.reply_text("We stopped sending jokes to you")
            await update.message.reply_text("You can add jokes using /addjoke command")
            return

        await self._send_joke(chat, joke, context)
        logger.info(f"Handled /joke command for chat ID {chat.id}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /sendingjokes command.
        Toggles continuous joke-sending on or off.
        """
        if not await self.is_user_admin_or_owner(update, context):
            await update.message.reply_text(
                "You are not authorized to start the bot. only admins or owners can do this."
            )
            return
        try:
            # Retrieve or create the chat
            chat = self.get_chat(update=update, context=context)
            # Retrieve the chat
            chat = self.get_chat(update=update, context=context)
            chat.setting.sending_jokes = "on"
            chat.setting.save()
            schedule_minutes = int(chat.setting.schedule / 60)
            self.send_joke(update, context)
            await update.message.reply_text(
                f"You will receive a joke every {schedule_minutes} minutes. If you want to stop receiving jokes, click on /stop.\nFor more information, click on /help.\n"
            )

        except Exception as e:
            logger.error(f"Error while handling /sendingjokes command: {e}")
            await update.message.reply_text(
                "Oops! Something went wrong while toggling joke-sending."
            )

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /stop command.
        Stops any ongoing processes and notifies the user.
        """
        if not await self.is_user_admin_or_owner(update, context):
            await update.message.reply_text(
                "You are not authorized to stop the bot. only admins or owners can do this."
            )
            return

        try:
            # Retrieve the chat
            chat = self.get_chat(update=update, context=context)
            chat.setting.sending_jokes = "off"
            chat.setting.save()
            await update.message.reply_text(
                f"You stopped this bot from sending jokes  automaticlly \n if you want to start recieve random jokes execute /start"
            )
        except Exception as e:
            logger.error(f"Error while handling /stop command: {e}")
            await update.message.reply_text(
                "Oops! Something went wrong while stopping the bot."
            )

    async def sending_jokes_to_active_chats(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Periodically sends jokes to active chats (sending_jokes == 'on').
        Scheduled using the JobQueue.
        """
        try:
            # Get the current time

            current_time = int(asyncio.get_event_loop().time())
            # Fetch all chats with sending_jokes == 'on'
            query = """
            SELECT c.id, s.schedule, c.last_joke_sent_at
            FROM chats c
            JOIN settings s ON c.id = s.chat_id
            WHERE s.sending_jokes = 'on'
            """
            results = Chat.db.fetch_all(query)

            for chat_id, schedule, last_joke_sent_at in results:
                # Check if it's time to send a joke
                if last_joke_sent_at + schedule <= current_time:
                    # Load the chat object
                    chat = Chat(chat_id=chat_id)
                    chat.load()
                    joke = chat.get_random_joke()
                    if joke is None:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="No jokes available for your preferred tags and language",
                        )
                        chat.setting.sending_jokes = "off"
                        chat.setting.save()
                        continue
                    else:
                        await self._send_joke(chat, joke, context)

        except Exception as e:
            logger.error(f"Error in sending_jokes_to_active_chats: {e}")

    def setup_handler(self):
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("joke", self.send_joke))
        self.application.add_handler(CommandHandler("stop", self.stop))
