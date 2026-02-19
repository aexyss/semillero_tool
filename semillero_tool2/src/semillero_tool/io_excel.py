from __future__ import annotations

from pathlib import Path
import pandas as pd

from .errors import ExcelReadError, SchemaError


def leer_excel(input_path: Path, sheet: str | None) -> pd.DataFrame:
    try:
        if sheet:
            df = pd.read_excel(input_path, sheet_name=sheet, engine="openpyxl")
        else:
            xls = pd.ExcelFile(input_path, engine="openpyxl")
            if not xls.sheet_names:
                raise ExcelReadError("El archivo no contiene hojas.")
            df = pd.read_excel(input_path, sheet_name=xls.sheet_names[0], engine="openpyxl")
    except FileNotFoundError as e:
        raise ExcelReadError(f"No existe input: {input_path}") from e
    except ValueError as e:
        # Ej: hoja no existe
        raise ExcelReadError(f"Lectura inválida de Excel: {e}") from e
    except Exception as e:
        raise ExcelReadError(f"Error leyendo Excel ({input_path}): {e}") from e

    # Guardrail: pandas puede devolver dict si sheet_name es lista o None raro.
    if isinstance(df, dict):
        raise ExcelReadError(
            "pd.read_excel devolvió un dict (multiples hojas). "
            "Este tool exige una sola hoja. Usa --sheet para especificar."
        )

    if not isinstance(df, pd.DataFrame):
        raise ExcelReadError(f"Tipo inesperado al leer Excel: {type(df)!r}")

    if df.shape[0] == 0 and df.shape[1] == 0:
        raise SchemaError("Excel leído pero está vacío (0 filas, 0 columnas). ¿Hoja correcta? ¿Header correcto?")

    return df


def escribir_excel(output_path: Path, data: pd.DataFrame, reportes: dict[str, pd.DataFrame] | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    reportes = reportes or {}

    with pd.ExcelWriter(output_path, engine="openpyxl") as w:
        data.to_excel(w, sheet_name="DATA", index=False)
        for name, rep in reportes.items():
            sheet_name = name[:31]
            rep.to_excel(w, sheet_name=sheet_name, index=False)
