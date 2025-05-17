# File: app/db/entities/language.py
# Import necessary modules and classes


from app.db.db_manager import DBManager

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


class Language:

    db = DBManager()

    def __init__(self, code=None, name=None):
        self.code = code
        self.name = name

    def _insert(self) -> "Language":
        """
        Inserts a new language into the database.
        """
        query = "INSERT INTO languages (code, name) VALUES (?, ?)"
        try:
            self.db.execute(query, (self.code, self.name))
            logger.info(f"Inserted new language: {self.name} ({self.code})")
        except Exception as e:
            logger.error(f"Failed to insert language {self.name}: {e}")
            raise

    def _update(self) -> "Language":
        """
        Updates an existing language in the database.
        """
        query = "UPDATE languages SET name = ? WHERE code = ?"
        try:
            self.db.execute(query, (self.name, self.code))
            logger.info(f"Updated language: {self.name} ({self.code})")
        except Exception as e:
            logger.error(f"Failed to update language {self.name}: {e}")
            raise

    def is_exists(self) -> bool:
        """
        Checks if the language exists in the database.
        Returns True if the language exists, False otherwise.
        """
        query = "SELECT EXISTS(SELECT 1 FROM languages WHERE code = ?)"
        try:
            result = self.db.fetch_one(query, (self.code,))
            exists = bool(result[0])
            logger.info(
                f"Checked existence of language {self.name}: {'Exists' if exists else 'Does not exist'}"
            )
            return exists
        except Exception as e:
            logger.error(f"Failed to check existence of language {self.name}: {e}")
            raise

        def get(self) -> "Language":
            """
            Retrieves the language from the database based on the code.
            """
            query = "SELECT code, name FROM languages WHERE code = ?"
            try:
                result = self.db.fetch_one(query, (self.code,))
                if result:
                    self.code, self.name = result
                    logger.info(f"Loaded language: {self.name} ({self.code})")
                    return self
                else:
                    logger.warning(f"No language found with code {self.code}.")
                    return None
            except Exception as e:
                logger.error(f"Failed to load language with code {self.code}: {e}")
                raise

    def save(self) -> "Language":
        """
        Saves the language to the database.
        If the language exists, it updates it; otherwise, it inserts a new one.
        """
        if self.is_exists():
            return self._update()
        else:
            return self._insert()

    def delete(self) -> None:
        """
        Deletes the language from the database.
        """
        query = "DELETE FROM languages WHERE code = ?"
        try:
            self.db.execute(query, (self.code,))
            logger.info(f"Deleted language: {self.name} ({self.code})")
        except Exception as e:
            logger.error(f"Failed to delete language {self.name}: {e}")
            raise

    @classmethod
    def select(cls, from_row=None, count=None) -> list:
        """
        Retrieves a list of languages from the database.
        - If `from_row` and `count` are None, retrieves all languages.
        - If only `count` is provided, retrieves the first `count` languages.
        - If both `from_row` and `count` are provided, retrieves `count` languages starting from `from_row`.
        """
        try:
            # Base query to select languages
            query = "SELECT code, name FROM languages"

            # Add LIMIT clause if either `from_row` or `count` is provided
            if from_row is not None or count is not None:
                # Default values for pagination
                from_row = from_row if from_row is not None else 0
                count = count if count is not None else -1  # -1 indicates no limit

                # Ensure `count` is positive
                if count < 0:
                    query += " LIMIT ? OFFSET ?"
                    result = cls.db.fetch_all(query, (None, from_row))
                else:
                    query += " LIMIT ? OFFSET ?"
                    result = cls.db.fetch_all(query, (count, from_row))
            else:
                # No pagination: fetch all languages
                result = cls.db.fetch_all(query)

            # Convert results into Language objects
            languages = [Language(code=row[0], name=row[1]) for row in result]
            logger.info(f"Retrieved {len(languages)} languages from the database.")
            return languages

        except Exception as e:
            logger.error(f"Failed to retrieve languages: {e}")
            raise

    def get(self) -> "Language":
        """
        Loads this instance with data from the database where code = self.code.
        """
        query = "SELECT code, name FROM languages WHERE code = ?"
        try:
            result = self.db.fetch_one(query, (self.code,))
            if result:
                self.code, self.name = result
                logger.info(f"Loaded language: {self.name} ({self.code})")
                return self
            else:
                logger.warning(f"No language found with code {self.code}.")
                return None
        except Exception as e:
            logger.error(f"Failed to load language with code {self.code}: {e}")
            raise
