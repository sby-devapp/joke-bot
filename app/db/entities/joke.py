# File: app/db/entities/joke.py

from typing import Optional, Dict, List, Tuple
from app.db.db_manager import DBManager
from app.db.entities.user import User  # Import the User class
import random

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


class Joke:
    """
    Represents a joke and its associated attributes.
    Manages interactions with the 'jokes' table in the database.
    Implements lazy loading for tags, reactions, and user.
    """
    db = DBManager()

    def __init__(self, id=None):
        """
        Initializes a Joke object.
        If joke_id is provided, loads the joke's basic details from the database.
        """
        self.id = id
        self.add_by = None  # Foreign key pointing to the User who added the joke
        self.content = None
        self.language_code = None
        self.status = None

        self.created_at = None
        self.updated_at = None

        # Lazy-loaded attributes
        self.tags = []  # List of tuples/dict (id, tag)
        self.reactions = []  # List of tuples/dict (id, reaction, count, emoji)
        self.user = None  # Must be None or an instance of User()

        if self.id:
            self.load()

    def _insert(self):
        """
        Inserts a new joke into the database.
        """
        query = """
        INSERT INTO jokes (add_by, content, language_code, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            self.db.execute(query, (
                self.add_by,
                self.content,
                self.language_code,
                self.status,
                self.created_at,
                self.updated_at
            ))
            #logger.info(f"Inserted new joke with ID {self.id}")
        except Exception as e:
            logger.error(f"Failed to insert joke: {e}")
            raise

    def _update(self):
        """
        Updates an existing joke in the database.
        """
        query = """
        UPDATE jokes
        SET add_by = ?, content = ?, language_code = ?, status = ?, updated_at = ?
        WHERE id = ?
        """
        try:
            self.db.execute(query, (
                self.add_by,
                self.content,
                self.language_code,
                self.status,
                self.updated_at,
                self.id
            ))
            #logger.info(f"Updated joke with ID {self.id}")
        except Exception as e:
            logger.error(f"Failed to update joke with ID {self.id}: {e}")
            raise

    def save(self):
        """
        Saves the joke to the database.
        Inserts a new record if it doesn't exist; updates the record if it does.
        """
        try:
            if self.id:
                self._update()
            else:
                self._insert()
        except Exception as e:
            logger.error(f"Failed to save joke: {e}")
            raise

    def delete(self):
        """
        Deletes the joke from the database.
        Also clears associated tags and reactions.
        """
        try:
            query = "DELETE FROM jokes WHERE id = ?"
            self.db.execute(query, (self.id,))
            #logger.info(f"Deleted joke with ID {self.id}")

            # Clear associated tags and reactions
            self.db.execute("DELETE FROM joke_tags WHERE joke_id = ?", (self.id,))
            self.db.execute("DELETE FROM joke_reactions WHERE joke_id = ?", (self.id,))
            #logger.info(f"Cleared tags and reactions for joke ID {self.id}")
        except Exception as e:
            logger.error(f"Failed to delete joke with ID {self.id}: {e}")
            raise

    def get(self):
        """
        Fetches the joke's details from the database based on the ID.
        """
        query = """
        SELECT add_by, content, language_code, status, created_at, updated_at
        FROM jokes
        WHERE id = ?
        """
        try:
            result = self.db.fetch_one(query, (self.id,))
            if result:
                self.add_by, self.content, self.language_code, self.status, self.created_at, self.updated_at = result
                #logger.info(f"Loaded joke with ID {self.id}: "
                            #f"content={self.content}, language_code={self.language_code}, status={self.status}")
            else:
                logger.warning(f"No joke found with ID {self.id}.")
        except Exception as e:
            logger.error(f"Failed to fetch joke with ID {self.id}: {e}")
            raise

    def load_tags(self):
        """
        Loads the tags associated with the joke.
        """
        query = """
        SELECT t.id, t.name
        FROM joke_tags jt
        JOIN tags t ON jt.tag_id = t.id
        WHERE jt.joke_id = ?
        """
        try:
            results = self.db.fetch_all(query, (self.id,))
            self.tags = [(row[0], row[1]) for row in results]
            #logger.info(f"Loaded tags for joke ID {self.id}: {self.tags}")
        except Exception as e:
            logger.error(f"Failed to load tags for joke ID {self.id}: {e}")
            raise

    def load_reactions(self):
        """
        Loads the reactions associated with the joke.
        Populates the `reactions` attribute as a list of tuples: (id, reaction, count, emoji).
        Includes all reactions, even those with a count of 0.
        """
        query = """
        SELECT 
            r.id AS id,
            r.name AS reaction,
            COALESCE(COUNT(jr.reaction_id), 0) AS count,
            r.emoji AS emoji
        FROM 
            reactions r
        LEFT JOIN 
            joke_reactions jr ON r.id = jr.reaction_id AND jr.joke_id = ?
        GROUP BY 
            r.id, r.name, r.emoji
        ORDER BY
            r.id
        """
        try:
            # Execute the query and fetch all results
            results = self.db.fetch_all(query, (self.id,))
            
            # Populate the `reactions` attribute as a list of tuples
            self.reactions = [
                (row[0], row[1], row[2], row[3])  # (id, reaction, count, emoji)
                for row in results
            ]
            
            #(f"Loaded reactions for joke ID {self.id}: {self.reactions}")
        except Exception as e:
            logger.error(f"Failed to load reactions for joke ID {self.id}: {e}")
            raise

    def load_user(self):
        """
        Loads the user who added the joke.
        """
        try:
            self.user = User(id=self.add_by)
            self.user.load()
            #logger.info(f"Loaded user for joke ID {self.id}: user_id={self.user.id}, username={self.user.username}")
        except Exception as e:
            logger.error(f"Failed to load user for joke ID {self.id}: {e}")
            raise

    def load(self):
        """
        Loads the joke's details, tags, reactions, and user.
        """
        try:
            if self.id:
                self.get()  # Load joke details
                self.load_tags()  # Load tags
                self.load_reactions()  # Load reactions
                self.load_user()  # Load user
            else:
                logger.warning("Cannot load joke: ID is not set.")
        except Exception as e:
            logger.error(f"Failed to load joke: {e}")
            raise

    def add_tag(self, tag_id: int):
        """
        Adds a tag to the joke and updates the database.
        """
        if tag_id not in [tag[0] for tag in self.tags]:
            query = "INSERT INTO joke_tags (joke_id, tag_id) VALUES (?, ?)"
            try:
                self.db.execute(query, (self.id, tag_id))
                #logger.info(f"Added tag_id {tag_id} to joke ID {self.id}")
                self.load_tags()  # Reload tags after adding
            except Exception as e:
                logger.error(f"Failed to add tag_id {tag_id} to joke ID {self.id}: {e}")
                raise
        else:
            logger.warning(f"Tag_id {tag_id} is already associated with joke ID {self.id}")

    def delete_tag(self, tag_id: int):
        """
        Removes a tag from the joke and updates the database.
        """
        if tag_id in [tag[0] for tag in self.tags]:
            query = "DELETE FROM joke_tags WHERE joke_id = ? AND tag_id = ?"
            try:
                self.db.execute(query, (self.id, tag_id))
                #logger.info(f"Removed tag_id {tag_id} from joke ID {self.id}")
                self.load_tags()  # Reload tags after removing
            except Exception as e:
                logger.error(f"Failed to remove tag_id {tag_id} from joke ID {self.id}: {e}")
                raise
        else:
            logger.warning(f"Tag_id {tag_id} is not associated with joke ID {self.id}")



    @classmethod
    def get_random_joke(cls, preferred_language: str, tags: Optional[List[Tuple[int, str]]] = None, status: str = "approved"):
        """
        Fetches a random joke that matches the given criteria:
        - preferred_language: The language code of the joke (e.g., 'en', 'fr').
        - tags: A list of tag tuples (id, name) to filter jokes by (optional).
        - status: The status of the joke (default: 'approved').

        Returns:
        - A Joke object representing the selected joke, or None if no matching jokes are found.
        """
        try:
            # Base query to fetch jokes
            query = """
            SELECT j.id
            FROM jokes j
            """

            # Add JOINs and WHERE clauses based on the criteria
            conditions = ["j.language_code = ?", "j.status = ?"]
            params = [preferred_language, status]

            if tags:
                # Extract tag IDs from the list of tuples
                tag_ids = [tag[0] for tag in tags]

                # Join with joke_tags to filter by tag IDs
                query += """
                INNER JOIN joke_tags jt ON j.id = jt.joke_id
                """
                tag_placeholders = ", ".join(["?"] * len(tag_ids))
                conditions.append(f"jt.tag_id IN ({tag_placeholders})")
                params.extend(tag_ids)

            # Combine conditions
            query += " WHERE " + " AND ".join(conditions)

            # Group by joke ID to handle multiple tags per joke
            query += " GROUP BY j.id"


            logger.info(f"EXECUTE Query: {query}")
            # Fetch all matching joke IDs
            results = cls.db.fetch_all(query, tuple(params))
            joke_ids = [row[0] for row in results]

            if not joke_ids:
                #logger.info("No jokes found matching the given criteria.")
                return None

            # Select a random joke ID
            random_joke_id = random.choice(joke_ids)
            
               
            # Load and return the corresponding Joke object
            joke = cls(id=random_joke_id)
            joke.load()
            logger.info(f"Fetched random joke ID {joke.id} with content: {joke.content}")
            return joke

        except Exception as e:
            logger.error(f"Error while fetching a random joke: {e}")
            raise

    def is_exists(self) -> bool:
        """
        Checks if the joke exists in the database.
        Returns True if the joke exists, False otherwise.
        """
        query = "SELECT EXISTS(SELECT 1 FROM jokes WHERE id = ?)"
        if not self.id:
            return False  # If ID is not set, joke cannot exist
        #logger.info(f"Checking existence of joke with ID {self.id}")   
        try:
            result = self.db.fetch_one(query, (self.id,))
            exists = bool(result[0])
            #logger.info(f"Checked existence of joke with ID {self.id}: {'Exists' if exists else 'Does not exist'}")
            return exists
        except Exception as e:
            logger.error(f"Failed to check existence of joke with ID {self.id}: {e}")
            raise