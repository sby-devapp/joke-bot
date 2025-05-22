# File: app/db/entities/user.py

import logging
from typing import Optional, List
from app.db.db_manager import DBManager
from app.db.entities.joke import Joke


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(funcName)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


class User:
    """
    Represents a user and their interactions with jokes.
    Manages reactions, joke additions, and other user-specific actions.
    """

    # Static DBManager instance shared by all User instances
    db = DBManager()

    def __init__(self, id=None, username=None):
        """
        Initializes a User object.
        If id is provided, loads the user's data from the database.
        """
        self.id = id
        self.username = username

        if self.id and self.is_exists():
            self.load()

    def load(self):
        """
        Loads user data from the database based on the ID.
        """
        query = "SELECT id, username FROM users WHERE id = ?"
        try:
            result = self.db.fetch_one(query, (self.id,))
            if result:
                self.id, self.username = result
                # logger.info(f"Loaded user with ID {self.id}: username={self.username}")
            else:
                logger.warning(f"No user found with ID {self.id}.")
        except Exception as e:
            logger.error(f"Failed to load user with ID {self.id}: {e}")
            raise

    def is_exists(self) -> bool:
        """
        Checks if the user exists in the database.
        Returns True if the user exists, False otherwise.
        """
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE id = ?)"
        try:
            result = self.db.fetch_one(query, (self.id,))
            exists = bool(result[0])
            logger.info(
                f"Checked existence of user with ID {self.id}: {'Exists' if exists else 'Does not exist'}"
            )
            return exists
        except Exception as e:
            logger.error(f"Failed to check user existence for ID {self.id}: {e}")
            raise

    def _insert(self) -> "User":
        """
        Inserts a new user into the database.
        """
        query = "INSERT INTO users (id, username) VALUES (?, ?)"
        try:
            self.db.execute(query, (self.id, self.username))
            # logger.info(f"Inserted new user with ID {self.id}: username={self.username}")
            return self
        except Exception as e:
            logger.error(f"Failed to insert user with ID {self.id}: {e}")
            raise

    def _update(self) -> "User":
        """
        Updates an existing user in the database.
        """
        query = "UPDATE users SET username = ? WHERE id = ?"
        try:
            self.db.execute(query, (self.username, self.id))
            # logger.info(f"Updated user with ID {self.id}: username={self.username}")
            return self
        except Exception as e:
            logger.error(f"Failed to update user with ID {self.id}: {e}")
            raise

    def save(self) -> "User":
        """
        Saves the user to the database.
        Inserts a new record if it doesn't exist; updates the record if it does.
        """
        try:
            if self.is_exists():
                # logger.info(f"User with ID {self.id} already exists. Updating...")
                self._update()
            else:
                # logger.info(f"No user found with ID {self.id}. Inserting...")
                self._insert()
            return self
        except Exception as e:
            logger.error(f"Failed to save user with ID {self.id}: {e}")
            raise

    def get(self) -> "User":
        """
        Fetches the user from the database and updates the object's attributes.
        """
        query = "SELECT id, username FROM users WHERE id = ?"
        try:
            result = self.db.fetch_one(query, (self.id,))
            if result:
                self.id, self.username = result
                # logger.info(f"Fetched user with ID {self.id}: username={self.username}")
                return self
            else:
                # logger.warning(f"No user found with ID {self.id}.")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch user with ID {self.id}: {e}")
            raise

    def react_to_joke(self, joke_id: int, reaction_id: int):
        """
        Records, updates, or deletes a user's reaction to a joke in the database.
        - Inserts a new reaction if none exists.
        - Deletes the reaction if the user reacts with the same reaction_id again.
        - Updates the reaction if the user reacts with a different reaction_id.
        """
        try:
            # Step 1: Check if the user has already reacted to the joke
            query_check = """
            SELECT reaction_id FROM joke_reactions
            WHERE user_id = ? AND joke_id = ?
            """
            result = self.db.fetch_one(query_check, (self.id, joke_id))

            if result:
                existing_reaction_id = result[0]

                if existing_reaction_id == reaction_id:
                    # Case 1: User reacts with the same reaction -> Delete the reaction
                    query_delete = """
                    DELETE FROM joke_reactions
                    WHERE user_id = ? AND joke_id = ?
                    """
                    self.db.execute(query_delete, (self.id, joke_id))
                    # logger.info(f"Deleted reaction: user_id={self.id}, joke_id={joke_id}")
                else:
                    # Case 2: User reacts with a different reaction -> Update the reaction
                    query_update = """
                    UPDATE joke_reactions
                    SET reaction_id = ?
                    WHERE user_id = ? AND joke_id = ?
                    """
                    self.db.execute(query_update, (reaction_id, self.id, joke_id))
                    # logger.info(f"Updated reaction: user_id={self.id}, joke_id={joke_id}, new_reaction_id={reaction_id}")
            else:
                # Case 3: No existing reaction -> Insert a new reaction
                query_insert = """
                INSERT INTO joke_reactions (user_id, joke_id, reaction_id)
                VALUES (?, ?, ?)
                """
                self.db.execute(query_insert, (self.id, joke_id, reaction_id))
                # logger.info(f"Inserted new reaction: user_id={self.id}, joke_id={joke_id}, reaction_id={reaction_id}")

        except Exception as e:
            logger.error(
                f"Failed to process reaction for user_id={self.id}, joke_id={joke_id}: {e}"
            )
            raise

    def my_jokes(self, where=None) -> List[Joke]:

        query = """
        SELECT *
        FROM jokes
        WHERE add_by = ?
        """
        if where != None:
            query = query + where

        jokes = []
        try:
            results = self.db.fetch_all(query, (self.id,))
            for row in results:
                joke = Joke()
                joke.id = row[0]
                joke.added_by = row[1]
                joke.language_code = row[2]
                joke.content = row[3]
                joke.status = row[4]
                joke.created_at = row[5]
                joke.updated_at = row[6]
                joke.deleted_at = row[7]

                jokes.append(joke)
            return jokes
        except Exception as e:
            logger.error(f"Failed to fetch jokes for user with ID {self.id}: {e}")
            raise
