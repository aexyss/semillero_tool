# src/semillero_tool/config.py
# Config central del proyecto (declarativo).
#
# Aquí vive TODO lo que debería ser fácil de auditar/cambiar:
# - listas de columnas (FU, IDs)
# - universo canon de programas
# - reglas de expansión/matching de PROGRAMA
#
# La lógica (funciones) vive en sus módulos: programa.py, fu.py, etc.

VERSION = "0.3.0"

# Columnas que tratamos como identificadores (forzamos string/strip)
COLUMNAS_ID = {"ID", "NROIDENTI", "NROIDENTI_1", "NROIDENTI.1"}

# Bloque F..U (variables psicométricas core)
FU_COLS = [
    "V", "E", "A", "CON", "R", "N", "M", "O",
    "TOTAL_CAPACIDAD",
    "INTELIGENCIA_FLUIDA",
    "INTELIGENCIA_CRISTALIZADA",
    "MOTIVACION_SUPERFICIAL",
    "MOTIVACION_PROFUNDA",
    "MOTIVACION_DE_RENDIMIENTO",
    "P._TOTAL_PROCRASTINACION",
    "ANSIEDAD_A_LA_EVALUACION",
]

# ============================================================
# PROGRAMA: canonización determinista
# ------------------------------------------------------------
# Meta: que "inge.sistemas", "Ing.Sistemas", "Ingenieria en sistemas"
# terminen en la MISMA etiqueta estable ("Ing. Sistemas").
#
# Estrategia:
# 1) Normalización básica (sin tildes, separadores -> espacios)
# 2) Expansión de abreviaturas/variantes (inge -> ingenieria, sist -> sistemas)
# 3) Matching por tokens (robusto al orden y a la puntuación)
# 4) Regex fallback
# 5) Fuzzy (último recurso, umbral alto para no alucinar)
# ============================================================

# Universo canon: si PROGRAMA_CANON queda aquí, es “oficial”.
PROGRAMA_LABELS_CANON = [
    "Ing. Sistemas",
    "Ing. Electronica",
    "Ing. Industrial",
    "Ing. Ambiental",
    "Lic. Lenguas Extranjeras",
    "Lic. Lenguas",
    "Lic. Educación Infantil",
    "Lic. Educación Física",
    "Lic. Ciencias Naturales",
    "Psicología",
    "Derecho",
    "Comunicación Social",
    "Trabajo Social",
    "Teología Virtual",
    "Teología",
    "Gerontología Virtual",
    "Gerontología",
    "Administración de Empresas",
    "Contaduría Pública",
    "Contaduría",
    "Comercio Exterior",
    "Agronomía",
    "Zootecnia",
    "Enfermería",
    "Nutrición y Dietética",
]

# Abreviaturas / variantes reales -> expansión a tokens base.
# Se aplican como regex word-boundary antes de tokenizar.
PROGRAMA_ABREVIATURAS = [
    # --- ingeniería ---
    (r"\binge\b", "ingenieria"),
    (r"\bing\b", "ingenieria"),
    (r"\bingen\b", "ingenieria"),
    (r"\bing\.\b", "ingenieria"),
    (r"\bingenieria\b", "ingenieria"),
    (r"\bingeniería\b", "ingenieria"),

    # ruido semántico
    (r"\bdel\b", " "),
    (r"\bde\b", " "),
    (r"\ben\b", " "),

    # --- sistemas ---
    (r"\bsist\b", "sistemas"),
    (r"\bsistema\b", "sistemas"),
    (r"\bsistemas\b", "sistemas"),

    # --- electrónica ---
    (r"\belectronica\b", "electronica"),
    (r"\belectrónica\b", "electronica"),
    (r"\belectronico\b", "electronica"),
    (r"\belectrónico\b", "electronica"),

    # --- industrial / ambiental ---
    (r"\bindustrial\b", "industrial"),
    (r"\bambiental\b", "ambiental"),

    # --- licenciaturas ---
    (r"\blicenciatura\b", "lic"),
    (r"\blic\b", "lic"),
    (r"\blic\.\b", "lic"),
    (r"\bl\.\b", "lic"),

    (r"\beducación\b", "educacion"),
    (r"\beducacion\b", "educacion"),
    (r"\bedu\b", "educacion"),
    (r"\bed\b", "educacion"),

    (r"\bfísica\b", "fisica"),
    (r"\bfisica\b", "fisica"),
    (r"\bfis\b", "fisica"),

    (r"\bciencias\b", "ciencias"),
    (r"\bnaturales\b", "naturales"),
    (r"\blenguas\b", "lenguas"),
    (r"\bextranjeras\b", "extranjeras"),

    # --- administración ---
    (r"\badm\b", "administracion"),
    (r"\badm\.\b", "administracion"),
    (r"\badmin\b", "administracion"),
    (r"\badministracion\b", "administracion"),
    (r"\badministración\b", "administracion"),
    (r"\badministacion\b", "administracion"),
    (r"\badministación\b", "administracion"),
    (r"\bempresas\b", "empresas"),

    # --- contaduría ---
    (r"\bcontaduria\b", "contaduria"),
    (r"\bcontaduría\b", "contaduria"),
    (r"\bpublica\b", "publica"),
    (r"\bpública\b", "publica"),

    # --- comercio ---
    (r"\bcomercio\b", "comercio"),
    (r"\bexterior\b", "exterior"),

    # --- sociales ---
    (r"\bpsicología\b", "psicologia"),
    (r"\bpsicologia\b", "psicologia"),
    (r"\bderecho\b", "derecho"),
    (r"\bcomunicación\b", "comunicacion"),
    (r"\bcomunicacion\b", "comunicacion"),
    (r"\bsocial\b", "social"),
    (r"\btrabajo\b", "trabajo"),

    # --- teología / gerontología ---
    (r"\bteol\b", "teologia"),
    (r"\bteología\b", "teologia"),
    (r"\bteologia\b", "teologia"),
    (r"\bvirtual\b", "virtual"),

    (r"\bgerontología\b", "gerontologia"),
    (r"\bgerontologia\b", "gerontologia"),

    # --- agro / salud ---
    (r"\bagronomía\b", "agronomia"),
    (r"\bagronomia\b", "agronomia"),
    (r"\bzootecnia\b", "zootecnia"),

    (r"\benfermería\b", "enfermeria"),
    (r"\benfermeria\b", "enfermeria"),
    (r"\benfemería\b", "enfermeria"),
    (r"\benfemeria\b", "enfermeria"),
    (r"\benferemería\b", "enfermeria"),
    (r"\benferemeria\b", "enfermeria"),

    (r"\bnutrición\b", "nutricion"),
    (r"\bnutricion\b", "nutricion"),
    (r"\bdietética\b", "dietetica"),
    (r"\bdietetica\b", "dietetica"),
]