"""
s03f — Regenera la Figura 1 (diagrama de rutas) desde el estimador unico
corregido (punto 4, docs/decisiones_auditoria_20261015.md).

La Figura 1 original se generaba desde los beta y p-valores NAIVE de semopy
(s03_structural_model.py::main(), antes de cualquier ajuste cluster-robust).
Esto ya habia sido senalado por la auditoria de Paula como desactualizado
("Figura 1: sigue mostrando el patron de significancia anterior al ajuste
cluster-robust y debe regenerarse", comentario #2 de la ronda). Esta version
usa los beta y la significancia t(14) de table4_single_estimator.csv
(lavaan, Heywood fijado, cluster-robusto) -- la misma fuente que ahora
alimenta la Tabla 4 del manuscrito.

Requiere haber corrido antes: scripts/s03e_single_estimator_heywood_fixed.R

Salida:
    outputs/figures/figure1_path_diagram.png (sobrescrito)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import config as cfg
from s03_structural_model import plot_path_diagram


def main():
    df = pd.read_csv(cfg.OUT_TABLES / "table4_single_estimator.csv")
    coef_table = df.rename(columns={"sig": "sig"})[
        ["outcome_en", "predictor_en", "beta", "sig"]
    ].copy()
    coef_table["sig"] = coef_table["sig"].fillna("")
    plot_path_diagram(coef_table)
    print("Figura 1 regenerada desde table4_single_estimator.csv "
          "(lavaan, Heywood fijado, cluster-robusto t14).")


if __name__ == "__main__":
    main()
