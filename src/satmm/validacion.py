"""Validación temporal por años, líneas base y métricas."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from satmm.variables import ANIO_INICIO, FEATURES, OBJETIVO

LLUVIAS = ["lluvia_t1", "lluvia_t2", "lluvia_2m", "lluvia_anom"]


@dataclass(frozen=True)
class Pliegue:
    anio_valida: int
    anios_train: tuple[int, ...]


def pliegues(desde: int = 2021, hasta: int = 2024) -> list[Pliegue]:
    """Ventana expansiva: entrena con todos los años anteriores, valida con un año completo."""
    return [Pliegue(a, tuple(range(ANIO_INICIO, a))) for a in range(desde, hasta + 1)]


def separar(df: pd.DataFrame, p: Pliegue) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = df[df["anio"].isin(p.anios_train)]
    valida = df[df["anio"] == p.anio_valida]
    assert train["anio"].max() < valida["anio"].min(), "el entrenamiento ve el futuro"
    return train, valida


# --- Líneas base (devuelven una "probabilidad" por fila) ---

def linea_base_anio_anterior(df: pd.DataFrame) -> np.ndarray:
    """A: repetir lo que pasó el mismo mes del año anterior."""
    return df["hubo_mm_hace_12m"].to_numpy(dtype=float)


def linea_base_climatologia(df: pd.DataFrame) -> np.ndarray:
    """B: tasa histórica del municipio en ese mes calendario (solo años previos)."""
    return df["mm_hist_mes"].to_numpy(dtype=float)


def logistica() -> object:
    pre = ColumnTransformer(
        [("log", FunctionTransformer(np.log1p), LLUVIAS)], remainder="passthrough")
    return make_pipeline(pre, StandardScaler(),
                         LogisticRegression(class_weight="balanced", max_iter=2000))


# --- Métricas ---

def precision_top_k(df: pd.DataFrame, p: np.ndarray, k: int = 10) -> float:
    """Precisión promedio si cada mes se atienden solo los k municipios con mayor p."""
    d = df[["anio", "mes", OBJETIVO]].assign(p=p)
    top = d.sort_values("p", ascending=False).groupby(["anio", "mes"]).head(k)
    return float(top[OBJETIVO].mean())


def metricas(df: pd.DataFrame, p: np.ndarray, umbral: float) -> dict:
    y = df[OBJETIVO].to_numpy()
    pred = (p >= umbral).astype(int)
    return {
        "pr_auc": average_precision_score(y, p),
        "recall": recall_score(y, pred, zero_division=0),
        "precision": precision_score(y, pred, zero_division=0),
        "brier": brier_score_loss(y, np.clip(p, 0, 1)),
        "top10_precision": precision_top_k(df, p),
        "alertas_mes": pred.sum() / df[["anio", "mes"]].drop_duplicates().shape[0],
        "tasa_real": y.mean(),
    }


def evaluar(df: pd.DataFrame, modelos: dict, features: list[str] = FEATURES) -> pd.DataFrame:
    """modelos: nombre -> (fabrica | None para línea base, función de p, umbral)."""
    filas = []
    for pl in pliegues():
        train, valida = separar(df, pl)
        for nombre, (fabrica, base, umbral) in modelos.items():
            if fabrica is None:
                p = base(valida)
            else:
                m = fabrica().fit(train[features], train[OBJETIVO])
                p = m.predict_proba(valida[features])[:, 1]
            filas.append({"modelo": nombre, "anio": pl.anio_valida, **metricas(valida, p, umbral)})
    return pd.DataFrame(filas)


def resumen(res: pd.DataFrame) -> pd.DataFrame:
    cols = ["pr_auc", "recall", "precision", "brier", "top10_precision", "alertas_mes"]
    r = res.groupby("modelo")[cols].agg(["mean", "min", "max"]).round(3)
    return r.sort_values(("pr_auc", "mean"), ascending=False)
