# File: app/db/entities/setting.py

from app.db.db_manager import DBManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


class Setting:
    """
    Represents a setting for a specific chat in the 'settings' table.
    Manages CRUD operations for settings, including preferred tags.
    """

    db = DBManager()

    def __init__(
        self,
        id=None,
        chat_id=None,
        preferred_language=None,
        schedule=None,
        sending_jokes=None,
        delete_last_joke=None,
    ):
        """
        Initializes a Setting object.
        """
        self.id = id
        self.chat_id = chat_id
        self.preferred_language = preferred_language
        self.schedule = schedule
        self.sending_jokes = sending_jokes
        self.delete_last_joke = delete_last_joke
        self.preferred_tags = []  # List of (id, name) tuples

        # Load settings if chat_id is provided
        if self.chat_id:
            self.load()
        else:
            logger.warning(
                "Setting object initialized without chat_id. Default settings will not be applied."
            )

    def _insert(self):
        """
        Inserts a new setting into the database.
        """
        query = """
        INSERT INTO settings (chat_id, preferred_language, schedule, sending_jokes, delete_last_joke)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.db.execute(
                query,
                (
                    self.chat_id,
                    self.preferred_language,
                    self.schedule,
                    self.sending_jokes,
                    self.delete_last_joke,
                ),
            )
            logger.info(f"Inserted new setting for chat_id {self.chat_id}")
        except Exception as e:
            logger.error(f"Failed to insert setting for chat_id {self.chat_id}: {e}")
            raise

    def _update(self):
        """
        Updates an existing setting in the database.
        """
        query = """
        UPDATE settings
        SET preferred_language = ?, schedule = ?, sending_jokes = ?, delete_last_joke = ?
        WHERE chat_id = ?
        """
        try:
            self.db.execute(
                query,
                (
                    self.preferred_language,
                    self.schedule,
                    self.sending_jokes,
                    self.delete_last_joke,
                    self.chat_id,
                ),
            )
            logger.info(f"Updated setting for chat_id {self.chat_id}")
        except Exception as e:
            logger.error(f"Failed to update setting for chat_id {self.chat_id}: {e}")
            raise

    def is_exists(self) -> bool:
        """
        Checks if a setting exists for the given chat_id.
        Returns True if the setting exists, False otherwise.
        """
        query = "SELECT EXISTS(SELECT 1 FROM settings WHERE chat_id = ?)"
        try:
            result = self.db.fetch_one(query, (self.chat_id,))
            exists = bool(result[0])
            logger.info(
                f"Checked existence of setting for chat_id {self.chat_id}: {'Exists' if exists else 'Does not exist'}"
            )
            return exists
        except Exception as e:
            logger.error(
                f"Failed to check setting existence for chat_id {self.chat_id}: {e}"
            )
            raise

    def save(self):
        """
        Saves the setting to the database.
        Inserts a new record if it doesn't exist; updates the record if it does.
        """
        try:
            if self.is_exists():
                logger.info(
                    f"Setting for chat_id {self.chat_id} already exists. Updating..."
                )
                self._update()
            else:
                logger.info(
                    f"No setting found for chat_id {self.chat_id}. Inserting..."
                )
                self._insert()
        except Exception as e:
            logger.error(f"Failed to save setting for chat_id {self.chat_id}: {e}")
            raise

    def default_setting(self):
        """
        Sets the default values for the setting and inserts it if it doesn't exist.
        """
        try:
            if not self.is_exists():
                logger.info(
                    f"No setting found for chat_id {self.chat_id}. Applying default settings..."
                )
                self._default_setting()
                self._insert()
            else:
                logger.info(
                    f"Setting already exists for chat_id {self.chat_id}. Skipping default application."
                )
        except Exception as e:
            logger.error(
                f"Failed to apply default setting for chat_id {self.chat_id}: {e}"
            )
            raise

    def reset_settings(self):
        """
        Resets the setting to its default values and updates the database.
        """
        try:
            logger.info(
                f"Resetting settings for chat_id {self.chat_id} to default values..."
            )
            self._default_setting()
            self.save()
        except Exception as e:
            logger.error(f"Failed to reset settings for chat_id {self.chat_id}: {e}")
            raise

    def _default_setting(self):
        """
        Sets the default values for the setting.
        """
        try:
            self.preferred_language = "en"
            self.schedule = 600  # 10 minutes
            self.sending_jokes = "off"  # Sending jokes should be off by default
            self.delete_last_joke = "yes"  # Delete last joke should be no
            self.preferred_tags = []  # Reset preferred tags
            logger.info(f"Applied default settings for chat_id {self.chat_id}")
        except Exception as e:
            logger.error(
                f"Failed to apply default settings for chat_id {self.chat_id}: {e}"
            )
            raise

    def delete(self):
        """
        Deletes the setting for the given chat_id from the database.
        Also clears the preferred_tags association.
        """
        try:
            logger.info(f"Deleting setting for chat_id {self.chat_id}...")
            self.db.execute("DELETE FROM settings WHERE chat_id = ?", (self.chat_id,))
            self.db.execute(
                "DELETE FROM preferred_tags WHERE chat_id = ?", (self.chat_id,)
            )
            logger.info(
                f"Deleted setting and cleared preferred tags for chat_id {self.chat_id}"
            )
        except Exception as e:
            logger.error(f"Failed to delete setting for chat_id {self.chat_id}: {e}")
            raise

    def load(self):
        """
        Loads the setting from the database if it exists; otherwise, applies default settings.
        Also loads the preferred tags.
        """
        try:
            if self.chat_id:
                if self.is_exists():
                    logger.info(
                        f"Loading existing settings for chat_id {self.chat_id}..."
                    )
                    self.get()  # Load attributes from the database
                    self.load_preferred_tags()  # Load preferred tags
                else:
                    logger.info(
                        f"No settings found for chat_id {self.chat_id}. Applying default settings..."
                    )
                    self.default_setting()  # Apply default values and save them in the database
            else:
                logger.warning("Cannot load settings: chat_id is not set.")
        except Exception as e:
            logger.error(f"Failed to load settings for chat_id {self.chat_id}: {e}")
            raise

    def get(self):
        """
        Fetches the setting from the database and updates the object's attributes.
        """
        query = """
        SELECT id, preferred_language, schedule, sending_jokes, delete_last_joke
        FROM settings
        WHERE chat_id = ?
        """
        try:
            result = self.db.fetch_one(query, (self.chat_id,))
            if result:
                (
                    self.id,
                    self.preferred_language,
                    self.schedule,
                    self.sending_jokes,
                    self.delete_last_joke,
                ) = result
                logger.info(
                    f"Loaded settings for chat_id {self.chat_id}: "
                    f"preferred_language={self.preferred_language}, "
                    f"schedule={self.schedule}, "
                    f"sending_jokes={self.sending_jokes}, "
                    f"delete_last_joke={self.delete_last_joke}"
                )
            else:
                logger.warning(f"No settings found for chat_id {self.chat_id}.")
        except Exception as e:
            logger.error(f"Failed to fetch settings for chat_id {self.chat_id}: {e}")
            raise

    def load_preferred_tags(self):
        """
        Loads the preferred tags for the chat_id from the preferred_tags table.
        """
        query = """
        SELECT t.id, t.name
        FROM preferred_tags pt
        JOIN tags t ON pt.tag_id = t.id
        WHERE pt.chat_id = ?
        """
        try:
            results = self.db.fetch_all(query, (self.chat_id,))
            self.preferred_tags = [(row[0], row[1]) for row in results]
            logger.info(
                f"Loaded preferred tags for chat_id {self.chat_id}: {self.preferred_tags}"
            )
        except Exception as e:
            logger.error(
                f"Failed to load preferred tags for chat_id {self.chat_id}: {e}"
            )
            raise

    def add_preferred_tag(self, tag_id: int):
        """
        Adds a tag to the preferred_tags list and updates the database.
        """
        if tag_id not in [tag[0] for tag in self.preferred_tags]:
            query = "INSERT INTO preferred_tags (chat_id, tag_id) VALUES (?, ?)"
            try:
                self.db.execute(query, (self.chat_id, tag_id))
                logger.info(
                    f"Added tag_id {tag_id} to preferred_tags for chat_id {self.chat_id}"
                )
                self.load_preferred_tags()  # Reload preferred tags after adding
            except Exception as e:
                logger.error(
                    f"Failed to add tag_id {tag_id} to preferred_tags for chat_id {self.chat_id}: {e}"
                )
                raise
        else:
            logger.warning(
                f"Tag_id {tag_id} is already in preferred_tags for chat_id {self.chat_id}"
            )

    def remove_preferred_tag(self, tag_id: int):
        """
        Removes a tag from the preferred_tags list and updates the database.
        """
        if tag_id in [tag[0] for tag in self.preferred_tags]:
            query = "DELETE FROM preferred_tags WHERE chat_id = ? AND tag_id = ?"
            try:
                self.db.execute(query, (self.chat_id, tag_id))
                logger.info(
                    f"Removed tag_id {tag_id} from preferred_tags for chat_id {self.chat_id}"
                )
                self.load_preferred_tags()  # Reload preferred tags after removing
            except Exception as e:
                logger.error(
                    f"Failed to remove tag_id {tag_id} from preferred_tags for chat_id {self.chat_id}: {e}"
                )
                raise
        else:
            logger.warning(
                f"Tag_id {tag_id} is not in preferred_tags for chat_id {self.chat_id}"
            )
