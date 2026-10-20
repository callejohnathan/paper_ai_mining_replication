"""
s08 — Exporta las Figuras 1-3 en PDF vectorial para el envío a Resources Policy.

La guía de autores exige que los gráficos de líneas se entreguen en formato
vectorial (EPS/PDF, fuentes incrustadas) o como mapa de bits a 1000 dpi; los
PNG actuales (~1300 px de ancho) no alcanzan ese mínimo. Este script no
recalcula nada: reutiliza las mismas funciones de graficado del pipeline y las
tablas ya generadas, solo cambia el formato de salida.

    Figura 1: SVG de outputs/figures/figure1_interactive.html (s03b), impreso a
              PDF con Edge/Chrome headless (vectorial, fuentes incrustadas).
    Figura 2: s05_nca.plot_ceiling_lines sobre los compuestos de survey_clean.csv.
    Figura 3: s06_multilevel.plot_blups sobre
              outputs/tables/blups_DES_estructural_SOS_ambiental.csv.

Salida: outputs/figures/vector/Figure_1.pdf, Figure_2.pdf, Figure_3.pdf
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.figure
import pandas as pd

import config as cfg
from _common import compute_composites

OUT = ROOT / "outputs" / "figures" / "vector"
OUT.mkdir(parents=True, exist_ok=True)
matplotlib.rcParams["pdf.fonttype"] = 42   # fuentes TrueType incrustadas
matplotlib.rcParams["ps.fonttype"] = 42

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def redirect_savefig(target: Path):
    """Las funciones del pipeline guardan PNG en outputs/figures; aquí se
    redirige ese savefig a un PDF vectorial en la carpeta de envío."""
    original = matplotlib.figure.Figure.savefig

    def _save(self, *args, **kwargs):
        original(self, target, format="pdf", bbox_inches="tight")
        print(f"  -> {target.relative_to(ROOT)}")
    matplotlib.figure.Figure.savefig = _save
    return original


def figure1():
    html = (cfg.OUT_FIGURES / "figure1_interactive.html").read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    svg = re.search(r"<svg\b.*?</svg>", html, re.S).group(0)
    w, h = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups()
    page = (f"<!doctype html><html><head><meta charset='utf-8'><style>{style}"
            f"@page {{ size: {w}px {h}px; margin: 0; }} html, body {{ margin: 0; padding: 0; }}"
            f".viz-root {{ padding: 0 !important; display: block !important; }}</style></head>"
            f"<body><div class='viz-root'>{svg}</div></body></html>")
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        raise SystemExit("Se requiere Edge o Chrome para exportar la Figura 1.")
    target = OUT / "Figure_1.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "figure1.html"
        src.write_text(page, encoding="utf-8")
        subprocess.run([browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={target}", src.as_uri()], capture_output=True, timeout=120)
    if not target.exists():
        raise SystemExit("No se pudo generar Figure_1.pdf")
    print(f"  -> {target.relative_to(ROOT)}")


def figure2():
    from s05_nca import plot_ceiling_lines
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))
    original = redirect_savefig(OUT / "Figure_2.pdf")
    try:
        plot_ceiling_lines(df, df[cfg.NCA_OUTCOME].values)
    finally:
        matplotlib.figure.Figure.savefig = original


def figure3():
    from s06_multilevel import plot_blups
    blups = pd.read_csv(cfg.OUT_TABLES / "blups_DES_estructural_SOS_ambiental.csv", index_col=0)
    fe_slope = float((blups["slope_total"] - blups["slope_deviation"]).iloc[0])
    original = redirect_savefig(OUT / "Figure_3.pdf")
    try:
        plot_blups(blups, fe_slope)
    finally:
        matplotlib.figure.Figure.savefig = original


if __name__ == "__main__":
    print("Exportando figuras vectoriales:")
    figure1()
    figure2()
    figure3()
