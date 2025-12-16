from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import sys

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db_manager import DBManager

app = FastAPI()

# Initialize DB Manager
db = DBManager()

# API Endpoint
@app.get("/api/search")
async def search_notams(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(10, description="Radius in Nautical Miles")
):
    results = db.search_nearby(lat, lon, radius)
    
    # Convert ObjectId to string for JSON serialization
    for r in results:
        if '_id' in r:
            r['_id'] = str(r['_id'])
            
    return {"count": len(results), "results": results}

# Serve Static Files (HTML)
# We mount this last so it doesn't override API routes
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
