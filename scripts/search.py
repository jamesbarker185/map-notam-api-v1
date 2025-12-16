import argparse
import json
import textwrap
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db_manager import DBManager

def main():
    parser = argparse.ArgumentParser(description="Search for NOTAMs by Location")
    parser.add_argument("lat", type=float, help="Latitude (Decimal Degrees)")
    parser.add_argument("lon", type=float, help="Longitude (Decimal Degrees)")
    parser.add_argument("--radius", type=int, default=10, help="Search radius in Nautical Miles (default: 10)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full NOTAM details")
    
    args = parser.parse_args()
    
    print(f"Searching for NOTAMs within {args.radius} NM of ({args.lat}, {args.lon})...")
    
    db = DBManager()
    results = db.search_nearby(args.lat, args.lon, args.radius)
    
    count = len(results)
    print(f"Found {count} NOTAMs.")
    
    if count > 0:
        print("-" * 40)
        for r in results:
            print(f"ID: {r.get('number', 'N/A')}")
            print(f"Location: {r.get('location_code', 'N/A')}")
            
            if args.verbose:
                print(f"Start: {r.get('start_time', 'N/A')}")
                print(f"End:   {r.get('end_time', 'N/A')}")
                print(f"Radius: {r.get('radius_nm', 'N/A')} NM")
                print(f"Raw Coord: {r.get('raw_coordinates', 'N/A')}")
                print("\nText:")
                print(textwrap.fill(r.get('text', ''), width=80))
            else:
                text_preview = r.get('text', '')[:100].replace('\n', ' ')
                print(f"Text: {text_preview}...")
                
            print("-" * 40)

if __name__ == "__main__":
    main()
