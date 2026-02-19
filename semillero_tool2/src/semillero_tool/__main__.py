import sys
from pathlib import Path

from .cli import parse_args
from .config import VERSION
from .errors import SemilleroToolError
from .pipeline import RunConfig, run


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = parse_args(argv)

    if getattr(args, "version", False):
        print(VERSION)
        return 0

    try:
        cfg = RunConfig(
            input_path=Path(args.input).expanduser(),
            output_path=Path(args.output).expanduser(),
            sheet=args.sheet,

            strict_schema=bool(getattr(args, "strict_schema", False)),

            fu_validate=bool(getattr(args, "fu_validate", False)),
            fu_drop_mode=str(getattr(args, "fu_drop_mode", "none")),
            min_non_missing_fu=getattr(args, "min_non_missing_fu", None),

            canonizar_programa=bool(getattr(args, "canonizar_programa", False)),
            reemplazar_programa=bool(getattr(args, "reemplazar_programa", False)),

            drop_missing_mode=str(getattr(args, "drop_missing_mode", "none")),
            critical_cols_csv=getattr(args, "critical_cols", None),
        )

        df = run(cfg)

    except SemilleroToolError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[FATAL] Error inesperado: {e}", file=sys.stderr)
        return 3

    print(f"[OK] Output escrito en: {cfg.output_path}")
    print(f"[OK] Filas: {len(df)} | Columnas: {len(df.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
