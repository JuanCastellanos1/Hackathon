"""Genera out/tablero.html (estética Windows 98): mapa por mes, alertas, boletines y desempeño."""
import html
import json
import re
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from satmm import boletin, explicacion, mapa, modelo as mo
from satmm.variables import FEATURES

PLANTILLAS = Path(__file__).parent / "plantillas"


def md_a_html(md: str) -> str:
    """Conversor mínimo para el boletín: títulos, viñetas y negritas."""
    out, lista = [], False
    for linea in md.splitlines():
        t = html.escape(linea)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        if t.startswith("- "):
            if not lista:
                out.append("<ul>"); lista = True
            out.append(f"<li>{t[2:]}</li>")
            continue
        if lista:
            out.append("</ul>"); lista = False
        if t.startswith("## "):
            out.append(f"<h3>{t[3:]}</h3>")
        elif t.startswith("# "):
            out.append(f"<h2>{t[2:]}</h2>")
        elif t.strip():
            out.append(f"<p>{t}</p>")
    if lista:
        out.append("</ul>")
    return "\n".join(out)


def generar(modelo_final, tabla: pd.DataFrame, umbrales: mo.Umbrales, municipios: pd.DataFrame,
            emergencias: pd.DataFrame, metricas_2025: dict, anio: int = 2025,
            destino: Path = Path("out")) -> dict:
    (destino / "mapas").mkdir(parents=True, exist_ok=True)
    (destino / "boletines").mkdir(parents=True, exist_ok=True)
    meses, total_boletines, intrusas_total = [], 0, 0

    for mes in range(1, 13):
        al = mo.alertas_mes(modelo_final, tabla, anio, mes, umbrales, municipios)
        al = explicacion.agregar_razones(al, modelo_final, FEATURES)
        nombre_mes = boletin.MESES[mes - 1]
        mapa.construir(al, f"{nombre_mes.capitalize()} {anio}").save(destino / "mapas" / f"{anio}-{mes:02d}.html")

        filas = []
        for _, a in al.iterrows():
            fila = {"puesto": int(a.ranking), "municipio": a.municipio, "nivel": a.nivel,
                    "p": round(100 * float(a.p), 1), "ocurrio": int(a.hubo_mm),
                    "razones": [explicacion.texto_razon(r, mes, boletin.num) for r in a.razones],
                    "boletin": None}
            if a.nivel == "Rojo":
                texto, _ = boletin.generar(a, emergencias, len(al))
                c = boletin.cifras(a, emergencias, len(al))
                intrusas = boletin.verificar(texto, c)
                total_boletines += 1
                intrusas_total += len(intrusas)
                slug = re.sub(r"[^a-z0-9]+", "-", a.municipio.lower())
                (destino / "boletines" / f"{anio}-{mes:02d}_{slug}.md").write_text(texto)
                fila["boletin"] = md_a_html(texto)
                fila["verificado"] = not intrusas
            filas.append(fila)

        meses.append({
            "mes": mes, "nombre": nombre_mes, "mapa": f"mapas/{anio}-{mes:02d}.html",
            "rojos": int((al.nivel == "Rojo").sum()), "amarillos": int((al.nivel == "Amarillo").sum()),
            "verdes": int((al.nivel == "Verde").sum()), "eventos": int(al.hubo_mm.sum()),
            "detectados": int(al.loc[al.nivel != "Verde", "hubo_mm"].sum()),
            "temporada": bool((al["aporte_temporada"] > 0).mean() > 0.5),
            "filas": filas,
        })

    env = Environment(loader=FileSystemLoader(PLANTILLAS), autoescape=False)
    pagina = env.get_template("tablero.html").render(
        anio=anio, datos=json.dumps(meses, ensure_ascii=False), metricas=metricas_2025,
        total_boletines=total_boletines, intrusas_total=intrusas_total, umbral=umbrales)
    (destino / "tablero.html").write_text(pagina)
    return {"boletines": total_boletines, "cifras_intrusas": intrusas_total}
