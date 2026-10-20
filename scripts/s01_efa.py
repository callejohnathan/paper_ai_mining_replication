"""
s01 — Análisis Factorial Exploratorio (EFA) por bloque, con análisis paralelo
de Horn para decidir el número de factores. Reproduce la Fase 1 de la
conversación original.

Nota: este script es de VALIDACIÓN/documentación de cómo se llegó a
config.MEASUREMENT_MODEL — no se usa para generar los datasets que consumen
los scripts siguientes (esos usan directamente los ítems fijados en config.py).

Salida:
    outputs/tables/efa_parallel_analysis.csv
    outputs/tables/efa_loadings_<bloque>.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity

import config as cfg

np.random.seed(cfg.RANDOM_SEED)


def rank_transform(data: pd.DataFrame) -> pd.DataFrame:
    return data.apply(lambda col: rankdata(col), axis=0)


def parallel_analysis(data: pd.DataFrame, n_iter=200, percentile=95):
    n, p = data.shape
    ranked = rank_transform(data)
    corr = np.corrcoef(ranked.values, rowvar=False)
    real_eigs = np.sort(np.linalg.eigvalsh(corr))[::-1]

    rand_eigs = np.zeros((n_iter, p))
    for i in range(n_iter):
        rand_data = np.column_stack([np.random.permutation(ranked.values[:, j]) for j in range(p)])
        rand_corr = np.corrcoef(rand_data, rowvar=False)
        rand_eigs[i, :] = np.sort(np.linalg.eigvalsh(rand_corr))[::-1]

    rand_mean = rand_eigs.mean(axis=0)
    n_factors = int(np.sum(real_eigs > rand_mean))
    return real_eigs, rand_mean, n_factors


def main():
    df = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")

    blocks = {
        "GOB": [it for it in cfg.GOB_ITEMS if it not in cfg.EXCLUDED_ITEMS],
        "SOS": [it for it in cfg.SOS_ITEMS if it not in cfg.EXCLUDED_ITEMS],
        "DES": [it for it in cfg.DES_ITEMS if it not in cfg.EXCLUDED_ITEMS],
    }

    pa_rows = []
    for block, items in blocks.items():
        data = df[items]
        ranked = rank_transform(data)
        kmo_all, kmo_model = calculate_kmo(ranked.values)
        chi2, p_bartlett = calculate_bartlett_sphericity(ranked.values)
        real_eigs, rand_mean, n_factors = parallel_analysis(data)

        print(f"\n=== Bloque {block} ({len(items)} ítems) ===")
        print(f"KMO={kmo_model:.3f}  Bartlett chi2={chi2:.1f} p={p_bartlett:.2g}  "
              f"-> {n_factors} factores sugeridos (análisis paralelo)")
        pa_rows.append({"bloque": block, "n_items": len(items), "KMO": round(kmo_model, 3),
                         "bartlett_chi2": round(chi2, 1), "n_factores_sugeridos": n_factors})

        fa = FactorAnalyzer(n_factors=n_factors, rotation="promax" if n_factors > 1 else None,
                             method="minres")
        fa.fit(ranked.values)
        loadings = pd.DataFrame(fa.loadings_, index=items,
                                 columns=[f"F{i+1}" for i in range(n_factors)])
        loadings["h2"] = fa.get_communalities()
        loadings.round(3).to_csv(cfg.OUT_TABLES / f"efa_loadings_{block}.csv")
        print(loadings.round(3).to_string())

    pd.DataFrame(pa_rows).to_csv(cfg.OUT_TABLES / "efa_parallel_analysis.csv", index=False)
    print("\nEstructura resultante (fijada en config.MEASUREMENT_MODEL):")
    for name, spec in cfg.MEASUREMENT_MODEL.items():
        print(f"  {name} ({spec['label_en']}): {spec['items']}")


if __name__ == "__main__":
    main()
