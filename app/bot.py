import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from app.db.entities.chat import Chat as ChatEntity
from app.db.entities.joke import Joke
from app.controllers.chat_controller import ChatController
from app.views.joke_view import JokeView

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class Bot:
    def __init__(self):
        self._joke_sending_tasks = {}  # Tracks ongoing joke-sending tasks per chat_id

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command.
        Greets the user and initializes their chat settings if not already present.
        """
        chat_id = update.effective_chat.id
        logger.info(f"Received /start command from chat_id: {chat_id}")
        chat = ChatController(chat_id=chat_id)

        # Load or initialize chat data
        chat.load()

        await update.message.reply_text(
            "Welcome to the Joke Bot! Use /joke to get a random joke, "
            "/sendingjokes to toggle continuous joke-sending, and react to jokes with buttons!"
        )

    async def send_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /joke command.
        Sends a single random joke to the user.
        """
        chat_id = update.effective_chat.id
        logger.info(f"Received /joke command from chat_id: {chat_id}")
        chat = ChatController(chat_id=chat_id)

        # Fetch a random joke
        joke = chat.get_random_joke()
        if not joke:
            await update.message.reply_text("No jokes found.")
            return

        # Format the joke using JokeView
        joke_view = JokeView(joke)
        formatted_joke = joke_view.format_private_chat()

        # Send the formatted joke with reaction buttons
        await update.message.reply_text(
            text=formatted_joke,
            reply_markup=joke_view.get_reaction_keyboard()
        )

    async def sending_jokes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /sendingjokes command.
        Toggles continuous joke-sending for the chat.
        """
        chat_id = update.effective_chat.id
        logger.info(f"Received /sendingjokes command from chat_id: {chat_id}")
        chat = ChatController(chat_id=chat_id)

        # Toggle the sending_jokes setting
        is_sending_jokes = chat.chat.settings["sending_jokes"] == "on"
        chat.toggle_sending_jokes(enable=not is_sending_jokes)

        if not is_sending_jokes:
            # Start continuous joke-sending
            await self._send_joke_recursive(chat_id=chat_id)
            await update.message.reply_text("Continuous joke-sending has been enabled!")
        else:
            # Stop continuous joke-sending
            await self.stop_joke_sending(chat_id=chat_id)
            await update.message.reply_text("Continuous joke-sending has been disabled!")

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays the current settings of the chat with buttons to modify each attribute.
        """
        chat_id = update.effective_chat.id
        logger.info(f"Received /settings command from chat_id: {chat_id}")
        chat = ChatController(chat_id=chat_id)

        # Load chat settings
        settings = chat.get_chat_settings()

        # Build the message text
        message_text = (
            "⚙️ <b>Chat Settings</b>\n\n"
            f"• Sending Jokes: <code>{settings['sending_jokes']}</code>\n"
            f"• Preferred Language: <code>{settings['preferred_language']}</code>\n"
            f"• Schedule (seconds): <code>{settings['schedule']}</code>\n"
            f"• Tags: <code>{', '.join(settings['tags']) if settings['tags'] else 'None'}</code>\n\n"
            "Click on a button below to change a setting."
        )

        # Create inline keyboard buttons
        keyboard = [
            [InlineKeyboardButton("Toggle Sending Jokes", callback_data="change_sending_jokes")],
            [InlineKeyboardButton("Change Preferred Language", callback_data="change_preferred_language")],
            [InlineKeyboardButton("Change Schedule", callback_data="change_schedule")],
            [InlineKeyboardButton("Manage Tags", callback_data="manage_tags")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the message with the inline keyboard
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="HTML"  # Enable HTML formatting for better readability
        )

    async def handle_setting_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles callback queries for changing chat settings.
        """
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query

        chat_id = query.message.chat_id
        chat = ChatController(chat_id=chat_id)
        data = query.data

        if data == "change_sending_jokes":
            # Toggle sending jokes
            is_sending_jokes = chat.chat.settings["sending_jokes"] == "on"
            chat.toggle_sending_jokes(enable=not is_sending_jokes)
            new_status = "on" if not is_sending_jokes else "off"
            await query.edit_message_text(
                text=f"✅ Sending jokes toggled to <code>{new_status}</code>.",
                parse_mode="HTML"
            )

        elif data == "change_preferred_language":
            # Prompt the user to select a new language
            keyboard = [
                [InlineKeyboardButton("English", callback_data="set_language_en")],
                [InlineKeyboardButton("French", callback_data="set_language_fr")],
                [InlineKeyboardButton("Spanish", callback_data="set_language_es")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Select your preferred language:",
                reply_markup=reply_markup
            )

        elif data.startswith("set_language_"):
            # Set the selected language
            language = data.split("_")[-1]
            chat.update_preferred_language(language)
            await query.edit_message_text(
                text=f"✅ Preferred language set to <code>{language}</code>.",
                parse_mode="HTML"
            )

        elif data == "change_schedule":
            # Prompt the user to enter a new schedule
            await query.edit_message_text(
                text="Please send the new joke-sending interval in seconds (e.g., 300)."
            )
            # Store the state in context to handle the next message
            context.user_data["awaiting_schedule_update"] = True

        elif data == "manage_tags":
            # Open a submenu for managing tags
            tags = chat.chat.tags
            keyboard = [
                [InlineKeyboardButton(f"Add Tag: {tag}", callback_data=f"add_tag_{tag}") for tag in ["funny", "dark", "puns"]],
                [InlineKeyboardButton(f"Remove Tag: {tag}", callback_data=f"remove_tag_{tag}") for tag in tags],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Manage your tags:",
                reply_markup=reply_markup
            )

        elif data.startswith("add_tag_"):
            # Add a tag
            tag = data.split("_")[-1]
            chat.add_tag(tag)
            await query.edit_message_text(
                text=f"✅ Added tag: <code>{tag}</code>.",
                parse_mode="HTML"
            )

        elif data.startswith("remove_tag_"):
            # Remove a tag
            tag = data.split("_")[-1]
            chat.remove_tag(tag)
            await query.edit_message_text(
                text=f"✅ Removed tag: <code>{tag}</code>.",
                parse_mode="HTML"
            )

    async def handle_reaction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles user reactions to jokes via callback queries.
        """
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query

        # Extract reaction details
        reaction_data = query.data.split(":")
        if len(reaction_data) != 3 or reaction_data[0] != "react":
            logger.warning(f"Invalid reaction data received: {query.data}")
            return

        _, joke_id, reaction_type = reaction_data
        logger.info(f"User reacted with '{reaction_type}' to joke_id: {joke_id}")

        # Save the reaction to the database
        joke = Joke(id=int(joke_id))
        joke.save_reaction(user_id=query.from_user.id, reaction_type=reaction_type)

        # Update the message to confirm the reaction
        await query.edit_message_text(
            text=f"Thank you for your reaction: {reaction_type}!",
            reply_markup=None  # Remove reaction buttons after reacting
        )

    async def _send_joke_recursive(self, chat_id: int):
        """
        Recursively sends jokes to the specified chat at the interval defined in the chat settings.
        Stops if `sending_jokes` is turned off.
        """
        logger.info(f"Entering recursive joke-sending loop for chat_id: {chat_id}")

        # Load chat settings from the database
        chat = ChatController(chat_id=chat_id)
        chat.load()

        # Check if joke-sending is enabled
        if chat.chat.settings["sending_jokes"] != "on":
            logger.info(f"Joke-sending is disabled for chat_id: {chat_id}. Exiting recursive loop.")
            return

        # Fetch and send a random joke
        joke = chat.get_random_joke()
        if joke:
            # Format the joke using JokeView
            joke_view = JokeView(joke)
            formatted_joke = joke_view.format_private_chat()

            # Send the formatted joke with reaction buttons
            await context.bot.send_message(
                chat_id=chat_id,
                text=formatted_joke,
                reply_markup=joke_view.get_reaction_keyboard()
            )
            logger.info(f"Sent joke to chat_id: {chat_id}: {joke.joke}")
        else:
            logger.warning(f"No jokes found for chat_id: {chat_id}. Skipping this iteration.")

        # Schedule the next joke
        interval = chat.chat.settings["schedule"]
        logger.info(f"Scheduling next joke for chat_id: {chat_id} in {interval} seconds")
        await asyncio.sleep(interval)

        # Recursively call the method to send the next joke
        await self._send_joke_recursive(chat_id=chat_id)

    async def stop_joke_sending(self, chat_id: int):
        """
        Stops the recursive joke-sending process for a specific chat.
        """
        logger.info(f"Stopping recursive joke-sending for chat_id: {chat_id}")

        # Disable joke-sending in the chat settings
        chat = ChatController(chat_id=chat_id)
        chat.toggle_sending_jokes(enable=False)

        logger.info(f"Recursive joke-sending stopped for chat_id: {chat_id}")