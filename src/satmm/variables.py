"""Variables del modelo. Regla: la fila del mes t solo usa información hasta t-1."""
import numpy as np
import pandas as pd

FEATURES = [
    "lluvia_t1", "lluvia_t2", "lluvia_2m", "lluvia_anom",
    "mm_12m", "mm_hist_mes", "eventos_12m",
    "altitud_m", "latitud", "longitud", "mes_sin", "mes_cos", "mes_sin2", "mes_cos2",
]
# Del mismo mes: no se conocen el día 1 (fuga de datos).
EXCLUIDAS = ["lluvia_mm", "eventos_mes", "hubo_mm"]
OBJETIVO = "hubo_mm"
ANIO_INICIO = 2016  # 2015 solo alimenta rezagos: sus ventanas de 12 meses están incompletas

assert not set(FEATURES) & set(EXCLUIDAS), "una variable con fuga se coló en FEATURES"


def _mm_por_mes(emergencias: pd.DataFrame) -> pd.DataFrame:
    mm = emergencias[emergencias["evento"] == "Movimiento en masa"]
    return mm.groupby(["codigo_dane", "anio", "mes"]).size().rename("mm_mes").reset_index()


def _media_anios_previos(df: pd.DataFrame, col: str) -> pd.Series:
    """Promedio de `col` del mismo municipio y mismo mes calendario en años anteriores."""
    return (df.groupby(["codigo_dane", "mes"])[col]
              .transform(lambda s: s.shift(1).expanding().mean()))


def construir(panel: pd.DataFrame, emergencias: pd.DataFrame,
              municipios: pd.DataFrame) -> pd.DataFrame:
    df = panel.sort_values(["codigo_dane", "anio", "mes"]).reset_index(drop=True)
    df = df.merge(municipios[["codigo_dane", "latitud", "longitud"]], on="codigo_dane", how="left")
    df = df.merge(_mm_por_mes(emergencias), on=["codigo_dane", "anio", "mes"], how="left")
    df["mm_mes"] = df["mm_mes"].fillna(0)

    g = df.groupby("codigo_dane")
    df["lluvia_t1"] = df["lluvia_mm_mes_anterior"]
    df["lluvia_t2"] = g["lluvia_mm"].shift(2)
    df["lluvia_2m"] = df["lluvia_t1"] + df["lluvia_t2"]
    df["mm_12m"] = g["mm_mes"].transform(lambda s: s.shift(1).rolling(12, min_periods=12).sum())
    df["hubo_mm_hace_12m"] = g[OBJETIVO].shift(12)  # línea base A

    df["mm_hist_mes"] = _media_anios_previos(df, OBJETIVO)  # línea base B
    clim = _media_anios_previos(df, "lluvia_t1")
    df["lluvia_anom"] = df["lluvia_t1"] / clim.replace(0, np.nan)

    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    # Segundo armónico: dos temporadas de lluvia al año (abr-may y oct-nov)
    df["mes_sin2"] = np.sin(4 * np.pi * df["mes"] / 12)
    df["mes_cos2"] = np.cos(4 * np.pi * df["mes"] / 12)

    df = df[df["anio"] >= ANIO_INICIO].reset_index(drop=True)
    return df.drop(columns=["mm_mes"])
