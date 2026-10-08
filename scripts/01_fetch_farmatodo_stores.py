"""
01_fetch_farmatodo_stores.py
Extrae y limpia la red de tiendas oficiales de Farmatodo Venezuela desde su API transactional.
Salidas:
  - data/farmatodo_stores_raw.json
  - data/farmatodo_stores.json
  - data/farmatodo_stores.geojson
"""

import sys
from pathlib import Path
import json
import urllib.request

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import STORES_RAW, STORES_JSON, STORES_GEOJSON

FARMATODO_API_URL = "https://api-transactional.farmatodo.com/catalog/r/VE/v1/cities/active/locations/"


def fetch_and_clean_stores():
    print(f"--> [01] Consultando API oficial de Farmatodo...")
    req = urllib.request.Request(
        FARMATODO_API_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.farmatodo.com.ve",
            "Referer": "https://www.farmatodo.com.ve/",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error al consultar API Farmatodo: {e}")
        if STORES_RAW.exists():
            print(f"Cargando respaldo local existente desde {STORES_RAW}...")
            with open(STORES_RAW, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        else:
            raise

    # Guardar raw
    with open(STORES_RAW, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)
    print(f"Respaldo raw guardado en: {STORES_RAW}")

    # Limpieza y estructuración
    cities = raw_data.get("data", [])
    features = []
    cleaned_stores = []
    seen_ids = set()

    for c in cities:
        city_group = c.get("name", "").strip()
        for s in c.get("stores", []):
            sid = s.get("id")
            if sid in seen_ids:
                continue
            seen_ids.add(sid)

            lat = s.get("latitude")
            lng = s.get("longitude")

            try:
                lat = float(lat)
                lng = float(lng)
            except (TypeError, ValueError):
                lat, lng = None, None

            store_entry = {
                "id": sid,
                "name": s.get("name", "").strip(),
                "commercialName": s.get("commercialName", "").strip(),
                "address": s.get("address", "").strip(),
                "city_group": city_group,
                "cityName": s.get("cityName", "").strip(),
                "municipality": s.get("municipality", "").strip(),
                "state": s.get("state", "").strip() if s.get("state") else "",
                "latitude": lat,
                "longitude": lng,
                "phone": s.get("phone", "").strip(),
                "schedule": s.get("scheduleMsn", "").strip(),
                "deliveryType": s.get("deliveryType", ""),
                "active": s.get("active", True),
                "photo": s.get("photo", ""),
            }
            cleaned_stores.append(store_entry)

            # Valid coordinates in Venezuela bbox
            if lat and lng and -75.0 <= lng <= -59.0 and 0.0 <= lat <= 15.0:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat],
                    },
                    "properties": store_entry,
                }
                features.append(feature)

    with open(STORES_JSON, "w", encoding="utf-8") as f:
        json.dump(cleaned_stores, f, indent=2, ensure_ascii=False)

    geojson_obj = {"type": "FeatureCollection", "features": features}
    with open(STORES_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_obj, f, indent=2, ensure_ascii=False)

    print(f"[OK] Éxito: {len(cleaned_stores)} tiendas procesadas ({len(features)} geolocalizadas).")
    print(f"  Guardado en {STORES_JSON} y {STORES_GEOJSON}")


if __name__ == "__main__":
    fetch_and_clean_stores()
