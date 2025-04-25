# init.py

from app.db.db_manager import DBManager  # Import the DBManager class
import os

# Paths to your SQL scripts
SCHEMA_FILE = "database/schema.sql"
TEST_DATA_FILE = "database/test.sql"

def init_db():
    """
    Initializes the database by executing the schema and test data SQL files.
    """
    print("Initializing database...")
    
    try:
        # Initialize the DBManager instance
        db = DBManager()
        
        db.execute_sql_file(SCHEMA_FILE)
        db.execute_sql_file(TEST_DATA_FILE)
    
    except Exception as e:
        print(f"Error occurred during database initialization: {e}")

if __name__ == "__main__":
    init_db()