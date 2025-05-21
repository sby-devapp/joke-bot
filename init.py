# File: init.py

from app.db.db_manager import DBManager
import os
import sys


SCHEMA_FILE = "database/schema.sql"


def sql_syntax_correct(file_path):
    return True


def display_menu_get_choice():
    print("\nWelcome to the Database Initialization Tool!")
    menu = """
            Please choose an option:
            1. Create Database Schema (db.schema.sql)
            2. Initialize Tags (db.tags.sql)
            3. Initialize Languages (db.languages.sql)
            4. Execute Custom SQL File
            5. Delete Database
            6. Exit
        """
    print(menu)
    return input("Enter your choice (1-6): ")


def main():
    if sys.stdin.isatty():
        print("Running in an interactive terminal.")
    else:
        print("Input is being redirected.")

    db_manager = DBManager()

    while True:
        choice = display_menu_get_choice()
        if choice == "1":
            db_manager.execute_sql_file(SCHEMA_FILE)
            print("Database schema created successfully.")
            db_manager.close()
        elif choice == "2":
            sql_file = "database/db.tags.sql"
            if sql_syntax_correct(sql_file):
                db_manager.connect()
                db_manager.execute_sql_file(sql_file)
                db_manager.close()
                print("Tags initialized successfully.")
        elif choice == "3":
            sql_file = "database/db.languages.sql"
            if sql_syntax_correct(sql_file):
                db_manager.connect()
                db_manager.execute_sql_file(sql_file)
                db_manager.close()
                print("Languages initialized successfully.")
        elif choice == "4":
            file_path = input("Enter the path to the SQL file: ")
            if os.path.exists(file_path):
                if sql_syntax_correct(file_path):
                    db_manager.connect()
                    db_manager.execute_sql_file(file_path)  # <-- FIXED HERE
                    db_manager.close()
                    print(f"SQL file '{file_path}' executed successfully.")
                else:
                    print(f"Failed to execute SQL file '{file_path}'.")
            else:
                print(f"File '{file_path}' does not exist.")
        elif choice == "5":
            input("Are you sure you want to delete the database? (yes/no): ")
            if input.lower() == "yes":
                db_manager = DBManager()
                db_manager.delete_database()
                print("Database deleted successfully.")
            else:
                print("Deleting the database is canceled.")

        elif choice == "6":
            print("Exiting the tool. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
