from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from .io_excel import leer_excel, escribir_excel
from .columns import detect_duplicate_columns, normalizar_columnas_suffix, normalizar_columna
from .text_clean import limpiar_texto, asegurar_ids_como_texto
from .fu import cast_fu_numeric, validate_fu_schema, audit_fu_missing, drop_fu_missing
from .dates import normalizar_fechas_iso
from .programa import canonizar_programa
from .drop import aplicar_drop_missing
from .config import FU_COLS
from .errors import ConfigError, SchemaError


@dataclass(frozen=True)
class RunConfig:
    input_path: Path
    output_path: Path
    sheet: str | None

    # Strict schema
    strict_schema: bool

    # FU
    fu_validate: bool
    fu_drop_mode: str
    min_non_missing_fu: int | None

    # Programa
    canonizar_programa: bool
    reemplazar_programa: bool

    # Drop general (no-FU)
    drop_missing_mode: str
    critical_cols_csv: str | None


def _validate_cfg(cfg: RunConfig) -> None:
    """
    Validaciones internas del pipeline (no dependas del CLI).
    Esto te protege si mañana alguien llama run() desde Python directo.
    """
    if cfg.reemplazar_programa and not cfg.canonizar_programa:
        raise ConfigError("--reemplazar-programa requiere --canonizar-programa")

    if cfg.fu_drop_mode == "threshold" and cfg.min_non_missing_fu is None:
        raise ConfigError("--fu-drop-mode=threshold requiere --min-non-missing-fu N")

    if cfg.fu_drop_mode != "threshold" and cfg.min_non_missing_fu is not None:
        raise ConfigError("--min-non-missing-fu solo aplica cuando --fu-drop-mode=threshold")

    if cfg.drop_missing_mode not in {"none", "all", "any"}:
        raise ConfigError(f"drop_missing_mode inválido: {cfg.drop_missing_mode}")

    if cfg.fu_drop_mode not in {"none", "all", "threshold"}:
        raise ConfigError(f"fu_drop_mode inválido: {cfg.fu_drop_mode}")


def _resolve_critical_cols(df: pd.DataFrame, cfg: RunConfig) -> list[str]:
    """
    Resuelve columnas críticas para drop general.

    Regla: si se pidió drop general y faltan columnas críticas, eso NO es un warning,
    es un error de esquema (ambigüedad -> excepción explícita).
    """
    if cfg.critical_cols_csv:
        cols = [normalizar_columna(x) for x in cfg.critical_cols_csv.split(",")]
    else:
        cols = ["PROGRAMA"] + list(FU_COLS)

    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SchemaError(f"Drop general solicitado pero faltan columnas críticas: {missing}")

    return cols


def run(cfg: RunConfig) -> pd.DataFrame:
    _validate_cfg(cfg)

    df = leer_excel(cfg.input_path, cfg.sheet)

    # Fail-fast duplicados crudos (solo en modo estricto)
    if cfg.strict_schema:
        detect_duplicate_columns(df)

    # =========================================================
    # ORDEN DETERMINISTA (core):
    # 1) normaliza headers (y resuelve duplicados por suffix)
    # 2) limpia texto (strip + NA safe)
    # 3) asegura IDs como texto + fix .0 (si tu asegurar_ids ya lo hace)
    # =========================================================
    df, rep_dups = normalizar_columnas_suffix(df)
    df, rep_texto = limpiar_texto(df)
    df, rep_ids = asegurar_ids_como_texto(df)

    # FU cast (siempre; no exige schema)
    df, rep_fu_cast = cast_fu_numeric(df)

    # Programa (solo si flag)
    rep_no_recon = pd.DataFrame(columns=["PROGRAMA_ORIGINAL", "PROGRAMA_BASE", "FRECUENCIA"])
    if cfg.canonizar_programa:
        df, rep_no_recon = canonizar_programa(df)

    if cfg.reemplazar_programa:
        # coherencia hard: si se pidió reemplazo y no existe, es bug/estado inválido
        if "PROGRAMA_CANON" not in df.columns:
            raise SchemaError("Se pidió reemplazar PROGRAMA pero no existe PROGRAMA_CANON.")
        df["PROGRAMA"] = df["PROGRAMA_CANON"]

    # Reportes FU (pre/post). Estructura estable.
    rep_fu_na_pre = pd.DataFrame(columns=["COLUMNA", "N_TOTAL", "N_NA", "PCT_NA"])
    rep_fu_resumen_pre = pd.DataFrame(
        columns=["N_TOTAL", "N_COMPLETAS_FU", "N_INCOMPLETAS_FU", "PCT_COMPLETAS_FU"]
    )
    rep_fu_dropped = pd.DataFrame()
    rep_fu_na_post = pd.DataFrame(columns=["COLUMNA", "N_TOTAL", "N_NA", "PCT_NA"])
    rep_fu_resumen_post = pd.DataFrame(
        columns=["N_TOTAL", "N_COMPLETAS_FU", "N_INCOMPLETAS_FU", "PCT_COMPLETAS_FU"]
    )

    # Strict_schema fuerza validar/auditar FU
    do_fu = cfg.strict_schema or cfg.fu_validate or (cfg.fu_drop_mode != "none")
    if do_fu:
        validate_fu_schema(df)
        rep_fu_na_pre, rep_fu_resumen_pre = audit_fu_missing(df)

        if cfg.fu_drop_mode != "none":
            df, rep_fu_dropped = drop_fu_missing(df, cfg.fu_drop_mode, cfg.min_non_missing_fu)
            rep_fu_na_post, rep_fu_resumen_post = audit_fu_missing(df)

    # Drop general (solo si flag)
    rep_drop_general = pd.DataFrame()
    if cfg.drop_missing_mode != "none":
        critical_cols = _resolve_critical_cols(df, cfg)
        df, rep_drop_general = aplicar_drop_missing(df, cfg.drop_missing_mode, critical_cols)

    # Fechas (siempre, al final)
    df, rep_fechas = normalizar_fechas_iso(df, col="FECHA")

    escribir_excel(cfg.output_path, df, reportes={
        "REPORTE_DUPLICADOS": rep_dups,
        "REPORTE_TEXTO": rep_texto,
        "REPORTE_IDS": rep_ids,

        "REPORTE_PROGRAMA_NO_RECONOCIDOS": rep_no_recon,

        "REPORTE_FU_CAST": rep_fu_cast,
        "REPORTE_FU_NA_PRE": rep_fu_na_pre,
        "REPORTE_FU_RESUMEN_PRE": rep_fu_resumen_pre,
        "REPORTE_FU_DROPEADAS": rep_fu_dropped,
        "REPORTE_FU_NA_POST": rep_fu_na_post,
        "REPORTE_FU_RESUMEN_POST": rep_fu_resumen_post,

        "REPORTE_DROP_GENERAL": rep_drop_general,
        "REPORTE_FECHAS": rep_fechas,
    })
    return df
