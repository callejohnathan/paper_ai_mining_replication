"""
s03c — Ajuste de la inferencia cluster-robusta a t(G-1) en vez de z-normal.

Contexto (docs/decisiones_auditoria_20261015.md, punto 2): `r_cluster_robust_sem.R`
reajusta el CB-SEM con el sandwich estimator de lavaan (cluster="Vereda"), pero
lavaan reporta el p-valor del coeficiente cluster-robusto con referencia normal
(z = est/se_cluster, p = 2*(1-Phi(|z|))) sin importar cuantos clusteres haya.
Con solo 15 clusteres (veredas), la referencia normal subestima la variabilidad
muestral del estimador sandwich -- el mismo problema, en espiritu, que llevo a
descartar el bootstrap por cluster de 15 grupos en la ronda 8. La correccion
ad hoc estandar en la literatura de inferencia por cluster con pocos grupos
(p. ej. Cameron & Miller 2015, "A Practitioner's Guide to Cluster-Robust
Inference") es usar t(G-1) en vez de z como distribucion de referencia.

Este script NO vuelve a ajustar el SEM (requiere R/lavaan, no disponible en
este entorno) -- recupera el estadistico z exacto a partir del p-valor normal
ya calculado por lavaan (invertible exactamente, z = qnorm(1 - p/2)) y aplica
la correccion t(14) sobre ese mismo z. Es equivalente a correr lavaan con un
test t si se conserva el mismo estadistico, y evita requerir R en esta maquina.

Entrada:  outputs/tables/table4_cluster_robust_lavaan.csv (de r_cluster_robust_sem.R)
Salida:   outputs/tables/table4_cluster_robust_t14.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from scipy.stats import norm, t

import config as cfg

N_CLUSTERS = 15  # veredas


def main():
    df = pd.read_csv(cfg.OUT_TABLES / "table4_cluster_robust_lavaan.csv")

    df["z_cluster"] = norm.ppf(1 - df["pvalue_cluster"] / 2)
    dfree = N_CLUSTERS - 1
    df["pvalue_cluster_t14"] = 2 * t.sf(df["z_cluster"].abs(), df=dfree)

    df["sig_naive"] = df["pvalue_naive"] < 0.05
    df["sig_cluster_normal"] = df["pvalue_cluster"] < 0.05
    df["sig_cluster_t14"] = df["pvalue_cluster_t14"] < 0.05
    df["cambia_normal_a_t14"] = df["sig_cluster_normal"] & ~df["sig_cluster_t14"]

    out = df[["lhs", "rhs", "std.all", "pvalue_naive", "pvalue_cluster",
              "pvalue_cluster_t14", "sig_naive", "sig_cluster_normal",
              "sig_cluster_t14", "cambia_normal_a_t14"]]
    out = out.sort_values("pvalue_cluster_t14")
    out.to_csv(cfg.OUT_TABLES / "table4_cluster_robust_t14.csv", index=False)

    print(f"Referencia t({dfree}) aplicada sobre el z-estadistico cluster-robusto de lavaan.")
    print(out.to_string(index=False))

    changed = out[out["cambia_normal_a_t14"]]
    print(f"\nPierden significancia al pasar de z-normal a t({dfree}): {len(changed)}")
    print(changed[["lhs", "rhs", "pvalue_cluster", "pvalue_cluster_t14"]].to_string(index=False))


if __name__ == "__main__":
    main()
