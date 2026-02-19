from __future__ import annotations

import pandas as pd
from .config import FU_COLS
from .errors import SchemaError


def cast_fu_numeric(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convierte columnas FU_COLS a numérico (errors='coerce').
    No crea columnas nuevas; si falta una columna, simplemente no la toca (aún).
    Devuelve (df, reporte_coercion).
    """
    df = df.copy()
    rows = []

    for c in FU_COLS:
        if c not in df.columns:
            rows.append({
                "COLUMNA": c,
                "EXISTE": False,
                "N_TOTAL": len(df),
                "NA_ANTES": None,
                "NA_DESPUES": None,
                "COERCIONES_A_NA": None,
            })
            continue

        before_na = int(df[c].isna().sum())
        coerced = pd.to_numeric(df[c], errors="coerce")
        after_na = int(coerced.isna().sum())

        new_nas = max(0, after_na - before_na)
        df[c] = coerced

        rows.append({
            "COLUMNA": c,
            "EXISTE": True,
            "N_TOTAL": len(df),
            "NA_ANTES": before_na,
            "NA_DESPUES": after_na,
            "COERCIONES_A_NA": int(new_nas),
        })

    rep = pd.DataFrame(rows, columns=[
        "COLUMNA", "EXISTE", "N_TOTAL", "NA_ANTES", "NA_DESPUES", "COERCIONES_A_NA"
    ])

    rep_exist = rep[rep["EXISTE"] == True].sort_values("COERCIONES_A_NA", ascending=False)  # noqa: E712
    rep_missing = rep[rep["EXISTE"] == False]  # noqa: E712
    rep = pd.concat([rep_exist, rep_missing], ignore_index=True)

    return df, rep


def validate_fu_schema(df: pd.DataFrame) -> None:
    """
    Exige que existan todas las columnas FU_COLS. Si falta alguna, explota.
    """
    missing = [c for c in FU_COLS if c not in df.columns]
    if missing:
        raise SchemaError(f"Faltan columnas F..U requeridas: {missing}")


def audit_fu_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Auditoría de missing SOLO para FU_COLS.
    Devuelve:
      - rep_na_cols: NA por columna FU
      - rep_resumen: filas completas vs incompletas (en FU)
    Requiere que validate_fu_schema haya pasado antes (para ser determinista).
    """
    na_rows = []
    for c in FU_COLS:
        s = df[c]
        na_rows.append({
            "COLUMNA": c,
            "N_TOTAL": len(df),
            "N_NA": int(s.isna().sum()),
            "PCT_NA": float(s.isna().mean()) if len(df) else 0.0,
        })

    rep_na_cols = (
        pd.DataFrame(na_rows, columns=["COLUMNA", "N_TOTAL", "N_NA", "PCT_NA"])
        .sort_values("N_NA", ascending=False)
    )

    mask_complete = ~df[FU_COLS].isna().any(axis=1)
    n_total = int(len(df))
    n_complete = int(mask_complete.sum())
    n_incomplete = int((~mask_complete).sum())

    rep_resumen = pd.DataFrame([{
        "N_TOTAL": n_total,
        "N_COMPLETAS_FU": n_complete,
        "N_INCOMPLETAS_FU": n_incomplete,
        "PCT_COMPLETAS_FU": (n_complete / n_total) if n_total else 0.0,
    }])

    return rep_na_cols, rep_resumen


def drop_fu_missing(
    df: pd.DataFrame,
    mode: str,
    min_non_missing: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Drop determinista sobre FU_COLS.

    mode:
      - none: no drop
      - all: dropea filas donde TODAS FU_COLS son NA
      - threshold: conserva filas con >= min_non_missing valores no-NA en FU_COLS

    Devuelve (kept, dropped).
    Requiere validate_fu_schema antes para ser determinista.
    """
    if mode == "none":
        return df.copy(), df.iloc[0:0].copy()

    if mode == "all":
        mask_drop = df[FU_COLS].isna().all(axis=1)

    elif mode == "threshold":
        if min_non_missing is None:
            raise ValueError("drop_fu_missing: mode='threshold' requiere min_non_missing")

        if min_non_missing < 0 or min_non_missing > len(FU_COLS):
            raise ValueError(
                f"min_non_missing_fu inválido: {min_non_missing} (rango 0..{len(FU_COLS)})"
            )

        non_missing = df[FU_COLS].notna().sum(axis=1)
        mask_drop = non_missing < min_non_missing

    else:
        raise ValueError(f"drop_fu_missing: mode inválido: {mode}")

    dropped = df.loc[mask_drop].copy()
    kept = df.loc[~mask_drop].copy()

    if len(dropped) > 0:
        dropped["_FU_NON_MISSING"] = dropped[FU_COLS].notna().sum(axis=1)

    return kept, dropped
