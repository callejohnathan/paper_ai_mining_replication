"""
s03 — Modelo estructural confirmatorio (CB-SEM completo: medida + estructura)
y Figura 1 (diagrama de rutas).

Diferencia clave respecto a la Fase 3 de la conversación original: el modelo
aquí usa SOLO `vulnerabilidad_hidrica` (Fuente, 0/1/2) como variable de
vulnerabilidad hídrica objetiva, SIN `acueducto_si` como covariable separada
— la Fase 4 de la conversación había mostrado que ambas variables corrigen en
direcciones opuestas y no deben fusionarse; el paper aparentemente resolvió
esto usando solo la de Fuente en el modelo estructural final (ver
docs/discrepancias_paper_vs_pipeline.md).

AVISO (2026-10-15, docs/decisiones_auditoria_20261015.md, punto 4): esta
versión (semopy, sin restricción del caso Heywood en DES_agencia) ya NO es
la fuente de la Tabla 4 ni de la Figura 1 del manuscrito -- esas vienen del
estimador único en scripts/s03e_single_estimator_heywood_fixed.R (lavaan,
Heywood fijado, cluster-robusto t14). table4_structural_coefficients.csv
sigue siendo útil como comparación/diagnóstico, pero correr este script
DESPUÉS de s03e sobrescribe figure1_path_diagram.png con la versión semopy
desactualizada -- si se vuelve a correr s03, correr s03f_regenerate_figure1.py
a continuación para restaurar la figura correcta.

Salida:
    outputs/tables/table4_structural_coefficients.csv
    outputs/figures/figure1_path_diagram.png (ver aviso arriba)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from semopy import Model, calc_stats

import config as cfg
from _common import compute_srmr


def build_full_syntax() -> str:
    measurement = [f"{name} =~ " + " + ".join(spec["items"])
                   for name, spec in cfg.MEASUREMENT_MODEL.items()]
    rhs = " + ".join(cfg.STRUCTURAL_PREDICTORS_ES)
    structural = [f"{outcome} ~ {rhs}" for outcome in cfg.PERFORMANCE_FACETS]
    return "\n".join(measurement + structural)


def main():
    df = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")

    syntax = build_full_syntax()
    model = Model(syntax)
    model.fit(df)

    stats = calc_stats(model)
    stats.loc["Value", "SRMR"] = compute_srmr(model, df)
    stats.to_csv(cfg.OUT_TABLES / "table4_fit_indices.csv")
    print("Índices de ajuste (modelo estructural completo):")
    print(stats[["chi2", "DoF", "chi2 p-value", "CFI", "TLI", "RMSEA", "SRMR"]].T.round(4).to_string())
    print("(comparar con paper: chi2(228)=1198.3, CFI=.940, TLI=.927, RMSEA=.066; "
          "SRMR no reportado en el paper original — se agrega en esta ronda)")

    ins = model.inspect(std_est=True)

    rows = []
    for outcome in cfg.PERFORMANCE_FACETS:
        for pred in cfg.STRUCTURAL_PREDICTORS_ES:
            r = ins[(ins["op"] == "~") & (ins["lval"] == outcome) & (ins["rval"] == pred)]
            if len(r) == 0:
                continue
            beta = r["Est. Std"].values[0]
            p = r["p-value"].values[0]
            sig = "" if p in ("-",) else ("***" if float(p) < .001 else "**" if float(p) < .01
                                           else "*" if float(p) < .05 else "")
            rows.append({
                "outcome_es": outcome, "outcome_en": cfg.LATENT_EN[outcome],
                "predictor_es": pred, "predictor_en": cfg.STRUCTURAL_PREDICTORS_EN[pred],
                "beta": round(beta, 3), "p": p, "sig": sig,
            })
    coef_table = pd.DataFrame(rows)
    coef_table.to_csv(cfg.OUT_TABLES / "table4_structural_coefficients.csv", index=False)

    pivot = coef_table.pivot(index="predictor_en", columns="outcome_en", values="beta")
    print("\nTabla 4 — Coeficientes estructurales estandarizados (comparar con Tabla 3 del paper):")
    print(pivot.round(3).to_string())

    # R^2 = 1 - varianza residual estandarizada del outcome (endógeno, varianza total=1)
    r2_rows = []
    for outcome in cfg.PERFORMANCE_FACETS:
        var_row = ins[(ins["op"] == "~~") & (ins["lval"] == outcome) & (ins["rval"] == outcome)]
        resid_std = var_row["Est. Std"].values[0]
        r2_rows.append({"outcome_en": cfg.LATENT_EN[outcome], "R2": round(1 - resid_std, 3)})
    r2_table = pd.DataFrame(r2_rows)
    r2_table.to_csv(cfg.OUT_TABLES / "table4_r2.csv", index=False)
    print("\nR² por outcome (comparar con paper: .085, .130, .375, .088):")
    print(r2_table.to_string(index=False))

    plot_path_diagram(coef_table)


# --- Figura 1: diagrama de rutas -------------------------------------------
# Paleta divergente documentada (skill dataviz, references/palette.md):
# blue #2a78d6 <-> red #e34948, polos ya validados por el sistema de diseño
# (no se eligieron a ojo). Positivo=azul, negativo=rojo; no-significativo
# queda en gris tenue, punteado, al fondo (menor z-order).
COLOR_POS = "#2a78d6"
COLOR_NEG = "#e34948"
COLOR_NS = "#c3c2b7"


def _minimize_crossings(edges, n_pred, n_out):
    """Busca el orden de predictores/outcomes que minimiza el cruce de líneas,
    ponderando fuerte las rutas significativas (w=1) y débil las no
    significativas (w=.15) para no dejar que el "fondo" dicte el orden."""
    from itertools import permutations

    best_order, best_cost = None, None
    for pred_perm in permutations(range(n_pred)):
        pred_pos = {orig: pos for pos, orig in enumerate(pred_perm)}
        for out_perm in permutations(range(n_out)):
            out_pos = {orig: pos for pos, orig in enumerate(out_perm)}
            cost = 0.0
            for i in range(len(edges)):
                a1, b1, w1 = edges[i]
                pa1, pb1 = pred_pos[a1], out_pos[b1]
                for j in range(i + 1, len(edges)):
                    a2, b2, w2 = edges[j]
                    pa2, pb2 = pred_pos[a2], out_pos[b2]
                    if (pa1 - pa2) * (pb1 - pb2) < 0:
                        cost += w1 * w2
            if best_cost is None or cost < best_cost:
                best_cost, best_order = cost, (pred_perm, out_perm)
    return best_order, best_cost


def _bezier_arc3_point(p0, p1, rad, t):
    """Punto a fracción `t` de la curva que matplotlib dibuja con
    connectionstyle='arc3,rad=rad' entre p0 y p1 — para colocar la etiqueta
    exactamente sobre la línea curva (no sobre la recta que ya no se dibuja),
    y en un punto propio de cada arco en vez de siempre el punto medio."""
    p0, p1 = np.array(p0), np.array(p1)
    mid = (p0 + p1) / 2
    d = p1 - p0
    perp = np.array([-d[1], d[0]])
    control = mid + perp * rad
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * control + t ** 2 * p1


def plot_path_diagram(coef_table: pd.DataFrame):
    predictors = list(dict.fromkeys(coef_table["predictor_en"]))
    outcomes = list(dict.fromkeys(coef_table["outcome_en"]))
    n_pred, n_out = len(predictors), len(outcomes)

    pred_idx = {p: i for i, p in enumerate(predictors)}
    out_idx = {o: i for i, o in enumerate(outcomes)}

    edges_all = []
    for _, r in coef_table.iterrows():
        significant = r["sig"] != "" and pd.notna(r["sig"])
        edges_all.append((pred_idx[r["predictor_en"]], out_idx[r["outcome_en"]],
                           1.0 if significant else 0.15))

    (pred_perm, out_perm), _ = _minimize_crossings(edges_all, n_pred, n_out)
    predictors_ordered = [predictors[i] for i in pred_perm]
    outcomes_ordered = [outcomes[i] for i in out_perm]

    fig, ax = plt.subplots(figsize=(13, 9), facecolor="white")
    ax.set_facecolor("white")

    y_pred = dict(zip(predictors_ordered, np.linspace(0.92, 0.08, n_pred)))
    y_out = dict(zip(outcomes_ordered, np.linspace(0.88, 0.12, n_out)))
    pred_row = {p: i for i, p in enumerate(predictors_ordered)}
    out_row = {o: i for i, o in enumerate(outcomes_ordered)}
    x_pred_right, x_out_left = 0.24, 0.76

    for name, y in y_pred.items():
        ax.add_patch(plt.Rectangle((0.02, y - 0.035), 0.22, 0.07, fill=True,
                                    facecolor="#cfe0f3", edgecolor="black", zorder=3))
        ax.text(0.13, y, name, ha="center", va="center", fontsize=9.5, zorder=4)

    for name, y in y_out.items():
        ax.add_patch(plt.Rectangle((0.76, y - 0.035), 0.22, 0.07, fill=True,
                                    facecolor="#f7ddc9", edgecolor="black", zorder=3))
        ax.text(0.87, y, name, ha="center", va="center", fontsize=9.5, zorder=4)

    # no-significativas primero (fondo, z-order bajo), significativas encima
    plot_order = sorted(coef_table.iterrows(), key=lambda kv: kv[1]["sig"] == "")

    for _, r in plot_order:
        beta = r["beta"]
        significant = r["sig"] != "" and pd.notna(r["sig"])
        p0 = (x_pred_right, y_pred[r["predictor_en"]])
        p1 = (x_out_left, y_out[r["outcome_en"]])

        # curvatura proporcional a la distancia entre filas: separa los
        # puntos medios de aristas que si no quedarian muy cerca entre si.
        row_diff = abs(pred_row[r["predictor_en"]] - out_row[r["outcome_en"]])
        rad = 0.09 + 0.028 * row_diff

        if significant:
            color = COLOR_POS if beta >= 0 else COLOR_NEG
            lw = max(0.9, abs(beta) * 7)
            alpha, zorder = 0.9, 5
        else:
            color = COLOR_NS
            lw = 0.7
            alpha, zorder = 0.55, 2

        arrow = plt.matplotlib.patches.FancyArrowPatch(
            p0, p1, connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-", linewidth=lw, linestyle="-" if significant else "--",
            color=color, alpha=alpha, zorder=zorder)
        ax.add_patch(arrow)

        if significant:
            lx, ly = _bezier_arc3_point(p0, p1, rad, 0.5)
            ax.text(lx, ly, f"{beta:.2f}", fontsize=8, color=color, fontweight="bold",
                    ha="center", va="center", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.95))

    legend_handles = [
        # CORREGIDO 2026-10-15 (docs/decisiones_auditoria_20261015.md, punto 4): la
        # leyenda estaba en español en una figura que acompaña un manuscrito en
        # inglés -- inconsistencia preexistente del pipeline, detectada al
        # regenerar la figura para el estimador unico Heywood-corregido.
        plt.Line2D([0], [0], color=COLOR_POS, lw=2, label="Significant, positive (p<.05)"),
        plt.Line2D([0], [0], color=COLOR_NEG, lw=2, label="Significant, negative (p<.05)"),
        plt.Line2D([0], [0], color=COLOR_NS, lw=1, linestyle="--", label="Not significant"),
    ]
    ax.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.04),
              ncol=3, frameon=False, fontsize=9)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(cfg.OUT_FIGURES / "figure1_path_diagram.png", dpi=200, facecolor="white")
    print(f"\nFigura guardada en {cfg.OUT_FIGURES / 'figure1_path_diagram.png'}")


if __name__ == "__main__":
    main()
