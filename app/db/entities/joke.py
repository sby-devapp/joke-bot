# File: app/db/entities/joke.py
from typing import Optional, List, Tuple, Dict
from app.db.db_manager import DBManager
from app.db.entities.tag import Tag
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Joke:
    """
    Represents a joke entity in the database.
    Provides CRUD operations and lazy loading of related entities like tags, reactions, and author.
    """

    db = DBManager()

    def __init__(
        self,
        id: Optional[int] = None,
        add_by: Optional[int] = None,
        content: str = "",
        language_code: str = "en",
        status: str = "draft",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        deleted_at: Optional[str] = None,
    ):
        self.id = id
        self.add_by = add_by
        self.content = content
        self.language_code = language_code
        self.status = status
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.deleted_at = deleted_at

        # Lazy-loaded fields
        self.tags = []  # List of Tag objects or tuples (id, name)
        self.reactions = []  # List of Reaction objects or tuples
        self.user = None  # User who added this joke
        self.language = None  # can have a Language instance

    def _insert(self):
        """
        Inserts a new joke into the database.
        """
        query = """
        INSERT INTO jokes (add_by, content, language_code, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            # Ensure connection is open
            self.db.connect()
            cursor = self.db.connection.cursor()
            cursor.execute(
                query,
                (
                    self.add_by,
                    self.content,
                    self.language_code,
                    self.status,
                    self.created_at,
                    self.updated_at,
                ),
            )

            # Retrieve last inserted ID
            self.id = cursor.lastrowid
            self.db.connection.commit()
            return self
        except Exception as e:
            # Only rollback if connection exists
            if self.db.connection:
                self.db.connection.rollback()
            logger.error(f"Failed to insert joke: {e}")
            raise

    def _update(self) -> "Joke":
        """
        Updates an existing joke in the database.
        Returns self after update.
        """
        if not self.id:
            raise ValueError("Cannot update joke: ID is not set.")

        query = """
        UPDATE jokes
        SET add_by = ?, content = ?, language_code = ?, status = ?, updated_at = ?
        WHERE id = ?
        """
        try:
            self.db.execute(
                query,
                (
                    self.add_by,
                    self.content,
                    self.language_code,
                    self.status,
                    self.updated_at,
                    self.id,
                ),
            )
            logger.info(f"[Joke._update] Updated joke with ID {self.id}")
            return self
        except Exception as e:
            logger.error(f"[Joke._update] Failed to update joke with ID {self.id}: {e}")
            raise

    def save(self) -> "Joke":
        """
        Saves the joke to the database. Inserts a new record if it doesn't exist;
        updates the record if it does.
        Returns the updated Joke instance with proper ID.
        """
        try:
            if self.id:
                return self._update()
            else:
                return self._insert()
        except Exception as e:
            logger.error(f"[Joke.save] Failed to save joke: {e}")
            raise

    def delete(self) -> None:
        """
        Deletes the joke from the database and clears its associations.
        """
        if not self.id:
            logger.warning("[Joke.delete] Cannot delete joke: ID is not set.")
            return

        try:
            self.db.execute("DELETE FROM jokes WHERE id = ?", (self.id,))
            self.db.execute("DELETE FROM joke_tags WHERE joke_id = ?", (self.id,))
            self.db.execute("DELETE FROM joke_reactions WHERE joke_id = ?", (self.id,))
            logger.info(f"[Joke.delete] Deleted joke with ID {self.id}")
        except Exception as e:
            logger.error(f"[Joke.delete] Failed to delete joke with ID {self.id}: {e}")
            raise

    def get(self) -> "Joke":
        """
        Fetches the joke's details from the database based on the ID.
        Returns self after loading data.
        """
        query = """
        SELECT add_by, content, language_code, status, created_at, updated_at
        FROM jokes
        WHERE id = ?
        """
        try:
            result = self.db.fetch_one(query, (self.id,))
            if result:
                (
                    self.add_by,
                    self.content,
                    self.language_code,
                    self.status,
                    self.created_at,
                    self.updated_at,
                ) = result
                logger.info(f"[Joke.get] Loaded joke with ID {self.id}")
            else:
                logger.warning(f"[Joke.get] No joke found with ID {self.id}.")
            return self
        except Exception as e:
            logger.error(f"[Joke.get] Failed to fetch joke with ID {self.id}: {e}")
            raise

    def load_tags(self) -> "Joke":
        """
        Loads associated tags for this joke.
        Returns self after loading tags.
        """
        query = """
        SELECT t.id, t.name
        FROM joke_tags jt
        JOIN tags t ON jt.tag_id = t.id
        WHERE jt.joke_id = ?
        """
        try:
            results = self.db.fetch_all(query, (self.id,))
            for row in results:
                tag = Tag()
                tag.id = int(row[0])
                tag.name = row[1]
                self.tags.append(tag)
            logger.info(
                f"[Joke.load_tags] Loaded {len(self.tags)} tags for joke ID {self.id}"
            )
            return self
        except Exception as e:
            logger.error(
                f"[Joke.load_tags] Failed to load tags for joke ID {self.id}: {e}"
            )
            raise

    def load_reactions(self) -> "Joke":
        """
        Loads associated reactions for this joke.
        Returns self after loading reactions.
        """
        query = """
        SELECT 
            r.id AS id,
            r.name AS reaction,
            COALESCE(COUNT(jr.reaction_id), 0) AS count,
            r.emoji AS emoji
        FROM reactions r
        LEFT JOIN joke_reactions jr ON r.id = jr.reaction_id AND jr.joke_id = ?
        GROUP BY r.id, r.name, r.emoji
        ORDER BY r.id
        """
        try:
            results = self.db.fetch_all(query, (self.id,))
            self.reactions = [(row[0], row[1], row[2], row[3]) for row in results]
            logger.info(
                f"[Joke.load_reactions] Loaded {len(self.reactions)} reactions for joke ID {self.id}"
            )
            return self
        except Exception as e:
            logger.error(
                f"[Joke.load_reactions] Failed to load reactions for joke ID {self.id}: {e}"
            )
            raise

    def load_user(self) -> "Joke":
        """
        Loads the user who added the joke.
        Returns self after loading user.
        """
        try:
            from .user import User

            if self.add_by:
                self.user = User(id=self.add_by).get()
                logger.info(
                    f"[Joke.load_user] Loaded user ID {self.add_by} for joke ID {self.id}"
                )
            else:
                logger.warning("[Joke.load_user] Cannot load user: add_by is not set.")
        except Exception as e:
            logger.error(
                f"[Joke.load_user] Failed to load user for joke ID {self.id}: {e}"
            )
        return self

    def load(self) -> "Joke":
        """
        Fully loads the joke including tags, reactions, and user.
        Returns self after loading all data.
        """
        try:
            if self.id:
                self.get()
                self.load_tags()
                self.load_reactions()
                self.load_user()
                self.load_language()
            else:
                logger.warning("[Joke.load] Cannot load joke: ID is not set.")
            return self
        except Exception as e:
            logger.error(f"[Joke.load] Failed to load joke: {e}")
            raise

    def add_tag(self, tag_id: int) -> "Joke":
        """
        Adds a tag to this joke using tag_id.
        Returns self after adding tag.
        """
        if not self.id:
            logger.warning("[Joke.add_tag] Cannot add tag: Joke ID is not set.")
            return self

        if any(tag[0] == tag_id for tag in self.tags):
            logger.info(
                f"[Joke.add_tag] Tag ID {tag_id} already exists for joke ID {self.id}"
            )
            return self

        query = "INSERT INTO joke_tags (joke_id, tag_id, created_at, updated_at) VALUES (?, ?, ?, ?)"
        try:
            self.db.execute(
                query,
                (
                    self.id,
                    tag_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )
            logger.info(f"[Joke.add_tag] Added tag ID {tag_id} to joke ID {self.id}")
            self.load_tags()
        except Exception as e:
            logger.error(
                f"[Joke.add_tag] Failed to add tag ID {tag_id} to joke ID {self.id}: {e}"
            )
            raise
        return self

    def delete_tag(self, tag_id: int) -> "Joke":
        """
        Removes a tag from this joke.
        Returns self after removing tag.
        """
        if any(tag[0] == tag_id for tag in self.tags):
            query = "DELETE FROM joke_tags WHERE joke_id = ? AND tag_id = ?"
            try:
                self.db.execute(query, (self.id, tag_id))
                logger.info(
                    f"[Joke.delete_tag] Removed tag ID {tag_id} from joke ID {self.id}"
                )
                self.load_tags()
            except Exception as e:
                logger.error(
                    f"[Joke.delete_tag] Failed to remove tag ID {tag_id} from joke ID {self.id}: {e}"
                )
                raise
        else:
            logger.warning(
                f"[Joke.delete_tag] Tag ID {tag_id} not found in joke ID {self.id}"
            )
        return self

    def tags_save(self) -> "Joke":
        """
        Syncs current tags list with the database.
        Returns self after syncing.
        """
        if not self.id:
            logger.warning("[Joke.tags_save] Cannot sync tags: Joke ID is not set.")
            return self

        try:
            # Delete existing tags for this joke
            self.db.execute("DELETE FROM joke_tags WHERE joke_id = ?", (self.id,))
            logger.info(f"[Joke.tags_save] Cleared existing tags for joke ID {self.id}")

            # Insert current tags into joke_tags table
            tag_ids = [tag.id for tag in self.tags]
            for tag_id in tag_ids:
                self.db.execute(
                    "INSERT INTO joke_tags (joke_id, tag_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (
                        self.id,
                        tag_id,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )
            logger.info(
                f"[Joke.tags_save] Synced {len(tag_ids)} tags for joke ID {self.id}"
            )
        except Exception as e:
            logger.error(
                f"[Joke.tags_save] Failed to sync tags for joke ID {self.id}: {e}"
            )
            raise

        return self

    @classmethod
    def get_random_joke(
        cls,
        preferred_language: str,
        tags: Optional[List[Tuple]] = None,
        status: str = "published",
    ) -> Optional["Joke"]:
        """
        Gets a random joke matching the given criteria.
        Returns a Joke object or None.
        """
        try:
            query = "SELECT id FROM jokes WHERE language_code = ? AND status = ?"
            params = [preferred_language, status]

            if tags:
                tag_ids = [t[0] for t in tags]
                placeholders = ", ".join("?" * len(tag_ids))
                query += f" AND id IN (SELECT joke_id FROM joke_tags WHERE tag_id IN ({placeholders}))"
                params.extend(tag_ids)

            results = cls.db.fetch_all(query, tuple(params))
            if not results:
                return None

            joke_id = random.choice([row[0] for row in results])
            return cls(id=joke_id).load()
        except Exception as e:
            logger.error(
                f"[Joke.get_random_joke] Error while fetching random joke: {e}"
            )
            raise

    def has_tag(self, tag_id: int) -> bool:
        """
        Check if the joke has a tag with the given tag_id in the database.
        Returns True if the tag exists, otherwise False.
        """
        if not self.id:
            logger.warning("[Joke.has_tag] Cannot check tags: Joke ID is not set.")
            return False

        try:
            query = """
            SELECT 1
            FROM joke_tags
            WHERE joke_id = ? AND tag_id = ?
            LIMIT 1
            """
            result = self.db.fetch_one(query, (self.id, tag_id))
            return result is not None
        except Exception as e:
            logger.error(
                f"[Joke.has_tag] Failed to check tag ID {tag_id} for joke ID {self.id}: {e}"
            )
            raise

    def load_language(self):
        """
        Loads the language details for the joke's language_code.
        Returns self after loading the language.
        """
        from app.db.entities.language import Language  # Ensure Language is imported

        if not self.language_code:
            logger.warning(
                "[Joke.load_language] Cannot load language: language_code is not set."
            )
            return self

        try:
            self.language = Language(code=self.language_code).get()
            logger.info(
                f"[Joke.load_language] Loaded language details for code {self.language_code}"
            )
        except Exception as e:
            logger.error(
                f"[Joke.load_language] Failed to load language for code {self.language_code}: {e}"
            )
            self.language = None
