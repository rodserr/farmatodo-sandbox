"""
run_pipeline.py
Ejecutor maestro de todo el flujo ETL, análisis espacial y compilación del dashboard.
Uso:
  python scripts/run_pipeline.py            # Ejecuta todo el pipeline
  python scripts/run_pipeline.py --build    # Solo compila bundle y HTML final
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATA_DIR, OUTPUT_HTML


def main():
    parser = argparse.ArgumentParser(description="Pipeline de Expansión Urbana Farmatodo")
    parser.add_argument("--build-only", action="store_true", help="Solo compila bundle y HTML usando datos existentes")
    parser.add_argument("--skip-downloads", action="store_true", help="Salta descargas pesadas de OSM y Kontur")
    args = parser.parse_args()

    print("=" * 70)
    print("  PIPELINE DE GEOMARKETING Y EXPANSIÓN URBANA - FARMATODO VENEZUELA")
    print(f"  Directorio de Datos: {DATA_DIR}")
    print("=" * 70)

    if args.build_only:
        print("\n[Modo Rápido: Compilación de Entregable]")
        from scripts import build_dashboard_bundle, build_final_html
        build_dashboard_bundle()
        build_final_html()
        print(f"\n[OK] Proceso completado: {OUTPUT_HTML}")
        return

    # Paso 1: Tiendas Farmatodo
    from scripts import fetch_and_clean_stores
    fetch_and_clean_stores()

    # Paso 2: OSM
    if not args.skip_downloads:
        from scripts import fetch_osm_pharmacies
        fetch_osm_pharmacies()

    # Paso 3: Google Places
    from scripts import query_google_places
    query_google_places()

    # Paso 4: Merge Competidores
    from scripts import merge_competitors
    merge_competitors()

    # Paso 5: Kontur GPKG
    if not args.skip_downloads:
        from scripts import download_kontur
        download_kontur()

    # Paso 6: Procesamiento de hexágonos Kontur
    from scripts import process_kontur_hexagons
    process_kontur_hexagons()

    # Paso 7: Clustering y Scoring
    from scripts import cluster_and_rank
    cluster_and_rank()

    # Paso 8: Enriquecimiento de clusters
    from scripts import enrich_clusters
    enrich_clusters()

    # Paso 9: Bundle web
    from scripts import build_dashboard_bundle
    build_dashboard_bundle()

    # Paso 10: Compilación HTML
    from scripts import build_final_html
    build_final_html()

    print("\n" + "=" * 70)
    print(f"  [OK] PIPELINE COMPLETADO EXITOSAMENTE")
    print(f"  Entregable: {OUTPUT_HTML}")
    print("=" * 70)


if __name__ == "__main__":
    main()
