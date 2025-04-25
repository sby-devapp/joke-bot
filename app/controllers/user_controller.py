# File: app/controllers/user_controller.py

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.controllers.controller import Controller
from app.db.entities.joke import Joke
from app.db.entities.user import User
from app.db.entities.chat import Chat  # Assuming you have a Chat entity
from app.views.joke_view import JokeView

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(funcName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UserController(Controller):
    """
    Manages interactions related to user-specific actions.
    Handles commands like /start, /myjokes, /myjoke, and callback queries for updating jokes.
    """

    def __init__(self):
        logger.info("Initializing UserController...")

    



    async def react_to_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles reactions to jokes.
        Extracts joke_id and reaction_id from callback_data and processes the reaction.
        """
        try:
            # Get the callback query
            query = update.callback_query
            data = json.loads(query.data)
            logger.info(f"data = {data}")  # Debugging line to check the data format
            joke_id = data.get("joke_id")
            reaction_id = data.get("reaction_id")

            user = await self.get_user(update=update, context=context)
            user.react_to_joke(joke_id=joke_id, reaction_id=reaction_id)
            logger.info(f"User {user.id} reacted to joke_id={joke_id} with reaction_id={reaction_id}")

            joke = Joke(id=joke_id)
            await self.update_keyboard_reactions(joke=joke, query=query)

            # Acknowledge the button press (important to avoid "loading" state on the button)
            await query.answer("Processing your reaction...")
   
        except KeyError:
            logger.error("Missing required fields in callback_data.")
            await query.answer("Oops! The reaction data is incomplete.")
        except Exception as e:
            logger.error(f"Unexpected error while handling reaction: {e}")
            await query.answer("Oops! Something went wrong while processing your reaction.")
            


