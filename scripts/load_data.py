
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
    load_xml_to_db("raw_notam_dump.xml")
