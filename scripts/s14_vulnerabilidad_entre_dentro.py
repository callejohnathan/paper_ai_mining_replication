"""
s14 — Ronda 20, paso F-a2: vulnerabilidad de la fuente entre veredas y dentro de vereda.

La vulnerabilidad de la fuente es casi una característica de la vereda
(ICC ,65) y su relación con el desempeño estructural cambia de signo al
controlar por vereda (ronda 14). Aquí se separan sus dos componentes en un
modelo de intercepto aleatorio por vereda:

    y ~ vul_entre + vul_dentro + GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + (1 | vereda)

    vul_entre  = promedio de la vereda (variación entre las 15 comunidades)
    vul_dentro = vulnerabilidad del hogar menos el promedio de su vereda

Las facetas y los demás predictores van estandarizados (como en s09b); los
dos componentes de la vulnerabilidad se dejan en su escala original (0/1/2),
para que sus coeficientes sean comparables entre sí. El efecto entre veredas
se estima con 15 unidades: es descriptivo.

Salida: outputs/tables/table_r20_vulnerabilidad_entre_dentro.csv
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import t as t_dist

import config as cfg
from _common import compute_composites

OPTIMIZERS = ["lbfgs", "cg", "bfgs", "nm", "powell"]


def ajustar(formula, df):
    best = None
    for opt in OPTIMIZERS:
        try:
            r = smf.mixedlm(formula, df, groups=df["Vereda"]).fit(reml=True, method=opt, maxiter=500)
            if r.converged and np.isfinite(r.llf) and (best is None or r.llf > best.llf):
                best = r
        except Exception:
            continue
    return best


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))
    otros = ["GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental"]
    for c in otros + cfg.PERFORMANCE_FACETS:
        df[c] = (df[c] - df[c].mean()) / df[c].std()
    df["vul_entre"] = df.groupby("Vereda")["vulnerabilidad_hidrica"].transform("mean")
    df["vul_dentro"] = df["vulnerabilidad_hidrica"] - df["vul_entre"]

    filas = []
    for y in cfg.PERFORMANCE_FACETS:
        r = ajustar(f"{y} ~ vul_entre + vul_dentro + " + " + ".join(otros), df)
        ci = r.conf_int()
        for x in ["vul_entre", "vul_dentro"]:
            # H8 (ronda 21): el componente entre veredas se estima con 15 grupos, así que
            # además del IC normal se reporta uno con referencia t(13) (15 grupos - 2)
            tq = t_dist.ppf(0.975, 13)
            filas.append({"outcome": y, "componente": x, "coef": r.fe_params[x],
                          "ic_inf": ci.loc[x, 0], "ic_sup": ci.loc[x, 1], "p": r.pvalues[x],
                          "ic_inf_t13": r.fe_params[x] - tq * r.bse[x], "ic_sup_t13": r.fe_params[x] + tq * r.bse[x]})
    t = pd.DataFrame(filas).round(3)
    t.to_csv(cfg.OUT_TABLES / "table_r20_vulnerabilidad_entre_dentro.csv", index=False)
    print(t.to_string(index=False))
    print("\nDesviación estándar de cada componente:",
          df[["vul_entre", "vul_dentro"]].std().round(3).to_dict())


if __name__ == "__main__":
    main()
