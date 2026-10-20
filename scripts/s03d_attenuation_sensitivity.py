"""
s03d — Análisis de sensibilidad por atenuación (CORREGIDO 2026-10-15,
docs/decisiones_auditoria_20261015.md, punto 3).

La ronda 7 (docs/ronda7_robustez_medicion.md, sección 3) reportó un efecto
desatenuado de External Institution Trust -> Structural Performance de .185
(desde un .062 observado), pero el código que produjo ese número nunca se
guardó — el propio documento de la ronda 7 dice "el código queda documentado
en este archivo" y el archivo no contiene código. La auditoría de Paula
(pmhd) intentó reproducir el .185 con la fórmula descrita (correlaciones
divididas por √(CR_x·CR_y), betas multivariados vía Rxx⁻¹·Rxy) y no lo logró:
obtuvo .122 con CR y .139 con alfa de Cronbach.

Este script reproduce el análisis de forma permanente y auditable, usando
exactamente la fórmula documentada en la ronda 7 (desatenuación multivariada
de Spearman 1904 sobre la matriz de correlaciones de puntajes compuestos,
resuelta para betas estandarizados). Resultado: coincide con la auditoría de
Paula, NO con el .185 original. Ver verificación independiente en
docs/decisiones_auditoria_20261015.md, punto 3.

Salida:
    outputs/tables/table4b_attenuation_sensitivity.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

import config as cfg
from _common import compute_composites


def cronbach_alpha(items_df: pd.DataFrame) -> float:
    k = items_df.shape[1]
    item_var = items_df.var(axis=0, ddof=1).sum()
    total_var = items_df.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_var / total_var)


def disattenuate(R: np.ndarray, reliab: np.ndarray) -> np.ndarray:
    """Spearman (1904): r'_xy = r_xy / sqrt(rel_x * rel_y), off-diagonal only."""
    out = R.copy()
    n = len(reliab)
    for i in range(n):
        for j in range(n):
            if i != j:
                out[i, j] = R[i, j] / np.sqrt(reliab[i] * reliab[j])
    return out


def solve_betas(R: np.ndarray, allvars: list, outcome: str) -> dict:
    idx_y = allvars.index(outcome)
    idx_x = [i for i in range(len(allvars)) if i != idx_y]
    Rxx = R[np.ix_(idx_x, idx_x)]
    Rxy = R[idx_x, idx_y]
    betas = np.linalg.solve(Rxx, Rxy)
    return dict(zip([allvars[i] for i in idx_x], betas))


def main():
    df = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")
    comp_full = compute_composites(df)
    comp = comp_full[list(cfg.MEASUREMENT_MODEL.keys())].copy()
    comp["vulnerabilidad_hidrica"] = df["vulnerabilidad_hidrica"]

    meas = pd.read_csv(cfg.OUT_TABLES / "table3_measurement_model.csv")
    CR = dict(zip(meas["construct_es"], meas["CR"]))
    CR["vulnerabilidad_hidrica"] = 1.0  # variable observada, no hay corrección

    alpha = {name: cronbach_alpha(df[spec["items"]])
             for name, spec in cfg.MEASUREMENT_MODEL.items()}
    alpha["vulnerabilidad_hidrica"] = 1.0

    predictors = cfg.STRUCTURAL_PREDICTORS_ES
    Z = (comp - comp.mean()) / comp.std(ddof=1)

    rows = []
    for outcome in cfg.PERFORMANCE_FACETS:
        allvars = predictors + [outcome]
        Rmat = Z[allvars].corr().values
        betas_obs = solve_betas(Rmat, allvars, outcome)

        reliab_cr = np.array([CR.get(v, 1.0) for v in allvars])
        betas_cr = solve_betas(disattenuate(Rmat, reliab_cr), allvars, outcome)

        reliab_alpha = np.array([alpha.get(v, 1.0) for v in allvars])
        betas_alpha = solve_betas(disattenuate(Rmat, reliab_alpha), allvars, outcome)

        for predictor in predictors:
            rows.append({
                "outcome": outcome,
                "outcome_en": cfg.LATENT_EN.get(outcome, outcome),
                "predictor": predictor,
                "predictor_en": cfg.STRUCTURAL_PREDICTORS_EN.get(predictor, predictor),
                "beta_observed": round(betas_obs[predictor], 4),
                "beta_disattenuated_CR": round(betas_cr[predictor], 4),
                "beta_disattenuated_alpha": round(betas_alpha[predictor], 4),
            })

    out = pd.DataFrame(rows)
    out.to_csv(cfg.OUT_TABLES / "table4b_attenuation_sensitivity.csv", index=False)

    print("Sensibilidad por atenuación — External Institution Trust (foco de la auditoría):")
    ext = out[out["predictor"] == "GOB_externo"]
    print(ext[["outcome_en", "beta_observed", "beta_disattenuated_CR",
               "beta_disattenuated_alpha"]].to_string(index=False))
    print("\nNota: el valor reproducible para External Trust -> Structural Performance "
          "es .122 (CR) / .139 (alfa), NO .185 (ver docs/decisiones_auditoria_20261015.md, "
          "punto 3). El CB-SEM (Tabla 4) ya reporta el efecto latente corregido por error "
          "de medida para este mismo path: .069, no significativo.")


if __name__ == "__main__":
    main()
