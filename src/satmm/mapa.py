"""Mapa de alertas con Folium: polígonos coloreados por semáforo."""
import json
from pathlib import Path

import folium
import pandas as pd

from satmm.boletin import num
from satmm.datos import DATA
from satmm.explicacion import texto_razon

TOPO = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"

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
            "prob": f"{num(100 * fila['p'])} %",
            "razones": "<br>".join("• " + texto_razon(r, int(fila["mes"]), num)
                                   for r in fila.get("razones", [])) or "—",
        })

    # Esri y no OpenStreetMap: OSM bloquea sus mosaicos (403) cuando el HTML se abre como archivo
    # local, porque el navegador no envía Referer. Sin internet queda el fondo gris y los polígonos.
    m = folium.Map(location=[6.9, -73.4], zoom_start=8, tiles=None)
    folium.TileLayer(TOPO, attr="Tiles &copy; Esri, HERE, Garmin, USGS, NGA", name="Relieve").add_to(m)
    m.get_root().header.add_child(folium.Element(
        "<style>.leaflet-container{background:#D9D9D9}</style>"))
    folium.GeoJson(
        geo,
        style_function=lambda f: {"fillColor": COLORES[f["properties"]["nivel"]],
                                  "color": "#555", "weight": 0.6, "fillOpacity": 0.75},
        tooltip=folium.GeoJsonTooltip(
            fields=["municipio", "nivel", "prob", "ranking"],
            aliases=["Municipio", "Nivel", "Probabilidad", "Puesto"]),
        popup=folium.GeoJsonPopup(
            fields=["municipio", "nivel", "prob", "lluvia_2m", "mm_12m", "razones"],
            aliases=["Municipio", "Nivel", "Probabilidad", "Lluvia 2 meses", "Mov. en masa 12 m",
                     "Por qué"], max_width=380),
    ).add_to(m)
    leyenda = "".join(f"<div><span style='background:{c};width:12px;height:12px;display:inline-block'></span> {n}</div>"
                      for n, c in COLORES.items())
    m.get_root().html.add_child(folium.Element(
        f"<div style='position:fixed;top:10px;right:10px;z-index:999;background:#C0C0C0;padding:6px 8px;"
        f"border:2px solid;border-color:#DFDFDF #000 #000 #DFDFDF;"
        f"box-shadow:inset 1px 1px 0 #FFF,inset -1px -1px 0 #808080;"
        f"font:11px Tahoma,sans-serif;line-height:1.6'><b>{titulo}</b>{leyenda}</div>"))
    return m

