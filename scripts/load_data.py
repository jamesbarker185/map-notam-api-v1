
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.xml_parser import parse_notam_xml
from app.db_manager import DBManager

def load_xml_to_db(file_path):
    print(f"Loading data from {file_path}...")
    
    db = DBManager()
    db.init_db()
    
    count = 0
    for notam in parse_notam_xml(file_path):
        db.insert_notam(notam)
        count += 1
        
    print(f"Successfully loaded {count} NOTAMs into MongoDB.")
    print(f"Total documents in DB: {db.get_count()}")


if __name__ == "__main__":
    # Check for file in data dir or current dir
    data_dir = os.getenv("DATA_DIR", "data")
    filename = "raw_notam_dump.xml"
    
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        # Fallback to current dir
        if os.path.exists(filename):
            path = filename
        else:
            # Ensure data dir exists if we are going to write (this is load, so read)
            # If neither exists, error
            print(f"Error: Could not find {filename} in {data_dir} or .")
            sys.exit(1)
            
    load_xml_to_db(path)
