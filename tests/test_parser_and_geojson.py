
import sys
import os
import json
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.notam_text_parser import NotamTextParser
from app.geojson_converter import GeoJsonConverter

class TestNotamProcessing(unittest.TestCase):

    def test_q_line_parsing(self):
        # Example Q-line
        q_line = "Q) CZEG/QFAXX/IV/NBO/A/000/999/5319N11335W005"
        data = NotamTextParser.parse_q_line(q_line)
        
        self.assertIsNotNone(data)
        self.assertEqual(data['fir'], "CZEG")
        self.assertEqual(data['subject_code'], "FA")
        self.assertEqual(data['condition_code'], "XX")
        self.assertEqual(data['category'], "Aerodrome")
        self.assertEqual(data['radius_nm'], 5)
        self.assertEqual(data['raw_coords'], "5319N11335W")
        
    def test_coordinate_parsing(self):
        coord_str = "5319N11335W"
        coords = NotamTextParser.parse_coordinate_str(coord_str)
        # 53 deg 19 min N -> 53 + 19/60 = 53.3166...
        # 113 deg 35 min W -> -(113 + 35/60) = -113.5833...
        
        self.assertAlmostEqual(coords[1], 53.31666, places=4)
        self.assertAlmostEqual(coords[0], -113.58333, places=4)
        
    def test_geojson_point_conversion(self):
        doc = {
            "notam_id": "TEST_1",
            "category": "Obstruction",
            "location": {
                "type": "Point",
                "coordinates": [-113.5, 53.3]
            },
            "radius_nm": 0
        }
        
        feature = GeoJsonConverter.to_geojson_feature(doc)
        self.assertEqual(feature['type'], "Feature")
        self.assertEqual(feature['geometry']['type'], "Point")
        self.assertEqual(feature['geometry']['coordinates'], [-113.5, 53.3])
        self.assertEqual(feature['properties']['category'], "Obstruction")
        
    def test_geojson_polygon_conversion(self):
        doc = {
            "notam_id": "TEST_2",
            "category": "Airspace",
            "location": {
                "type": "Point",
                "coordinates": [0, 0] # Equator/Prime Meridian
            },
            "radius_nm": 60 # 1 degree approx
        }
        
        feature = GeoJsonConverter.to_geojson_feature(doc)
        self.assertEqual(feature['geometry']['type'], "Polygon")
        self.assertEqual(len(feature['geometry']['coordinates']), 1) # One ring
        self.assertEqual(len(feature['geometry']['coordinates'][0]), 33) # 32 points + closure
        
if __name__ == '__main__':
    unittest.main()
