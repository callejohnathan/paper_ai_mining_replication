"""
s15b — Ronda 20, paso F-a5: External separado en el multinivel (S1).

Repite las pruebas de pendiente aleatoria de s06 (modelo bivariado, mezcla
50:50 chi2(1):chi2(2) de Self y Liang, BH) para las dos partes de External:
    ext_autoridad = promedio de GOB_2 y GOB_7 (Cornare / POMCA)
    ext_municipio = GOB_8 (un solo ítem)
sobre las 4 facetas (8 pruebas). Se compara con External combinado (GOB_externo).

Salida: outputs/tables/tableS_multinivel_external_separado.csv
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy.stats import chi2

import config as cfg
from _common import compute_composites
from s09b_mining_covariate_multilevel import mejor_ajuste, bh


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))
    df["ext_autoridad"] = df[["GOB_2", "GOB_7"]].mean(axis=1)
    df["ext_municipio"] = df["GOB_8"].astype(float)
    filas = []
    for x in ["GOB_externo", "ext_autoridad", "ext_municipio"]:
        for y in cfg.PERFORMANCE_FACETS:
            m0 = mejor_ajuste(f"{y} ~ {x}", df, "1", maxiter=300)
            m1 = mejor_ajuste(f"{y} ~ {x}", df, f"1 + {x}")
            lr = max(2 * (m1.llf - m0.llf), 0)
            p = 0.5 * chi2.sf(lr, 1) + 0.5 * chi2.sf(lr, 2)
            filas.append({"condicion": x, "outcome": y, "pendiente_fija": m1.fe_params[x], "LR": lr, "p": p})
    t = pd.DataFrame(filas)
    for x in t.condicion.unique():
        sel = t.condicion == x
        t.loc[sel, "heterogenea_BH_en_su_familia"] = bh(t.loc[sel, "p"].values)
    # H9 (ronda 21): también BH sobre las 12 pruebas juntas
    t["heterogenea_BH_12_pruebas"] = bh(t["p"].values)
    t = t.round(4)
    t.to_csv(cfg.OUT_TABLES / "tableS_multinivel_external_separado.csv", index=False)
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
