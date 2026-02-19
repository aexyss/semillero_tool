import argparse
from .config import VERSION


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="semillero_tool",
        description="Limpieza + normalización de datos psicométricos (Semillero).",
    )

    p.add_argument("-i", "--input", required=False,
                   help="Ruta del archivo Excel de entrada (.xlsx)")
    p.add_argument("-o", "--output", required=False,
                   help="Ruta del archivo Excel de salida (.xlsx)")
    p.add_argument("--sheet", default=None,
                   help="Nombre de hoja a leer (default: primera hoja)")
    p.add_argument("--version", action="store_true",
                   help="Imprime versión y sale")

    # Strict mode
    p.add_argument("--strict-schema", action="store_true",
                   help="Activa validación estricta del esquema (fail-fast).")

    # -----------------------------
    # FU block
    # -----------------------------

    p.add_argument("--fu-validate", action="store_true",
                   help="Valida que existan todas las columnas F..U y genera auditoría.")

    p.add_argument("--fu-drop-mode",
                   default="none",
                   choices=["none", "all", "threshold"],
                   help="Drop basado en missing de columnas F..U: none | all | threshold")

    p.add_argument("--min-non-missing-fu",
                   type=int,
                   default=None,
                   help="Para fu-drop-mode=threshold: mínimo de valores NO-NA requeridos en F..U para conservar la fila.")

    # -----------------------------
    # Programa
    # -----------------------------

    p.add_argument("--canonizar-programa", action="store_true",
                   help="Genera PROGRAMA_BASE y PROGRAMA_CANON.")

    p.add_argument("--reemplazar-programa", action="store_true",
                   help="Reemplaza PROGRAMA por PROGRAMA_CANON (requiere --canonizar-programa).")

    # -----------------------------
    # Drop general (no-FU)
    # -----------------------------

    p.add_argument("--drop-missing-mode",
                   default="none",
                   choices=["none", "all", "any"],
                   help="Drop por missing en columnas críticas: none | all | any")

    p.add_argument("--critical-cols",
                   default=None,
                   help="Lista CSV de columnas críticas para drop-missing.")

    return p


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = build_argparser()
    args = ap.parse_args(argv)

    # Version corta circuito
    if args.version:
        return args

    # I/O obligatorio
    if not args.input or not args.output:
        ap.error("Se requieren -i/--input y -o/--output (o usa --version).")

    # -----------------------------
    # Validaciones FU deterministas
    # -----------------------------

    if args.fu_drop_mode == "threshold" and args.min_non_missing_fu is None:
        ap.error("--fu-drop-mode=threshold requiere --min-non-missing-fu N")

    if args.fu_drop_mode != "threshold" and args.min_non_missing_fu is not None:
        ap.error("--min-non-missing-fu solo aplica cuando --fu-drop-mode=threshold")

    if args.min_non_missing_fu is not None and args.min_non_missing_fu < 0:
        ap.error("--min-non-missing-fu debe ser >= 0")

    # -----------------------------
    # Validaciones Programa
    # -----------------------------

    if args.reemplazar_programa and not args.canonizar_programa:
        ap.error("--reemplazar-programa requiere --canonizar-programa")

    # -----------------------------
    # Validaciones coherencia global
    # -----------------------------

    if args.drop_missing_mode != "none" and args.fu_drop_mode != "none":
        # No es ilegal, pero es importante que el usuario entienda
        # que el orden es: FU drop -> drop general.
        # No lo bloqueamos, pero podrías endurecerlo si quieres.
        pass

    return args
