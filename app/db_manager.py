import os
import pymongo
from pymongo import MongoClient, GEOSPHERE

DB_NAME = "notam_db"
COLLECTION_NAME = "notams"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

class DBManager:
    def __init__(self, uri=MONGO_URI):
        self.client = MongoClient(uri)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
    def init_db(self):
        """
        Initializes the database, creating indexes if they don't exist.
        """
        # Create 2dsphere index on the 'location' field for geospatial queries
        print("Ensuring 2dsphere index on 'location' field...")
        self.collection.create_index([("location", GEOSPHERE)])
        print("Index ensure complete.")
        
    def insert_notam(self, notam_doc):
        """
        Inserts or updates a NOTAM document.
        Uses notam_id as the unique identifier.
        """
        result = self.collection.update_one(
            {"notam_id": notam_doc["notam_id"]},
            {"$set": notam_doc},
            upsert=True
        )
        return result
        
    def search_nearby(self, lat, lon, radius_nm):
        """
        Finds NOTAMs within the specified radius (in nautical miles) of the point.
        """
        # MongoDB $centerSphere uses radians.
        # Radius in radians = radius_in_miles / 3963.2 (Earth radius in miles)
        # OR radius_in_nm / 3440.06 (Earth radius in NM)
        
        radius_radians = radius_nm / 3440.06
        
        query = {
            "location": {
                "$geoWithin": {
                    "$centerSphere": [[lon, lat], radius_radians]
                }
            }
        }
        
        results = list(self.collection.find(query))
        return results

    def get_count(self):
        return self.collection.count_documents({})
