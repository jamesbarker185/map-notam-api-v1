import re
import math

class NotamTextParser:
    """
    Parses NOTAM text fields (Q-line, E-field) to extract structured attributes.
    Prioritizes text parsing for Runway, Taxiway, Aerodrome, Obstruction, and Airspace NOTAMs.
    """
    
    # Q-line Regex: Q) FIR/CODE/TRAFFIC/PURPOSE/SCOPE/LOWER/UPPER/COORDINATES(RADIUS)
    # Example: Q) KZAU/QMRLC/IV/NBO/A/000/999/4159N08754W005
    Q_LINE_REGEX = re.compile(
        r"Q\)\s*"
        r"(?P<fir>[A-Z]{4})/"
        r"(?P<code>[A-Z]{5})/"
        r"(?P<traffic>[IV]{1,2})/"
        r"(?P<purpose>[NBOM]{1,3})/"
        r"(?P<scope>[AEW]{1,2})/"
        r"(?P<lower>[0-9]{3})/"
        r"(?P<upper>[0-9]{3})/"
        r"(?P<coords>[0-9]{4}[NS][0-9]{5}[EW])"
        r"(?P<radius>[0-9]{3})?"
    )
    
    # NOTAM Code decoding (Partial list for common types)
    # First letter: Subject (M=Movement Area, F=Facilities, O=Obstruction, R=Airspace)
    # Second, Third: Subject details
    # Fourth, Fifth: Condition
    SUBJECT_CODES = {
        'MR': 'Runway',
        'MX': 'Taxiway',
        'FA': 'Aerodrome',
        'OB': 'Obstacle',
        'RT': 'Restricted Area'
    }
    
    CONDITION_CODES = {
        'LC': 'Closed',
        'LT': 'Limited',
        'OG': 'Operating',
        'AP': 'Available Prior Permission',
        'AN': 'Available on Notice'
    }

    @staticmethod
    def parse_q_line(text):
        """
        Extracts structured data from the Q-line.
        Returns a dictionary or None if no Q-line found.
        """
        match = NotamTextParser.Q_LINE_REGEX.search(text)
        if not match:
            return None
            
        data = match.groupdict()
        
        # Decode NOTAM Code
        code = data['code']
        # The Q-code starts with 'Q', followed by 2-letter Subject and 2-letter Condition
        # e.g. QMRLC -> Q, MR, LC
        subject_code = code[1:3] # e.g. MR
        condition_code = code[3:5] # e.g. LC
        
        # Determine Category
        category = "Other"
        if subject_code == 'MR': category = "Runway"
        elif subject_code == 'MX': category = "Taxiway"
        elif subject_code == 'FA': category = "Aerodrome"
        elif subject_code == 'OB': category = "Obstruction"
        elif subject_code == 'RT': category = "Airspace"
        
        return {
            "fir": data['fir'],
            "q_code": code,
            "subject_code": subject_code,
            "condition_code": condition_code,
            "traffic": data['traffic'],
            "purpose": data['purpose'],
            "scope": data['scope'],
            "lower_fl": int(data['lower']),
            "upper_fl": int(data['upper']),
            "raw_coords": data['coords'],
            "radius_nm": int(data['radius']) if data['radius'] else 0,
            "category": category
        }

    @staticmethod
    def parse_e_field(text, category):
        """
        Parses the E-field (description) for detailed attributes based on category.
        """
        details = {}
        
        if category == "Runway":
            # Extract RWY ID: RWY 04L/22R, RWY 18, etc.
            rwy_match = re.search(r"RWY\s+(\d{2}[LRC]?)(?:/(\d{2}[LRC]?))?", text)
            if rwy_match:
                details['rwy_id'] = rwy_match.group(1)
                if rwy_match.group(2):
                    details['rwy_id_2'] = rwy_match.group(2)
                    
        elif category == "Taxiway":
            # Extract TWY ID: TWY A, TWY B2, etc.
            twy_match = re.search(r"TWY\s+([A-Z0-9]+)", text)
            if twy_match:
                details['twy_id'] = twy_match.group(1)

        elif category == "Obstruction":
             # Extract height: 100FT AGL, 200FT AMSL
             height_match = re.search(r"(\d+)(?:FT|M)\s+(AGL|AMSL)", text)
             if height_match:
                 details['height_val'] = int(height_match.group(1))
                 details['height_ref'] = height_match.group(2)

        return details

    @staticmethod
    def parse_coordinate_str(coord_str):
        """
        Parses coordinate string from Q-line (e.g., 4228N07117W) 
        into (longitude, latitude) list for GeoJSON.
        """
        if not coord_str:
            return None
            
        # Regex to capture Lat (4 digits + N/S) and Lon (5 digits + E/W)
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
