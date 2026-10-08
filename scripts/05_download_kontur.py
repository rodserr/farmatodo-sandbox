"""
05_download_kontur.py
Descarga el dataset de densidad de población H3 de Kontur (Venezuela) en formato GeoPackage (.gpkg).
Salidas:
  - data/kontur_population_VE.gpkg.gz
  - data/kontur_population_VE.gpkg
"""

import sys
from pathlib import Path
import os
import urllib.request
import gzip

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import KONTUR_GZ, KONTUR_GPKG

KONTUR_URL = "https://geodata-eu-central-1-kontur-public.s3.amazonaws.com/kontur_datasets/kontur_population_VE_20231101.gpkg.gz"


def download_kontur():
    print("--> [05] Verificando dataset de población Kontur GeoPackage...")

    if KONTUR_GPKG.exists() and KONTUR_GPKG.stat().st_size > 1024 * 1024:
        print(f"[OK] Archivo GeoPackage ya existe y es válido: {KONTUR_GPKG} ({KONTUR_GPKG.stat().st_size / (1024*1024):.1f} MB)")
        return

    if not KONTUR_GZ.exists() or KONTUR_GZ.stat().st_size < 1024 * 1024:
        print(f"Descargando Kontur Venezuela gzip desde S3 ({KONTUR_URL})...")
        urllib.request.urlretrieve(KONTUR_URL, KONTUR_GZ)
        print("Descarga completada!")

    print(f"Descomprimiendo {KONTUR_GZ} -> {KONTUR_GPKG}...")
    with gzip.open(KONTUR_GZ, "rb") as f_in:
        with open(KONTUR_GPKG, "wb") as f_out:
            f_out.write(f_in.read())

    print(f"[OK] Éxito: GeoPackage descomprimido en {KONTUR_GPKG} ({KONTUR_GPKG.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    download_kontur()
