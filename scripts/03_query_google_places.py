"""
03_query_google_places.py
Consulta Google Places API (New) para 25 zonas estratégicas prioritarias en Venezuela.
SEGURIDAD: La clave de API se obtiene de forma segura mediante la variable de entorno GOOGLE_MAPS_API_KEY.
Salidas:
  - data/google_places_pharmacies.json
"""

import sys
from pathlib import Path
import json
import time
import urllib.request

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import GOOGLE_PLACES, get_google_maps_api_key

PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Centroides estratégicos para sondeo de alta precisión
SEARCH_TARGETS = [
    # Caracas gaps
    {"city": "Caracas - Caricuao / Antímano", "lat": 10.4285, "lng": -66.9780},
    {"city": "Caracas - Catia / Sucre", "lat": 10.5180, "lng": -66.9420},
    {"city": "Caracas - El Junquito", "lat": 10.4650, "lng": -67.0420},
    {"city": "Caracas - El Valle / Coche", "lat": 10.4550, "lng": -66.9050},
    {"city": "Caracas - Petare Norte", "lat": 10.4850, "lng": -66.7890},
    {"city": "Miranda - Guarenas", "lat": 10.4700, "lng": -66.6200},
    {"city": "Miranda - Guatire", "lat": 10.4720, "lng": -66.5450},
    # Maracaibo & Zulia
    {"city": "Maracaibo - San Francisco", "lat": 10.5600, "lng": -71.6400},
    {"city": "Maracaibo - Oeste (La Curva)", "lat": 10.6800, "lng": -71.6900},
    {"city": "Zulia - Cabimas", "lat": 10.3950, "lng": -71.4450},
    # Valencia & Carabobo
    {"city": "Valencia - Flor Amarillo / Rafael Urdaneta", "lat": 10.1550, "lng": -67.9350},
    {"city": "Valencia - Los Guayos", "lat": 10.1850, "lng": -67.9250},
    {"city": "Carabobo - Puerto Cabello", "lat": 10.4700, "lng": -68.0150},
    # Barquisimeto & Lara
    {"city": "Barquisimeto - El Cují / Tamaca", "lat": 10.1450, "lng": -69.3100},
    {"city": "Lara - Carora", "lat": 10.1750, "lng": -70.0800},
    # Maracay & Aragua
    {"city": "Aragua - Cagua", "lat": 10.1850, "lng": -67.4550},
    {"city": "Aragua - Villa de Cura", "lat": 10.0400, "lng": -67.4900},
    # Oriente & Guayana
    {"city": "Anzoátegui - El Tigre", "lat": 8.8850, "lng": -64.2450},
    {"city": "Sucre - Cumaná", "lat": 10.4550, "lng": -64.1700},
    {"city": "Monagas - Maturín Centro-Sur", "lat": 9.7350, "lng": -63.1800},
    {"city": "Bolívar - Ciudad Bolívar", "lat": 8.1200, "lng": -63.5450},
    {"city": "Bolívar - Puerto Ordaz / Unare", "lat": 8.2950, "lng": -62.7400},
    # Andes & Llanos
    {"city": "Táchira - San Cristóbal Sur", "lat": 7.7450, "lng": -72.2350},
    {"city": "Barinas - Barinas Alto Barinas", "lat": 8.6050, "lng": -70.2500},
    {"city": "Portuguesa - Acarigua / Araure", "lat": 9.5550, "lng": -69.2100},
]


def classify_chain(name: str) -> str:
    nu = name.upper()
    if "FARMATODO" in nu:
        return "Farmatodo"
    elif "LOCATEL" in nu:
        return "Locatel"
    elif "FARMAHORRO" in nu:
        return "Farmahorro"
    elif "FARMAPATRIA" in nu:
        return "Farmapatria"
    elif "SAAS" in nu:
        return "Farmacia SAAS"
    elif "FARMARKET" in nu:
        return "Farmarket"
    elif "FARMABIEN" in nu:
        return "Farmabien"
    elif "REDVITAL" in nu:
        return "Redvital"
    elif "BOTELLERIA" in nu or "POPULAR" in nu:
        return "Farmacia Popular / Comunitaria"
    return "Farmacia Independiente"


def query_google_places():
    print("--> [03] Verificando clave de Google Maps Places API...")
    api_key = get_google_maps_api_key()

    if not api_key:
        print("⚠️ AVISO: Variable de entorno GOOGLE_MAPS_API_KEY no configurada.")
        if GOOGLE_PLACES.exists():
            print(f"   Utilizando dataset previo existente en {GOOGLE_PLACES}.")
            return
        else:
            print("   Para ejecutar una nueva consulta en Google Places API:")
            print("   - En Codespaces / local: export GOOGLE_MAPS_API_KEY='tu_clave' o en .env")
            print("   - En Google Colab: guarda en Secrets (ícono de llave) como GOOGLE_MAPS_API_KEY")
            return

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.types",
    }

    all_places = []
    seen_ids = set()

    for target in SEARCH_TARGETS:
        body = {
            "includedTypes": ["pharmacy", "drugstore"],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": target["lat"], "longitude": target["lng"]},
                    "radius": 5000.0,
                }
            },
        }

        req = urllib.request.Request(
            PLACES_URL,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                places = res.get("places", [])
                added = 0
                for p in places:
                    pid = p.get("id")
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    loc = p.get("location", {})
                    dname = p.get("displayName", {}).get("text", "Farmacia")
                    entry = {
                        "id": pid,
                        "name": dname,
                        "chain": classify_chain(dname),
                        "address": p.get("formattedAddress", ""),
                        "lat": loc.get("latitude"),
                        "lng": loc.get("longitude"),
                        "rating": p.get("rating"),
                        "userRatingCount": p.get("userRatingCount"),
                        "target_zone": target["city"],
                        "types": p.get("types", []),
                    }
                    all_places.append(entry)
                    added += 1
                print(f"   - {target['city']}: +{added} farmacias encontradas.")
                time.sleep(0.2)
        except Exception as e:
            print(f"   Error en {target['city']}: {e}")

    with open(GOOGLE_PLACES, "w", encoding="utf-8") as f:
        json.dump(all_places, f, indent=2, ensure_ascii=False)

    print(f"[OK] Éxito: {len(all_places)} farmacias únicas extraídas desde Google Places.")
    print(f"  Guardado en {GOOGLE_PLACES}")


if __name__ == "__main__":
    query_google_places()
