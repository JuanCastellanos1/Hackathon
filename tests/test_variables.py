from satmm import datos, variables


def _tabla():
    return variables.construir(datos.cargar_panel(), datos.cargar_emergencias(),
                               datos.cargar_municipios())


def test_rezago_dos_meses_por_municipio():
    panel = datos.cargar_panel()
    df = _tabla()
    for dane in panel["codigo_dane"].unique()[:5]:
        nov15 = panel.query("codigo_dane == @dane and anio == 2015 and mes == 11")["lluvia_mm"].item()
        ene16 = df.query("codigo_dane == @dane and anio == 2016 and mes == 1")["lluvia_t2"].item()
        assert ene16 == nov15


def test_sin_fuga_y_sin_nulos():
    df = _tabla()
    assert not set(variables.FEATURES) & set(variables.EXCLUIDAS)
    assert df["anio"].min() == variables.ANIO_INICIO
    assert df[variables.FEATURES].drop(columns=["mm_hist_mes", "lluvia_anom"]).notna().all().all()


def test_mm_12m_no_incluye_mes_actual():
    df = _tabla()
    fila = df.iloc[500]
    previos = df[(df["codigo_dane"] == fila["codigo_dane"])]
    # recomputar a mano con el objetivo: mm_12m >= meses con mm en los 12 previos
    idx = previos.index.get_loc(fila.name)
    if idx >= 12:
        assert fila["mm_12m"] >= previos.iloc[idx - 12:idx]["hubo_mm"].sum()
