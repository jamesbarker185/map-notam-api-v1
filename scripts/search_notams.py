
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db_manager import DBManager
import json

def test_search():
    db = DBManager()
    
    # Test 1: Search near Hanscom Field (KBED)
    # 42.466 N, 71.283 W
    print("\n--- Test 1: Search near KBED (Target matches) ---")
    lat_kbed = 42.466
    lon_kbed = -71.283
    radius = 10 # NM
    
    results = db.search_nearby(lat_kbed, lon_kbed, radius)
    print(f"Searching within {radius} NM of {lat_kbed}, {lon_kbed}...")
    print(f"Found {len(results)} NOTAMs.")
    for r in results:
        print(f" - {r['number']}: {r['text'][:50]}...")

    # Test 2: Search near Los Angeles (Ref matches none)
    print("\n--- Test 2: Search near LAX (Target matches none) ---")
    lat_lax = 33.9416
    lon_lax = -118.4085
    radius = 50 
    
    results = db.search_nearby(lat_lax, lon_lax, radius)
    print(f"Searching within {radius} NM of {lat_lax}, {lon_lax}...")
    print(f"Found {len(results)} NOTAMs.")

if __name__ == "__main__":
    test_search()
