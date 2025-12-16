
import re
import defusedxml.ElementTree as ET

# Namespaces for AIXM 5.1
NS = {
    'aixm': "http://www.aixm.aero/schema/5.1",
    'msg': "http://www.aixm.aero/schema/5.1/message",
    'event': "http://www.aixm.aero/schema/5.1/event",
    'gml': "http://www.opengis.net/gml/3.2",
    'fnse': "http://www.aixm.aero/schema/5.1/extensions/FAA/FNSE"
}

def parse_coordinate(coord_str):
    """
    Parses a string like "4228N07117W" into (longitude, latitude) dictionary/tuple.
    Format is typically: DDMM[N/S]DDDMM[E/W]
    Example: 4228N07117W -> 42 degrees 28 min North, 71 degrees 17 min West
    """
    if not coord_str:
        return None
        
    # Regex to capture Lat (4 digits + N/S) and Lon (5 digits + E/W)
    # 4228N -> 42° 28' N
    # 07117W -> 071° 17' W
    match = re.match(r"(\d{4})([NS])(\d{5})([EW])", coord_str)
    
    if not match:
        return None
        
    lat_digits, lat_hemi, lon_digits, lon_hemi = match.groups()
    
    # Latitude
    lat_deg = int(lat_digits[:2])
    lat_min = int(lat_digits[2:])
    lat_val = lat_deg + (lat_min / 60.0)
    if lat_hemi == 'S':
        lat_val = -lat_val
        
    # Longitude
    lon_deg = int(lon_digits[:3])
    lon_min = int(lon_digits[3:])
    lon_val = lon_deg + (lon_min / 60.0)
    if lon_hemi == 'W':
        lon_val = -lon_val
        
    return [lon_val, lat_val] # GeoJSON uses [Lon, Lat]

def _extract_notams_from_root(root):
    """
    Helper to yield NOTAM dicts from an AIXM root element.
    """
    for member in root.findall(".//msg:hasMember", NS):
        event_node = member.find(".//event:Event", NS)
        if event_node is None:
            continue
            
        # We need to find the NOTAM details within the TimeSlice
        time_slice = event_node.find(".//event:EventTimeSlice", NS)
        if time_slice is None:
            continue
            
        notam_node = time_slice.find(".//event:textNOTAM/event:NOTAM", NS)
        if notam_node is None:
            continue

        # Extract Fields
        notam_id = notam_node.get(f"{{{NS['gml']}}}id")
        
        series = notam_node.findtext("event:series", default="", namespaces=NS)
        number = notam_node.findtext("event:number", default="", namespaces=NS)
        year = notam_node.findtext("event:year", default="", namespaces=NS)
        full_number = f"{series}{number}/{year}"
        
        text = notam_node.findtext("event:text", default="", namespaces=NS)
        location_code = notam_node.findtext("event:location", default="", namespaces=NS)
        
        # Coordinates and Radius
        raw_coords = notam_node.findtext("event:coordinates", default="", namespaces=NS)
        geo_point = parse_coordinate(raw_coords)
        
        radius_str = notam_node.findtext("event:radius", default="0", namespaces=NS)
        try:
            radius_nm = int(radius_str)
        except ValueError:
            radius_nm = 0
            
        # Time
        start_time = notam_node.findtext("event:effectiveStart", default="", namespaces=NS)
        end_time = notam_node.findtext("event:effectiveEnd", default="", namespaces=NS)

        # Construct Document
        doc = {
            "notam_id": notam_id,
            "number": full_number,
            "text": text,
            "location_code": location_code,
            "start_time": start_time,
            "end_time": end_time,
            "radius_nm": radius_nm,
            "raw_coordinates": raw_coords
        }
        
        if geo_point:
            doc["location"] = {
                "type": "Point",
                "coordinates": geo_point
            }
            
        yield doc

def parse_notam_xml(file_path):
    """
    Parses the AIXM XML file and yields a dictionary for each NOTAM.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    yield from _extract_notams_from_root(root)

def parse_notam_str(xml_str):
    """
    Parses a raw AIXM XML string and yields a dictionary for each NOTAM.
    """
    if not xml_str or not xml_str.strip():
        return
    try:
        root = ET.fromstring(xml_str)
        yield from _extract_notams_from_root(root)
    except Exception as e:
        print(f"Error parsing XML string: {e}")
        return

if __name__ == "__main__":
    # Test Run
    import json
    for notam in parse_notam_xml("raw_notam_dump.xml"):
        print(json.dumps(notam, indent=2))
