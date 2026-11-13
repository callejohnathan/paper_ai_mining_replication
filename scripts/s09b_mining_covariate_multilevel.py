"""
s09b — Ronda 14, paso C: ocupación minera como covariable en los modelos multinivel.

Tres comprobaciones, sobre los mismos compuestos y la misma lógica de s06:

1. ICC de cada faceta de desempeño sin y con minería como efecto fijo:
   ¿la concentración de mineros en algunas veredas explica parte de la
   varianza entre veredas?
2. Las 16 pruebas de pendiente aleatoria de la Tabla 7b, repetidas con minería
   como efecto fijo adicional (misma mezcla 50:50 chi2(1):chi2(2) de
   Self y Liang, misma corrección BH). ¿Cambia qué pendientes son heterogéneas?
3. Modelo de intercepto aleatorio por vereda con los 5 predictores del modelo
   estructural, sin y con minería (análogo multinivel del chequeo OLS de s08).

Salidas (outputs/tables/):
    table_r14_mining_icc.csv
    table_r14_mining_random_slopes.csv
    table_r14_mining_multilevel_fixed.csv
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import chi2

import config as cfg
from _common import compute_composites

OPTIMIZERS = ["lbfgs", "cg", "bfgs", "nm", "powell"]
PREDS = cfg.STRUCTURAL_PREDICTORS_ES


def mejor_ajuste(formula, df, re_formula, reml=False, maxiter=500):
    best = None
    for opt in OPTIMIZERS:
        try:
            res = smf.mixedlm(formula, df, groups=df["Vereda"], re_formula=re_formula).fit(
                reml=reml, method=opt, maxiter=maxiter)
            if res.converged and np.isfinite(res.llf) and (best is None or res.llf > best.llf):
                best = res
        except Exception:
            continue
    return best


def icc(res):
    v = res.cov_re.iloc[0, 0]
    return v / (v + res.scale)


def bh(p, alpha=0.05):
    p = np.asarray(p)
    orden = np.argsort(p)
    m = len(p)
    pasa = p[orden] <= (np.arange(1, m + 1) / m * alpha)
    k = np.max(np.where(pasa)[0]) + 1 if pasa.any() else 0
    out = np.zeros(m, dtype=bool)
    out[orden[:k]] = True
    return out


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))
    df["mining"] = (df["Actividad"] == "mineria").astype(int)

    # 1. ICC -----------------------------------------------------------------
    filas = []
    for y in cfg.PERFORMANCE_FACETS:
        r0 = smf.mixedlm(f"{y} ~ 1", df, groups=df["Vereda"]).fit(reml=True)
        r1 = smf.mixedlm(f"{y} ~ mining", df, groups=df["Vereda"]).fit(reml=True)
        filas.append({"outcome": y, "ICC_sin_mining": round(icc(r0), 3),
                      "ICC_con_mining": round(icc(r1), 3),
                      "beta_mining": round(r1.fe_params["mining"], 3),
                      "p_mining": round(r1.pvalues["mining"], 3)})
    t_icc = pd.DataFrame(filas)
    t_icc.to_csv(cfg.OUT_TABLES / "table_r14_mining_icc.csv", index=False)

    # 2. Pendientes aleatorias ------------------------------------------------
    filas = []
    for y, x in cfg.RANDOM_SLOPE_PAIRS:
        for cov in ("", " + mining"):
            f = f"{y} ~ {x}{cov}"
            m0 = mejor_ajuste(f, df, "1", maxiter=300)
            m1 = mejor_ajuste(f, df, f"1 + {x}")
            if m0 is None or m1 is None:
                filas.append({"outcome": y, "slope": x, "mining": bool(cov), "LR": np.nan, "p": np.nan})
                continue
            lr = max(2 * (m1.llf - m0.llf), 0)
            p = 0.5 * chi2.sf(lr, 1) + 0.5 * chi2.sf(lr, 2)
            filas.append({"outcome": y, "slope": x, "mining": bool(cov), "LR": lr, "p": p,
                          "pendiente_fija": m1.fe_params[x]})
    rs = pd.DataFrame(filas)
    for flag in (False, True):
        sel = rs["mining"] == flag
        rs.loc[sel, "heterogenea"] = rs.loc[sel, "p"] < 0.05
        rs.loc[sel, "heterogenea_BH"] = bh(rs.loc[sel, "p"].values)
    ancho = rs.pivot_table(index=["outcome", "slope"], columns="mining",
                           values=["LR", "p", "pendiente_fija", "heterogenea", "heterogenea_BH"],
                           aggfunc="first")
    ancho.columns = [f"{v}_{'con' if m else 'sin'}_mining" for v, m in ancho.columns]
    ancho = ancho.reset_index()
    orden = ["outcome", "slope"] + [f"{v}_{s}_mining" for v in ("LR", "p", "pendiente_fija", "heterogenea", "heterogenea_BH")
                                    for s in ("sin", "con")]
    ancho = ancho[orden].round(4)
    ancho.to_csv(cfg.OUT_TABLES / "table_r14_mining_random_slopes.csv", index=False)

    # 3. Intercepto aleatorio con todos los predictores ----------------------
    z = df.copy()
    for c in PREDS + cfg.PERFORMANCE_FACETS:
        z[c] = (z[c] - z[c].mean()) / z[c].std()
    filas = []
    for y in cfg.PERFORMANCE_FACETS:
        base = f"{y} ~ " + " + ".join(PREDS)
        r0 = mejor_ajuste(base, z, "1", reml=True)
        r1 = mejor_ajuste(base + " + mining", z, "1", reml=True)
        for x in PREDS + ["mining"]:
            filas.append({"outcome": y, "predictor": x,
                          "beta_sin_mining": r0.fe_params.get(x, np.nan),
                          "p_sin_mining": r0.pvalues.get(x, np.nan),
                          "beta_con_mining": r1.fe_params[x], "p_con_mining": r1.pvalues[x]})
    fx = pd.DataFrame(filas).round(3)
    fx.to_csv(cfg.OUT_TABLES / "table_r14_mining_multilevel_fixed.csv", index=False)

    pd.set_option("display.width", 220)
    print("ICC:\n", t_icc.to_string(index=False))
    print("\nPendientes aleatorias:\n", ancho.to_string(index=False))
    print("\nIntercepto aleatorio, todos los predictores (estandarizados):\n", fx.to_string(index=False))


if __name__ == "__main__":
    main()
