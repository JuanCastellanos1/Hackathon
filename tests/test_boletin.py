import pandas as pd

from satmm import boletin

ALERTA = pd.Series({"codigo_dane": 68001, "municipio": "Bucaramanga", "anio": 2025, "mes": 4,
                    "nivel": "Rojo", "ranking": 3, "lluvia_2m": 1234.56, "lluvia_t1": 412.0,
                    "mm_12m": 4, "mm_hist_mes": 0.3, "p": 0.237,
                    "aporte_temporada": 0.4,
                    "razones": [{"factor": "Relieve", "aporte": 0.3,
                                 "plantilla": "cabecera a {0} m de altitud", "valores": [1650]}]})
EMERG = pd.DataFrame({"codigo_dane": [68001, 68001, 68002],
                      "fecha": pd.to_datetime(["2024-06-10", "2025-02-01", "2025-01-01"]),
                      "personas_afectadas": [20, 35, 999], "viviendas_afectadas": [4, 6, 99]})


def test_plantilla_pasa_el_verificador():
    texto, intrusas = boletin.generar(ALERTA, EMERG, 87)
    assert intrusas == []
    assert "55" in texto and "23,7 %" in texto  # 20 + 35 personas; coma decimal


def test_cifra_inventada_es_rechazada():
    c = boletin.cifras(ALERTA, EMERG, 87)
    texto = boletin.redactar(c) + "\nSe estiman 350 viviendas en riesgo."
    assert boletin.verificar(texto, c) == [350.0]


def test_texto_alternativo_con_cifra_falsa_se_descarta():
    falso = "Bucaramanga tiene 87 % de probabilidad de deslizamiento."
    texto, intrusas = boletin.generar(ALERTA, EMERG, 87, texto_alternativo=falso.replace("87", "92"))
    assert intrusas == [92.0]
    assert texto.startswith("# Boletín")


def test_formato_numeros():
    assert boletin.numeros_en("1.234,5 mm, 12 casos y 3,5 %") == [1234.5, 12.0, 3.5]


def test_razones_shap_entran_al_boletin_y_se_verifican():
    texto, intrusas = boletin.generar(ALERTA, EMERG, 87)
    assert "Cabecera a 1.650 m de altitud." in texto
    assert "temporada de lluvias" in texto
    assert intrusas == []


def test_razon_contraintuitiva_se_descarta():
    import pandas as pd
    from satmm import explicacion as ex
    fila = pd.Series({"lluvia_anom": 0.7, "lluvia_2m": 300.0, "lluvia_t1": 100.0, "altitud_m": 1800,
                      "mm_12m": 0, "eventos_12m": 0, "mm_hist_mes": 0.0})
    sv = pd.Series({"Lluvia inusual": 0.5, "Historial reciente": 0.4, "Relieve": 0.2,
                    "Lluvia reciente": 0.1, "Temporada": 0.9})
    assert [r["factor"] for r in ex.razones(fila, sv)] == ["Relieve", "Lluvia reciente"]
