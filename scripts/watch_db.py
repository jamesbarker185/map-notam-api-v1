import time
import os
import sys

# Add project root to path to find 'app' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db_manager import DBManager

def watch():
    db = DBManager()
    print("Watching MongoDB collection 'notams'...")
    print("Press Ctrl+C to stop.")
    
    last_count = -1
    
    try:
        while True:
            count = db.get_count()
            if count != last_count:
                print(f"[{time.strftime('%H:%M:%S')}] Total NOTAMs: {count}")
                last_count = count
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    watch()
