"""
s07 — Tabla síntesis (Tabla 7/8 del paper, la "money table"): para cada actor
de gobernanza, integra el resultado de los 4 métodos (CB-SEM, fsQCA, NCA,
multinivel). Requiere haber corrido s02-s06 y s03c primero (lee sus CSV de salida).

CORREGIDO 2026-10-15 (docs/decisiones_auditoria_20261015.md, punto 2): la
columna CB-SEM leía `table4_structural_coefficients.csv` (p-valores naive de
semopy), no los p-valores robustos al clúster. La ronda 9 (lavaan,
sandwich estimator) ya había encontrado que esto importa (Company Trust y
otros cambian de significancia), pero la recomendación de actualizar esta
tabla nunca se implementó aquí. Ahora lee `table4_cluster_robust_t14.csv`
(robusto al clúster + referencia t(14), no z-normal — ver s03c) para los 5
predictores que ese archivo cubre; `vulnerabilidad_hidrica` no es un "actor"
de gobernanza y no se reporta en esta tabla, igual que antes.

Salida:
    outputs/tables/table8_synthesis.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import config as cfg

SHORT = {"GOB_empresa": "Company", "GOB_confianza": "Community", "GOB_externo": "External"}


def main():
    coef_robust = pd.read_csv(cfg.OUT_TABLES / "table4_cluster_robust_t14.csv")
    fsqca = pd.read_csv(cfg.OUT_TABLES / "table5_fsqca_configurations.csv")
    nca = pd.read_csv(cfg.OUT_TABLES / "table6_nca_effect_sizes.csv")
    icc = pd.read_csv(cfg.OUT_TABLES / "table7a_icc.csv")
    slopes = pd.read_csv(cfg.OUT_TABLES / "table7b_random_slopes.csv")

    rows = []
    for gob_es, short in SHORT.items():
        label_en = cfg.LATENT_EN[gob_es]

        sub = coef_robust[coef_robust["rhs"] == gob_es]
        n_sig = sub["sig_cluster_t14"].sum()
        cbsem = (f"Significant (cluster-robust, t14), {n_sig}/4 facets" if n_sig
                 else "Not significant (cluster-robust, t14), 0/4 facets")

        n_config = len(fsqca)
        n_present = fsqca["configuration"].str.contains(fr"{short}(?!')", regex=True).sum() if n_config else 0
        fsqca_str = f"Present in {n_present}/{n_config} configurations" if n_config else "n/a"

        nca_row = nca[nca["condition"].str.contains(label_en.split()[0], case=False, na=False)]
        nca_str = f"d={nca_row['d'].values[0]:.4f}" if len(nca_row) else "n/a"

        icc_row = icc[icc["construct_es"] == gob_es]
        icc_val = icc_row["ICC"].values[0] if len(icc_row) else float("nan")

        het_rows = slopes[slopes["slope_es"] == gob_es]
        n_tested = len(het_rows)
        n_het = (het_rows["heterogeneous"] == "Yes").sum() if n_tested else 0
        het_str = f"heterogeneous in {n_het}/{n_tested} tested" if n_tested else "heterogeneity not tested"

        rows.append({
            "actor": label_en, "CB-SEM": cbsem, "fsQCA": fsqca_str, "NCA (necessity)": nca_str,
            "Multilevel": f"ICC={icc_val:.3f}; {het_str}",
        })

    table8 = pd.DataFrame(rows)
    table8.to_csv(cfg.OUT_TABLES / "table8_synthesis.csv", index=False)
    print("Tabla 8 — Síntesis por actor de gobernanza:")
    print(table8.to_string(index=False))


if __name__ == "__main__":
    main()
