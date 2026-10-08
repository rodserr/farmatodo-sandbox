"""
06_process_kontur_hexagons.py
Decodifica geometrías binarias de Kontur GPKG (EPSG:3857 -> WGS84), filtra hexágonos urbanos
(población >= 150) y calcula la distancia mínima a tiendas Farmatodo.
Salidas:
  - data/kontur_urban_hexagons.json
"""

import sys
from pathlib import Path
import sqlite3
import struct
import math
import json
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import STORES_JSON, KONTUR_GPKG, KONTUR_URBAN


def wgs84_to_mercator(lon, lat):
    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = y * 20037508.34 / 180.0
    return x, y


def mercator_to_wgs84(x, y):
    lon = (x / 20037508.34) * 180.0
    lat = (y / 20037508.34) * 180.0
    lat = 180.0 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return round(lon, 6), round(lat, 6)


def process_kontur_hexagons():
    print("--> [06] Procesando hexágonos urbanos de Kontur y calculando distancias a Farmatodo...")
    t0 = time.time()

    if not KONTUR_GPKG.exists():
        raise FileNotFoundError(f"No se encontró {KONTUR_GPKG}. Ejecuta primero el paso 05.")

    with open(STORES_JSON, "r", encoding="utf-8") as f:
        stores = json.load(f)

    # Coordenadas de tiendas en Mercator para cálculo euclidiano rápido
    store_coords_m = []
    for s in stores:
        if s.get("latitude") and s.get("longitude"):
            mx, my = wgs84_to_mercator(s["longitude"], s["latitude"])
            store_coords_m.append((s["name"], s["city_group"], mx, my, s["longitude"], s["latitude"]))

    print(f"Indexadas {len(store_coords_m)} tiendas Farmatodo para cálculo de proximidad.")

    conn = sqlite3.connect(KONTUR_GPKG)
    cur = conn.cursor()
    cur.execute("SELECT fid, geom, h3, population FROM population WHERE population >= 150;")

    envelope_lengths = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
    hexagons = []

    for fid, geom_bytes, h3, pop in cur:
        flags = geom_bytes[3]
        envelope_type = (flags >> 1) & 0x07
        wkb_offset = 8 + envelope_lengths.get(envelope_type, 0)
        wkb = geom_bytes[wkb_offset:]

        byte_order = wkb[0]
        endian = "<" if byte_order == 1 else ">"
        num_points = struct.unpack(endian + "I", wkb[9:13])[0]

        poly_m = []
        sum_x = 0.0
        sum_y = 0.0

        for i in range(num_points):
            x, y = struct.unpack(endian + "dd", wkb[13 + i * 16 : 13 + (i + 1) * 16])
            poly_m.append((x, y))
            sum_x += x
            sum_y += y

        cx_m = sum_x / num_points
        cy_m = sum_y / num_points
        c_lon, c_lat = mercator_to_wgs84(cx_m, cy_m)

        # Distancia mínima a Farmatodo
        min_dist_m = 99999999.0
        nearest_store = None
        for s_name, s_city, smx, smy, slon, slat in store_coords_m:
            d = math.hypot(cx_m - smx, cy_m - smy)
            if d < min_dist_m:
                min_dist_m = d
                nearest_store = (s_name, s_city)

        poly_wgs = []
        for x, y in poly_m:
            w_lon, w_lat = mercator_to_wgs84(x, y)
            poly_wgs.append([w_lon, w_lat])

        hexagons.append({
            "fid": fid,
            "h3": h3,
            "pop": round(pop),
            "cx": round(c_lon, 5),
            "cy": round(c_lat, 5),
            "min_dist_km": round(min_dist_m / 1000.0, 2),
            "nearest_store": nearest_store[0] if nearest_store else "",
            "nearest_city": nearest_store[1] if nearest_store else "",
            "coords": poly_wgs,
        })

    conn.close()
    print(f"[OK] Procesados {len(hexagons)} hexágonos urbanos en {time.time() - t0:.2f}s.")

    with open(KONTUR_URBAN, "w", encoding="utf-8") as f:
        json.dump(hexagons, f)

    print(f"  Guardado en {KONTUR_URBAN}")


if __name__ == "__main__":
    process_kontur_hexagons()
