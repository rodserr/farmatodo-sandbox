"""
08_enrich_clusters.py
Enriquece los clusters de oportunidad con nombres geográficos precisos (ciudades y estados de Venezuela)
y calcula el desglose específico de competidores por cadena en el radio de influencia.
Salidas:
  - data/opportunity_clusters_enriched.json
"""

import sys
from pathlib import Path
import json
import math
from collections import defaultdict, Counter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import OPPORTUNITY_CLUSTERS, MASTER_COMPS_JSON, OPPORTUNITY_CLUSTERS_ENRICHED

# Diccionario geográfico de referencia urbana venezolana
VZLA_CITIES = [
    ("Caracas", 10.4880, -66.8792, "Distrito Capital"),
    ("Maracaibo", 10.6427, -71.6125, "Zulia"),
    ("San Francisco", 10.5500, -71.6400, "Zulia"),
    ("Cabimas", 10.3950, -71.4450, "Zulia"),
    ("Ciudad Ojeda", 10.2000, -71.3000, "Zulia"),
    ("Machiques", 10.0600, -72.5500, "Zulia"),
    ("Santa Bárbara del Zulia", 8.9800, -71.9100, "Zulia"),
    ("Valencia", 10.1800, -67.9900, "Carabobo"),
    ("Naguanagua", 10.2500, -68.0100, "Carabobo"),
    ("Guacara", 10.2300, -67.8800, "Carabobo"),
    ("Los Guayos", 10.1900, -67.9300, "Carabobo"),
    ("Puerto Cabello", 10.4700, -68.0150, "Carabobo"),
    ("Barquisimeto", 10.0700, -69.3200, "Lara"),
    ("Cabudare", 10.0300, -69.2600, "Lara"),
    ("Carora", 10.1750, -70.0800, "Lara"),
    ("El Tocuyo", 9.7800, -69.7900, "Lara"),
    ("Quíbor", 9.9300, -69.6200, "Lara"),
    ("Maracay", 10.2469, -67.5958, "Aragua"),
    ("Turmero", 10.2280, -67.4740, "Aragua"),
    ("Cagua", 10.1850, -67.4550, "Aragua"),
    ("La Victoria", 10.2280, -67.3300, "Aragua"),
    ("Villa de Cura", 10.0400, -67.4900, "Aragua"),
    ("San Cristóbal", 7.7700, -72.2250, "Táchira"),
    ("Táriba", 7.8200, -72.2200, "Táchira"),
    ("Rubio", 7.7000, -72.3500, "Táchira"),
    ("San Antonio del Táchira", 7.8100, -72.4400, "Táchira"),
    ("Mérida", 8.5983, -71.1450, "Mérida"),
    ("El Vigía", 8.6250, -71.6500, "Mérida"),
    ("Valera", 9.3178, -70.6036, "Trujillo"),
    ("Trujillo", 9.3667, -70.4333, "Trujillo"),
    ("Boconó", 9.2500, -70.2600, "Trujillo"),
    ("Barinas", 8.6226, -70.2075, "Barinas"),
    ("Socopó", 8.2400, -70.9800, "Barinas"),
    ("Guanare", 9.0450, -69.7450, "Portuguesa"),
    ("Acarigua", 9.5550, -69.2000, "Portuguesa"),
    ("Araure", 9.5600, -69.2150, "Portuguesa"),
    ("San Felipe", 10.3400, -68.7400, "Yaracuy"),
    ("Yaritagua", 10.0800, -69.1200, "Yaracuy"),
    ("Chivacoa", 10.1600, -68.8900, "Yaracuy"),
    ("San Juan de los Morros", 9.9100, -67.3550, "Guárico"),
    ("Calabozo", 8.9240, -67.4280, "Guárico"),
    ("Valle de la Pascua", 9.2150, -66.0080, "Guárico"),
    ("Altagracia de Orituco", 9.8600, -66.3800, "Guárico"),
    ("San Fernando de Apure", 7.8878, -67.4722, "Apure"),
    ("Puerto Ayacucho", 5.6600, -67.6200, "Amazonas"),
    ("Ciudad Guayana / Puerto Ordaz", 8.3000, -62.7100, "Bolívar"),
    ("San Félix", 8.3400, -62.6500, "Bolívar"),
    ("Ciudad Bolívar", 8.1250, -63.5450, "Bolívar"),
    ("Upata", 8.0100, -62.3900, "Bolívar"),
    ("Caicara del Orinoco", 7.6300, -66.1600, "Bolívar"),
    ("Barcelona", 10.1300, -64.6900, "Anzoátegui"),
    ("Puerto La Cruz", 10.2100, -64.6300, "Anzoátegui"),
    ("Lechería", 10.1900, -64.6900, "Anzoátegui"),
    ("El Tigre", 8.8875, -64.2450, "Anzoátegui"),
    ("Anaco", 9.4280, -64.4600, "Anzoátegui"),
    ("Cumaná", 10.4536, -64.1825, "Sucre"),
    ("Carúpano", 10.6600, -63.2500, "Sucre"),
    ("Maturín", 9.7456, -63.1833, "Monagas"),
    ("Punta de Mata", 9.6800, -63.6300, "Monagas"),
    ("Porlamar / Pampatar", 10.9575, -63.8500, "Nueva Esparta"),
    ("Juan Griego", 11.0800, -63.9600, "Nueva Esparta"),
    ("Coro", 11.4045, -69.6734, "Falcón"),
    ("Punto Fijo", 11.6956, -70.1996, "Falcón"),
    ("Carora", 10.1750, -70.0800, "Lara"),
    ("Guarenas", 10.4700, -66.6200, "Miranda"),
    ("Guatire", 10.4720, -66.5450, "Miranda"),
    ("Los Teques", 10.3400, -67.0400, "Miranda"),
    ("San Antonio de Los Altos", 10.3700, -66.9600, "Miranda"),
    ("Charallave", 10.2400, -66.8600, "Miranda"),
    ("Cúa", 10.1600, -66.8800, "Miranda"),
    ("Ocumare del Tuy", 10.1100, -66.7700, "Miranda"),
    ("Higuerote", 10.4900, -66.1000, "Miranda"),
]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def enrich_clusters():
    print("--> [08] Enriqueciendo clusters territoriales con toponimia y análisis competitivo...")

    with open(OPPORTUNITY_CLUSTERS, "r", encoding="utf-8") as f:
        clusters = json.load(f)

    with open(MASTER_COMPS_JSON, "r", encoding="utf-8") as f:
        all_comps = json.load(f)
    competitors = [c for c in all_comps if c.get("chain") != "Farmatodo"]

    # Rejilla espacial de competidores
    comp_grid = defaultdict(list)
    for c in competitors:
        gx = int(c["lng"] / 0.02)
        gy = int(c["lat"] / 0.02)
        comp_grid[(gx, gy)].append(c)

    def get_nearby_comps(lat, lon, radius_km=2.5):
        gx = int(lon / 0.02)
        gy = int(lat / 0.02)
        found = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for c in comp_grid.get((gx + dx, gy + dy), []):
                    if haversine_km(lat, lon, c["lat"], c["lng"]) <= radius_km:
                        found.append(c)
        return found

    enriched = []
    for c in clusters:
        clat, clng = c["lat"], c["lng"]

        # Encontrar ciudad más cercana
        best_city = "Venezuela"
        best_state = ""
        min_d = 999999.0
        for name, city_lat, city_lng, state in VZLA_CITIES:
            d = haversine_km(clat, clng, city_lat, city_lng)
            if d < min_d:
                min_d = d
                best_city = name
                best_state = state

        # Ajuste de etiqueta contextual
        if min_d <= 4.0:
            zone_label = f"{best_city} (Casco Urbano)"
        elif min_d <= 15.0:
            zone_label = f"Eje {best_city} ({min_d:.1f} km)"
        else:
            zone_label = f"Área de Influencia {best_city}"

        # Competidores en el cluster
        nearby = get_nearby_comps(clat, clng, radius_km=2.5)
        chain_counts = Counter(x["chain"] for x in nearby)

        c_copy = dict(c)
        c_copy["city_name"] = best_city
        c_copy["state_name"] = best_state
        c_copy["zone_label"] = zone_label
        c_copy["competitor_breakdown"] = dict(chain_counts.most_common(5))
        enriched.append(c_copy)

    with open(OPPORTUNITY_CLUSTERS_ENRICHED, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"[OK] Éxito: {len(enriched)} clusters enriquecidos con toponimia y estado.")
    print(f"  Guardado en {OPPORTUNITY_CLUSTERS_ENRICHED}")


if __name__ == "__main__":
    enrich_clusters()
