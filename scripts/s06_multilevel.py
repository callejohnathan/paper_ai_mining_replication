"""
s06 — ICC, pendientes aleatorias (random slopes) y BLUPs por vereda.

ICC (Tabla 7a del paper) y pendientes aleatorias (Tabla 7b) — confirmado exacto
contra scripts_polanco/scripts/15_tabla6_multinivel_final.py y 16_blups_extraccion.py.

Dos detalles que NO son intuitivos y que sin el script original habría sido
difícil adivinar:
1. Los modelos de pendiente aleatoria son BIVARIADOS (outcome ~ predictor),
   SIN las demás covariables de gobernanza/sostenibilidad como efectos fijos
   — a diferencia del modelo estructural (s03), que sí las incluye todas.
2. CORREGIDO 2026-10-15 (ver docs/decisiones_auditoria_20261015.md, punto 1):
   `re_formula="1 + predictor"` estima una covarianza intercepto-pendiente NO
   estructurada (2x2) además de la varianza de la pendiente — es decir, el
   modelo con pendiente aleatoria tiene 2 parámetros más que el modelo con
   solo intercepto aleatorio (varianza de la pendiente Y covarianza). Ese es
   exactamente el caso en que Self & Liang (1987) exige la mezcla 50:50 de
   chi2(1) y chi2(2) como distribución de referencia del LR test — no
   0.5*chi2(1) solo, que es la corrección apropiada únicamente cuando se
   añade un único parámetro de varianza en el borde del espacio (p. ej.
   comparar un modelo sin efectos aleatorios contra uno con un solo
   intercepto aleatorio). La versión anterior de este script usaba
   0.5*chi2(1) para el caso de 2 parámetros, heredado sin corregir del
   script original (ver docs/discrepancias_paper_vs_pipeline.md, punto 5) y
   así publicado en 20260828_Paper_VF.docx. Es anticonservador: declara
   heterogéneas pendientes que no lo son al nivel .05.
   LR se trunca en 0 para evitar valores negativos de ajustes casi-degenerados.
3. Con 16 pruebas simultáneas (8 ya reportadas + 8 de Company/External Trust,
   ronda 6), se aplica además corrección de Benjamini-Hochberg (FDR) sobre el
   p-valor de la mezcla corregida — no se aplicaba antes.

Salida:
    outputs/tables/table7a_icc.csv
    outputs/tables/table7b_random_slopes.csv
    outputs/tables/blups_<outcome>_<slope>.csv
    outputs/figures/figure3_blups_sustainability_structural.png
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from scipy.stats import chi2

import config as cfg
from _common import compute_composites

OPTIMIZERS = ["lbfgs", "cg", "bfgs", "nm", "powell"]


def _converged(res) -> bool:
    return res is not None and res.converged and np.isfinite(res.llf)


def compute_icc(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name in cfg.MEASUREMENT_MODEL:
        md = smf.mixedlm(f"{name} ~ 1", data=df, groups=df["Vereda"])
        res = md.fit(reml=True)
        var_group = res.cov_re.iloc[0, 0]
        var_resid = res.scale
        icc = var_group / (var_group + var_resid)
        rows.append({"construct_es": name, "construct_en": cfg.LATENT_EN[name], "ICC": round(icc, 3)})
    return pd.DataFrame(rows).sort_values("ICC", ascending=False)


def fit_intercept_only(df, outcome, predictor):
    """Modelo bivariado con solo intercepto aleatorio (sin pendiente aleatoria)."""
    best = None
    for opt in OPTIMIZERS:
        try:
            md = smf.mixedlm(f"{outcome} ~ {predictor}", df, groups=df["Vereda"], re_formula="1")
            res = md.fit(reml=False, method=opt, maxiter=300)
            if _converged(res) and (best is None or res.llf > best.llf):
                best = res
        except Exception:
            continue
    return best


def fit_random_slope(df, outcome, predictor):
    """Modelo bivariado con intercepto Y pendiente aleatoria para `predictor`."""
    best = None
    for opt in OPTIMIZERS:
        try:
            md = smf.mixedlm(f"{outcome} ~ {predictor}", df, groups=df["Vereda"],
                              re_formula=f"1 + {predictor}")
            res = md.fit(reml=False, method=opt, maxiter=500)
            if _converged(res) and (best is None or res.llf > best.llf):
                best = res
        except Exception:
            continue
    return best


def random_slope_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Bivariado (outcome ~ predictor, sin otras covariables) + corrección
    Self & Liang (1987), mezcla 50:50 chi2(1):chi2(2) — el modelo con
    pendiente aleatoria añade 2 parámetros (varianza de la pendiente +
    covarianza intercepto-pendiente) respecto al modelo con solo intercepto
    aleatorio, no 1. Ver docs/decisiones_auditoria_20261015.md, punto 1.
    Se aplica además correción Benjamini-Hochberg (FDR) sobre las 16 pruebas."""
    rows = []
    for y, slope_var in cfg.RANDOM_SLOPE_PAIRS:
        m0 = fit_intercept_only(df, y, slope_var)
        m1 = fit_random_slope(df, y, slope_var)

        if m0 is None or m1 is None:
            rows.append({"outcome_en": cfg.LATENT_EN[y], "slope_en": cfg.LATENT_EN[slope_var],
                         "outcome_es": y, "slope_es": slope_var, "LR": np.nan, "p": np.nan,
                         "heterogeneous": "fit_failed", "model": None})
            continue

        lr = max(2 * (m1.llf - m0.llf), 0)
        p = 0.5 * chi2.sf(lr, df=1) + 0.5 * chi2.sf(lr, df=2)
        rows.append({
            "outcome_en": cfg.LATENT_EN[y], "slope_en": cfg.LATENT_EN[slope_var],
            "outcome_es": y, "slope_es": slope_var,
            "LR": round(lr, 2), "p": round(p, 4),
            "heterogeneous": "Yes" if p < 0.05 else "No",
            "model": m1,
        })

    out = pd.DataFrame(rows)

    # Benjamini-Hochberg sobre las filas con p-valor válido (excluye fit_failed)
    valid = out["p"].notna()
    m = valid.sum()
    ranks = out.loc[valid, "p"].rank(method="first").astype(int)
    bh_crit = ranks / m * 0.05
    sorted_p = out.loc[valid, "p"].sort_values()
    # mayor k tal que p_(k) <= (k/m)*alpha; todos los p_(1..k) se marcan significativos
    sorted_ranks = sorted_p.rank(method="first").astype(int)
    passes = sorted_p.values <= (sorted_ranks.values / m * 0.05)
    k_max = sorted_ranks.values[passes].max() if passes.any() else 0
    bh_threshold_rank = k_max
    out.loc[valid, "p_rank"] = ranks.values
    out["heterogeneous_bh"] = "fit_failed"
    out.loc[valid, "heterogeneous_bh"] = np.where(
        out.loc[valid, "p_rank"] <= bh_threshold_rank, "Yes", "No")
    out = out.drop(columns="p_rank")
    return out


def extract_blups(model, df, outcome, slope_var):
    """BLUPs + IC 95% aproximado (tareas_revision_paper.md sección 4): usa
    random_effects_cov de statsmodels (varianza posterior de la predicción del
    efecto aleatorio) para distinguir señal real de artefacto de shrinkage en
    veredas con n pequeño."""
    fe_slope = model.fe_params[slope_var]
    fe_se = model.bse[slope_var]
    re = pd.DataFrame(model.random_effects).T
    re["slope_total"] = fe_slope + re[slope_var]

    cov_re = model.random_effects_cov
    slope_var_post = pd.Series({g: cov_re[g].loc[slope_var, slope_var] for g in cov_re})
    # varianza total aproximada = varianza posterior del BLUP + varianza del efecto fijo
    # (asume independencia; aproximación estándar cuando no hay covarianza reportada entre ambos)
    re["se_total"] = np.sqrt(slope_var_post + fe_se ** 2)
    re["ci_low"] = re["slope_total"] - 1.96 * re["se_total"]
    re["ci_high"] = re["slope_total"] + 1.96 * re["se_total"]
    re["n"] = df.groupby("Vereda").size()

    out = re[[slope_var, "slope_total", "se_total", "ci_low", "ci_high", "n"]].rename(
        columns={slope_var: "slope_deviation"})
    return out.sort_values("slope_total", ascending=False), fe_slope


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))

    icc = compute_icc(df)
    icc.to_csv(cfg.OUT_TABLES / "table7a_icc.csv", index=False)
    print("Tabla 7a — ICC (comparar con paper: .326/.308/.231/.217/.206/.185/.099/.027):")
    print(icc.to_string(index=False))

    slope_results = random_slope_tests(df)
    slope_summary = slope_results.drop(columns="model")
    slope_summary.to_csv(cfg.OUT_TABLES / "table7b_random_slopes.csv", index=False)
    print("\nTabla 7b — Tests de razón de verosimilitud para pendientes aleatorias "
          "(mezcla 50:50 chi2(1):chi2(2) + BH sobre 16 pruebas; "
          "ver docs/decisiones_auditoria_20261015.md punto 1):")
    print(slope_summary.to_string(index=False))
    print("\n(LR calculado igual que antes; el p-valor YA NO es comparable 1:1 con el "
          "paper publicado, que usaba 0.5*chi2(1) solamente — p's anteriores reportados "
          "en 20260828_Paper_VF.docx: 4.58/.016, 9.80/<.001, 12.16/<.001, 9.37/.001, "
          "8.44/.002, 0.72/.198, 0.23/.315, 3.06/.040)")

    n_bh = (slope_summary["heterogeneous_bh"] == "Yes").sum()
    n_nominal = (slope_summary["heterogeneous"] == "Yes").sum()
    print(f"\nSignificativas al .05 nominal (mezcla corregida): {n_nominal}/16. "
          f"Significativas tras Benjamini-Hochberg (FDR .05): {n_bh}/16.")

    # BLUPs: se extraen para las significativas al .05 nominal con la mezcla
    # correcta (criterio usado en el paper hasta ahora); la columna
    # heterogeneous_bh en la Tabla 7b muestra cuáles sobreviven además el
    # control de FDR más estricto, para que el equipo decida qué estándar
    # reportar en el texto.
    significant = slope_results[slope_results["heterogeneous"] == "Yes"]
    for _, row in significant.iterrows():
        blups, fe_slope = extract_blups(row["model"], df, row["outcome_es"], row["slope_es"])
        fname = f"blups_{row['outcome_es']}_{row['slope_es']}.csv"
        blups.to_csv(cfg.OUT_TABLES / fname)
        print(f"\nBLUPs {row['slope_en']} -> {row['outcome_en']} (pendiente fija={fe_slope:.3f}):")
        print(blups.round(3).to_string())

    # Figura 3: el pathway destacado en el paper (Sustainability -> Structural Performance)
    target = significant[(significant["outcome_es"] == "DES_estructural")
                          & (significant["slope_es"] == "SOS_ambiental")]
    if len(target):
        blups, fe_slope = extract_blups(target.iloc[0]["model"], df, "DES_estructural", "SOS_ambiental")
        plot_blups(blups, fe_slope)


def plot_blups(blups: pd.DataFrame, fe_slope: float):
    # orden ascendente al graficar -> con hlines/categorico, el primer item
    # queda al pie del eje, así el valor más alto (último) queda arriba,
    # igual que la convención de la figura original del paper.
    ordered = blups.sort_values("slope_total", ascending=True)
    veredas = ordered.index
    values = ordered["slope_total"].values

    fig, ax = plt.subplots(figsize=(8.5, 8))
    colors = ["#4C72B0"] * len(values)
    colors[0] = "firebrick"   # el menor
    colors[-1] = "seagreen"   # el mayor

    ax.hlines(veredas, 0, values, color=colors, linewidth=2, zorder=2)
    for y, v, c in zip(veredas, values, colors):
        ax.plot(v, y, "o", color=c, markersize=7, zorder=3)

    x_range = values.max() - min(0, values.min())
    offset = x_range * 0.018
    for y, v in zip(veredas, values):
        ha = "left" if v >= 0 else "right"
        lx = v + offset if v >= 0 else v - offset
        ax.text(lx, y, f"{v:.3f}", va="center", ha=ha, fontsize=8.5,
                color="#333333", zorder=4)

    ax.axvline(fe_slope, color="black", linestyle="--", zorder=1,
               label=f"Fixed-effect slope ({fe_slope:.3f})")
    ax.set_xlabel("Community-specific slope (Environmental Sustainability -> Structural Performance)")
    ax.set_xlim(min(0, values.min()) - offset * 2, values.max() + offset * 6)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(cfg.OUT_FIGURES / "figure3_blups_sustainability_structural.png", dpi=150)
    print(f"\nFigura guardada en {cfg.OUT_FIGURES / 'figure3_blups_sustainability_structural.png'}")


if __name__ == "__main__":
    main()
