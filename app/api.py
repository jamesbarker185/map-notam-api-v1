from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import sys

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db_manager import DBManager
from app.geojson_converter import GeoJsonConverter
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/geojson")
async def get_notam_geojson(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(10, description="Radius in Nautical Miles"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Runway, Airspace)")
):
    """
    Returns NOTAMs as a GeoJSON FeatureCollection.
    Approximates circular areas as Polygons.
    """
    results = db.search_nearby(lat, lon, radius)
    
    # Filter by category if provided
    if category:
        results = [r for r in results if r.get("category") == category]
    
    feature_collection = GeoJsonConverter.to_feature_collection(results)
    
    return feature_collection

# Serve Static Files (HTML) - ONLY IN DEV MODE
# To enable: set ENV=DEV in environment
if os.getenv("ENV") == "DEV":
    print("Mounting Static Files (DEV MODE)...")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def read_index():
        return HTMLResponse(open(os.path.join(static_dir, "map.html")).read())

    @app.get("/map.html")
    async def read_map():
        return HTMLResponse(open(os.path.join(static_dir, "map.html")).read())
