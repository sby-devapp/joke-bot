from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from app.controllers.controller import Controller
from app.db.entities.joke import Joke
from app.db.entities.language import Language
from app.db.entities.tag import Tag
from app.views.joke_view import JokeView

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(funcName)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)

# Define conversation states


class UserController(Controller):

    def __init__(self):
        """
        Initializes the UserController.
        """
        print("")
