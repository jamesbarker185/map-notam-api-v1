
import os
import requests

STATIC_DIR = os.path.join("app", "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

files = {
    "maplibre-gl.js": "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js",
    "maplibre-gl.css": "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css"
}

print(f"Downloading assets to {STATIC_DIR}...")

for name, url in files.items():
    dest = os.path.join(STATIC_DIR, name)
    try:
        print(f"Downloading {name}...")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
        print(f"Saved {name}")
    except Exception as e:
        print(f"FAILED to download {name}: {e}")

print("Done.")
