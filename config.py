"""
Decisiones centrales del pipeline — Water Governance / Mining SES paper.

Cambiar aquí, no en cada script. Todos los scripts de /scripts/ importan de este
archivo en vez de hardcodear rutas, listas de ítems o mapeos de nombres.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
# Los datos no se distribuyen con este repositorio (ver README.md, "Data availability").
DATA_RAW = ROOT / "data" / "raw" / "Datos Mineria objetivo 2.xlsx"
DATA_PROCESSED = ROOT / "data" / "processed"
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGURES = ROOT / "outputs" / "figures"

for _p in (DATA_PROCESSED, OUT_TABLES, OUT_FIGURES):
    _p.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Bloques de ítems originales del cuestionario (34 ítems, ver DATA_DICTIONARY.md)
# ---------------------------------------------------------------------------
GOB_ITEMS = [f"GOB_{i}" for i in range(1, 15)]
SOS_ITEMS = [f"SOS_{i}" for i in range(1, 6)]
DES_ITEMS = [f"DES_{i}" for i in range(1, 16)]

# ---------------------------------------------------------------------------
# Ítems excluidos del modelo de medición (Fase 0-1 y limpieza final) y por qué.
# Ver docs/Resumen_Analisis_Gobernanza_Agua.md secciones 2 y "Cierre de limpieza
# de ítems" para el detalle y evidencia de cada decisión.
# ---------------------------------------------------------------------------
EXCLUDED_ITEMS = {
    "SOS_1": "r item-total ~0 (.013); 88% de respuestas en el máximo (efecto techo)",
    "SOS_2": "no correlaciona con el resto del bloque de sostenibilidad (r~.13); "
             "decisión del equipo de descartarlo",
    "DES_8": "varianza casi nula (SD=.14, 98.7% responde el máximo)",
    "DES_15": "r item-total negativo (-.028); ítem 'global/puente', no reflectivo del resto",
    "GOB_3": "81.2% de respuestas en el punto medio (3) — probable 'no conozco este "
             "programa de la empresa' usado como respuesta por defecto",
    "GOB_4": "70.3% de respuestas en el punto medio (3) — mismo patrón que GOB_3, "
             "otro programa específico de la empresa",
}

# ---------------------------------------------------------------------------
# Estructura de medición reespecificada (EFA Fase 1, confirmada en CFA/CB-SEM).
# Nombres en español (usados en el pipeline/código) -> nombres en inglés
# (usados en el manuscrito, ver Tabla 3 del paper).
# ---------------------------------------------------------------------------
MEASUREMENT_MODEL = {
    "GOB_empresa": {
        "items": ["GOB_1", "GOB_6", "GOB_11", "GOB_12", "GOB_13"],
        "label_en": "Company Trust",
    },
    "GOB_confianza": {
        "items": ["GOB_9", "GOB_10"],
        "label_en": "Community Trust",
    },
    "GOB_externo": {
        "items": ["GOB_2", "GOB_7", "GOB_8"],
        "label_en": "External Institution Trust",
    },
    "SOS_ambiental": {
        "items": ["SOS_3", "SOS_4", "SOS_5"],
        "label_en": "Environmental Sustainability",
    },
    "DES_relacional": {
        "items": ["DES_5", "DES_6", "DES_7"],
        "label_en": "Relational Performance",
    },
    "DES_regulacion": {
        "items": ["DES_12", "DES_13", "DES_14"],
        "label_en": "Ecological Regulation",
    },
    "DES_estructural": {
        "items": ["DES_1", "DES_3"],
        "label_en": "Structural Performance",
    },
    "DES_agencia": {
        "items": ["DES_2", "DES_9"],
        "label_en": "Individual Agency",
    },
}

LATENT_ES = list(MEASUREMENT_MODEL.keys())
LATENT_EN = {k: v["label_en"] for k, v in MEASUREMENT_MODEL.items()}

GOVERNANCE_FACTORS = ["GOB_empresa", "GOB_confianza", "GOB_externo"]
PERFORMANCE_FACETS = ["DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia"]

# ---------------------------------------------------------------------------
# Variables objetivas de fuente de agua (Fase 2/4). El paper reporta una única
# variable estructural, "Water-Source Vulnerability"/"Water-Source Security" —
# ver docs/discrepancias_paper_vs_pipeline.md: la reconstrucción usa
# `vulnerabilidad_hidrica` (0/1/2, solo Fuente) como la variable que mejor
# reproduce los coeficientes de la Tabla 3/4, NO la combinación con Acueducto
# que se exploró y descartó en la Fase 4 de la conversación original.
# ---------------------------------------------------------------------------
FUENTE_VULNERABILIDAD_MAP = {
    "segura": 0,      # nacimiento propio/comunal, formal
    "informal": 1,
    "otro": 1,
    "comprada": 2,
}

STRUCTURAL_PREDICTORS_ES = GOVERNANCE_FACTORS + ["SOS_ambiental", "vulnerabilidad_hidrica"]
STRUCTURAL_PREDICTORS_EN = {
    "GOB_empresa": "Company Trust",
    "GOB_confianza": "Community Trust",
    "GOB_externo": "External Institution Trust",
    "SOS_ambiental": "Environmental Sustainability",
    "vulnerabilidad_hidrica": "Water-Source Vulnerability",
}

# ---------------------------------------------------------------------------
# fsQCA / NCA
# ---------------------------------------------------------------------------
FSQCA_CONDITIONS = ["GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental", "seguridad_hidrica"]
FSQCA_OUTCOME = "DES_estructural"
FSQCA_CONSISTENCY_THRESHOLD = 0.80
FSQCA_MIN_N = 10  # el paper usa n>=10, no n>=15 como en la exploración original

NCA_CONDITIONS = FSQCA_CONDITIONS
NCA_OUTCOME = "DES_estructural"
NCA_N_PERMUTATIONS = 1000  # para el p-valor de permutación de la Tabla 6

# ---------------------------------------------------------------------------
# Multinivel
# ---------------------------------------------------------------------------
RANDOM_SLOPE_PAIRS = [
    ("DES_relacional", "GOB_confianza"),
    ("DES_estructural", "GOB_confianza"),
    ("DES_regulacion", "SOS_ambiental"),
    ("DES_agencia", "SOS_ambiental"),
    ("DES_estructural", "SOS_ambiental"),
    ("DES_regulacion", "GOB_confianza"),
    ("DES_agencia", "GOB_confianza"),
    ("DES_relacional", "SOS_ambiental"),
    # Completado tareas_revision_paper.md sección 3: Company Trust y External
    # Institution Trust como pendientes aleatorias en las 4 facetas (no estaban
    # en el diseño original del paper, quedaban como limitación explícita).
    ("DES_relacional", "GOB_empresa"),
    ("DES_regulacion", "GOB_empresa"),
    ("DES_estructural", "GOB_empresa"),
    ("DES_agencia", "GOB_empresa"),
    ("DES_relacional", "GOB_externo"),
    ("DES_regulacion", "GOB_externo"),
    ("DES_estructural", "GOB_externo"),
    ("DES_agencia", "GOB_externo"),
]
