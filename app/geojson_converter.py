import math

class GeoJsonConverter:
    """
    Converts parsed NOTAM data into GeoJSON format.
    Handles Point geometries and approximates circles/radius as Polygons.
    """

    @staticmethod
    def create_circle_polygon(center_lon, center_lat, radius_nm, num_points=32):
        """
        Creates a Polygon geometry approximating a circle.
        
        Args:
            center_lon: Longitude of center point
            center_lat: Latitude of center point
            radius_nm: Radius in Nautical Miles
            num_points: Number of vertices for the polygon (default 32)
            
        Returns:
            List of coordinates [[lon, lat], ...] closed loop
        """
        if radius_nm <= 0:
            return None
            
        coords = []
        # Convert NM to degrees (approximate)
        # 1 NM = 1/60 degree latitude approx
        # For longitude, we need to adjust by cos(lat)
        
        radius_deg = radius_nm / 60.0
        
        for i in range(num_points):
            angle = math.radians(float(i) / num_points * 360.0)
            dx = radius_deg * math.cos(angle) / math.cos(math.radians(center_lat))
            dy = radius_deg * math.sin(angle)
            
            p_lon = center_lon + dx
            p_lat = center_lat + dy
            coords.append([p_lon, p_lat])
            
        # Close the loop
        coords.append(coords[0])
        
        return [coords] # Polygon format requires list of rings

    @staticmethod
    def to_geojson_feature(notam_doc):
        """
        Converts a single NOTAM document to a GeoJSON Feature.
        """
        props = notam_doc.copy()
        
        # Remove DB specific fields if present
        if "_id" in props:
            props["_id"] = str(props["_id"])
        
        # Determine Geometry
        geometry = None
        
        if "location" in notam_doc and notam_doc["location"]:
            center = notam_doc["location"]["coordinates"]
            # Expose Decimal Degrees as separate attributes
            props["longitude"] = center[0]
            props["latitude"] = center[1]
            
            radius = notam_doc.get("radius_nm", 0)
            
            # If significant radius, create Polygon
            if radius > 0.5: # 0.5 NM threshold
                poly_coords = GeoJsonConverter.create_circle_polygon(center[0], center[1], radius)
                geometry = {
                    "type": "Polygon",
                    "coordinates": poly_coords
                }
            else:
                # Default to Point
                geometry = {
                    "type": "Point",
                    "coordinates": center
                }
        
        # Remove location from properties to avoid duplication/confusion
        if "location" in props:
            del props["location"]
            
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": props
        }

    @staticmethod
    def to_feature_collection(notam_docs):
        """
        Converts a list of NOTAM documents to a GeoJSON FeatureCollection.
        """
        features = [
            GeoJsonConverter.to_geojson_feature(doc) 
            for doc in notam_docs 
            if doc.get("location") # Only include NOTAMs with location
        ]
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
