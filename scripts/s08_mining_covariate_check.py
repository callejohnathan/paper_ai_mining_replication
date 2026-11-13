"""
Ronda 12 — Chequeo de sensibilidad: ocupacion minera como covariable.

Aproximacion rapida (NO reemplaza el modelo lavaan): OLS sobre promedios de items
estandarizados, errores robustos por vereda. Compara los coeficientes de los 5
predictores con y sin la dummy `mining` (Actividad == 'mineria').
Salida: outputs/tables/table_r12_mining_covariate_check.csv
Pendiente: confirmar en lavaan (covariable observada sobre los 4 outcomes).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
import statsmodels.formula.api as smf
import config as cfg

d = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")
for k, v in cfg.MEASUREMENT_MODEL.items():
    d[k] = d[v["items"]].mean(axis=1)
d["mining"] = (d["Actividad"] == "mineria").astype(int)

preds = ["GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental", "vulnerabilidad_hidrica"]
outs = ["DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia"]
z = d.copy()
for c in preds + outs:
    z[c] = (z[c] - z[c].mean()) / z[c].std()
groups = z["Vereda"].astype("category").cat.codes

rows = []
for y in outs:
    f0 = f"{y} ~ " + " + ".join(preds)
    m0 = smf.ols(f0, z).fit(cov_type="cluster", cov_kwds={"groups": groups})
    m1 = smf.ols(f0 + " + mining", z).fit(cov_type="cluster", cov_kwds={"groups": groups})
    for p in preds:
        rows.append({"outcome": y, "predictor": p, "beta_sin_mining": m0.params[p],
                     "beta_con_mining": m1.params[p],
                     "beta_mining": m1.params["mining"], "p_mining": m1.pvalues["mining"]})
out = pd.DataFrame(rows).round(3)
out.to_csv(cfg.OUT_TABLES / "table_r12_mining_covariate_check.csv", index=False)
print(out.to_string(index=False))
print("\nMineros por vereda:")
print(d.groupby("Vereda")["mining"].agg(["sum", "mean", "count"]).round(2).sort_values("mean", ascending=False))
