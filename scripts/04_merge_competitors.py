"""
04_merge_competitors.py
Fusiona y desduplica (radio 60m) los censos de farmacias de Google Places y OpenStreetMap.
Salidas:
  - data/master_competitors.json
  - data/master_competitors.geojson
"""

import sys
from pathlib import Path
import json
import math
from collections import defaultdict, Counter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import OSM_ALL, GOOGLE_PLACES, MASTER_COMPS_JSON, MASTER_COMPS_GEOJSON


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def merge_competitors():
    print("--> [04] Fusionando fuentes de competidores (Google Places + OpenStreetMap)...")

    osm_pharmacies = []
    if OSM_ALL.exists():
        with open(OSM_ALL, "r", encoding="utf-8") as f:
            osm_pharmacies = json.load(f)

    gplaces_pharmacies = []
    if GOOGLE_PLACES.exists():
        with open(GOOGLE_PLACES, "r", encoding="utf-8") as f:
            gplaces_pharmacies = json.load(f)

    print(f"Cargadas {len(osm_pharmacies)} de OSM y {len(gplaces_pharmacies)} de Google Places.")

    master_list = []
    spatial_index = defaultdict(list)

    # 1. Prioridad: Google Places (alta fidelidad comercial)
    for gp in gplaces_pharmacies:
        lat = gp.get("lat")
        lng = gp.get("lng")
        if not lat or not lng:
            continue
        entry = {
            "id": f"gp_{gp['id']}",
            "name": gp["name"],
            "chain": gp["chain"],
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "address": gp.get("address", ""),
            "rating": gp.get("rating"),
            "userRatingCount": gp.get("userRatingCount"),
            "source": "Google Places",
            "target_zone": gp.get("target_zone", ""),
        }
        master_list.append(entry)
        gx = int(lng / 0.01)
        gy = int(lat / 0.01)
        spatial_index[(gx, gy)].append(entry)

    # 2. OSM (complemento nacional)
    osm_added = 0
    for op in osm_pharmacies:
        if op["chain"] == "Farmatodo":
            continue
        lat = op.get("lat")
        lng = op.get("lng")
        if not lat or not lng:
            continue

        gx = int(lng / 0.01)
        gy = int(lat / 0.01)

        # Desduplicación espacial a 60 metros
        is_dup = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for candidate in spatial_index.get((gx + dx, gy + dy), []):
                    if haversine_m(lat, lng, candidate["lat"], candidate["lng"]) < 60.0:
                        is_dup = True
                        break
                if is_dup:
                    break

        if not is_dup:
            entry = {
                "id": f"osm_{op['id']}",
                "name": op["name"],
                "chain": op["chain"],
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "address": op.get("tags", {}).get("addr:street", ""),
                "rating": None,
                "userRatingCount": None,
                "source": "OpenStreetMap",
                "target_zone": "",
            }
            master_list.append(entry)
            spatial_index[(gx, gy)].append(entry)
            osm_added += 1

    print(f"Incorporadas {osm_added} farmacias adicionales no duplicadas desde OSM.")

    # Guardar JSON
    with open(MASTER_COMPS_JSON, "w", encoding="utf-8") as f:
        json.dump(master_list, f, indent=2, ensure_ascii=False)

    # Guardar GeoJSON
    features = []
    for item in master_list:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [item["lng"], item["lat"]],
            },
            "properties": item,
        })

    geojson_obj = {"type": "FeatureCollection", "features": features}
    with open(MASTER_COMPS_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_obj, f, indent=2, ensure_ascii=False)

    print(f"[OK] Éxito: {len(master_list)} competidores consolidados en total.")
    chain_counts = Counter(m["chain"] for m in master_list)
    for c, cnt in chain_counts.most_common(7):
        print(f"   - {c}: {cnt}")
    print(f"  Guardado en {MASTER_COMPS_JSON} y {MASTER_COMPS_GEOJSON}")


if __name__ == "__main__":
    merge_competitors()
