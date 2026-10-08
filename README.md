# 🏥 Farmatodo Urban Analytics & Expansion Sandbox

Plataforma de geomarketing, análisis territorial de densidad poblacional (Kontur H3) y modelado de oportunidades de expansión comercial para farmacias en Venezuela.

---

## 🚀 Entornos de Desarrollo en la Nube

Este repositorio está preparado para desarrollarse **sin depender de tu computadora local**, permitiendo iterar desde cualquier navegador mediante **GitHub Codespaces** o **Google Colab**.

```
                           ┌──────────────────────────────┐
                           │   GitHub Repository          │
                           │   (scripts, config, visor)   │
                           └──────────────┬───────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     ┌─────────────────────────┐                     ┌─────────────────────────┐
     │    GitHub Codespaces    │                     │      Google Colab       │
     │  - Contenedor en nube   │                     │  - Notebook interactivo │
     │  - VS Code en navegador │                     │  - GPU/CPU en nube      │
     │  - Datos en ./data      │                     │  - Datos en Google Drive│
     └─────────────────────────┘                     └────────────┬────────────┘
                                                                  ▼
                                                     ┌─────────────────────────┐
                                                     │      Google Drive       │
                                                     │  (farmatodo-sandbox)    │
                                                     │  - GPKG Kontur (37 MB)  │
                                                     │  - Censos de farmacias  │
                                                     │  - Clusters y scoring   │
                                                     └─────────────────────────┘
```

---

### Opción 1: GitHub Codespaces (Recomendado para desarrollo de scripts)

1. En la página de este repositorio en GitHub, haz clic en el botón verde **`<> Code`** -> pestaña **Codespaces** -> **`Create codespace on main`**.
2. Codespaces iniciará un entorno completo de Linux en la nube con Python 3.11, dependencias de `requirements.txt` y extensiones de VS Code preinstaladas automáticamente (`.devcontainer`).
3. Para configurar tu clave de Google Maps de forma segura:
   - Copia `.env.example` a `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edita `.env` y coloca tu API key: `GOOGLE_MAPS_API_KEY=tu_clave_aqui`
   - O agrégala en GitHub Settings -> Codespaces -> Secrets.
4. Ejecuta el pipeline:
   ```bash
   python scripts/run_pipeline.py --build-only
   ```

---

### Opción 2: Google Colab + Google Drive (Recomendado para análisis interactivo)

1. **Subir los datos a Google Drive**:
   - Sube la carpeta llamada **`farmatodo-sandbox`** a la raíz de tu Google Drive (**Mi Unidad** / **My Drive**).
   - Esta carpeta contiene los datasets procesados (`kontur_population_VE.gpkg`, censos de farmacias, clusters, etc.).
2. **Abrir el Notebook**:
   - Abre [notebooks/farmatodo_sandbox_colab.ipynb](notebooks/farmatodo_sandbox_colab.ipynb) en Google Colab.
3. **Configurar la API Key de forma segura**:
   - En la barra lateral izquierda de Google Colab, haz clic en el ícono de llave **Secrets (🔑)**.
   - Crea un secreto con el nombre `GOOGLE_MAPS_API_KEY` y pega tu clave.
   - Activa el interruptor *"Notebook access"*. De esta forma tus credenciales nunca quedan escritas en el código.
4. **Ejecutar**:
   - Ejecuta las celdas en orden. El notebook montará Google Drive, detectará automáticamente la carpeta `/content/drive/MyDrive/farmatodo-sandbox` y compilará el dashboard interactivo.

---

## 📁 Estructura del Proyecto

```
farmatodo-sandbox/
├── .devcontainer/
│   └── devcontainer.json          # Configuración para 1-click GitHub Codespaces
├── config/
│   ├── __init__.py
│   └── config.py                  # Detección dinámica de rutas (Drive / local) y API keys
├── scripts/
│   ├── 01_fetch_farmatodo_stores.py # Extracción de tiendas Farmatodo desde API oficial
│   ├── 02_fetch_osm_pharmacies.py   # Censo nacional de farmacias OpenStreetMap
│   ├── 03_query_google_places.py    # Consulta segura a Google Places API (New)
│   ├── 04_merge_competitors.py      # Fusión y desduplicación espacial (60m)
│   ├── 05_download_kontur.py        # Descarga y descompresión de Kontur H3 GPKG
│   ├── 06_process_kontur_hexagons.py# Conversión EPSG:3857->WGS84 y proximidad Farmatodo
│   ├── 07_cluster_and_rank.py       # Modelo de scoring y clustering espacial (3.5km)
│   ├── 08_enrich_clusters.py        # Toponimia nacional y taxonomía Greenfield / Intraurbana
│   ├── 09_build_dashboard_bundle.py # Generación de bundle liviano (dashboard_data.json)
│   ├── 10_build_final_html.py       # Compilación del HTML web interactivo
│   └── run_pipeline.py              # Ejecutor maestro por línea de comandos
├── templates/
│   └── template.html              # Plantilla web del dashboard (Leaflet + Bootstrap)
├── notebooks/
│   └── farmatodo_sandbox_colab.ipynb# Notebook optimizado para Google Colab y Codespaces
├── analisis_contexto_urbano_farmatodo.html # Entregable web autónomo compilado
├── .env.example                   # Plantilla de variables de entorno
├── .gitignore                     # Exclusión estricta de datasets y credenciales
├── requirements.txt               # Dependencias de Python
└── README.md
```

---

## 📊 Metodología y Modelo de Scoring

El modelo prioriza zonas con alta densidad demográfica que actualmente se encuentran desatendidas por Farmatodo y con baja saturación de competidores:

$$\text{Score de Oportunidad} = \frac{\text{Población} \times f(d_{\text{FTD}})}{1 + 0.20 \times \text{Competidores}_{2\text{km}}}$$

Donde $f(d_{\text{FTD}})$ es la función de distancia a la tienda Farmatodo más cercana:
- $< 1.5\text{ km}$: Factor $0.10$ (Canibalización comercial).
- $1.5\text{ – }2.5\text{ km}$: Factor $0.60$ (Borde de área de servicio).
- $> 2.5\text{ km}$: Factor $\min(d/2.5, 3.5)$ (Zona desatendida / Vacío comercial).

### Taxonomía de Oportunidad
- **Densificación Intraurbana y Cobertura de Vacíos**: Micro-zonas desatendidas ($>2\text{ km}$) dentro de grandes metrópolis donde Farmatodo ya tiene presencia (Caracas, Valencia, Maracaibo, Maracay, Barquisimeto).
- **Expansión Greenfield (Nuevas Plazas Estratégicas)**: Ciudades secundarias e intermedias a más de $15\text{–}20\text{ km}$ de cualquier Farmatodo con poblaciones entre 25k y 100k+ habitantes.

---

## 🔒 Buenas Prácticas de Seguridad
- **Ninguna credencial** está escrita en el código.
- Los datasets pesados (`.gpkg`, `.json`, `.geojson`) están ignorados en `.gitignore` para mantener el repositorio ágil y liviano.
