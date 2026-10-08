import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root if it exists
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()


def resolve_data_dir() -> Path:
    """
    Resolves data directory across environments:
    1. Explicit DATA_DIR environment variable
    2. Google Colab Google Drive mount: /content/drive/MyDrive/farmatodo-sandbox
    3. Local data/ directory within repo
    4. Sibling directory ../farmatodo-sandbox
    """
    env_dir = os.getenv("DATA_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists():
            return p

    # Google Colab Drive checks
    colab_subdata = Path("/content/drive/MyDrive/farmatodo-sandbox/data")
    if colab_subdata.exists():
        return colab_subdata

    colab_drive = Path("/content/drive/MyDrive/farmatodo-sandbox")
    if colab_drive.exists():
        return colab_drive

    # Local data inside repo
    local_data = BASE_DIR / "data"
    if local_data.exists():
        return local_data

    # Sibling folder
    sibling = BASE_DIR.parent / "farmatodo-sandbox"
    if sibling.exists():
        return sibling

    local_data.mkdir(parents=True, exist_ok=True)
    return local_data


DATA_DIR = resolve_data_dir()

# File paths
STORES_RAW = DATA_DIR / "farmatodo_stores_raw.json"
STORES_JSON = DATA_DIR / "farmatodo_stores.json"
STORES_GEOJSON = DATA_DIR / "farmatodo_stores.geojson"

OSM_RAW = DATA_DIR / "osm_pharmacies_raw.json"
OSM_ALL = DATA_DIR / "all_pharmacies.json"
GOOGLE_PLACES = DATA_DIR / "google_places_pharmacies.json"

MASTER_COMPS_JSON = DATA_DIR / "master_competitors.json"
MASTER_COMPS_GEOJSON = DATA_DIR / "master_competitors.geojson"

KONTUR_GZ = DATA_DIR / "kontur_population_VE.gpkg.gz"
KONTUR_GPKG = DATA_DIR / "kontur_population_VE.gpkg"
KONTUR_URBAN = DATA_DIR / "kontur_urban_hexagons.json"
SCORED_HEXES = DATA_DIR / "scored_hexagons.json"

OPPORTUNITY_CLUSTERS = DATA_DIR / "opportunity_clusters.json"
OPPORTUNITY_CLUSTERS_ENRICHED = DATA_DIR / "opportunity_clusters_enriched.json"
DISPLAY_HEXES_GEOJSON = DATA_DIR / "kontur_display_hexes.geojson"

DASHBOARD_DATA = DATA_DIR / "dashboard_data.json"

TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATE_HTML = TEMPLATES_DIR / "template.html"
OUTPUT_HTML = BASE_DIR / "analisis_contexto_urbano_farmatodo.html"


def get_google_maps_api_key() -> str:
    """
    Safely retrieves the Google Maps API key from environment or Google Colab userdata.
    Raises ValueError if key is missing when required.
    """
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()

    # If running in Colab and key not set in os.environ, try colab userdata
    if not key and "google.colab" in sys.modules:
        try:
            from google.colab import userdata
            key = userdata.get("GOOGLE_MAPS_API_KEY")
        except Exception:
            pass

    return key or ""
