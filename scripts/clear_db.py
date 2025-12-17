import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db_manager import DBManager

def main():
    print("WARNING: This will delete ALL NOTAMs from the database.")
    confirm = os.getenv("CONFIRM_CLEAR", "false")
    
    if confirm.lower() != "true":
        print("To confirm, set environment variable CONFIRM_CLEAR=true")
        sys.exit(1)
        
    db = DBManager()
    db.clear_db()
    print("Database cleared successfully.")

if __name__ == "__main__":
    main()
