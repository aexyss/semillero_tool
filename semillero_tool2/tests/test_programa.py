import pandas as pd

from semillero_tool.programa import canonizar_programa


def test_programa_sistemas_variants_canonize():
    df = pd.DataFrame({
        "PROGRAMA": ["inge.sistemas", "Ing.Sistemas", "Ing. Sistema", "Ingenieria en sistemas"]
    })

    out, rep = canonizar_programa(df)

    assert (out["PROGRAMA_CANON"] == "Ing. Sistemas").all()

    # opcional: si tu decisión metodológica es "cerrado", rep debería estar vacío
    # porque todo quedó canon
    # assert len(rep) == 0
