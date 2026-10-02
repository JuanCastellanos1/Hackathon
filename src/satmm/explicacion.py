"""Explicación por municipio con SHAP, agrupada en factores entendibles y traducida a frases."""
import numpy as np
import pandas as pd
import shap

# Variables técnicas -> factor que entiende un consejo municipal
GRUPOS = {
    "lluvia_t1": "Lluvia reciente", "lluvia_t2": "Lluvia reciente", "lluvia_2m": "Lluvia reciente",
    "lluvia_anom": "Lluvia inusual",
    "mm_12m": "Historial reciente", "eventos_12m": "Historial reciente",
    "mm_hist_mes": "Antecedentes en este mes",
    "mes_sin": "Temporada", "mes_cos": "Temporada", "mes_sin2": "Temporada", "mes_cos2": "Temporada",
    "altitud_m": "Relieve", "latitud": "Ubicación", "longitud": "Ubicación",
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def valores_shap(modelo, X: pd.DataFrame) -> pd.DataFrame:
    """Aporte de cada variable a la predicción (en log-odds), una fila por municipio-mes."""
    sv = shap.TreeExplainer(modelo).shap_values(X)
    return pd.DataFrame(sv, columns=X.columns, index=X.index)


def por_factor(sv: pd.DataFrame) -> pd.DataFrame:
    return sv.T.groupby(GRUPOS).sum().T


def _r(x, nd=1):
    return round(float(x), nd)


def _frase(factor: str, f: pd.Series) -> tuple[str, list[float]]:
    """Frase con los valores reales de la fila. Devuelve (frase con marcadores, valores)."""
    if factor == "Lluvia reciente":
        return "lluvia de los dos meses anteriores: {0} mm (mes anterior: {1} mm)", [_r(f.lluvia_2m), _r(f.lluvia_t1)]
    if factor == "Lluvia inusual":
        return "la lluvia del mes anterior fue {0} veces su promedio para esa época", [_r(f.lluvia_anom)]
    if factor == "Historial reciente":
        return "{0} movimientos en masa y {1} emergencias en total en los últimos {2} meses", [_r(f.mm_12m, 0), _r(f.eventos_12m, 0), 12]
    if factor == "Antecedentes en este mes":
        return "en años anteriores hubo movimiento en masa en {mes} el {0} % de las veces", [_r(100 * f.mm_hist_mes)]
    if factor == "Relieve":
        return "cabecera a {0} m de altitud", [_r(f.altitud_m, 0)]
    return "ubicación dentro del departamento", []


def _es_legible(factor: str, f: pd.Series) -> bool:
    """Descarta razones que un lector entendería al revés: p. ej. 'lluvia 0,7 veces su
    promedio' como motivo de alerta (pasa por la correlación entre variables de lluvia)."""
    if factor == "Lluvia inusual":
        return f.lluvia_anom > 1
    if factor == "Historial reciente":
        return f.mm_12m + f.eventos_12m > 0
    if factor == "Antecedentes en este mes":
        return f.mm_hist_mes > 0
    return True


def razones(fila: pd.Series, sv_factor: pd.Series, k: int = 3) -> list[dict]:
    """Los k factores propios del municipio que más empujan la probabilidad HACIA ARRIBA.
    La temporada se excluye: es igual para todos los municipios del mes (se reporta aparte)."""
    propios = sv_factor.drop(labels="Temporada", errors="ignore")
    candidatos = propios[propios > 0].sort_values(ascending=False)
    candidatos = candidatos[[_es_legible(f, fila) for f in candidatos.index]]
    out = []
    for factor, aporte in candidatos.head(k).items():
        plantilla, valores = _frase(factor, fila)
        out.append({"factor": factor, "aporte": float(aporte), "plantilla": plantilla, "valores": valores})
    return out


def texto_razon(r: dict, mes: int, fmt=lambda x: str(x)) -> str:
    return r["plantilla"].format(*[fmt(v) for v in r["valores"]], mes=MESES[mes - 1])


def agregar_razones(alertas: pd.DataFrame, modelo, features: list[str], k: int = 3) -> pd.DataFrame:
    sv = por_factor(valores_shap(modelo, alertas[features]))
    alertas = alertas.copy()
    alertas["razones"] = [razones(alertas.loc[i], sv.loc[i], k) for i in alertas.index]
    alertas["aporte_temporada"] = sv["Temporada"].to_numpy()
    return alertas


def chequeo_monotonia(modelo, X: pd.DataFrame, col: str = "lluvia_2m") -> float:
    """Correlación de Spearman entre el valor de `col` y su aporte SHAP. Debe ser positiva."""
    sv = valores_shap(modelo, X)
    return float(pd.Series(X[col].to_numpy()).corr(pd.Series(sv[col].to_numpy()), method="spearman"))
