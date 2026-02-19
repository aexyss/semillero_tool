import pandas as pd

from semillero_tool.text_clean import asegurar_ids_como_texto


def test_ids_float_and_string_dot0_become_plain_int_string():
    df = pd.DataFrame({
        "ID": [1040039503.0, "1040039503.0", None],
    })

    out, rep = asegurar_ids_como_texto(df)

    assert out.loc[0, "ID"] == "1040039503"
    assert out.loc[1, "ID"] == "1040039503"
    assert pd.isna(out.loc[2, "ID"])

    # opcional: el reporte existe y menciona ID
    assert "COLUMNA" in rep.columns
    assert "ID" in set(rep["COLUMNA"])
