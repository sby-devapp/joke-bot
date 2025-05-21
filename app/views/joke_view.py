# File: app/views/joke_view.py

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json

from app.db.entities.joke import Joke
from app.db.entities.user import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


class JokeView:
    """
    Formats a joke into a visually appealing design for presentation.
    Generates an inline keyboard for reactions.
    """

    break_line = "_" * 30 + "\n"

    def __init__(self, joke):
        """
        Initializes the JokeView with a Joke object.
        """
        self.joke = joke

    def format_my_joke(self):
        """
        Formats the joke for display in the user's list of jokes.
        """
        return self._format_joke()

    def edit_joke_keyboard(self):
        """
        Generates an inline keyboard for editing the joke.
        """
        buttons = [
            InlineKeyboardButton("Edit", callback_data=f"edit_joke_{self.joke.id}"),
            InlineKeyboardButton("Delete", callback_data=f"delete_joke_{self.joke.id}"),
            InlineKeyboardButton(
                "Puplish" if self.joke.status == "pending" else "Pending",
                callback_data=f"set_status_joke_{self.joke.id}_{'published' if self.joke.status == 'pending' else 'pending'}",
            ),
        ]
        return InlineKeyboardMarkup([buttons])

    def format_private_chat(self):
        """
        Formats the joke for private chat display.
        """
        return self._format_joke()

    def _format_joke(self):
        """
        Formats the joke content, tags, reactions, and metadata into the desired structure.
        """
        # Define the separator line

        # Format joke content
        joke_content = f"{self.break_line}{self.joke.content}\n{self.break_line}"

        # Format metadata (Added by and tags)
        added_by = (
            f"Added by: @{self.joke.user.username}"
            if self.joke.user and self.joke.user.username
            else "Added by: Unknown"
        )

        # Extract tag names and format them as hashtags
        tags = (
            ", ".join([f"#{tag.name}" for tag in self.joke.tags])
            if self.joke.tags
            else "No tags"
        )
        metadata = f"{added_by}\nTags: {tags}\n"
        metadata += f"Language: {self.joke.language.name}"

        # Combine all parts
        formatted_joke = f"{joke_content}\n" f"{metadata}\n" f"{self.break_line}"

        logger.info(
            f"Formatted joke successfully: joke_id={self.joke.id}, content={formatted_joke}"
        )
        return formatted_joke

    def get_reaction_keyboard(self):
        """
        Generates an inline keyboard with allowed emojis.
        Buttons are displayed in a single row or split into multiple rows if there are more than 8 reactions.
        """
        self.joke.load_reactions()
        # Load reactions from the joke object
        reactions = self.joke.reactions

        # Handle empty reactions
        if not reactions:
            logger.warning("No reactions available for the joke.")
            return InlineKeyboardMarkup(
                [[InlineKeyboardButton("No reactions", callback_data="no_reactions")]]
            )

        # Create buttons with a maximum of 8 per row
        buttons = [
            InlineKeyboardButton(
                f"{emoji} ({count})",
                callback_data=f"react_{self.joke.id}_{reaction_id}",
            )
            for reaction_id, reaction_type, count, emoji in reactions
        ]

        # Split buttons into rows of 8
        rows = [buttons[i : i + 8] for i in range(0, len(buttons), 8)]
        return InlineKeyboardMarkup(rows)

    def get_joke_data(self):
        """
        Returns the joke data in JSON format.
        """
        joke_data = {
            "id": self.joke.id,
            "content": self.joke.content,
            "language_code": self.joke.language_code,
            "tags": [tag[1] for tag in self.joke.tags],
            "status": self.joke.status,
            "added_by": self.joke.user.username if self.joke.user else None,
        }
        return json.dumps(joke_data, indent=4)

    def temp_joke(self, joke=None, user=None, language_code="en", content=None):
        """
        Returns a temporary joke for testing purposes.
        """
        # create a temporary joke object
        if joke is None:
            joke = Joke()
        if user:
            joke.added_by = user.id
            joke.user = user
        if language_code:
            joke.language_code = language_code
        if content:
            joke.content = content

        # Set default values for the joke object
        joke.status = "draft"

        return joke
