"""
s18 — Ronda 20, paso F-b: Material suplementario del manuscrito reformulado.

Arma un .docx con las secciones S1–S5 que cita el manuscrito, leyendo todas las
cifras de outputs/tables/ (nada se escribe a mano):
    S1  Modelo estructural completo: β, EE cluster-robusto, IC 95 %, p, q (BH), Holm y efecto de diseño
    S2  Ocupación minera como covariable (SEM y multinivel)
    S3  fsQCA: calibración y grilla de robustez
    S4  Sensibilidades: estimador ordinal (WLSMV) y External separado (SEM y multinivel)
    S5  NCA: tamaños de efecto en las 4 facetas y figura de techos

Requiere python-docx. Uso:
    python scripts/s18_suplemento.py <salida.docx>
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs" / "tables"
LABEL = "Perceived Value of Trust and Transparency"
NOMBRE = {"GOB_empresa": "Company Trust", "GOB_confianza": LABEL, "GOB_externo": "External Institution Trust",
          "SOS_ambiental": "Environmental Sustainability", "vulnerabilidad_hidrica": "Water-Source Vulnerability",
          "VUL": "Water-Source Vulnerability", "mining": "Mining occupation",
          "EXT_autoridad": "External: environmental authority", "EXT_municipio": "External: municipality",
          "ext_autoridad": "External: environmental authority", "ext_municipio": "External: municipality",
          "DES_relacional": "Relational Performance", "DES_regulacion": "Ecological Regulation",
          "DES_estructural": "Structural Performance", "DES_agencia": "Individual Agency",
          "seguridad_hidrica": "Water-Source Security"}


def leer(n):
    with open(T / n, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f3(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    s = f"{v:.3f}"
    return ("-" + s[1:].replace("0.", ".", 1)) if s.startswith("-") else s.replace("0.", ".", 1)


def tabla(doc, titulo, cab, filas, nota=None):
    doc.add_paragraph(titulo).runs[0].bold = True
    t = doc.add_table(rows=1, cols=len(cab))
    t.style = "Table Grid"
    for c, h in zip(t.rows[0].cells, cab):
        c.text = h
        c.paragraphs[0].runs[0].bold = True
    for fila in filas:
        celdas = t.add_row().cells
        for c, v in zip(celdas, fila):
            c.text = str(v)
    for fila in t.rows:
        for c in fila.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.5)
    if nota:
        p = doc.add_paragraph(nota)
        p.runs[0].font.size = Pt(9)
    doc.add_paragraph()


def main():
    salida = Path(sys.argv[1])
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(11)
    doc.add_heading("Supplementary Material", 0)
    doc.add_paragraph("Water Governance Perceptions and Socio-Ecological Performance Across Gold-Mining Communities: "
                      "A Multilevel Mixed-Methods Analysis of Territorial Heterogeneity").italic = True
    doc.add_paragraph("All values are produced by the analysis scripts in the project repository; the script that "
                      "generates each table is named in its note.")

    # S1 ---------------------------------------------------------------
    doc.add_heading("S1. Structural model: full estimates", 1)
    doc.add_paragraph("Exploratory CB-SEM estimated with maximum likelihood in lavaan; Water-Source Vulnerability entered "
                      "as a single-indicator latent variable; DES_2 residual variance fixed to .05. p-values use "
                      "cluster-robust standard errors (15 veredas) against a t(14) reference; q-values (Benjamini–Hochberg) "
                      "and Holm-adjusted p-values are computed across the 20 paths. The 95% confidence interval uses the "
                      "cluster-robust standard error of the standardized coefficient and t(14). The design effect is the "
                      "ratio of the cluster-robust to the naive standard error.")
    t4 = {(r["lhs"], r["rhs"]): r for r in leer("table4_single_estimator.csv")}
    pr = {(r["outcome"], r["predictor"]): r for r in leer("table_r17_precision_coeficientes.csv")}
    de = {(r["lhs"], r["rhs"]): r for r in leer("tableS_efecto_diseno.csv")}
    filas = []
    for (o, p), r in sorted(t4.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        x, d = pr[(o, p)], de[(o, p)]
        filas.append([NOMBRE[o], NOMBRE[p], f3(r["beta"]), f3(x["se_cluster"]), f"[{f3(x['ic_inf'])}, {f3(x['ic_sup'])}]",
                      f3(r["p_cluster_t14"]), f3(r["q_bh"]), f3(r["p_holm"]), f"{float(d['deff']):.2f}"])
    tabla(doc, "Table S1. Standardized structural coefficients with uncertainty and multiplicity correction",
          ["Outcome", "Predictor", "β", "SE", "95% CI", "p", "q (BH)", "p (Holm)", "Design effect"], filas,
          "Sources: s03e_single_estimator_heywood_fixed.R, s11_precision_coeficientes.R, s16_efecto_diseno.R. "
          "p-values come from the unstandardized cluster-robust test; the interval uses the standardized standard error, "
          "so a path can show p slightly above or below .05 while its interval crosses or excludes zero.")

    # S2 ---------------------------------------------------------------
    doc.add_heading("S2. Mining occupation as a covariate", 1)
    doc.add_paragraph("Mining occupation (117 of 980 respondents) was added as a single-indicator latent covariate of the "
                      "four performance facets (model M1), and as a fixed effect in the multilevel models. Respondents "
                      "working in sugar-cane mills (trapiche, n = 80) are not counted as miners.")
    m = leer("table_r14_mining_lavaan.csv")
    tabla(doc, "Table S2a. Structural coefficients without (M0b) and with (M1) mining occupation",
          ["Outcome", "Predictor", "β M0b", "p M0b", "β M1", "p M1", "Change"],
          [[NOMBRE[r["outcome"]], NOMBRE[r["predictor"]], f3(r["beta.M0b"]) if r["beta.M0b"] != "NA" else "—",
            f3(r["p_t14.M0b"]) if r["p_t14.M0b"] != "NA" else "—", f3(r["beta.M1"]), f3(r["p_t14.M1"]),
            f3(r["cambio_M0b_M1"]) if r["cambio_M0b_M1"] != "NA" else "—"] for r in m],
          "Source: s09_mining_covariate_lavaan.R. M0b differs from Table 4 only in rounding; labels follow the revised construct names.")
    ic = leer("table_r14_mining_icc.csv")
    tabla(doc, "Table S2b. Intraclass correlations with and without mining occupation",
          ["Outcome", "ICC without mining", "ICC with mining", "b mining", "p mining"],
          [[NOMBRE[r["outcome"]], f3(r["ICC_sin_mining"]), f3(r["ICC_con_mining"]), f3(r["beta_mining"]), f3(r["p_mining"])] for r in ic],
          "Source: s09b_mining_covariate_multilevel.py. Random-slope tests with mining occupation: the same seven of sixteen "
          "slopes are heterogeneous at .05; after Benjamini–Hochberg correction, six (External Institution Trust → "
          "Ecological Regulation no longer passes).")

    # S3 ---------------------------------------------------------------
    doc.add_heading("S3. fsQCA calibration and robustness grid", 1)
    doc.add_paragraph("Conditions: Company Trust, Perceived Value of Trust and Transparency, External Institution Trust, "
                      "Environmental Sustainability. Outcomes: Structural Performance and Ecological Regulation, and their "
                      "absence. Main specification: anchors 2 / 3.25 / 4.5 on the 1–5 scale, consistency ≥ .80, PRI ≥ .70, "
                      "frequency ≥ 10. The grid crosses six calibrations (five sets of scale-based anchors and the "
                      "percentile-based calibration used in the originally submitted analysis), three consistency "
                      "thresholds (.75, .80, .85), three PRI thresholds (.50, .65, .70), three frequency thresholds "
                      "(5, 10, 20), two outcomes, and their absence: 648 specifications. Water-source security is excluded "
                      "as a condition because 98% of cases fall in the set under the scale-based anchors.")
    g = leer("tableS_fsqca_grilla.csv")
    resumen = defaultdict(Counter)
    for r in g:
        k = (r["anclas"], r["resultado"])
        resumen[k]["n"] += 1
        sol = r["solucion_intermedia"]
        if sol != "sin solución":
            resumen[k]["con"] += 1
            import re as _re
            for lab in ["ValueTrust", "Company", "External", "Sustainability"]:
                if _re.search(rf"(?<!~){lab}", sol):
                    resumen[k][lab] += 1
    filas = []
    for (a, res), c in sorted(resumen.items()):
        filas.append([a, NOMBRE.get(res.lstrip("~"), res) if not res.startswith("~") else "Absence of " + NOMBRE[res[1:]],
                      c["n"], c["con"], c["ValueTrust"], c["Company"], c["External"], c["Sustainability"]])
    tabla(doc, "Table S3. Robustness grid: specifications with a solution and conditions present in the intermediate solution",
          ["Calibration", "Outcome", "Specifications", "With solution", "Value of Trust & Transp.", "Company", "External", "Sustainability"],
          filas, "Source: s04c_fsqca_final.py; every specification is listed in outputs/tables/tableS_fsqca_grilla.csv.")

    # S4 ---------------------------------------------------------------
    doc.add_heading("S4. Sensitivity analyses", 1)
    w = leer("tableS_sem_wlsmv.csv")
    tabla(doc, "Table S4a. Structural coefficients with items treated as ordinal (WLSMV)",
          ["Outcome", "Predictor", "β", "p (t14)", "q (BH)"],
          [[NOMBRE[r["outcome"]], NOMBRE[r["predictor"]], f3(r["beta"]), f3(r["p_cluster_t14"]), f3(r["q_bh"])] for r in w],
          "Source: s15_sensibilidades_sem.R. Cluster-robust standard errors by vereda with a t(14) reference; "
          "Benjamini–Hochberg q-values across the 20 paths. Under this estimator six associations survive the correction, "
          "including Company Trust and Perceived Value of Trust and Transparency → Structural Performance. lavaan reports a "
          "correlation of nearly 1.0 between DES_5 and DES_6, negative estimated variances, and a non-positive-definite "
          "parameter covariance matrix, so this model is a sensitivity check, not a preferred specification.")
    e = leer("tableS_sem_external_separado.csv")
    tabla(doc, "Table S4b. Structural model with External Institution Trust split into its two components",
          ["Outcome", "Predictor", "β", "p (t14)", "q (BH)"],
          [[NOMBRE[r["outcome"]], NOMBRE[r["predictor"]], f3(r["beta"]), f3(r["p_cluster_t14"]), f3(r["q_bh"])] for r in e],
          "Source: s15_sensibilidades_sem.R. Environmental authority: GOB_2 (POMCA led by Cornare) and GOB_7 (Cornare "
          "actions to resolve water conflicts); municipality: GOB_8 (single item, modeled without measurement error). "
          "Latent correlation between the two components: .48. q-values are computed across the 24 paths of this model.")
    ms = leer("tableS_multinivel_external_separado.csv")
    tabla(doc, "Table S4c. Random-slope tests for External Institution Trust and its two components",
          ["Predictor", "Outcome", "Fixed slope", "LR", "p", "Heterogeneous (BH, 4 tests per predictor)", "Heterogeneous (BH, 12 tests)"],
          [[NOMBRE[r["condicion"]], NOMBRE[r["outcome"]], f3(r["pendiente_fija"]), f"{float(r['LR']):.2f}", f3(r["p"]),
            "Yes" if r["heterogenea_BH_en_su_familia"] == "True" else "No",
            "Yes" if r["heterogenea_BH_12_pruebas"] == "True" else "No"] for r in ms],
          "Source: s15b_external_separado_multinivel.py. Bivariate random-slope models; 50:50 χ²(1):χ²(2) mixture reference "
          "(Self & Liang, 1987). Benjamini–Hochberg correction is shown within the four tests of each predictor and across "
          "all twelve tests; the two environmental-authority slopes remain heterogeneous under both. Table 6 of the main "
          "text corrects across its own sixteen tests.")

    # S5 ---------------------------------------------------------------
    doc.add_heading("S5. Necessary Condition Analysis", 1)
    doc.add_paragraph("NCA (CE-FDH ceiling envelope) was run for each condition and each performance facet. With 980 "
                      "respondents and five-point scales, respondents combining the minimum value of a condition with the "
                      "maximum value of the outcome exist for almost every pair, so the empty upper-left area that NCA "
                      "requires to detect necessity is occupied and the effect size is zero by construction. NCA therefore "
                      "cannot discriminate between conditions in these data, and the main text does not use it.")
    n6 = leer("table6_nca_effect_sizes.csv")
    tabla(doc, "Table S5a. NCA effect sizes for Structural Performance (CE-FDH, as in the submitted analysis)",
          ["Condition", "d", "p (permutation, 1,000)"], [[r["condition"], f"{float(r['d']):.4f}", f3(r["p_permutation"])] for r in n6],
          "Source: s05_nca.py.")
    nt = leer("table_r17_nca_todas_facetas.csv")
    tabla(doc, "Table S5b. NCA effect sizes for every condition and facet, and number of respondents with the condition at its minimum and the outcome at its maximum",
          ["Outcome", "Condition", "d", "Respondents at (min, max)"],
          [[NOMBRE[r["outcome"]], NOMBRE[r["condition"]], f"{float(r['d']):.4f}", r["casos_x_min_y_max"]] for r in nt],
          "Source: s11b_medicion_items_nca.py.")
    fig = ROOT / "outputs" / "figures" / "figure2_nca_ceiling_lines.png"
    doc.add_picture(str(fig), width=Cm(16))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Figure S1. NCA ceiling lines (CE-FDH) against Structural Performance.").runs[0].italic = True

    doc.save(salida)
    # La plantilla de python-docx deja <w:zoom/> sin el atributo obligatorio w:percent;
    # Word lo tolera, pero el esquema OOXML no. Se completa con 100.
    import re
    import zipfile
    with zipfile.ZipFile(salida) as z:
        partes = {n: z.read(n) for n in z.namelist()}
    s = partes["word/settings.xml"].decode("utf-8")
    s = re.sub(r"<w:zoom(?![^>]*w:percent)([^>]*)/>", r'<w:zoom\1 w:percent="100"/>', s)
    partes["word/settings.xml"] = s.encode("utf-8")
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in partes.items():
            z.writestr(n, data)
    print(f"Suplemento guardado en {salida}")


if __name__ == "__main__":
    main()
