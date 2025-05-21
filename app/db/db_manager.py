# File: app/db/db_manager.py

import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(funcName)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Logs will be printed to the console
)
logger = logging.getLogger(__name__)


class QueryBuilder:
    """
    A utility class to dynamically build SQL queries using method chaining.
    """

    def __init__(self, table_name):
        self.table_name = table_name
        self.query_parts = {"select": "*", "where": None, "order": None, "limit": None}

    def select(self, columns="*"):
        """Specify the columns to select."""
        self.query_parts["select"] = (
            ", ".join(columns) if isinstance(columns, list) else columns
        )
        return self

    def where(self, condition):
        """Add a WHERE clause to the query."""
        self.query_parts["where"] = f"WHERE {condition}"
        return self

    def order(self, column, direction="ASC"):
        """Add an ORDER BY clause to the query."""
        self.query_parts["order"] = f"ORDER BY {column} {direction.upper()}"
        return self

    def limit(self, limit):
        """Add a LIMIT clause to the query."""
        self.query_parts["limit"] = f"LIMIT {limit}"
        return self

    def get(self):
        """Construct and return the final SQL query."""
        query = f"SELECT {self.query_parts['select']} FROM {self.table_name}"
        if self.query_parts["where"]:
            query += f" {self.query_parts['where']}"
        if self.query_parts["order"]:
            query += f" {self.query_parts['order']}"
        if self.query_parts["limit"]:
            query += f" {self.query_parts['limit']}"
        return query


class DBManager:
    """
    A utility class to manage database connections and execute queries.
    """

    db_file = None
    connection = None

    def __init__(self, db_file="database/database.db"):
        """
        Initialize the DBManager with the path to the SQLite database file.
        """
        self.db_file = db_file

    def connect(self):
        """
        Establish a connection to the SQLite database.
        """
        if self.connection is None:
            try:
                self.connection = sqlite3.connect(self.db_file)
                logger.info(f"Connected to database at {self.db_file}")
            except sqlite3.Error as e:
                logger.error(f"Failed to connect to database: {e}")
                raise

    def disconnect(self):
        """
        Close the connection to the SQLite database.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            # logger.info("Database connection closed.")

    def execute(self, query, params=None):
        """
        Execute a single SQL query with optional parameters.
        Returns the cursor object for further processing.
        """
        if self.connection is None:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            # logger.info(f"Executed query: {query}")
            return cursor
        except sqlite3.Error as e:
            # logger.error(f"Query execution failed: {e}")
            raise

    def fetch_all(self, query, params=None):
        """
        Execute a SELECT query and return all results as a list of tuples.
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=None):
        """
        Execute a SELECT query and return the first result as a tuple.
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def execute_sql_file(self, file_path):
        cursor = None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sql = f.read()
            self.connect()
            cursor = self.connection.cursor()
            cursor.executescript(sql)
            self.connection.commit()
        except Exception as e:
            print(f"Error executing SQL file '{file_path}': {e}")
        finally:
            if cursor is not None:
                cursor.close()  # Ensure the cursor is closed only if it was created
            self.close()

    def export(self, sql_file_path):
        """
        Export the entire database schema and data as an SQL file.
        """
        try:
            with open(sql_file_path, "w") as file:
                for line in self.connection.iterdump():
                    file.write(f"{line}\n")
            # logger.info(f"Database exported to {sql_file_path}")
        except Exception as e:
            # logger.error(f"Failed to export database: {e}")
            raise

    @classmethod
    def close(cls):
        """
        Close the database connection.
        """
        if cls.connection:
            cls.connection.close()
            cls.connection = None
            # logger.info("Database connection closed.")
        else:
            # logger.info("No database connection to close.")
            pass
        return cls

    @classmethod
    def delete_database(cls):
        """
        Delete the database file.
        """
        try:
            if cls.connection:
                cls.connection.close()
            os.remove(cls.db_file)
            # logger.info(f"Database file {self.db_file} deleted.")
        except Exception as e:
            # logger.error(f"Failed to delete database: {e}")
            raise
