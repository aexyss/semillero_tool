from __future__ import annotations

import re
from difflib import SequenceMatcher

import pandas as pd
from unidecode import unidecode


# ============================================================
# PROGRAMA CANON ENGINE (determinista, no magia)
# ------------------------------------------------------------
# Objetivo:
# - Convertir entradas humanas sucias ("inge.sistemas", "Ing Sist", "ingeneria sist.")
#   en labels estables (p.ej. "Ing. Sistemas") para análisis reproducible.
#
# Decisión metodológica:
# - MODO CERRADO (recomendado): si NO asigna a un label canon -> NA.
#   Nada de "quedó parecido", nada de "déjelo como estaba".
#   Lo no canónico se reporta y se corrige en reglas (o en la fuente).
#
# Principios:
# - Normalización fuerte (bajar ruido).
# - Expansión de abreviaturas (subir semántica).
# - Tokens primero (robusto al orden).
# - Regex como respaldo (cobertura).
# - Fuzzy al final (umbral alto; solo typos plausibles).
#
# Resultado:
# - PROGRAMA_BASE: string normalizada (debug / auditoría)
# - PROGRAMA_CANON: label estable o NA (modo cerrado)
# ============================================================


# Universo canon (lo que aceptamos como categorías finales estables)
LABELS_CANON = [
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


# ------------------------------------------------------------
# (1) Normalización fuerte
# ------------------------------------------------------------
def clean_label(x) -> object:
    """
    Limpieza final para labels (incluye NBSP y whitespace raro).
    Evita casos tipo "Administración de empresas" (NBSP) que parecen iguales pero no lo son.
    """
    if pd.isna(x):
        return pd.NA
    s = str(x)
    s = s.replace("\u00a0", " ")          # NBSP (espacio fantasma típico de Excel)
    s = re.sub(r"\s+", " ", s).strip()    # colapsa espacios
    return s if s else pd.NA


def forma_base(x) -> str:
    """
    Convierte una entrada humana en una base comparable:
    - lower
    - sin tildes
    - separadores (. / - _) -> espacios
    - whitespace colapsado
    - typos comunes corregidos

    Nota: esto NO canoniza; solo prepara para matching.
    """
    if pd.isna(x):
        return ""

    s = str(x)
    s = s.replace("\u00a0", " ")          # NBSP
    s = s.strip()
    s = unidecode(s).lower()

    # Typos comunes (si aparecen más, se agregan aquí)
    s = s.replace("ingeneria", "ingenieria")
    s = s.replace("ingeniera", "ingenieria")   # tu caso real
    s = s.replace("administacion", "administracion")
    s = s.replace("administación", "administracion")

    # Separadores típicos -> espacio (incluye punto, guión, slash, underscore)
    s = re.sub(r"[._/\\\-]+", " ", s)

    # Basura no alfanumérica -> espacio
    s = re.sub(r"[^a-z0-9\s]+", " ", s)

    # whitespace final
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ------------------------------------------------------------
# (2) Expansión determinista de abreviaturas
# ------------------------------------------------------------
# Clave para “inge.sistemas”, “ing sist”, “ing. sistema”, etc.
# No inventa programas: solo expande tokens frecuentes a su forma estable.
ABREVIATURAS = [
    # Ingeniería (autocontenido: no dependas de que el input venga "bonito")
    (r"\binge\b", "ingenieria"),
    (r"\bing\b", "ingenieria"),
    (r"\bing\.\b", "ingenieria"),
    (r"\bingen\b", "ingenieria"),
    (r"\bingenieria\b", "ingenieria"),

    # Sistemas (captura singular “sistema” -> “sistemas”)
    (r"\bsist\b", "sistemas"),
    (r"\bsistema\b", "sistemas"),

    # Licenciatura / educación
    (r"\blic\b", "lic"),
    (r"\bedu\b", "educacion"),
    (r"\bed\b", "educacion"),
    (r"\bfis\b", "fisica"),

    # Administración
    (r"\badmon\b", "administracion"),
    (r"\badm\b", "administracion"),
    (r"\badmin\b", "administracion"),

    # Teología
    (r"\bteol\b", "teologia"),

    # Pública
    (r"\bpub\b", "publica"),
    (r"\bpúb\b", "publica"),
]


def expandir_abreviaturas(s: str) -> str:
    """
    Convierte abreviaturas frecuentes en tokens estables.
    Esto hace que el matching por tokens sea viable incluso con inputs "tipo WhatsApp".
    """
    if not s:
        return ""
    out = s
    for patron, repl in ABREVIATURAS:
        out = re.sub(patron, repl, out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


# ------------------------------------------------------------
# (3) Tokenización + reglas por tokens (lo robusto)
# ------------------------------------------------------------
def tokenize(s: str) -> set[str]:
    if not s:
        return set()
    return set(s.split(" "))


# Reglas canónicas por tokens:
# Si estos tokens están presentes -> asignar etiqueta.
TOKEN_RULES = [
    # Ingenierías (cubre: ingenieria de/en sistemas, ing sistema, etc.)
    ({"ingenieria", "sistemas"}, "Ing. Sistemas"),
    ({"ingenieria", "electronica"}, "Ing. Electronica"),
    ({"ingenieria", "industrial"}, "Ing. Industrial"),
    ({"ingenieria", "ambiental"}, "Ing. Ambiental"),

    # Licenciaturas
    ({"lic", "lenguas", "extranjeras"}, "Lic. Lenguas Extranjeras"),
    ({"lenguas", "extranjeras"}, "Lic. Lenguas Extranjeras"),
    ({"lic", "lenguas"}, "Lic. Lenguas"),
    ({"lic", "educacion", "infantil"}, "Lic. Educación Infantil"),
    ({"lic", "educacion", "fisica"}, "Lic. Educación Física"),
    ({"lic", "ciencias", "naturales"}, "Lic. Ciencias Naturales"),
    ({"ciencias", "naturales"}, "Lic. Ciencias Naturales"),

    # Sociales / humanas
    ({"psicologia"}, "Psicología"),
    ({"derecho"}, "Derecho"),
    ({"comunicacion", "social"}, "Comunicación Social"),
    ({"trabajo", "social"}, "Trabajo Social"),
    ({"teologia", "virtual"}, "Teología Virtual"),
    ({"teologia"}, "Teología"),
    ({"gerontologia", "virtual"}, "Gerontología Virtual"),
    ({"gerontologia"}, "Gerontología"),

    # Administración/economía
    ({"administracion", "empresas"}, "Administración de Empresas"),

    # DECISIÓN: “administracion” sola -> Administración de Empresas
    # (si te arrepientes, se borra esta regla y se obliga a que venga “empresas”)
    ({"administracion"}, "Administración de Empresas"),

    ({"contaduria", "publica"}, "Contaduría Pública"),
    ({"contaduria"}, "Contaduría"),
    ({"comercio", "exterior"}, "Comercio Exterior"),

    # Agro / salud
    ({"agronomia"}, "Agronomía"),
    ({"zootecnia"}, "Zootecnia"),
    ({"enfermeria"}, "Enfermería"),
    ({"nutricion", "dietetica"}, "Nutrición y Dietética"),
]


# ------------------------------------------------------------
# (4) Regex de respaldo (por cobertura)
# ------------------------------------------------------------
# Nota: acá también cubrimos "ingenieria de sistemas" / "ingenieria en sistemas"
# porque a veces la gente escribe frases largas y los tokens siguen siendo válidos,
# pero regex ayuda si aparecen formatos raros.
PATRONES_PROGRAMA = [
    # Ingenierías: ing/inge/ingenieria + (de|en)? + sistemas (sing/plural)
    (r"\b(ing|inge|ingenieria|ingeniería)\b(?:\s+(de|en))?\s+\b(sist|sistemas|sistema)\b", "Ing. Sistemas"),
    (r"\b(ing|inge|ingenieria|ingeniería)\b.*\b(electronica|electrónica)\b", "Ing. Electronica"),
    (r"\b(ing|inge|ingenieria|ingeniería)\b.*\b(industrial)\b", "Ing. Industrial"),
    (r"\b(ing|inge|ingenieria|ingeniería)\b.*\b(ambiental)\b", "Ing. Ambiental"),

    # Licenciaturas
    (r"\b(lic|licenciatura|l)\b.*\b(lenguas)\b.*\b(extranjeras)\b", "Lic. Lenguas Extranjeras"),
    (r"\b(lenguas)\b.*\b(extranjeras)\b", "Lic. Lenguas Extranjeras"),
    (r"\b(lic|licenciatura|l)\b.*\b(lenguas)\b", "Lic. Lenguas"),
    (r"\b(lic|licenciatura|l)\b.*\b(educacion|educación|edu)\b.*\b(infantil)\b", "Lic. Educación Infantil"),
    (r"\b(lic|licenciatura|l)\b.*\b(educacion|educación|edu)\b.*\b(fisica|física|fis)\b", "Lic. Educación Física"),
    (r"\b(lic|licenciatura|l)\b.*\b(ciencias)\b.*\b(naturales)\b", "Lic. Ciencias Naturales"),

    # Sociales / humanas
    (r"\b(psicologia|psicología)\b", "Psicología"),
    (r"\b(derecho)\b", "Derecho"),
    (r"\b(comunicacion|comunicación)\b.*\b(social)\b", "Comunicación Social"),
    (r"\b(trabajo)\b.*\b(social)\b", "Trabajo Social"),
    (r"\b(teologia|teología|teol)\b.*\b(virtual)\b", "Teología Virtual"),
    (r"\b(teologia|teología|teol)\b", "Teología"),
    (r"\b(gerontologia|gerontología)\b.*\b(virtual)\b", "Gerontología Virtual"),
    (r"\b(gerontologia|gerontología)\b", "Gerontología"),

    # Administración/economía
    (r"\b(adm|admin|administracion|administración)\b.*\b(empresas)\b", "Administración de Empresas"),
    (r"\b(adm|admin|administracion|administración)\b$", "Administración de Empresas"),  # administración sola
    (r"\b(contaduria|contaduría)\b.*\b(publica|pública)\b", "Contaduría Pública"),
    (r"\b(contaduria|contaduría)\b", "Contaduría"),
    (r"\b(comercio)\b.*\b(exterior)\b", "Comercio Exterior"),

    # Agro / salud
    (r"\b(agronomia|agronomía)\b", "Agronomía"),
    (r"\b(zootecnia)\b", "Zootecnia"),
    (r"\b(enfermeria|enfermería|enfemeria|enferemeria|enferemería)\b", "Enfermería"),
    (r"\b(nutricion|nutrición)\b.*\b(dietetica|dietética)\b", "Nutrición y Dietética"),
]


# ------------------------------------------------------------
# (5) Fuzzy (último recurso, umbral alto)
# ------------------------------------------------------------
def fuzzy_best_label(base: str, min_ratio: float = 0.90) -> str | None:
    """
    Último recurso: fuzzy contra labels canon ya normalizados.
    Umbral alto para NO inventar matches con ruido.
    """
    best = None
    best_r = 0.0
    for lab in LABELS_CANON:
        r = SequenceMatcher(None, base, forma_base(lab)).ratio()
        if r > best_r:
            best_r = r
            best = lab
    return best if best is not None and best_r >= min_ratio else None


# ------------------------------------------------------------
# API pública: canonizar_programa()
# ------------------------------------------------------------
def canonizar_programa(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Canoniza la columna PROGRAMA.

    Output:
      - PROGRAMA_BASE: forma base normalizada (debug)
      - PROGRAMA_CANON: label estable o NA (modo cerrado)

    Reporte:
      - PROGRAMA_ORIGINAL, PROGRAMA_BASE, FRECUENCIA para los no reconocidos
        (todo lo que NO quedó dentro de LABELS_CANON).
    """
    df = df.copy()

    if "PROGRAMA" not in df.columns:
        df["PROGRAMA_BASE"] = pd.NA
        df["PROGRAMA_CANON"] = pd.NA
        rep = pd.DataFrame(columns=["PROGRAMA_ORIGINAL", "PROGRAMA_BASE", "FRECUENCIA"])
        return df, rep

    prog_original = df["PROGRAMA"].copy()

    # 1) Base limpia
    base = prog_original.map(forma_base)

    # 2) Expansión de abreviaturas
    base_exp = base.map(expandir_abreviaturas)

    canon: list[object] = []
    for s in base_exp:
        if not s:
            canon.append(pd.NA)
            continue

        asignado = None

        # A) Tokens primero (robusto al orden)
        toks = tokenize(s)
        for req, etiqueta in TOKEN_RULES:
            if req.issubset(toks):
                asignado = etiqueta
                break

        # B) Regex (backup por cobertura)
        if not asignado:
            for patron, etiqueta in PATRONES_PROGRAMA:
                if re.search(patron, s):
                    asignado = etiqueta
                    break

        # C) Fuzzy (último recurso)
        if not asignado:
            fb = fuzzy_best_label(s, min_ratio=0.90)
            if fb:
                asignado = fb

        # MODO CERRADO: si no asigna a canon -> NA (se reporta)
        canon.append(asignado if asignado else pd.NA)

    df["PROGRAMA_BASE"] = base_exp
    df["PROGRAMA_CANON"] = pd.Series(canon, index=df.index).map(clean_label)

    # Reporte: lo que NO quedó en el universo canon (incluye NA? no, NA se queda fuera)
    canon_set = set(LABELS_CANON)
    mask_no = df["PROGRAMA_CANON"].isna() | (~df["PROGRAMA_CANON"].isin(canon_set))

    rep = (
        df.loc[mask_no, ["PROGRAMA", "PROGRAMA_BASE"]]
        .value_counts(dropna=False)
        .reset_index(name="FRECUENCIA")
        .rename(columns={"PROGRAMA": "PROGRAMA_ORIGINAL"})
        .sort_values("FRECUENCIA", ascending=False)
    )

    return df, rep
