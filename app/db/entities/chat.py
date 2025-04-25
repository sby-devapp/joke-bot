# File: app/db/entities/chat.py

from app.db.db_manager import DBManager
from app.db.entities.user import User
from app.db.entities.setting import Setting
from app.db.entities.joke import Joke

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class Chat:
    """
    Represents a chat and its associated settings.
    Manages interactions with the 'chats' table in the database.
    """
    db = DBManager()

    def __init__(self, chat_id=None):
        """
        Initializes a Chat object.
        If chat_id is provided, loads the chat's data from the database.
        """
        self.id = chat_id
        self.type = None
        self.username = None
        self.last_message_id = None
        self.user_id = None
        self.last_joke_sent_at = 0  # Timestamp of the last joke sent (default: 0)

        # Associated entities
        self.user = None
        self.setting = None

        if self.id and self.is_exists():
            self.load()

    def load(self):
        """
        Loads chat data from the database based on the ID.
        """
        query = """
        SELECT type, username, last_message_id, user_id, last_joke_sent_at
        FROM chats
        WHERE id = ?
        """
        try:
            result = self.db.fetch_one(query, (self.id,))
            if result:
                self.type, self.username, self.last_message_id, self.user_id, self.last_joke_sent_at = result
                
                # Load the associated user
                self.user = User(id=self.user_id)
                self.user.load()

                # Load or create the associated setting
                self.setting = Setting(chat_id=self.id)
                if self.setting.is_exists():
                    self.setting.load()
                else:
                    self.setting.default_setting()
            else:
                logger.warning(f"No chat found with ID {self.id}.")
        except Exception as e:
            logger.error(f"Failed to load chat with ID {self.id}: {e}")
            raise

    def is_exists(self) -> bool:
        """
        Checks if a chat exists for the given chat_id.
        Returns True if the chat exists, False otherwise.
        """
        query = "SELECT EXISTS(SELECT 1 FROM chats WHERE id = ?)"
        try:
            result = self.db.fetch_one(query, (self.id,))
            exists = bool(result[0])
            #logger.info(f"Checked existence of chat with ID {self.id}: {'Exists' if exists else 'Does not exist'}")
            return exists
        except Exception as e:
            logger.error(f"Failed to check chat existence for ID {self.id}: {e}")
            raise

    def save(self):
        """
        Saves the chat to the database.
        Inserts a new record if it doesn't exist; updates the record if it does.
        """
        try:
            if self.is_exists():
                #logger.info(f"Updating chat with ID {self.id}...")
                self._update()
            else:
                #logger.info(f"Inserting new chat with ID {self.id}...")
                self._insert()
        except Exception as e:
            logger.error(f"Failed to save chat with ID {self.id}: {e}")
            raise

    def delete(self):
        """
        Deletes the chat from the database.
        Also deletes the associated setting but keeps the user intact.
        """
        query = "DELETE FROM chats WHERE id = ?"
        try:
            self.db.execute(query, (self.id,))
            #logger.info(f"Deleted chat with ID {self.id}")

            # Delete the associated setting
            if self.setting:
                self.setting.delete()
                #logger.info(f"Deleted setting for chat with ID {self.id}")
        except Exception as e:
            logger.error(f"Failed to delete chat with ID {self.id}: {e}")
            raise

    def _insert(self):
        """
        Inserts a new chat into the database.
        """
        query = """
        INSERT INTO chats (id, type, username, last_message_id, user_id, last_joke_sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            self.db.execute(query, (
                self.id,
                self.type,
                self.username,
                self.last_message_id,
                self.user_id,
                self.last_joke_sent_at
            ))
            #logger.info(f"Inserted new chat with ID {self.id}")
        except Exception as e:
            logger.error(f"Failed to insert chat with ID {self.id}: {e}")
            raise

    def _update(self):
        """
        Updates an existing chat in the database.
        """
        query = """
        UPDATE chats
        SET type = ?, username = ?, last_message_id = ?, user_id = ?, last_joke_sent_at = ?
        WHERE id = ?
        """
        try:
            self.db.execute(query, (
                self.type,
                self.username,
                self.last_message_id,
                self.user_id,
                self.last_joke_sent_at,
                self.id
            ))
            #logger.info(f"Updated chat with ID {self.id}")
        except Exception as e:
            logger.error(f"Failed to update chat with ID {self.id}: {e}")
            raise

    def update_last_joke_sent_at(self, timestamp: int):
        """
        Updates the last_joke_sent_at timestamp in the database.
        """
        query = "UPDATE chats SET last_joke_sent_at = ? WHERE id = ?"
        try:
            self.db.execute(query, (timestamp, self.id))
            self.last_joke_sent_at = timestamp
            #logger.info(f"Updated last_joke_sent_at for chat ID {self.id} to {timestamp}")
        except Exception as e:
            logger.error(f"Failed to update last_joke_sent_at for chat ID {self.id}: {e}")
            raise

    def reset_settings(self):
        """
        Resets the chat's settings to default values.
        """
        if self.setting:
            self.setting.reset_settings()
            #logger.info(f"Reset settings for chat ID {self.id}")


    
    def get_random_joke(self):
        """
        Fetches a random joke based on the chat's preferred language and tags.
        Returns a Joke object representing the selected joke, or None if no matching jokes are found.
        """
        try:
            # Extract preferred tags as a list of tag IDs
            preferred_tags = self.setting.preferred_tags  # List of tuples (id, name)
            tag_ids = [tag[0] for tag in preferred_tags] if preferred_tags else []

            # Get the preferred language
            preferred_language = self.setting.preferred_language

            # Fetch a random joke using the Joke class
            joke = Joke.get_random_joke(
                preferred_language=preferred_language,
                tags=preferred_tags,  # Pass the full list of tuples (id, name)
                status="published"
            )

            if joke:
                #logger.info(f"Selected random joke ID {joke.id} for chat ID {self.id}")
                return joke
            else:
                logger.warning("No jokes found matching the chat's preferences.")
                return None

        except Exception as e:
            logger.error(f"Error while fetching a random joke for chat ID {self.id}: {e}")
            raise
        