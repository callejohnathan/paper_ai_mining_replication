"""
s11b — Ronda 17, paso E (medición): redundancia de ítems y alcance de la NCA.

1. Para cada par de ítems consecutivos del cuestionario: porcentaje de respuestas
   idénticas y correlación. Los pares con más del 90 % de respuestas idénticas
   indican un sesgo de respuesta por bloque (repetir la respuesta anterior),
   que infla la confiabilidad (CR/AVE) del constructo que forman.
2. NCA (CE-FDH, misma función de s05) para las 5 condiciones y las 4 facetas de
   desempeño, con el número de casos que tienen la condición en su mínimo y el
   resultado en su máximo. Si ese número es > 0, la esquina superior izquierda
   está ocupada y d = 0 por construcción.

Salidas (outputs/tables/):
    table_r17_items_consecutivos.csv
    table_r17_nca_todas_facetas.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import config as cfg
from _common import compute_composites
from s05_nca import ce_fdh_effect_size


def constructo(item):
    return next((k for k, v in cfg.MEASUREMENT_MODEL.items() if item in v["items"]), "excluido/otro")


def main():
    raw = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")
    items = [c for c in raw.columns if c.split("_")[0] in ("GOB", "SOS", "DES") and c.split("_")[-1].isdigit()]

    def kappa(a, b):
        """Acuerdo exacto, acuerdo esperado por las marginales y kappa de Cohen (ronda 22)."""
        po = (raw[a] == raw[b]).mean()
        pa, pb = raw[a].value_counts(normalize=True), raw[b].value_counts(normalize=True)
        pe = sum(pa.get(k, 0) * pb.get(k, 0) for k in set(pa.index) | set(pb.index))
        return pe, (po - pe) / (1 - pe)

    filas = []
    for a, b in zip(items, items[1:]):
        pe, k = kappa(a, b)
        filas.append({"par": f"{a}-{b}", "constructo_a": constructo(a), "constructo_b": constructo(b),
                      "pct_identicas": round((raw[a] == raw[b]).mean() * 100, 1),
                      "pct_esperado_marginales": round(pe * 100, 1), "kappa": round(k, 3),
                      "r": round(raw[[a, b]].corr().iloc[0, 1], 3)})
    t1 = pd.DataFrame(filas).sort_values("pct_identicas", ascending=False)
    t1.to_csv(cfg.OUT_TABLES / "table_r17_items_consecutivos.csv", index=False)
    # Pares del mismo bloque que no son contiguos y que el manuscrito cita (DES_5-DES_7) y pares de External
    extra = []
    for a, b in [("DES_5", "DES_7"), ("GOB_2", "GOB_7"), ("GOB_2", "GOB_8"), ("GOB_7", "GOB_8")]:
        pe, k = kappa(a, b)
        extra.append({"par": f"{a}-{b}", "pct_identicas": round((raw[a] == raw[b]).mean() * 100, 1),
                      "pct_esperado_marginales": round(pe * 100, 1), "kappa": round(k, 3)})
    pd.DataFrame(extra).to_csv(cfg.OUT_TABLES / "table_r22_kappa_pares_citados.csv", index=False)

    df = compute_composites(raw)
    filas = []
    for y in cfg.PERFORMANCE_FACETS:
        for c in cfg.NCA_CONDITIONS:
            x, yy = df[c].values, df[y].values
            filas.append({"outcome": y, "condition": c, "d": round(ce_fdh_effect_size(x, yy), 4),
                          "casos_x_min_y_max": int(((x == x.min()) & (yy == yy.max())).sum())})
    t2 = pd.DataFrame(filas)
    t2.to_csv(cfg.OUT_TABLES / "table_r17_nca_todas_facetas.csv", index=False)

    pd.set_option("display.width", 200)
    print(t1.to_string(index=False))
    print(t2.pivot(index="condition", columns="outcome", values="d"))


if __name__ == "__main__":
    main()
