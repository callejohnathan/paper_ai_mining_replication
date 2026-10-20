"""
s00 — Carga de datos crudos, diagnóstico de ítems y exclusión de ítems débiles.

Reproduce la Fase 0 de la conversación original (diagnóstico ítem por ítem) y
la limpieza final (GOB_3, GOB_4). Guarda un dataset procesado en
/data/processed/ que todos los scripts siguientes (s01+) deben leer, en vez de
tocar el Excel crudo directamente.

Salida:
    data/processed/survey_clean.csv   — ítems retenidos + demográficas + variables derivadas
    outputs/tables/item_diagnostics.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from scipy import stats

import config as cfg


def load_raw() -> pd.DataFrame:
    return pd.read_excel(cfg.DATA_RAW)


def item_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución, asimetría y correlación ítem-total corregida por bloque (Fase 0)."""
    blocks = {"GOB": cfg.GOB_ITEMS, "SOS": cfg.SOS_ITEMS, "DES": cfg.DES_ITEMS}
    rows = []
    for block, items in blocks.items():
        block_df = df[items]
        total = block_df.sum(axis=1)
        for item in items:
            x = block_df[item]
            r_it = x.corr(total - x, method="spearman")
            rows.append({
                "bloque": block,
                "item": item,
                "media": round(x.mean(), 2),
                "sd": round(x.std(), 2),
                "asimetria": round(stats.skew(x.dropna()), 2),
                "%min": round((x == x.min()).mean() * 100, 1),
                "%max": round((x == x.max()).mean() * 100, 1),
                "%punto_medio_3": round((x == 3).mean() * 100, 1),
                "r_item_total_corr": round(r_it, 3),
                "excluido": item in cfg.EXCLUDED_ITEMS,
                "motivo_exclusion": cfg.EXCLUDED_ITEMS.get(item, ""),
            })
    return pd.DataFrame(rows)


def simplify_fuente(f):
    if pd.isna(f):
        return "otro"
    f = str(f).strip().lower()
    if "nacimiento" in f or f == "formal":
        return "segura"
    if "comprada" in f:
        return "comprada"
    if f == "informal":
        return "informal"
    return "otro"


def build_clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # variables objetivas derivadas de Fuente / Acueducto (Fase 2/4)
    out["fuente_cat"] = out["Fuente"].apply(simplify_fuente)
    out["vulnerabilidad_hidrica"] = out["fuente_cat"].map(cfg.FUENTE_VULNERABILIDAD_MAP)
    out["seguridad_hidrica"] = 2 - out["vulnerabilidad_hidrica"]  # invertido, para fsQCA
    out["acueducto_si"] = (out["Acueducto"].astype(str).str.lower() == "si").astype(int)

    retained_items = [it for it in (cfg.GOB_ITEMS + cfg.SOS_ITEMS + cfg.DES_ITEMS)
                       if it not in cfg.EXCLUDED_ITEMS]
    keep_cols = retained_items + [
        "Vereda", "Actividad", "Acueducto", "Responde", "Fuente",
        "fuente_cat", "vulnerabilidad_hidrica", "seguridad_hidrica", "acueducto_si",
    ]
    return out[keep_cols]


def main():
    df_raw = load_raw()
    print(f"Datos crudos: {df_raw.shape[0]} filas, {df_raw.shape[1]} columnas")

    diag = item_diagnostics(df_raw)
    diag.to_csv(cfg.OUT_TABLES / "item_diagnostics.csv", index=False)
    print(f"\nÍtems excluidos ({len(cfg.EXCLUDED_ITEMS)}):")
    print(diag[diag["excluido"]][["item", "%punto_medio_3", "r_item_total_corr", "motivo_exclusion"]]
          .to_string(index=False))

    df_clean = build_clean_dataset(df_raw)
    out_path = cfg.DATA_PROCESSED / "survey_clean.csv"
    df_clean.to_csv(out_path, index=False)
    print(f"\nDataset limpio guardado en {out_path} — {df_clean.shape[1]} columnas retenidas")


if __name__ == "__main__":
    main()
