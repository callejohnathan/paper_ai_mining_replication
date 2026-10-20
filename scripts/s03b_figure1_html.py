"""
s03b — Figura 1 (versión final): generada como SVG/HTML en vez de matplotlib,
y luego rasterizada a PNG con Chromium/Edge en modo headless.

Por qué existe este script aparte de la Figura 1 de s03_structural_model.py:
en revisión visual, la versión matplotlib (curvas + halo de texto) seguía
leyéndose "desordenada" con las 13 etiquetas de coeficientes cerca del punto
medio. La versión SVG con el mismo diseño (mismo layout, colores, orden de
nodos que minimiza cruces) se leyó mucho más clara — el renderizado vectorial
nítido del navegador y el halo de fondo en las etiquetas hacen más diferencia
de la esperada. Este script formaliza esa versión como la Figura 1 definitiva.

ACTUALIZADO 2026-10-15 (docs/decisiones_auditoria_20261015.md, punto 4): ahora
lee table4_single_estimator.csv (lavaan, DES_2 fijado a .05, SE cluster-robustos
con referencia t(14)), la MISMA fuente de la Tabla 4 del manuscrito, y las
etiquetas muestran los coeficientes con el formato de la Tabla 4 (3 decimales,
sin cero inicial, con asteriscos). Antes leia la tabla semopy/naive.

Requiere haber corrido antes: scripts/s03e_single_estimator_heywood_fixed.R

Salida:
    outputs/figures/figure1_interactive.html  (para inspeccionar/editar)
    outputs/figures/figure1_path_diagram.png  (versión final para el manuscrito
                                                 — reemplaza la de matplotlib)
"""
import shutil
import subprocess
import sys
from itertools import permutations
from pathlib import Path
from urllib.request import pathname2url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

import config as cfg

COLORS = {
    "pred_fill": "#dbe7f5", "pred_stroke": "#2c5c8a",
    "out_fill": "#f7ded0", "out_stroke": "#a85426",
    "pos": "#2a78d6", "neg": "#e34948", "ns": "#c3c2b7",
    "ink": "#0b0b0b", "ink_muted": "#52514e",
}

W, H = 1180, 830
BOX_W, BOX_H = 210, 64
PRED_X = 40
OUT_X = W - 40 - BOX_W
TOP_MARGIN, BOTTOM_MARGIN = 72, 78
HEADER_Y = 30


def minimize_crossings(edges, n_pred, n_out):
    best_order, best_cost = None, None
    for pp in permutations(range(n_pred)):
        ppos = {o: p for p, o in enumerate(pp)}
        for op in permutations(range(n_out)):
            opos = {o: p for p, o in enumerate(op)}
            cost = 0.0
            for i in range(len(edges)):
                a1, b1, w1 = edges[i]
                pa1, pb1 = ppos[a1], opos[b1]
                for j in range(i + 1, len(edges)):
                    a2, b2, w2 = edges[j]
                    pa2, pb2 = ppos[a2], opos[b2]
                    if (pa1 - pa2) * (pb1 - pb2) < 0:
                        cost += w1 * w2
            if best_cost is None or cost < best_cost:
                best_cost, best_order = cost, (pp, op)
    return best_order


def row_ys(n):
    if n == 1:
        return [TOP_MARGIN + (H - TOP_MARGIN - BOTTOM_MARGIN) / 2]
    span = H - TOP_MARGIN - BOTTOM_MARGIN - BOX_H
    return [TOP_MARGIN + span * i / (n - 1) for i in range(n)]


def bezier_mid(p0, p1, rad):
    p0, p1 = np.array(p0), np.array(p1)
    mid = (p0 + p1) / 2
    d = p1 - p0
    perp = np.array([-d[1], d[0]])
    control = mid + perp * rad
    return control, 0.25 * p0 + 0.5 * control + 0.25 * p1


def fmt_beta(b: float) -> str:
    """Formato de la Tabla 4: 3 decimales, sin cero inicial (-.257, .152)."""
    t = f"{b:.3f}"
    return t.replace("0.", ".", 1) if t.startswith("0.") else t.replace("-0.", "-.", 1)


def build_svg(df: pd.DataFrame) -> str:
    predictors = list(dict.fromkeys(df["predictor_en"]))
    outcomes = list(dict.fromkeys(df["outcome_en"]))
    n_pred, n_out = len(predictors), len(outcomes)
    pred_idx = {p: i for i, p in enumerate(predictors)}
    out_idx = {o: i for i, o in enumerate(outcomes)}

    edges_all = [(pred_idx[r["predictor_en"]], out_idx[r["outcome_en"]],
                  1.0 if r["sig"] != "" else 0.15) for _, r in df.iterrows()]
    pp, op = minimize_crossings(edges_all, n_pred, n_out)
    predictors_ordered = [predictors[i] for i in pp]
    outcomes_ordered = [outcomes[i] for i in op]

    pred_y = dict(zip(predictors_ordered, row_ys(n_pred)))
    out_y = dict(zip(outcomes_ordered, row_ys(n_out)))
    pred_row = {p: i for i, p in enumerate(predictors_ordered)}
    out_row = {o: i for i, o in enumerate(outcomes_ordered)}

    boxes = [
        f'<text x="{PRED_X + BOX_W/2:.1f}" y="{HEADER_Y}" class="col-header">Predictors</text>',
        f'<text x="{OUT_X + BOX_W/2:.1f}" y="{HEADER_Y - 10}" class="col-header">Socio-Ecological Performance</text>',
        f'<text x="{OUT_X + BOX_W/2:.1f}" y="{HEADER_Y + 12}" class="col-header">(facets)</text>',
    ]
    for name, y in pred_y.items():
        cy = y + BOX_H / 2
        boxes.append(f'<rect x="{PRED_X}" y="{y:.1f}" width="{BOX_W}" height="{BOX_H}" rx="8" class="box box-pred"/>'
                      f'<text x="{PRED_X + BOX_W/2:.1f}" y="{cy:.1f}" class="box-label">{name}</text>')
    for name, y in out_y.items():
        cy = y + BOX_H / 2
        boxes.append(f'<rect x="{OUT_X}" y="{y:.1f}" width="{BOX_W}" height="{BOX_H}" rx="8" class="box box-out"/>'
                      f'<text x="{OUT_X + BOX_W/2:.1f}" y="{cy:.1f}" class="box-label">{name}</text>')

    rows = sorted(df.iterrows(), key=lambda kv: kv[1]["sig"] == "")  # no-sig primero (fondo)
    paths, labels = [], []
    for _, r in rows:
        beta, sig = r["beta"], r["sig"] != ""
        p0 = (PRED_X + BOX_W, pred_y[r["predictor_en"]] + BOX_H / 2)
        p1 = (OUT_X, out_y[r["outcome_en"]] + BOX_H / 2)
        row_diff = abs(pred_row[r["predictor_en"]] - out_row[r["outcome_en"]])
        rad = 0.16 + 0.045 * row_diff
        control, mid = bezier_mid(p0, p1, rad)
        d = f"M {p0[0]:.1f},{p0[1]:.1f} Q {control[0]:.1f},{control[1]:.1f} {p1[0]:.1f},{p1[1]:.1f}"
        if sig:
            cls = "edge-pos" if beta >= 0 else "edge-neg"
            lw = max(1.4, abs(beta) * 11)
            paths.append(f'<path d="{d}" class="edge {cls}" style="stroke-width:{lw:.2f}"/>')
            txt = fmt_beta(beta) + r["sig"]
            lw_box = 14 + 8.2 * len(txt)
            labels.append(f'<g class="lbl {cls}">'
                           f'<rect x="{mid[0]-lw_box/2:.1f}" y="{mid[1]-11:.1f}" width="{lw_box:.1f}" height="18" rx="5" class="lbl-bg"/>'
                           f'<text x="{mid[0]:.1f}" y="{mid[1]:.1f}" class="lbl-text">{txt}</text></g>')
        else:
            paths.append(f'<path d="{d}" class="edge edge-ns"/>')

    return "\n".join(boxes) + "\n" + "\n".join(paths) + "\n" + "\n".join(labels)


def build_html(svg_body: str) -> str:
    return f"""<title>Figure 1 — Structural Path Diagram</title>
<style>
  .viz-root {{
    --ink: {COLORS['ink']}; --ink-muted: {COLORS['ink_muted']};
    --pred-fill: {COLORS['pred_fill']}; --pred-stroke: {COLORS['pred_stroke']};
    --out-fill: {COLORS['out_fill']}; --out-stroke: {COLORS['out_stroke']};
    --pos: {COLORS['pos']}; --neg: {COLORS['neg']}; --ns: {COLORS['ns']};
    --lbl-bg: #ffffff;
  }}
  html, body {{ margin: 0; background: #ffffff; }}
  .viz-root {{
    background: #ffffff; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 20px 16px 28px; display: flex; flex-direction: column; align-items: center; gap: 14px;
  }}
  .card {{ background: #ffffff; max-width: 100%; overflow-x: auto; }}
  figure {{ margin: 0; }}
  svg {{ display: block; }}
  .box {{ stroke-width: 1.3; }}
  .box-pred {{ fill: var(--pred-fill); stroke: var(--pred-stroke); }}
  .box-out {{ fill: var(--out-fill); stroke: var(--out-stroke); }}
  .box-label {{ fill: var(--ink); font-size: 14px; text-anchor: middle; dominant-baseline: middle; font-weight: 500; }}
  .col-header {{ fill: var(--ink); font-size: 16px; font-weight: 700; text-anchor: middle; dominant-baseline: middle; }}
  .edge {{ fill: none; }}
  .edge-pos {{ stroke: var(--pos); opacity: 0.92; }}
  .edge-neg {{ stroke: var(--neg); opacity: 0.92; }}
  .edge-ns {{ stroke: var(--ns); stroke-width: 1; stroke-dasharray: 5 4; opacity: 0.5; }}
  .lbl-bg {{ fill: var(--lbl-bg); opacity: 0.92; }}
  .lbl-text {{ text-anchor: middle; dominant-baseline: middle; font-size: 12.5px; font-weight: 700; font-variant-numeric: tabular-nums; }}
  .lbl.edge-pos .lbl-text {{ fill: var(--pos); }}
  .lbl.edge-neg .lbl-text {{ fill: var(--neg); }}
  .legend {{ display: flex; gap: 22px; align-items: center; font-size: 12.5px; color: var(--ink-muted); flex-wrap: wrap; justify-content: center; }}
  .legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .swatch {{ width: 22px; height: 3px; border-radius: 2px; display: inline-block; }}
  .swatch.ns {{ border-top: 2px dashed var(--ns); height: 0; }}
</style>
<div class="viz-root">
  <div class="card">
    <figure>
      <svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">
        {svg_body}
      </svg>
    </figure>
  </div>
  <div class="legend">
    <span><span class="swatch" style="background:var(--pos)"></span>Significant, positive (p&lt;.05)</span>
    <span><span class="swatch" style="background:var(--neg)"></span>Significant, negative (p&lt;.05)</span>
    <span><span class="swatch ns"></span>Not significant</span>
    <span>Standardized &beta;; *p&lt;.05, **p&lt;.01, ***p&lt;.001 (cluster-robust, t(14))</span>
  </div>
</div>
"""


def find_chromium():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    pw = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    if pw:
        return str(pw[-1])
    return shutil.which("msedge") or shutil.which("chrome") or shutil.which("google-chrome")


def render_png(html_path: Path, png_path: Path) -> bool:
    browser = find_chromium()
    if not browser:
        print("\n(!) No se encontró Edge/Chrome en este equipo para rasterizar automáticamente.")
        print(f"    Abrí {html_path} en el navegador, tomá una captura, o instalá Edge/Chrome"
              " y volvé a correr este script.")
        return False
    uri = html_path.resolve().as_uri()
    subprocess.run([
        browser, "--headless", "--disable-gpu", "--no-sandbox",
        "--force-device-scale-factor=2", "--window-size=1300,1100",
        f"--screenshot={png_path}", uri,
    ], capture_output=True, timeout=60)
    if png_path.exists():
        # recorta el blanco sobrante (la ventana headless es mas alta que el contenido)
        from PIL import Image, ImageChops
        im = Image.open(png_path).convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 40
            im.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                     min(bbox[2] + pad, im.width), min(bbox[3] + pad, im.height))).save(png_path)
    return png_path.exists()


def main():
    coef_path = cfg.OUT_TABLES / "table4_single_estimator.csv"
    if not coef_path.exists():
        raise SystemExit("Corré primero scripts/s03e_single_estimator_heywood_fixed.R.")
    df = pd.read_csv(coef_path, keep_default_na=False)

    svg_body = build_svg(df)
    html = build_html(svg_body)

    html_path = cfg.OUT_FIGURES / "figure1_interactive.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML guardado en {html_path}")

    png_path = cfg.OUT_FIGURES / "figure1_path_diagram.png"
    if render_png(html_path, png_path):
        print(f"PNG (versión final, reemplaza la de matplotlib) guardado en {png_path}")
    else:
        print("PNG no generado automáticamente — ver instrucciones arriba.")


if __name__ == "__main__":
    main()
