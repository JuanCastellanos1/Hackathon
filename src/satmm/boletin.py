"""Boletín al consejo municipal. Toda cifra sale de `cifras()` y se verifica al final."""
import re

import pandas as pd
from jinja2 import Environment

from satmm.explicacion import texto_razon

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

ACCIONES = {
    "Rojo": ["Convocar al consejo municipal de gestión del riesgo.",
             "Inspeccionar taludes, vías y viviendas con antecedentes de deslizamiento.",
             "Preparar rutas de evacuación y alojamientos temporales."],
    "Amarillo": ["Vigilar zonas con antecedentes y reforzar canales de reporte comunitario.",
                 "Revisar drenajes y cunetas en vías rurales."],
    "Verde": ["Mantener la preparación ordinaria."],
}

PLANTILLA = """\
# Boletín de alerta temprana: movimientos en masa

**Municipio:** {{ municipio }} · **Mes:** {{ mes_nombre }} de {{ anio }} · **Nivel:** {{ nivel }}

{{ municipio }} quedó en el puesto {{ ranking }} de {{ total_municipios }} municipios de Santander \
por riesgo estimado de movimiento en masa para {{ mes_nombre }}. \
Probabilidad estimada de al menos un movimiento en masa en el mes: {{ prob_pct | num }} %.

## {{ "Por qué está en alerta" if nivel != "Verde" else "Factores que más pesan" }}
{% if temporada_sube %}- {{ mes_nombre | capitalize }} es temporada de lluvias en Santander: el riesgo sube en todo el departamento.
{% endif %}{% for r in razones %}- {{ r | capitalize }}.
{% endfor %}
## Antecedentes (últimos {{ ventana_meses }} meses)
- Emergencias registradas: {{ emergencias_12m | num }}.
- Personas afectadas: {{ personas_12m | num }}.
- Viviendas afectadas: {{ viviendas_12m | num }}.

## Acciones sugeridas
{% for a in acciones %}- {{ a }}
{% endfor %}
## Límites
Estimación mensual con lluvia medida en la cabecera municipal: no anticipa aguaceros de pocas horas, \
el lugar exacto ni eventos no reportados.
"""


def num(x) -> str:
    """Formato colombiano: punto de miles, coma decimal, máximo 1 decimal."""
    x = round(float(x), 1)
    if x == int(x):
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


_env = Environment(trim_blocks=False, keep_trailing_newline=True)
_env.filters["num"] = num


def cifras(alerta: pd.Series, emergencias: pd.DataFrame, total_municipios: int) -> dict:
    """Única fuente de cifras del boletín. Las razones vienen de explicacion.agregar_razones."""
    anio, mes = int(alerta["anio"]), int(alerta["mes"])
    inicio = pd.Timestamp(anio, mes, 1) - pd.DateOffset(months=12)
    fin = pd.Timestamp(anio, mes, 1)
    hist = emergencias[(emergencias["codigo_dane"] == alerta["codigo_dane"])
                       & (emergencias["fecha"] >= inicio) & (emergencias["fecha"] < fin)]
    c = {
        "municipio": alerta["municipio"],
        "anio": anio,
        "mes_nombre": MESES[mes - 1],
        "nivel": alerta["nivel"],
        "ranking": int(alerta["ranking"]),
        "total_municipios": total_municipios,
        "ventana_meses": 12,
        "prob_pct": round(100 * float(alerta["p"]), 1),
        "emergencias_12m": len(hist),
        "personas_12m": int(hist["personas_afectadas"].sum()),
        "viviendas_12m": int(hist["viviendas_afectadas"].sum()),
        "acciones": ACCIONES[alerta["nivel"]],
        "temporada_sube": bool(alerta.get("aporte_temporada", 0) > 0),
        "razones": [texto_razon(r, mes, num) for r in alerta.get("razones", [])],
    }
    for i, r in enumerate(alerta.get("razones", [])):
        for j, v in enumerate(r["valores"]):
            c[f"razon_{i}_{j}"] = v
    return c


def redactar(c: dict, plantilla: str = PLANTILLA) -> str:
    return _env.from_string(plantilla).render(**c)


_NUMERO = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")


def numeros_en(texto: str) -> list[float]:
    return [float(n.replace(".", "").replace(",", ".")) for n in _NUMERO.findall(texto)]


def verificar(texto: str, c: dict, tol: float = 0.051) -> list[float]:
    """Devuelve las cifras del texto que NO salen de `c`. Lista vacía = boletín válido."""
    permitidas = [float(v) for v in c.values()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return [n for n in numeros_en(texto) if not any(abs(n - v) <= tol for v in permitidas)]


def generar(alerta: pd.Series, emergencias: pd.DataFrame, total_municipios: int,
            texto_alternativo: str | None = None) -> tuple[str, list[float]]:
    """Si llega un texto alternativo (p. ej. de un modelo de lenguaje) y no pasa el verificador,
    se descarta y se usa la plantilla. Devuelve (boletín, cifras intrusas del alternativo)."""
    c = cifras(alerta, emergencias, total_municipios)
    if texto_alternativo is not None:
        intrusas = verificar(texto_alternativo, c)
        if not intrusas:
            return texto_alternativo, []
    else:
        intrusas = []
    texto = redactar(c)
    assert not verificar(texto, c), "la plantilla produjo una cifra sin fuente"
    return texto, intrusas
