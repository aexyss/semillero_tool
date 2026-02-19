from __future__ import annotations

import pandas as pd
from .config import COLUMNAS_ID


def limpiar_texto(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Strip seguro para columnas string/object SIN convertir NaN a "nan".
    Devuelve (df, reporte) con conteo de valores modificados por columna.
    """
    df = df.copy()
    rows = []

    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object:
            s = df[c]

            # Preserva NA
            s2 = s.where(s.isna(), s.astype(str))

            # Limpia representaciones basura típicas
            s2 = s2.replace({"nan": pd.NA, "None": pd.NA, "NaT": pd.NA})

            # Strip solo donde no es NA
            stripped = s2.where(s2.isna(), s2.astype(str).str.strip())

            # Conteo de cambios (aprox) en no-NA
            before = s2.where(s2.isna(), s2.astype(str))
            after = stripped.where(stripped.isna(), stripped.astype(str))
            n_changed = int(((before != after) & before.notna() & after.notna()).sum())

            df[c] = stripped

            if n_changed:
                rows.append({"COLUMNA": c, "N_STRIP_CAMBIOS": n_changed})

    rep = (
        pd.DataFrame(rows, columns=["COLUMNA", "N_STRIP_CAMBIOS"])
        .sort_values("N_STRIP_CAMBIOS", ascending=False)
        if rows
        else pd.DataFrame(columns=["COLUMNA", "N_STRIP_CAMBIOS"])
    )

    return df, rep


def asegurar_ids_como_texto(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fuerza columnas ID conocidas (o que empiecen por 'ID') a texto.
    Arregla el bug clásico: Excel/Pandas tienden a leer IDs como float y exportarlos como "123.0".

    Reglas:
    - NO inventa IDs.
    - Solo normaliza representación: strip + remover sufijo ".0" si existe.

    Devuelve (df, reporte) con columnas afectadas y conteo de fixes.
    """
    df = df.copy()
    rows = []

    for c in df.columns:
        if c in COLUMNAS_ID or c.startswith("ID"):
            s = df[c]

            # 1) convertir a string preservando NA
            s2 = s.where(s.isna(), s.astype(str).str.strip())

            # 2) fix quirúrgico: si termina en ".0", lo quitamos.
            #    Esto cubre el caso típico: 1040039503.0 -> 1040039503
            s3 = s2.where(s2.isna(), s2.astype(str).str.replace(r"\.0$", "", regex=True))

            # conteo de cambios por strip + fix .0 (solo donde no es NA)
            before = s.where(s.isna(), s.astype(str))
            after = s3.where(s3.isna(), s3.astype(str))
            n_changed = int(((before != after) & before.notna() & after.notna()).sum())

            # conteo específico del fix ".0" (para saber cuántos eran floats disfrazados)
            # Ojo: lo calculamos sobre s2->s3 (después del strip)
            n_dot0_fixed = int(
                ((s2.notna()) & (s2.astype(str).str.endswith(".0"))).sum()
            )

            df[c] = s3

            rows.append({
                "COLUMNA": c,
                "ACCION": "ID_AS_TEXT_STRIP_DOT0_FIX",
                "N_CAMBIOS_TOTAL": n_changed,
                "N_DOT0_FIX": n_dot0_fixed,
            })

    rep = (
        pd.DataFrame(rows, columns=["COLUMNA", "ACCION", "N_CAMBIOS_TOTAL", "N_DOT0_FIX"])
        if rows
        else pd.DataFrame(columns=["COLUMNA", "ACCION", "N_CAMBIOS_TOTAL", "N_DOT0_FIX"])
    )

    return df, rep
