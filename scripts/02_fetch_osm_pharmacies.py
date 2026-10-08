"""
02_fetch_osm_pharmacies.py
Consulta la API Overpass de OpenStreetMap para obtener el censo nacional de farmacias en Venezuela.
Salidas:
  - data/osm_pharmacies_raw.json
  - data/all_pharmacies.json
"""

import sys
from pathlib import Path
import json
import time
import urllib.request
import urllib.parse
from collections import Counter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import OSM_RAW, OSM_ALL

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:60];
area["ISO3166-1"="VE"][admin_level=2]->.vzla;
(
  node["amenity"="pharmacy"](area.vzla);
  way["amenity"="pharmacy"](area.vzla);
);
out center;
"""


def fetch_osm_pharmacies():
    print("--> [02] Consultando OpenStreetMap Overpass API para farmacias en Venezuela...")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=f"data={urllib.parse.quote(OVERPASS_QUERY)}".encode("utf-8"),
        headers={"User-Agent": "FarmatodoGeomarketingAnalysis/1.0"},
    )

    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=80) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elements = data.get("elements", [])
            print(f"Obtenidos {len(elements)} elementos OSM en {time.time() - t0:.2f}s.")
            with open(OSM_RAW, "w", encoding="utf-8") as f:
                json.dump(elements, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Aviso/Error en Overpass API: {e}")
        if OSM_RAW.exists():
            print(f"Cargando respaldo local existente desde {OSM_RAW}...")
            with open(OSM_RAW, "r", encoding="utf-8") as f:
                elements = json.load(f)
        else:
            raise

    # Clasificación y estandarización
    pharmacies = []
    chains = []

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "Farmacia").strip()
        brand = tags.get("brand", "").strip()

        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")

        if not lat or not lon:
            continue

        name_upper = (name + " " + brand).upper()
        if "FARMATODO" in name_upper:
            chain = "Farmatodo"
        elif "LOCATEL" in name_upper:
            chain = "Locatel"
        elif "FARMAHORRO" in name_upper:
            chain = "Farmahorro"
        elif "FARMAPATRIA" in name_upper:
            chain = "Farmapatria"
        elif "SAAS" in name_upper:
            chain = "Farmacia SAAS"
        elif "FARMARKET" in name_upper:
            chain = "Farmarket"
        elif "FARMABIEN" in name_upper:
            chain = "Farmabien"
        elif "REDVITAL" in name_upper:
            chain = "Redvital"
        elif "BOTELLERIA" in name_upper or "POPULAR" in name_upper:
            chain = "Farmacia Popular / Comunitaria"
        else:
            chain = "Farmacia Independiente"

        pharmacies.append({
            "id": el.get("id"),
            "name": name,
            "chain": chain,
            "lat": round(lat, 6),
            "lng": round(lon, 6),
            "tags": {k: v for k, v in tags.items() if k in ["opening_hours", "phone", "addr:street", "addr:city"]},
        })
        chains.append(chain)

    with open(OSM_ALL, "w", encoding="utf-8") as f:
        json.dump(pharmacies, f, indent=2, ensure_ascii=False)

    print(f"[OK] Éxito: {len(pharmacies)} farmacias procesadas desde OSM.")
    counter = Counter(chains)
    for c, cnt in counter.most_common(6):
        print(f"   - {c}: {cnt}")
    print(f"  Guardado en {OSM_ALL}")


if __name__ == "__main__":
    fetch_osm_pharmacies()
