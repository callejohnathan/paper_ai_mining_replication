"""
s04 — fsQCA: calibración por método directo (log-odds), tabla de verdad y
configuraciones suficientes para Structural Performance.

Diferencia respecto a la exploración original de la conversación: aquí se usa
calibración log-odds (método directo de Ragin) en vez de interpolación lineal
en el espacio de probabilidad — más estándar en la literatura fsQCA y lo que
mejor reproduce los valores de consistencia/cobertura del paper (Tabla 5).
Ver docs/discrepancias_paper_vs_pipeline.md para el detalle de este ajuste.

Incluye PRI (Proportional Reduction in Inconsistency, Ragin 2008) además de
consistencia y cobertura — ver docs/ronda10_fsqca_nca_reproducibilidad.md
para el procedimiento de calibración documentado y el detalle de PRI.

Salida:
    outputs/tables/table5_fsqca_configurations.csv
"""
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

import config as cfg
from _common import compute_composites

def calibrate_direct(x: pd.Series, p_out=10, p_cross=50, p_in=90) -> pd.Series:
    """Calibración por método directo (Ragin), sigmoide con anclas de percentil.

    Confirmado exacto contra scripts_polanco/scripts/12_tabla4_fsqca.py: reproduce
    dígito por dígito las 7 configuraciones suficientes de la Tabla 5 del paper
    (consistencias .807-.841). No clampea más allá de las anclas (a diferencia de
    intentos anteriores con interpolación lineal o log-odds truncado), por eso
    los casos extremos reciben membresías más cercanas a 0/1.
    """
    thr_out, crossover, thr_in = np.percentile(x, [p_out, p_cross, p_in])
    xv = x.values.astype(float)
    if thr_out == crossover:
        thr_out = crossover - 1e-6
    if thr_in == crossover:
        thr_in = crossover + 1e-6
    z = np.where(
        xv >= crossover,
        (xv - crossover) / (thr_in - crossover) * 3.0,
        (xv - crossover) / (crossover - thr_out) * 3.0,
    )
    fuzzy = np.exp(z) / (1 + np.exp(z))
    return pd.Series(fuzzy, index=x.index)


def calibrate_ordinal_3level(x: pd.Series) -> pd.Series:
    """Para seguridad_hidrica (0/1/2): calibración directa, no hay suficientes
    niveles para anclas de percentil (ver bug documentado en la exploración original)."""
    return x.map({0: 0.05, 1: 0.50, 2: 0.95})


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))

    conditions = cfg.FSQCA_CONDITIONS
    outcome = cfg.FSQCA_OUTCOME

    fs = pd.DataFrame(index=df.index)
    for c in conditions + [outcome]:
        if c == "seguridad_hidrica":
            fs[c] = calibrate_ordinal_3level(df[c])
        else:
            fs[c] = calibrate_direct(df[c])

    labels_bool = {
        "GOB_empresa": "Company", "GOB_confianza": "Community",
        "GOB_externo": "External", "SOS_ambiental": "Sustainability",
        "seguridad_hidrica": "Security",
    }

    rows = []
    for combo in product([0, 1], repeat=len(conditions)):
        membership = np.ones(len(fs))
        for cond, present in zip(conditions, combo):
            m = fs[cond].values if present else (1 - fs[cond].values)
            membership = np.minimum(membership, m)
        n_in = int((membership > 0.5).sum())
        if n_in == 0:
            continue
        y = fs[outcome].values
        consistency = np.minimum(membership, y).sum() / membership.sum()
        coverage = np.minimum(membership, y).sum() / y.sum()  # fórmula fsQCA estándar

        # PRI (Proportional Reduction in Inconsistency, Ragin 2008): penaliza
        # configuraciones que son simultáneamente subconjunto de Y y de ~Y
        # (casos ambiguos donde la pertenencia al resultado es incierta).
        not_y = 1 - y
        ambiguous = np.minimum(membership, np.minimum(y, not_y))
        pri_num = np.minimum(membership, y).sum() - ambiguous.sum()
        pri_den = membership.sum() - ambiguous.sum()
        pri = pri_num / pri_den if pri_den > 1e-9 else np.nan

        bool_label = "*".join(
            labels_bool[c] if present else labels_bool[c][0].lower() + labels_bool[c][1:] + "'"
            for c, present in zip(conditions, combo)
        )
        rows.append({"configuration": bool_label, "n": n_in,
                     "consistency": round(consistency, 3), "PRI": round(pri, 3),
                     "raw_coverage": round(coverage, 3)})

    truth = pd.DataFrame(rows).sort_values("consistency", ascending=False)
    truth.to_csv(cfg.OUT_TABLES / "truth_table_full.csv", index=False)

    sufficient = truth[(truth["consistency"] >= cfg.FSQCA_CONSISTENCY_THRESHOLD)
                        & (truth["n"] >= cfg.FSQCA_MIN_N)]
    sufficient.to_csv(cfg.OUT_TABLES / "table5_fsqca_configurations.csv", index=False)

    print(f"Configuraciones suficientes (consistencia >= {cfg.FSQCA_CONSISTENCY_THRESHOLD}, "
          f"n >= {cfg.FSQCA_MIN_N}):")
    print(sufficient.to_string(index=False))
    print("\n(comparar con Tabla 5 del paper: 7 configuraciones, consistencias .807-.841)")


if __name__ == "__main__":
    main()
