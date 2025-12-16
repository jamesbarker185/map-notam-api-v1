import sys
import os
sys.path.append(os.path.abspath('app'))
try:
    import db_manager
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
