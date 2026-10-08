import importlib.util
from pathlib import Path

# Helper to import numeric-prefixed scripts
def _import_module(module_name, file_name):
    script_path = Path(__file__).parent / file_name
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_mod_01 = _import_module("step01", "01_fetch_farmatodo_stores.py")
_mod_02 = _import_module("step02", "02_fetch_osm_pharmacies.py")
_mod_03 = _import_module("step03", "03_query_google_places.py")
_mod_04 = _import_module("step04", "04_merge_competitors.py")
_mod_05 = _import_module("step05", "05_download_kontur.py")
_mod_06 = _import_module("step06", "06_process_kontur_hexagons.py")
_mod_07 = _import_module("step07", "07_cluster_and_rank.py")
_mod_08 = _import_module("step08", "08_enrich_clusters.py")
_mod_09 = _import_module("step09", "09_build_dashboard_bundle.py")
_mod_10 = _import_module("step10", "10_build_final_html.py")

fetch_and_clean_stores = _mod_01.fetch_and_clean_stores
fetch_osm_pharmacies = _mod_02.fetch_osm_pharmacies
query_google_places = _mod_03.query_google_places
merge_competitors = _mod_04.merge_competitors
download_kontur = _mod_05.download_kontur
process_kontur_hexagons = _mod_06.process_kontur_hexagons
cluster_and_rank = _mod_07.cluster_and_rank
enrich_clusters = _mod_08.enrich_clusters
build_dashboard_bundle = _mod_09.build_dashboard_bundle
build_final_html = _mod_10.build_final_html
