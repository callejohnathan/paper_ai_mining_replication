"""Utilidades compartidas entre scripts s02+ (SRMR) y s04+ (fsQCA, NCA,
multinivel), que trabajan sobre puntajes compuestos por constructo en vez de
ítems individuales."""
import numpy as np
import pandas as pd

import config as cfg


def compute_srmr(fitted_model, df: pd.DataFrame) -> float:
    """SRMR: raíz del promedio de residuales al cuadrado entre la matriz de
    correlación observada y la implicada por el modelo (incluye diagonal
    superior con diagonal). No lo reporta semopy.calc_stats() directamente."""
    sigma, *_ = fitted_model.calc_sigma()
    order = fitted_model.vars["observed"]
    obs_cov = df[order].cov().values

    def to_corr(cov):
        d = np.sqrt(np.diag(cov))
        return cov / np.outer(d, d)

    resid = to_corr(obs_cov) - to_corr(sigma)
    p = len(order)
    iu = np.triu_indices(p, k=0)
    return float(np.sqrt(np.mean(resid[iu] ** 2)))


def compute_composites(df: pd.DataFrame) -> pd.DataFrame:
    """Puntaje compuesto (media simple 1-5) por constructo de config.MEASUREMENT_MODEL.

    La Fase 4 de la conversación original validó que estos promedios simples
    correlacionan .84-.98 con los factor scores del CB-SEM — proxy suficiente
    para fsQCA/NCA/multinivel sin tener que extraer factor scores cada vez.
    """
    out = df.copy()
    for name, spec in cfg.MEASUREMENT_MODEL.items():
        out[name] = df[spec["items"]].mean(axis=1)
    return out
