import asyncio
import logging
from telegram import ChatMember, Update
from telegram.ext import ContextTypes
from app.db.entities.chat import Chat
from app.db.entities.joke import Joke
from app.db.entities.user import User
from app.db.entities.setting import Setting
from app.views.joke_view import JokeView
from anyio import current_time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Controller:
    """
    Base controller class providing shared functionality for managing chats, users, and settings.
    """

    application = None

    def __init__(self):
        logger.info("Initializing Controller...")

    def get_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Chat:
        """
        Retrieves or creates a Chat object for the given chat_id.
        Ensures the associated User and Setting objects are properly initialized.
        Returns the Chat object.
        """
        try:
            user = self.get_user(update=update, context=context)
            if not user:
                logger.error("Failed to retrieve or create user.")
                return None

            chat = Chat()
            chat.user_id = user.id

            # Extract chat details from the update
            if update.callback_query:
                chat.id = update.callback_query.message.chat.id
                chat.type = update.callback_query.message.chat.type
                chat.username = update.callback_query.message.chat.username
            else:
                chat.id = update.effective_chat.id
                chat.type = update.effective_chat.type
                chat.username = update.effective_chat.username

            # Save and load the chat
            chat.save()
            chat.load()

            logger.info(
                f"Retrieved or created chat: Chat ID: {chat.id}, Username: {chat.username}"
            )
            return chat
        except Exception as e:
            logger.error(f"Error while retrieving or creating chat: {e}")
            return None

    def get_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> User:
        """
        Retrieves or creates a user object based on the update.
        Handles both Message and CallbackQuery updates.
        """
        try:
            user = User()

            # Extract user details from the update
            if update.callback_query:
                from_user = update.callback_query.from_user
                if not from_user:
                    logger.error("CallbackQuery does not contain a valid user.")
                    return None
                user.id = from_user.id
                user.username = from_user.username
            else:
                effective_user = update.effective_user
                if not effective_user:
                    logger.error("Update does not contain a valid user.")
                    return None
                user.id = effective_user.id
                user.username = effective_user.username

            # Save the user to the database
            user.save()
            logger.info(
                f"Retrieved or created user: User ID: {user.id}, Username: {user.username}"
            )
            return user
        except Exception as e:
            logger.error(f"Error while retrieving or creating user: {e}")
            return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command.
        Greets the user and initializes their chat settings.
        """
        try:
            chat = await self.get_chat(update=update, context=context)
            if not chat:
                await self.send_error_message(update, "Failed to initialize chat.")
                return

            message = (
                f"Hi, {chat.username}!\n\n"
                "Welcome to the Joke Bot! 😄 Here’s what you can do:\n"
                "- Use /joke to get a random joke.\n"
                "- Use /settings to manage your preferences."
            )

            await update.message.reply_text(message)
            logger.info(f"Sent welcome message to chat ID {chat.id}")
        except Exception as e:
            logger.error(f"Error while handling /start command: {e}")
            await self.send_error_message(
                update, "Oops! Something went wrong. Please try again later."
            )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command.
        Displays a list of available commands and their descriptions.
        """
        try:
            chat = self.get_chat(update=update, context=context)
            if not chat:
                await self.send_error_message(update, "Failed to initialize chat.")
                return

            message = (
                f"Hi, {chat.username}!\n\n"
                "Here’s a list of available commands and what they do:\n"
                "- /start - Initializes the bot and displays a welcome message.\n"
                "- /joke - Sends a random joke to the chat.\n"
                "- /jokes - Displays all of your jokes.\n"
                "- /addjoke - Allows you to submit a new joke for others to enjoy (coming soon!).\n"
                "- /settings - Opens the settings menu to manage your preferences.\n"
                "- /stop - Stops the bot from sending jokes to this chat.\n\n"
                "For more information, feel free to ask! @groot_n"
            )

            await update.message.reply_text(message)
            logger.info(f"Sent help message to chat ID {chat.id}")
        except Exception as e:
            logger.error(f"Error while handling /help command: {e}")
            await self.send_error_message(
                update, "Oops! Something went wrong. Please try again later."
            )

    async def send_error_message(self, update: Update, message: str):
        """
        Sends an error message to the user.
        Handles both Message and CallbackQuery updates.
        """
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            elif update.message:
                await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Error while sending error message: {e}")

    async def _send_joke(self, chat: Chat, joke, context: ContextTypes.DEFAULT_TYPE):
        """
        Sends a joke to the specified chat.
        Deletes the last joke if the setting is enabled.
        Updates the chat with the new message ID and timestamp.
        """
        current_time = int(asyncio.get_event_loop().time())
        joke_view = JokeView(joke=joke)

        # Delete the last message if required
        if chat.setting.delete_last_joke == "yes" and chat.last_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=chat.id, message_id=chat.last_message_id
                )
                logger.info(
                    f"Deleted last message with ID {chat.last_message_id} in chat ID {chat.id}"
                )
            except Exception as e:
                logger.error(f"Failed to delete last message: {e}")
                chat.last_message_id = None  # Reset last_message_id if deletion fails

        try:

            # Send the joke message with the inline keyboard
            message = await context.bot.send_message(
                chat_id=chat.id,
                text=joke_view.format_private_chat(),
                reply_markup=joke_view.get_reaction_keyboard(),
            )

            # Update the chat with the new message ID and timestamp
            chat.last_message_id = message.message_id
            chat.update_last_joke_sent_at(current_time)
            chat.save()

            logger.info(f"Sent joke ID {joke.id} to chat ID {chat.id}")
        except Exception as e:
            logger.error(f"Error while sending joke: {e}")

    async def react_to_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles user reactions to a joke.
        Records the reaction and updates the inline keyboard.
        """
        query = update.callback_query
        try:
            _, joke_id, reaction_id = query.data.split("_")
            joke_id = int(joke_id)
            reaction_id = int(reaction_id)
            user_id = query.from_user.id

            # Record the reaction
            user = User(id=user_id)
            user.react_to_joke(joke_id=joke_id, reaction_id=reaction_id)
            await query.answer("Your reaction has been recorded.")

            # Update the keyboard
            joke = Joke(id=joke_id)
            await self.update_keyboard_reactions(joke=joke, query=query)
        except Exception as e:
            logger.error(f"Error while handling reaction: {e}")
            await query.answer("Failed to process your reaction. Please try again.")

    async def update_keyboard_reactions(self, joke, query):
        """
        Updates the inline keyboard for the joke message with the new reaction options.
        """
        try:
            joke_view = JokeView(joke=joke)
            await query.edit_message_reply_markup(joke_view.get_reaction_keyboard())
            logger.info(f"Updated keyboard for joke ID {joke.id}")
        except Exception as e:
            logger.error(f"Error while updating keyboard: {e}")
            await query.answer("Failed to update the keyboard. Please try again.")

    async def is_user_admin_or_owner(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Verifies if the user issuing the command/callback query is the owner or an admin in a group chat.
        In private chats, any user is allowed to execute commands.
        Returns True if the user is authorized, False otherwise.
        """
        try:
            # Check if the chat is a group or supergroup
            chat_type = update.effective_chat.type
            if chat_type == "private":
                # In private chats, the user is always authorized
                return True

            # Get the user's ID and chat ID
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id

            # Fetch the user's status in the chat
            chat_member = await context.bot.get_chat_member(
                chat_id=chat_id, user_id=user_id
            )

            # Check if the user is an admin or owner
            if chat_member.status == "administrator" or chat_member.status == "creator":
                return True  # User is an admin or owner

            # If the user is not an admin or owner, deny access
            logger.warning(
                f"User {user_id} attempted to execute a restricted command in chat {chat_id}."
            )
            return False
        except Exception as e:
            logger.error(f"Error while verifying user permissions: {e}")
            return False

    async def user_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays the user's profile information, including their role (Owner, Admin, or Member).
        """
        try:
            user = update.effective_user
            chat = update.effective_chat

            chat_member = await context.bot.get_chat_member(
                chat_id=chat.id, user_id=user.id
            )

            # Construct the profile message
            message = (
                f"User ID: {user.id}\n"
                f"Username: {user.username}\n"
                f"First Name: {user.first_name}\n"
                f"Last Name: {user.last_name}\n"
                f"Role/status: {chat_member.status}"
            )

            # Send the profile message
            await update.message.reply_text(message)
            logger.info(f"{message}")
        except Exception as e:
            logger.error(f"Error while displaying user profile: {e}")
            await update.message.reply_text(
                "Failed to retrieve profile information. Please try again."
            )

    def is_private_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Checks if the chat is a private chat.
        Returns True if it is a private chat, False otherwise.
        """
        try:
            chat_type = update.effective_chat.type
            return chat_type == "private"
        except Exception as e:
            logger.error(f"Error while checking chat type: {e}")
            return False

    async def check_is_private_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Checks if the chat is a private chat.
        Returns True if it is a private chat, False otherwise.
        """
        try:
            if not self.is_private_chat(update=update, context=context):
                # i don't want to update the mesage just sent alert to the user as new message or anwser
                # if the chat is not private, send an alert to the user
                await update.message.reply_text(
                    "This command can only be used in private chats."
                )
                # use this function to stop the execution of the command
                return False
            return True
        except Exception as e:
            logger.error(f"Error while checking chat type: {e}")
            await update.message.reply_text(
                "Failed to check chat type. Please try again."
            )
            return False
