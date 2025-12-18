import re
import math

class NotamTextParser:
    """
    Parses NOTAM text fields (Q-line, E-field) to extract structured attributes.
    Prioritizes text parsing for Runway, Taxiway, Aerodrome, Obstruction, and Airspace NOTAMs.
    """
    
    # Q-line Regex: Q) FIR/CODE/TRAFFIC/PURPOSE/SCOPE/LOWER/UPPER/COORDINATES(RADIUS)
    # Example: Q) KZAU/QMRLC/IV/NBO/A/000/999/4159N08754W005
    # Q-line Regex: Q) FIR/CODE/TRAFFIC/PURPOSE/SCOPE/LOWER/UPPER/COORDINATES(RADIUS)
    # Example: Q) KZAU/QMRLC/IV/NBO/A/000/999/4159N08754W005
    Q_LINE_REGEX = re.compile(
        r"(?:Q\)\s*)?" # Optional Q) prefix
        r"(?P<fir>[A-Z]{4})/"
        r"(?P<code>Q[A-Z]{4})/" # Q-code always starts with Q
        r"(?P<traffic>[IV]*)/" # Relaxed to * (was {1,2})
        r"(?P<purpose>[NBOM]*)/" # Relaxed to * (was {1,3})
        r"(?P<scope>[AEW]*)/" # Relaxed to * (was {1,2})
        r"((?P<lower>[0-9]{3})/(?P<upper>[0-9]{3}))?" # Optional Altitude
        r"(?:/(?P<coords>[0-9]{4}[NS][0-9]{5}[EW]))?" # Optional Coords
        r"(?P<radius>[0-9]{3})?" # Optional Radius
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
            "lower_fl": int(data['lower']) if data['lower'] else 0,
            "upper_fl": int(data['upper']) if data['upper'] else 0, # Default to 0 per user request
            "raw_coords": data['coords'],
            "radius_nm": int(data['radius']) if data.get('radius') else 0,
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

    @staticmethod
    def parse_validity_times(text):
        """
        Extracts start and end validity times from text.
        Look for B) YYMMDDHHMM and C) YYMMDDHHMM, or standalone timestamps.
        """
        import datetime
        
        # Regex for B) and C) fields
        # B) 2512160925 C) 2512161200
        b_match = re.search(r"B\)\s*(\d{10})", text)
        c_match = re.search(r"C\)\s*(\d{10}|PERM)", text)
        
        start_str = b_match.group(1) if b_match else None
        end_str = c_match.group(1) if c_match else None
        
        # Fallback: Find any 10-digit sequence that looks like a date
        # If strict B/C checks failed, try to guess from raw text
        if not start_str or not end_str:
            timestamps = re.findall(r"\b(\d{10})\b", text)
            if len(timestamps) >= 1 and not start_str:
                start_str = timestamps[0]
            if len(timestamps) >= 2 and not end_str:
                end_str = timestamps[1]

        def convert_to_iso(dt_str):
            if not dt_str: return None
            if dt_str == "PERM": return None # Permanent
            try:
                # YYMMDDHHMM -> 20YY-MM-DDTHH:MM:00
                year = int(dt_str[:2])
                month = int(dt_str[2:4])
                day = int(dt_str[4:6])
                hour = int(dt_str[6:8])
                minute = int(dt_str[8:10])
                
                # Assumption: 2000-2099
                full_year = 2000 + year
                return f"{full_year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"
            except:
                return None

        return convert_to_iso(start_str), convert_to_iso(end_str)
