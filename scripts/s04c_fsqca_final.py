"""
s04c — Ronda 20, paso F-a3: fsQCA final para el manuscrito reformulado.

Decisiones (docs/trazabilidad_reformulacion.md D3, D12; ronda 18 §3.5; ronda 19):
- Condiciones: Company Trust, Perceived Value of Trust and Transparency,
  External Institution Trust y Environmental Sustainability. Se SACA la
  seguridad de la fuente: con las anclas teóricas el 98 % de los casos queda
  "dentro", así que es casi constante y su presencia en una solución es trivial.
- Calibración con anclas fijadas por el significado de la escala Likert 1-5,
  no por el desempeño: 2 = en desacuerdo (fuera), 3,25 = por encima del punto
  neutro (cruce; ningún promedio de 2, 3 o 5 ítems vale 3,25, así que ningún
  caso queda en 0,5), 4,5 = de acuerdo (dentro).
- Dos resultados, reportados ambos: Structural Performance y Ecological
  Regulation (no se elige "el que mejor se comporte").
- Especificación principal: consistencia >= ,80, PRI >= ,70, frecuencia >= 10.
- Grilla completa al suplemento: 5 juegos de anclas teóricas + calibración por
  percentiles del manuscrito enviado, x consistencia {,75, ,80, ,85}
  x PRI {,50, ,65, ,70} x frecuencia {5, 10, 20} x 2 resultados x (Y, ~Y).

Reutiliza la minimización de s04b_fsqca_minimizado.py.

Salidas (outputs/tables/):
    table5_fsqca_final.csv          Tabla 5 del manuscrito (Y y ~Y, dos resultados)
    tableS_fsqca_grilla.csv         grilla de robustez para el suplemento
"""
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import config as cfg
from _common import compute_composites
import s04b_fsqca_minimizado as s

s.CONDS = ["GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental"]
s.LABEL["GOB_confianza"] = "ValueTrust"
OUTCOMES = ["DES_estructural", "DES_regulacion"]
ANCLAS_MAIN = (2, 3.25, 4.5)
ANCLAS = [(2, 3.25, 4.5), (1.5, 3.25, 4.5), (2, 3.1, 4.5), (2.5, 3.75, 4.75), (2, 3.4, 4.8)]


def calibrar(df, anclas):
    """anclas = tupla teórica, o 'p10-50-90' para la calibración del manuscrito enviado."""
    fs = {}
    for c in s.CONDS + OUTCOMES:
        x = df[c].values.astype(float)
        if anclas == "p10-50-90":
            out, cross, inn = np.percentile(x, [10, 50, 90])
            if inn <= cross:
                return None
            m = s.sigmoide(x, out, cross, inn)
        else:
            m = s.sigmoide(x, *anclas)
        fs[c] = np.where(np.isclose(m, 0.5), 0.501, m)
    return fs


def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))

    # --- especificación principal (Tabla 5) ---
    fs = calibrar(df, ANCLAS_MAIN)
    filas = []
    for y_name in OUTCOMES:
        for negado in (False, True):
            y = 1 - fs[y_name] if negado else fs[y_name]
            etq = ("~" if negado else "") + y_name
            _, res = s.analizar(fs, y, 0.80, 0.70, 10, expectativa=0 if negado else 1)
            if res is None:
                filas.append({"resultado": etq, "termino": "ninguna configuración supera los umbrales"})
                continue
            inter, pars = res["intermedia"][0], res["parsimoniosa"][0]
            terms, glob = s.metricas_solucion(inter, fs, y)
            for t, tr in zip(inter, terms):
                nuc = s.nucleo(t, pars)
                filas.append({"resultado": etq, **tr,
                              "nucleo": "; ".join(f"{'~' if v == 0 else ''}{s.LABEL[c]}" for c, (e, v) in nuc.items() if e == "núcleo"),
                              "periferica": "; ".join(f"{'~' if v == 0 else ''}{s.LABEL[c]}" for c, (e, v) in nuc.items() if e != "núcleo"),
                              "sol_consistencia": glob["consistencia"], "sol_PRI": glob["PRI"],
                              "sol_cobertura": glob["cobertura"], "filas_positivas": res["n_pos"],
                              "modelos_alternativos": len(res["intermedia"])})
    t5 = pd.DataFrame(filas).round(3)
    t5.to_csv(cfg.OUT_TABLES / "table5_fsqca_final.csv", index=False)

    # consistencia de cada actor combinado con sostenibilidad (para el texto)
    print("Consistencia de X*Sustainability (anclas principales):")
    for y_name in OUTCOMES:
        for a in ["GOB_empresa", "GOB_confianza", "GOB_externo"]:
            x = np.minimum(fs[a], fs["SOS_ambiental"])
            c_, p_, cv = s.metricas(x, fs[y_name])
            print(f"  {y_name:16s} {s.LABEL[a]:11s}*Sust  cons={c_:.3f} PRI={p_:.3f} cob={cv:.3f}")

    # --- grilla para el suplemento ---
    grid = []
    for anclas in ANCLAS + ["p10-50-90"]:
        fs = calibrar(df, anclas)
        if fs is None:
            continue
        for y_name in OUTCOMES:
            for negado in (False, True):
                y = 1 - fs[y_name] if negado else fs[y_name]
                for cons, pri, freq in product([0.75, 0.80, 0.85], [0.50, 0.65, 0.70], [5, 10, 20]):
                    _, res = s.analizar(fs, y, cons, pri, freq, expectativa=0 if negado else 1)
                    reg = {"anclas": anclas if isinstance(anclas, str) else "/".join(map(str, anclas)),
                           "resultado": ("~" if negado else "") + y_name, "cons": cons, "PRI_min": pri, "freq": freq}
                    if res is None:
                        grid.append({**reg, "solucion_intermedia": "sin solución"})
                        continue
                    inter = res["intermedia"][0]
                    _, glob = s.metricas_solucion(inter, fs, y)
                    grid.append({**reg, "solucion_intermedia": " + ".join(s.nombre(t) for t in inter),
                                 "parsimoniosa": " + ".join(s.nombre(t) for t in res["parsimoniosa"][0]),
                                 "sol_consistencia": round(glob["consistencia"], 3), "sol_PRI": round(glob["PRI"], 3),
                                 "sol_cobertura": round(glob["cobertura"], 3)})
    g = pd.DataFrame(grid)
    g.to_csv(cfg.OUT_TABLES / "tableS_fsqca_grilla.csv", index=False)

    pd.set_option("display.width", 250, "display.max_colwidth", 80)
    print("\nTabla 5:\n", t5.drop(columns=["modelos_alternativos"], errors="ignore").to_string(index=False))
    ok = g[g.solucion_intermedia != "sin solución"]
    print(f"\nGrilla: {len(g)} especificaciones, {len(ok)} con solución.")
    for y_name in OUTCOMES:
        sub = ok[ok.resultado == y_name]
        for lab in ["ValueTrust", "Company", "External", "Sustainability"]:
            pres = sub.solucion_intermedia.str.contains(rf"(?<!~){lab}").sum()
            print(f"  {y_name}: {lab} presente en {pres} de {len(sub)}")


if __name__ == "__main__":
    main()
