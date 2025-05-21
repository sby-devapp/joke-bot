# File: app/db/entities/tag.py

"""
-- Table: tags
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- Unique ID for each tag
    name TEXT NOT NULL UNIQUE,                -- Tag name (e.g., 'ar: Arabic', 'cs: Computer Science')
    created_by INTEGER NOT NULL,              -- User ID of the person who added the tag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the tag was added
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the tag was last updated
    FOREIGN KEY (created_by) REFERENCES users(id) -- Link to the user who created the tag
);

"""
from app.db.db_manager import DBManager


class Tag:

    db = DBManager()

    def __init__(
        self, id=None, name=None, created_by=None, created_at=None, updated_at=None
    ):
        """
        Initializes a Tag object.
        """
        self.id = id
        self.name = name
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at

        if self.id and self.is_exists():
            self.get()

    def is_exists(self) -> bool:
        """
        Checks if the tag exists in the database.
        Returns True if the tag exists, False otherwise.
        """
        query = "SELECT EXISTS(SELECT 1 FROM tags WHERE id = ?)"
        result = self.db.fetch_one(query, (self.id,))
        return bool(result[0]) if result else False

    def _insert(self) -> "Tag":
        """
        Inserts a new tag into the database.
        """
        query = "INSERT INTO tags (name, created_by) VALUES (?, ?)"
        self.db.execute(query, (self.name, self.created_by))
        return self.get()

    def _update(self) -> "Tag":
        """
        Updates an existing tag in the database.
        """
        query = "UPDATE tags SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute(query, (self.name, self.id))
        return self.get()

    def get(self) -> "Tag":
        """
        Retrieves the tag from the database based on the ID.
        """
        query = (
            "SELECT id, name, created_by, created_at, updated_at FROM tags WHERE id = ?"
        )
        result = self.db.fetch_one(query, (self.id,))
        if result:
            self.id, self.name, self.created_by, self.created_at, self.updated_at = (
                result
            )
            return self
        else:
            raise ValueError(f"Tag with ID {self.id} does not exist.")

    def delete(self) -> None:
        """
        Deletes the tag from the database based on the ID.
        """
        query = "DELETE FROM tags WHERE id = ?"
        self.db.execute(query, (self.id,))

    def get_all_tags(self) -> list:
        """
        Retrieves all tags from the database.
        """
        query = "SELECT id, name FROM tags"
        result = self.db.fetch_all(query)
        return [Tag(id=row[0], name=row[1]) for row in result] if result else []

    def get_tag_by_name(self, name: str) -> "Tag":
        """
        Retrieves a tag from the database based on the name.
        """
        query = "SELECT id, name FROM tags WHERE name = ?"
        result = self.db.fetch_one(query, (name,))
        if result:
            return Tag(id=result[0], name=result[1])
        else:
            raise ValueError(f"Tag with name {name} does not exist.")

    def save(self) -> "Tag":
        """
        Saves the tag to the database.
        Inserts a new record if it doesn't exist; updates the record if it does.
        """
        try:
            if self.is_exists():
                return self._update()
            else:
                return self._insert()
        except Exception as e:
            raise e

    @classmethod
    def select(cls, number_of_raws=None, start_from=None):
        """
        Retrieves a limited number of tags from the database.
        Returns a list of Tag instances.
        """
        query = "SELECT id FROM tags"
        if number_of_raws:
            query += f" LIMIT {number_of_raws}"
        if start_from:
            query += f" OFFSET {start_from}"
        result = cls.db.fetch_all(query)
        return [cls(id=row[0]) for row in result] if result else []

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.id == other.id  # Compare based on ID

    def __hash__(self):
        return hash(self.id)  # Optional: needed if you use in sets or dicts
