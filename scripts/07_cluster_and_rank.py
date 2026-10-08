"""
07_cluster_and_rank.py
Calcula la presión competitiva en radio de 2km para cada hexágono, evalúa el modelo
de scoring de oportunidades y agrupa los hexágonos mediante clustering espacial (3.5km).
Salidas:
  - data/scored_hexagons.json
  - data/opportunity_clusters.json
  - data/kontur_display_hexes.geojson
"""

import sys
from pathlib import Path
import json
import math
from collections import defaultdict, Counter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import (
    STORES_JSON,
    MASTER_COMPS_JSON,
    KONTUR_URBAN,
    SCORED_HEXES,
    OPPORTUNITY_CLUSTERS,
    DISPLAY_HEXES_GEOJSON,
)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def cluster_and_rank():
    print("--> [07] Ejecutando Scoring de Oportunidad y Clustering Espacial...")

    with open(MASTER_COMPS_JSON, "r", encoding="utf-8") as f:
        all_comps = json.load(f)
    competitors = [c for c in all_comps if c.get("chain") != "Farmatodo"]

    with open(KONTUR_URBAN, "r", encoding="utf-8") as f:
        hexagons = json.load(f)

    # Rejilla espacial de competidores (0.02 deg ~ 2.2km)
    comp_grid = defaultdict(list)
    for c in competitors:
        gx = int(c["lng"] / 0.02)
        gy = int(c["lat"] / 0.02)
        comp_grid[(gx, gy)].append(c)

    def get_competitor_stats(lat, lon, radius_km=2.0):
        gx = int(lon / 0.02)
        gy = int(lat / 0.02)
        comps = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for c in comp_grid.get((gx + dx, gy + dy), []):
                    dist = haversine_km(lat, lon, c["lat"], c["lng"])
                    if dist <= radius_km:
                        comps.append(c)
        return len(comps), comps

    processed_hexes = []
    display_features = []

    for h in hexagons:
        pop = h["pop"]
        if pop < 250:
            continue
        lat, lng = h["cy"], h["cx"]
        dist_ftd = h["min_dist_km"]

        comp_count, comps = get_competitor_stats(lat, lng, radius_km=2.0)

        # Categorización base
        if dist_ftd < 2.0:
            cat = "Cobertura Consolidada"
        elif 2.0 <= dist_ftd <= 15.0:
            cat = "Densificación Intraurbana"
        else:
            cat = "Expansión Greenfield"

        # Función multiplicadora de distancia Farmatodo
        if dist_ftd < 1.5:
            dist_factor = 0.10
        elif 1.5 <= dist_ftd <= 2.5:
            dist_factor = 0.60
        else:
            dist_factor = min(dist_ftd / 2.5, 3.5)

        # Oportunidad = (Población * Factor_Distancia_FTD) / (1 + 0.20 * Competidores)
        opp_score = (pop * dist_factor) / (1.0 + 0.20 * comp_count)

        h_entry = {
            "h3": h["h3"],
            "pop": pop,
            "cx": lng,
            "cy": lat,
            "dist_ftd_km": dist_ftd,
            "comp_2km": comp_count,
            "opp_score": round(opp_score, 1),
            "category": cat,
            "nearest_city": h.get("nearest_city", ""),
        }
        processed_hexes.append(h_entry)

        # Feature GeoJSON optimizada para visualización
        display_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [h["coords"]],
            },
            "properties": {
                "h": h["h3"],
                "p": pop,
                "d": dist_ftd,
                "c": comp_count,
                "s": round(opp_score, 1),
                "cat": cat,
                "city": h.get("nearest_city", ""),
            },
        })

    # Guardar scored hexagons
    with open(SCORED_HEXES, "w", encoding="utf-8") as f:
        json.dump(processed_hexes, f)

    # Guardar GeoJSON para mapa (top más relevantes)
    display_geojson = {"type": "FeatureCollection", "features": display_features}
    with open(DISPLAY_HEXES_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(display_geojson, f)

    print(f"Evaluados {len(processed_hexes)} hexágonos urbanos.")

    # 3. Clustering Espacial voraz (3.5 km) de hexágonos con oportunidad relevante
    opp_hexes = [h for h in processed_hexes if h["opp_score"] >= 300 and h["category"] != "Cobertura Consolidada"]
    opp_hexes.sort(key=lambda x: x["opp_score"], reverse=True)

    clusters = []
    assigned = set()
    cluster_id = 1

    for hex_center in opp_hexes:
        if hex_center["h3"] in assigned:
            continue

        c_hexes = [hex_center]
        assigned.add(hex_center["h3"])

        # Buscar vecinos en 3.5 km
        for cand in opp_hexes:
            if cand["h3"] in assigned:
                continue
            d = haversine_km(hex_center["cy"], hex_center["cx"], cand["cy"], cand["cx"])
            if d <= 3.5:
                c_hexes.append(cand)
                assigned.add(cand["h3"])

        total_pop = sum(x["pop"] for x in c_hexes)
        sum_lat = sum(x["cy"] for x in c_hexes)
        sum_lng = sum(x["cx"] for x in c_hexes)
        clat = round(sum_lat / len(c_hexes), 5)
        clng = round(sum_lng / len(c_hexes), 5)

        avg_dist = round(sum(x["dist_ftd_km"] for x in c_hexes) / len(c_hexes), 2)
        total_comps = sum(x["comp_2km"] for x in c_hexes)
        avg_comps = round(total_comps / len(c_hexes), 1)
        tot_score = round(sum(x["opp_score"] for x in c_hexes), 1)

        # Categoría predominante
        is_greenfield = sum(1 for x in c_hexes if x["dist_ftd_km"] > 15.0) > (len(c_hexes) / 2)
        category = "Expansión Greenfield (Nuevas Plazas)" if is_greenfield else "Densificación Intraurbana"

        clusters.append({
            "id": cluster_id,
            "lat": clat,
            "lng": clng,
            "hex_count": len(c_hexes),
            "total_pop": total_pop,
            "avg_dist_ftd_km": avg_dist,
            "competitors_2km": avg_comps,
            "score": tot_score,
            "category": category,
            "hexes": [x["h3"] for x in c_hexes],
        })
        cluster_id += 1

    clusters.sort(key=lambda x: x["score"], reverse=True)

    with open(OPPORTUNITY_CLUSTERS, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=2, ensure_ascii=False)

    print(f"[OK] Éxito: Generados {len(clusters)} clusters de oportunidad territorial.")
    print(f"  Guardado en {OPPORTUNITY_CLUSTERS}")


if __name__ == "__main__":
    cluster_and_rank()
