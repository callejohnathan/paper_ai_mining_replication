"""
s05 — Necessary Condition Analysis (CE-FDH) con test de permutación, y
Figura 2 (líneas de techo para Community Trust y Water-Source Security).

Salida:
    outputs/tables/table6_nca_effect_sizes.csv
    outputs/figures/figure2_nca_ceiling_lines.png
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import config as cfg
from _common import compute_composites

# Rampa secuencial azul documentada (skill dataviz, references/palette.md,
# pasos 100->700) — magnitud (conteo de encuestados), no un color a ojo.
SEQ_BLUE = LinearSegmentedColormap.from_list("seq_blue", [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#0d366b",
])

np.random.seed(cfg.RANDOM_SEED)


def ce_fdh_effect_size(x: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    scope = (x_max - x_min) * (y_max - y_min)
    if scope == 0:
        return 0.0

    ceiling = np.maximum.accumulate(ys)
    ux = np.unique(xs)
    ceiling_at_ux = np.array([ceiling[xs == v].max() for v in ux])
    widths = np.diff(np.concatenate([ux, [x_max]]))
    ceiling_zone = np.sum(widths * (y_max - ceiling_at_ux))
    return ceiling_zone / scope


def permutation_test(x: np.ndarray, y: np.ndarray, n_perm: int) -> float:
    d_obs = ce_fdh_effect_size(x, y)
    d_perm = np.empty(n_perm)
    for i in range(n_perm):
        x_shuffled = np.random.permutation(x)
        d_perm[i] = ce_fdh_effect_size(x_shuffled, y)
    p = (np.sum(d_perm >= d_obs) + 1) / (n_perm + 1)
    return d_obs, p


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))
    y = df[cfg.NCA_OUTCOME].values

    label_map = {
        "GOB_empresa": "Company Trust", "GOB_confianza": "Community Trust",
        "GOB_externo": "External Institution Trust",
        "SOS_ambiental": "Environmental Sustainability",
        "seguridad_hidrica": "Water-Source Security",
    }

    rows = []
    for cond in cfg.NCA_CONDITIONS:
        x = df[cond].values
        d, p = permutation_test(x, y, cfg.NCA_N_PERMUTATIONS)
        rows.append({"condition": label_map[cond], "d": round(d, 4), "p_permutation": round(p, 3)})
        print(f"{label_map[cond]:30s} d={d:.4f}  p={p:.3f}")

    table6 = pd.DataFrame(rows)
    table6.to_csv(cfg.OUT_TABLES / "table6_nca_effect_sizes.csv", index=False)
    print("\n(comparar con paper: d=.0125/.0000/.0000/.0000/.0000; "
          "solo Company Trust significativo p=.001)")

    plot_ceiling_lines(df, y)


def plot_ceiling_lines(df: pd.DataFrame, y: np.ndarray):
    """Burbujas en la posición exacta (x,y) con área y color proporcionales al
    conteo de encuestados en esa combinación — sin jitter. Los datos son muy
    discretos (Community Trust solo tiene 9 valores posibles, Water-Source
    Security solo 3); un scatter con jitter diluye visualmente dónde se
    concentra realmente la masa de respuestas, que es justo lo que hay que
    ver para leer una línea de techo NCA."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    S_MIN, S_MAX = 10, 700

    for ax, cond, label in [
        (axes[0], "GOB_confianza", "Community Trust"),
        (axes[1], "seguridad_hidrica", "Water-Source Security"),
    ]:
        x = df[cond].values
        counts = (pd.DataFrame({"x": x.round(4), "y": y.round(4)})
                  .groupby(["x", "y"]).size().reset_index(name="n"))
        n_max = counts["n"].max()
        sizes = S_MIN + (S_MAX - S_MIN) * (counts["n"] / n_max)

        sc = ax.scatter(counts["x"], counts["y"], s=sizes, c=counts["n"],
                         cmap=SEQ_BLUE, vmin=0, vmax=n_max,
                         alpha=0.9, edgecolors="white", linewidths=0.6, zorder=3)

        order = np.argsort(x)
        xs, ys = x[order], y[order]
        ceiling = np.maximum.accumulate(ys)
        ux = np.unique(xs)
        ceiling_at_ux = np.array([ceiling[xs == v].max() for v in ux])
        ax.step(np.concatenate([ux, [xs.max()]]),
                np.concatenate([ceiling_at_ux, [ceiling_at_ux[-1]]]),
                where="post", color="firebrick", linewidth=2, zorder=4,
                label="Ceiling line (CE-FDH)")

        ax.set_xlabel(label)
        ax.set_ylabel("Structural Performance")
        ax.legend(loc="lower right", fontsize=8)
        cbar = fig.colorbar(sc, ax=ax, pad=0.02)
        cbar.set_label("N respondents", fontsize=8)
        cbar.ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(cfg.OUT_FIGURES / "figure2_nca_ceiling_lines.png", dpi=150)
    print(f"\nFigura guardada en {cfg.OUT_FIGURES / 'figure2_nca_ceiling_lines.png'}")


if __name__ == "__main__":
    main()
