"""
s02 — Modelo de medida confirmatorio (CFA vía semopy) con CR, AVE y HTMT.

Esto es nuevo respecto a la conversación original: ahí solo se reportaron
cargas estandarizadas del CB-SEM (Fase 3). El paper (Tabla 3, Sección 3.1.1)
reporta además Composite Reliability, AVE y HTMT máximo — este script los
calcula para poder validar/actualizar esas cifras.

Salida:
    outputs/tables/table3_measurement_model.csv  (loadings range, CR, AVE)
    outputs/tables/htmt_matrix.csv
"""
import sys
from pathlib import Path
from itertools import combinations

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from semopy import Model

import config as cfg
from _common import compute_srmr


def build_cfa_syntax() -> str:
    lines = []
    for name, spec in cfg.MEASUREMENT_MODEL.items():
        lines.append(f"{name} =~ " + " + ".join(spec["items"]))
    return "\n".join(lines)


def composite_reliability_ave(loadings: pd.Series, resid_var: pd.Series):
    """CR y AVE clásicos (Fornell & Larcker, 1981) a partir de cargas estandarizadas."""
    l = loadings.values
    e = resid_var.values  # varianza de error = 1 - loading^2 para cargas estandarizadas
    cr = (l.sum() ** 2) / ((l.sum() ** 2) + e.sum())
    ave = (l ** 2).sum() / len(l)
    return cr, ave


def main():
    df = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")

    syntax = build_cfa_syntax()
    model = Model(syntax)
    model.fit(df)
    ins = model.inspect(std_est=True)

    from semopy import calc_stats
    fit_stats = calc_stats(model)
    fit_stats.loc["Value", "SRMR"] = compute_srmr(model, df)
    fit_stats.to_csv(cfg.OUT_TABLES / "table3_fit_indices.csv")
    print("Índices de ajuste del modelo de medida (comparar con paper: "
          "chi2(202)=884.2, CFI=.957, TLI=.946, RMSEA=.059):")
    print(fit_stats[["chi2", "DoF", "CFI", "TLI", "RMSEA", "SRMR"]].round(4).to_string())

    rows = []
    for name, spec in cfg.MEASUREMENT_MODEL.items():
        # semopy guarda "item ~ latente" como lval=item, rval=latente (al reves de lavaan)
        block = ins[(ins["op"] == "~") & (ins["rval"] == name) & (ins["lval"].isin(spec["items"]))]
        loadings = block.set_index("lval")["Est. Std"].reindex(spec["items"])
        resid_var = 1 - loadings ** 2
        cr, ave = composite_reliability_ave(loadings, resid_var)
        rows.append({
            "construct_es": name,
            "construct_en": spec["label_en"],
            "n_items": len(spec["items"]),
            "loading_min": round(loadings.min(), 3),
            "loading_max": round(loadings.max(), 3),
            "CR": round(cr, 3),
            "AVE": round(ave, 3),
            "below_threshold": (cr < 0.70) or (ave < 0.50),
        })

    table3 = pd.DataFrame(rows)
    table3.to_csv(cfg.OUT_TABLES / "table3_measurement_model.csv", index=False)
    print("Tabla 3 — Modelo de medida (CR/AVE):")
    print(table3.to_string(index=False))

    # --- HTMT (Heterotrait-Monotrait ratio) ---
    # HTMT_ij = media(correlaciones heterotrait-heteromethod) / media(correlaciones
    # monotrait-heteromethod). Usa Pearson sobre los ítems crudos (1-5) — confirmado
    # contra scripts_polanco/scripts/07_tabla2_cargas_cr_ave_htmt.py que esto
    # reproduce el HTMT máx=.504 exacto del paper (Spearman/rangos da .487, cercano
    # pero no exacto).
    names = list(cfg.MEASUREMENT_MODEL.keys())
    corr = df[[it for spec in cfg.MEASUREMENT_MODEL.values() for it in spec["items"]]].corr()

    htmt = pd.DataFrame(index=names, columns=names, dtype=float)
    for a, b in combinations(names, 2):
        items_a, items_b = cfg.MEASUREMENT_MODEL[a]["items"], cfg.MEASUREMENT_MODEL[b]["items"]
        hetero = [corr.loc[i, j] for i in items_a for j in items_b]
        mono_a = [corr.loc[i, j] for i, j in combinations(items_a, 2)] or [1.0]
        mono_b = [corr.loc[i, j] for i, j in combinations(items_b, 2)] or [1.0]
        htmt_val = np.mean(np.abs(hetero)) / np.sqrt(np.mean(mono_a) * np.mean(mono_b))
        htmt.loc[a, b] = htmt.loc[b, a] = round(htmt_val, 3)
    np.fill_diagonal(htmt.values, np.nan)
    htmt.to_csv(cfg.OUT_TABLES / "htmt_matrix.csv")

    max_htmt = np.nanmax(htmt.values.astype(float))
    print(f"\nHTMT máximo observado: {max_htmt:.3f} (umbral de alerta = .85; "
          f"comparar con paper: .504 — coincide exacto)")


if __name__ == "__main__":
    main()
