"""
09_build_dashboard_bundle.py
Compila y optimiza el paquete de datos en un solo JSON liviano para el visor web interactivo.
Salidas:
  - data/dashboard_data.json
"""

import sys
from pathlib import Path
import json
import os
from collections import Counter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import (
    STORES_JSON,
    MASTER_COMPS_JSON,
    OPPORTUNITY_CLUSTERS_ENRICHED,
    DISPLAY_HEXES_GEOJSON,
    DASHBOARD_DATA,
)


def build_dashboard_bundle():
    print("--> [09] Construyendo paquete de datos unificado para el Dashboard...")

    # 1. Tiendas Farmatodo
    with open(STORES_JSON, "r", encoding="utf-8") as f:
        stores_raw = json.load(f)

    stores = []
    for s in stores_raw:
        if s.get("latitude") and s.get("longitude"):
            stores.append({
                "id": s["id"],
                "n": s["name"],
                "a": s.get("address", ""),
                "c": s.get("city_group", ""),
                "m": s.get("municipality", ""),
                "lat": s["latitude"],
                "lng": s["longitude"],
                "p": s.get("phone", ""),
                "h": s.get("schedule", ""),
                "d": s.get("deliveryType", ""),
            })

    # 2. Competidores
    with open(MASTER_COMPS_JSON, "r", encoding="utf-8") as f:
        comps_raw = json.load(f)

    competitors = []
    for c in comps_raw:
        if c.get("chain") == "Farmatodo":
            continue
        competitors.append({
            "n": c["name"],
            "ch": c["chain"],
            "lat": c["lat"],
            "lng": c["lng"],
            "a": c.get("address", ""),
            "r": c.get("rating"),
            "rc": c.get("userRatingCount"),
            "s": c.get("source", ""),
        })

    # 3. Clusters Enriquecidos (Top 60)
    with open(OPPORTUNITY_CLUSTERS_ENRICHED, "r", encoding="utf-8") as f:
        clusters_raw = json.load(f)

    clusters = []
    for c in clusters_raw[:60]:
        clusters.append({
            "id": c["id"],
            "zl": c["zone_label"],
            "cat": c["category"],
            "city": c["city_name"],
            "state": c["state_name"],
            "pop": c["total_pop"],
            "dist": c["avg_dist_ftd_km"],
            "comp": c["competitors_2km"],
            "cbd": c["competitor_breakdown"],
            "score": c["score"],
            "lat": c["lat"],
            "lng": c["lng"],
        })

    # 4. Hexágonos compactos para renderizado Leaflet
    with open(DISPLAY_HEXES_GEOJSON, "r", encoding="utf-8") as f:
        hex_geojson = json.load(f)

    features = hex_geojson.get("features", [])
    features.sort(key=lambda x: x["properties"].get("s", 0) + x["properties"].get("p", 0), reverse=True)
    selected_features = features[:4500]

    hexagons_compact = []
    for feat in selected_features:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"][0]
        c_rounded = [[round(pt[1], 5), round(pt[0], 5)] for pt in coords]
        hexagons_compact.append([
            props.get("p", 0),      # 0: pop
            props.get("d", 0),      # 1: dist_ftd
            props.get("c", 0),      # 2: comp_2km
            props.get("s", 0),      # 3: opp_score
            props.get("cat", ""),   # 4: category
            props.get("city", ""),  # 5: nearest_city
            c_rounded,              # 6: coords [[lat, lng], ...]
        ])

    # 5. KPIs globales
    comp_by_chain = Counter(c["ch"] for c in competitors)
    stores_by_city = Counter(s["c"] for s in stores)

    stats = {
        "total_stores": len(stores),
        "total_competitors": len(competitors),
        "total_urban_hexes_analyzed": len(features),
        "top_stores_cities": stores_by_city.most_common(10),
        "competitors_by_chain": comp_by_chain.most_common(),
        "tier1_count": len([c for c in clusters if c["cat"] == "Densificación Intraurbana"]),
        "tier2_count": len([c for c in clusters if c["cat"] == "Expansión Greenfield (Nuevas Plazas)"]),
        "total_opp_pop": sum(c["pop"] for c in clusters),
    }

    bundle = {
        "stats": stats,
        "stores": stores,
        "competitors": competitors,
        "clusters": clusters,
        "hexagons": hexagons_compact,
    }

    with open(DASHBOARD_DATA, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False)

    size_mb = os.path.getsize(DASHBOARD_DATA) / (1024 * 1024)
    print(f"[OK] Éxito: Bundle de datos generado en {DASHBOARD_DATA} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    build_dashboard_bundle()
