"""Carga y validación de los archivos del reto. Todo se une por codigo_dane."""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"

ESQUEMAS = {
    "panel": ["codigo_dane", "municipio", "anio", "mes", "lluvia_mm",
              "lluvia_mm_mes_anterior", "eventos_mes", "hubo_mm", "eventos_12m", "altitud_m"],
    "emergencias": ["fecha", "municipio", "codigo_dane", "evento",
                    "personas_afectadas", "viviendas_afectadas", "vias_afectadas"],
    "municipios": ["codigo_dane", "municipio", "latitud", "longitud", "altitud_m"],
}


def validar_esquema(df: pd.DataFrame, nombre: str) -> None:
    faltan = set(ESQUEMAS[nombre]) - set(df.columns)
    if faltan:
        raise ValueError(f"{nombre}: faltan columnas {sorted(faltan)}")


def cargar_panel(ruta: Path = DATA / "panel_municipio_mes.csv") -> pd.DataFrame:
    df = pd.read_csv(ruta)
    validar_esquema(df, "panel")
    if df.duplicated(["codigo_dane", "anio", "mes"]).any():
        raise ValueError("panel: filas duplicadas por municipio-mes")
    return df.sort_values(["codigo_dane", "anio", "mes"]).reset_index(drop=True)


def cargar_emergencias(ruta: Path = DATA / "emergencias_santander.csv") -> pd.DataFrame:
    df = pd.read_csv(ruta, parse_dates=["fecha"])
    validar_esquema(df, "emergencias")
    df["municipio"] = df["municipio"].str.strip()
    df["evento"] = df["evento"].str.strip()
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    return df


def cargar_municipios(ruta: Path = DATA / "municipios_santander.csv") -> pd.DataFrame:
    df = pd.read_csv(ruta)
    validar_esquema(df, "municipios")
    return df


def diagnostico(panel: pd.DataFrame, emergencias: pd.DataFrame,
                municipios: pd.DataFrame) -> pd.DataFrame:
    """Tabla de problemas de calidad encontrados: lo que pide el punto 'limpien y digan'."""
    dane = set(municipios["codigo_dane"])
    nombres_por_codigo = emergencias.groupby("codigo_dane")["municipio"].nunique()
    filas = [
        ("Nulos en panel", int(panel.isna().sum().sum())),
        ("Nulos en emergencias", int(emergencias.isna().sum().sum())),
        ("Eventos duplicados", int(emergencias.duplicated().sum())),
        ("Códigos del panel sin cabecera", len(set(panel["codigo_dane"]) - dane)),
        ("Códigos de emergencias sin cabecera", len(set(emergencias["codigo_dane"]) - dane)),
        ("Códigos con más de un nombre", int((nombres_por_codigo > 1).sum())),
        ("Eventos con 0 personas afectadas", int((emergencias["personas_afectadas"] == 0).sum())),
        ("Meses en el panel", panel[["anio", "mes"]].drop_duplicates().shape[0]),
        ("Municipios en el panel", panel["codigo_dane"].nunique()),
    ]
    return pd.DataFrame(filas, columns=["chequeo", "valor"])
