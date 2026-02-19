from __future__ import annotations

import pandas as pd
from .errors import ConfigError


def aplicar_drop_missing(
    df: pd.DataFrame,
    mode: str,
    critical_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Drop controlado por missing en columnas críticas.

    mode:
      - none: no elimina nada
      - all : elimina filas donde TODAS las critical_cols están NA
      - any : elimina filas donde CUALQUIERA de las critical_cols está NA

    Devuelve:
      - df_filtrado
      - rep_dropeadas (subset de filas eliminadas)
    """
    df = df.copy()

    if mode == "none":
        return df, df.iloc[0:0].copy()

    if not critical_cols:
        # Si el usuario pidió drop pero no hay cols, es configuración inválida.
        raise ConfigError("Drop solicitado pero critical_cols está vacío.")

    # Nota: el pipeline ya valida que existan (SchemaError) antes de llamar aquí.
    if mode == "all":
        mask_drop = df[critical_cols].isna().all(axis=1)
    elif mode == "any":
        mask_drop = df[critical_cols].isna().any(axis=1)
    else:
        raise ConfigError(f"drop_missing_mode inválido: {mode}")

    dropped = df.loc[mask_drop].copy()
    kept = df.loc[~mask_drop].copy()

    return kept, dropped
