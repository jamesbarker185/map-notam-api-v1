
import sys
import os
import pymongo
from pymongo import MongoClient

print("--- Database Connection Debugger ---")
uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
print(f"Target URI: {uri}")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    print("Attempting to connect...")
    # Force connection
    info = client.server_info()
    print("SUCCESS: Connected to MongoDB!")
    print(f"Server Version: {info.get('version')}")
    
    db = client["notam_db"]
    count = db.notams.count_documents({})
    print(f"Document Count: {count}")
    
except Exception as e:
    print(f"FAILURE: Could not connect to MongoDB.")
    print(f"Error: {e}")
