from satmm import validacion


def test_pliegues_no_mezclan_anios():
    for p in validacion.pliegues():
        assert max(p.anios_train) == p.anio_valida - 1
        assert p.anio_valida not in p.anios_train
    assert [p.anio_valida for p in validacion.pliegues()] == [2021, 2022, 2023, 2024]
