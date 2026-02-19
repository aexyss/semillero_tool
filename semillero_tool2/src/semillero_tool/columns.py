from __future__ import annotations

import re
from dataclasses import dataclass
import pandas as pd
from unidecode import unidecode

from .errors import SchemaError


def normalizar_columna(nombre: str) -> str:
    s = str(nombre).strip().replace("\n", " ")
    s = unidecode(s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "_").upper()
    return s


@dataclass(frozen=True)
class DuplicateEvent:
    original_name: str
    normalized_name: str
    assigned_name: str
    duplicate_index: int  # 0 si fue la primera, 1+ si fue duplicada


def detect_duplicate_columns(df: pd.DataFrame) -> None:
    """
    Falla si el Excel trae columnas duplicadas EXACTAS (antes de normalizar).
    """
    dups = df.columns[df.columns.duplicated()].tolist()
    if dups:
        raise SchemaError(f"Columnas duplicadas detectadas en input: {dups}")


def normalizar_columnas_suffix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normaliza columnas y resuelve duplicados por sufijo __{n} (legacy).
    Devuelve (df_normalizado, reporte_duplicados).
    """
    df = df.copy()
    original_cols = list(df.columns)

    normalized = [normalizar_columna(c) for c in original_cols]

    vistos: dict[str, int] = {}
    nuevas: list[str] = []
    events: list[DuplicateEvent] = []

    for orig, norm in zip(original_cols, normalized):
        if norm not in vistos:
            vistos[norm] = 0
            assigned = norm
            nuevas.append(assigned)
            events.append(DuplicateEvent(orig, norm, assigned, 0))
        else:
            vistos[norm] += 1
            assigned = f"{norm}__{vistos[norm]}"
            nuevas.append(assigned)
            events.append(DuplicateEvent(orig, norm, assigned, vistos[norm]))

    df.columns = nuevas

    dup_rows = [
        {
            "ORIGINAL": e.original_name,
            "NORMALIZADA": e.normalized_name,
            "ASIGNADA": e.assigned_name,
            "N_DUP": e.duplicate_index,
        }
        for e in events
        if e.duplicate_index >= 1
    ]
    rep = pd.DataFrame(dup_rows, columns=["ORIGINAL", "NORMALIZADA", "ASIGNADA", "N_DUP"])

    return df, rep
