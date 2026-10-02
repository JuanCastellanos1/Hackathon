"""Mapa de alertas con Folium: polígonos coloreados por semáforo."""
import json
from pathlib import Path

import folium
import pandas as pd

from satmm.datos import DATA

COLORES = {"Rojo": "#d7301f", "Amarillo": "#fdae35", "Verde": "#41ab5d"}


def construir(alertas: pd.DataFrame, titulo: str,
              ruta_geojson: Path = DATA / "santander_municipios.geojson") -> folium.Map:
    geo = json.loads(Path(ruta_geojson).read_text())
    info = alertas.set_index("codigo_dane")
    for f in geo["features"]:
        dane = int(f["properties"]["codigo_dane"])
        fila = info.loc[dane]
        f["properties"].update({
            "nivel": fila["nivel"],
            "ranking": f"{int(fila['ranking'])} de {len(info)}",
            "lluvia_2m": f"{fila['lluvia_2m']:.0f} mm",
            "mm_12m": int(fila["mm_12m"]),
        })

    m = folium.Map(location=[6.9, -73.4], zoom_start=8, tiles="OpenStreetMap")
    folium.GeoJson(
        geo,
        style_function=lambda f: {"fillColor": COLORES[f["properties"]["nivel"]],
                                  "color": "#555", "weight": 0.6, "fillOpacity": 0.75},
        tooltip=folium.GeoJsonTooltip(
            fields=["municipio", "nivel", "ranking", "lluvia_2m", "mm_12m"],
            aliases=["Municipio", "Nivel", "Ranking", "Lluvia 2 meses", "Mov. en masa 12 m"]),
    ).add_to(m)
    leyenda = "".join(f"<div><span style='background:{c};width:12px;height:12px;display:inline-block'></span> {n}</div>"
                      for n, c in COLORES.items())
    m.get_root().html.add_child(folium.Element(
        f"<div style='position:fixed;top:10px;right:10px;z-index:999;background:#fff;padding:8px;"
        f"border:1px solid #999;font:12px sans-serif'><b>{titulo}</b>{leyenda}</div>"))
    return m
