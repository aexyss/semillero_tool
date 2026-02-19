from __future__ import annotations

import pandas as pd


def normalizar_fechas_iso(df: pd.DataFrame, col: str = "FECHA") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fuerza FECHA a string ISO 'YYYY-MM-DD' (Excel-friendly).
    - No deja datetime en el df final (evita '00:00:00').
    - Devuelve (df, reporte) con conteos de parseo.
    """
    df = df.copy()

    if col not in df.columns:
        rep = pd.DataFrame([{
            "COLUMNA": col,
            "EXISTE": False,
            "N_TOTAL": len(df),
            "N_PARSE_OK": 0,
            "N_PARSE_NA": 0,
        }])
        return df, rep

    before_na = df[col].isna().sum()

    parsed = pd.to_datetime(df[col], errors="coerce")

    # ISO string
    out = parsed.dt.strftime("%Y-%m-%d")
    out = out.replace({"NaT": pd.NA, "nan": pd.NA, "None": pd.NA})
    df[col] = out

    after_na = df[col].isna().sum()

    rep = pd.DataFrame([{
        "COLUMNA": col,
        "EXISTE": True,
        "N_TOTAL": len(df),
        "N_PARSE_OK": int(len(df) - after_na),
        "N_PARSE_NA": int(after_na),
        "NA_ANTES": int(before_na),
        "NA_DESPUES": int(after_na),
    }])

    return df, rep
