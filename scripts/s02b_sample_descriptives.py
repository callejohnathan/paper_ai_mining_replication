"""
s02b — Descriptivos de la muestra (Tabla 2 del paper: N, género, acueducto,
actividad, vereda, fuente de agua agrupada).

Salida:
    outputs/tables/table2_sample_descriptives.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import config as cfg


def main():
    df = pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv")
    n = len(df)

    rows = [{"grupo": "Muestra", "categoria": "N total", "n": n, "pct": 100.0}]
    rows.append({"grupo": "Muestra", "categoria": "N veredas", "n": df["Vereda"].nunique(), "pct": None})

    for grupo, col in [("Género", "Responde"), ("Acueducto", "Acueducto"), ("Actividad", "Actividad")]:
        for cat, cnt in df[col].value_counts().items():
            rows.append({"grupo": grupo, "categoria": cat, "n": cnt, "pct": round(cnt / n * 100, 1)})

    for cat, cnt in df["fuente_cat"].value_counts().items():
        rows.append({"grupo": "Fuente de agua", "categoria": cat, "n": cnt, "pct": round(cnt / n * 100, 1)})

    table2 = pd.DataFrame(rows)
    table2.to_csv(cfg.OUT_TABLES / "table2_sample_descriptives.csv", index=False)
    print("Tabla 2 — Descriptivos de la muestra:")
    print(table2.to_string(index=False))


if __name__ == "__main__":
    main()
