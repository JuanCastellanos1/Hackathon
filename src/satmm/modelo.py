"""Modelo principal, umbrales y semáforo."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from satmm.variables import FEATURES, OBJETIVO

NIVELES = ["Verde", "Amarillo", "Rojo"]


def xgboost() -> XGBClassifier:
    """Sin peso de clase a propósito: así la probabilidad queda calibrada (se publica en el
    boletín). El desbalance se maneja con el umbral, no con pesos. Árboles poco profundos:
    con 87 municipios, más profundidad sobreajusta (ver comparación en el cuaderno)."""
    return XGBClassifier(n_estimators=300, max_depth=2, learning_rate=0.05, subsample=0.8,
                         colsample_bytree=0.8, min_child_weight=5, eval_metric="logloss",
                         n_jobs=4, random_state=42)


@dataclass(frozen=True)
class Umbrales:
    """Amarillo: umbral fijo de alta sensibilidad (vigilancia).
    Rojo: los `rojos_mes` municipios más altos de cada mes que además superan el amarillo
    (capacidad del consejo departamental para movilizar recursos)."""
    amarillo: float
    rojos_mes: int = 10


def umbral_por_recall(y: np.ndarray, p: np.ndarray, recall_min: float) -> float:
    """Mayor umbral que aún detecta al menos `recall_min` de los positivos."""
    positivos = np.sort(p[y == 1])[::-1]
    k = int(np.ceil(recall_min * len(positivos))) - 1
    return float(positivos[max(k, 0)])


def elegir_umbrales(df: pd.DataFrame, p: np.ndarray, recall_amarillo: float = 0.70,
                    rojos_mes: int = 10) -> Umbrales:
    return Umbrales(umbral_por_recall(df[OBJETIVO].to_numpy(), p, recall_amarillo), rojos_mes)


def semaforo(df: pd.DataFrame, p: np.ndarray, u: Umbrales) -> np.ndarray:
    puesto = (pd.Series(p, index=df.index)
                .groupby([df["anio"], df["mes"]]).rank(ascending=False, method="first"))
    alerta = p >= u.amarillo
    rojo = alerta & (puesto.to_numpy() <= u.rojos_mes)
    return np.select([rojo, alerta], ["Rojo", "Amarillo"], "Verde")


def evaluar_semaforo(df: pd.DataFrame, p: np.ndarray, u: Umbrales) -> dict:
    """Cómo le va al semáforo frente a lo que pasó realmente."""
    nivel = semaforo(df, p, u)
    y = df[OBJETIVO].to_numpy() == 1
    meses = df[["anio", "mes"]].drop_duplicates().shape[0]
    rojo, alerta = nivel == "Rojo", nivel != "Verde"
    return {
        "recall_rojo_o_amarillo": alerta[y].mean(),
        "recall_rojo": rojo[y].mean(),
        "precision_rojo": y[rojo].mean() if rojo.any() else np.nan,
        "precision_amarillo": y[nivel == "Amarillo"].mean() if (nivel == "Amarillo").any() else np.nan,
        "rojos_por_mes": rojo.sum() / meses,
        "amarillos_por_mes": (nivel == "Amarillo").sum() / meses,
        "eventos_por_mes": y.sum() / meses,
    }


def alertas_mes(modelo, df: pd.DataFrame, anio: int, mes: int, u: Umbrales,
                municipios: pd.DataFrame) -> pd.DataFrame:
    """Tabla de alertas de un mes: una fila por municipio, ordenada por probabilidad."""
    filas = df[(df["anio"] == anio) & (df["mes"] == mes)].copy()
    filas["p"] = modelo.predict_proba(filas[FEATURES])[:, 1]
    filas["nivel"] = semaforo(filas, filas["p"].to_numpy(), u)
    filas["ranking"] = filas["p"].rank(ascending=False, method="first").astype(int)
    filas = filas.drop(columns=["latitud", "longitud"]).merge(
        municipios[["codigo_dane", "latitud", "longitud"]], on="codigo_dane")
    return filas.sort_values("ranking").reset_index(drop=True)
