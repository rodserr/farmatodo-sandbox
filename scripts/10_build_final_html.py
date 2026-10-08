"""
10_build_final_html.py
Inyecta el bundle de datos dentro de template.html para compilar la aplicación web autónoma final.
Salidas:
  - analisis_contexto_urbano_farmatodo.html
"""

import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import TEMPLATE_HTML, DASHBOARD_DATA, OUTPUT_HTML


def build_final_html():
    print("--> [10] Compilando entregable web final (analisis_contexto_urbano_farmatodo.html)...")

    if not TEMPLATE_HTML.exists():
        raise FileNotFoundError(f"Plantilla no encontrada: {TEMPLATE_HTML}")

    if not DASHBOARD_DATA.exists():
        raise FileNotFoundError(f"Bundle no encontrado: {DASHBOARD_DATA}. Ejecuta el paso 09 primero.")

    with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
        template = f.read()

    with open(DASHBOARD_DATA, "r", encoding="utf-8") as f:
        data_str = f.read()

    final_html = template.replace("__DASHBOARD_DATA__", data_str)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)

    size_mb = os.path.getsize(OUTPUT_HTML) / (1024 * 1024)
    print(f"[OK] Éxito: HTML final generado en {OUTPUT_HTML} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    build_final_html()
