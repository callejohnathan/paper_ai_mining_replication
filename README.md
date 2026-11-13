# Replication materials — Water Governance Perceptions and Socio-Ecological Performance Across Gold-Mining Communities

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23504943.svg)](https://doi.org/10.5281/zenodo.23504943)

Analysis code and results for:

> Polanco, J.-A., Calle Gallego, J. M., & Hernández-Díaz, P. M. *Water Governance
> Perceptions and Socio-Ecological Performance Across Gold-Mining Communities: A
> Multilevel Mixed-Methods Analysis of Territorial Heterogeneity.*

The study combines confirmatory factor analysis, an exploratory covariance-based
structural equation model (CB-SEM) with cluster-robust inference and correction for
multiple testing, multilevel models with random slopes, and fuzzy-set qualitative
comparative analysis (fsQCA) as a robustness check, on a household survey (N = 980)
in 15 veredas (rural districts) of a gold-mining territory in Antioquia, Colombia.

**Version 2.0.0** accompanies the revised manuscript. Version 1.0.0
(https://doi.org/10.5281/zenodo.23504944) accompanies the originally submitted
manuscript (*Fragmented Trust, Uneven Returns*); see "Changes from version 1.0.0".

## Contents

```
config.py              Central pipeline decisions: paths, excluded items, construct mapping
scripts/               Analysis pipeline (Python + R)
outputs/tables/        CSV for every table and supplementary analysis
outputs/figures/       Figures of the revised manuscript and supplementary Figure S1
outputs/figures/vector Figure 2 as vector PDF
DATA_DICTIONARY.md     Variables the pipeline expects in the (non-distributed) dataset
```

## Data availability

The survey microdata and the questionnaire are **not included**. They contain
information on households in small rural communities and are subject to the
confidentiality terms of the informed consent and of the agreement under which
the data were collected. Researchers who wish to replicate the analysis may
request access from the corresponding author (Jorge-Andrés Polanco,
japolanco@udemedellin.edu.co); requests will be assessed case by case.

`DATA_DICTIONARY.md` documents the structure of the analysis dataset so that the
pipeline can be run once access has been granted. All results reported in the
article and its Supplementary Material are available in `outputs/`.

## Map to the article

Some file names keep the table numbering of version 1.0.0; the column "Article"
gives the numbering of the revised manuscript.

| Article | File(s) in `outputs/` | Script |
|---|---|---|
| Table 2 — Sample characteristics | `tables/table2_sample_descriptives.csv`, `tables/table_n_por_vereda.csv` | `s02b` |
| Table 3 — Measurement model (lavaan) | `tables/table3_measurement_lavaan.csv`, `tables/table3_fit_lavaan.csv` | `s19` |
| Item redundancy (Section 4.1.1: identical responses, κ) | `tables/table_r17_items_consecutivos.csv`, `tables/table_r22_kappa_pares_citados.csv` | `s11b` |
| Table 4 — Exploratory CB-SEM (β, p t(14), q BH, Holm) | `tables/table4_single_estimator.csv`, `tables/table4_single_estimator_fit.csv`, `tables/table4_single_estimator_r2.csv` | `s03e` |
| Figure 1 — Path diagram | `figures/figure1_path_diagram.png`, `figures/figure1_path_diagram.pdf`, `figures/figure1_interactive.html` | `s03b` |
| Sensitivity analyses (Section 4.1.2) | `tables/tableS_efecto_diseno.csv`, `tables/tableS_sem_wlsmv.csv`, `tables/tableS_sem_external_separado.csv`, `tables/table_r14_mining_lavaan*.csv` | `s16`, `s15`, `s09` |
| Table 5 — fsQCA robustness check | `tables/table5_fsqca_final.csv` | `s04c` (uses `s04b`) |
| Table 6 — ICC and random slopes | `tables/table7a_icc.csv`, `tables/table7b_random_slopes.csv` | `s06` |
| Water-source vulnerability between/within veredas; External split (Section 4.2.1) | `tables/table_r20_vulnerabilidad_entre_dentro.csv`, `tables/tableS_multinivel_external_separado.csv` | `s14`, `s15b` |
| Figure 2 — Vereda-level slopes (BLUPs) | `figures/figure2_blups_sustainability_structural.png`, `figures/vector/Figure_2.pdf`, `tables/blups_*.csv` | `s06` |
| Table 7 — Synthesis | assembled from the tables above (Table 4, Table 6, vulnerability decomposition, design effects, mining) | — |
| Supplementary S1 — Full structural estimates | `tables/table4_single_estimator.csv`, `tables/table_r17_precision_coeficientes.csv`, `tables/tableS_efecto_diseno.csv` | `s03e`, `s11`, `s16` |
| Supplementary S2 — Mining occupation | `tables/table_r14_mining_lavaan.csv`, `tables/table_r14_mining_icc.csv`, `tables/table_r14_mining_random_slopes.csv` | `s09`, `s09b` |
| Supplementary S3 — fsQCA grid (648 specifications) | `tables/tableS_fsqca_grilla.csv` | `s04c` |
| Supplementary S4 — WLSMV and split External | `tables/tableS_sem_wlsmv.csv`, `tables/tableS_sem_external_separado.csv`, `tables/tableS_multinivel_external_separado.csv` | `s15`, `s15b` |
| Supplementary S5 — NCA, Figure S1 | `tables/table6_nca_effect_sizes.csv`, `tables/table_r17_nca_todas_facetas.csv`, `figures/figureS1_nca_ceiling_lines.png` | `s05`, `s11b` |
| Supplementary Material document | built from the tables above | `s18` |
| Item screening, EFA | `tables/item_diagnostics.csv`, `tables/efa_*.csv` | `s00`, `s01` |

Files kept from version 1.0.0 for continuity, not reported in the revised article:
`table3_measurement_model.csv`, `table3_fit_indices.csv`, `htmt_matrix.csv` (`s02`, semopy);
`table4_structural_coefficients.csv`, `table4_fit_indices.csv`, `table4_r2.csv` (`s03`, semopy);
`table4_cluster_robust_*.csv` (`r_cluster_robust_sem.R`, `s03c`); `table4b_attenuation_sensitivity.csv` (`s03d`);
`table5_fsqca_configurations.csv`, `truth_table_full.csv` (`s04`); `table8_synthesis.csv` (`s07`);
`table_r12_mining_covariate_check.csv` (`s08_mining_covariate_check`, OLS approximation);
`table_r13_*.csv` (`s04b`, exploratory fsQCA grid with water-source security).

Variable and construct codes are in Spanish in the code and in English in the
article; the correspondence is in `config.py` (`MEASUREMENT_MODEL`,
`STRUCTURAL_PREDICTORS_EN`) and in `DATA_DICTIONARY.md`.

## Running the pipeline

Requirements: Python 3.13 (`pip install -r requirements.txt`) and R ≥ 4.3 with
`lavaan` (results produced with R 4.6.2 and lavaan 0.7.3). Place the dataset at
`data/raw/Datos Mineria objetivo 2.xlsx` and run from the repository root:

```
python scripts/s00_load_clean.py                    # item screening -> data/processed/survey_clean.csv
python scripts/s01_efa.py                           # exploratory factor analysis
python scripts/s02b_sample_descriptives.py          # Table 2
Rscript scripts/s19_medicion_lavaan.R               # Table 3 (CFA in lavaan)
python scripts/s11b_medicion_items_nca.py           # item redundancy (κ) and NCA for all facets
Rscript scripts/s03e_single_estimator_heywood_fixed.R   # Table 4 (exploratory CB-SEM, q and Holm)
python scripts/s03b_figure1_html.py                 # Figure 1 (HTML; PNG/PDF rendered from it)
Rscript scripts/s11_precision_coeficientes.R        # 95% CIs and minimum detectable effects (S1)
Rscript scripts/s16_efecto_diseno.R                 # design effects of clustering (S1)
Rscript scripts/s09_mining_covariate_lavaan.R       # mining occupation in the SEM (S2)
python scripts/s09b_mining_covariate_multilevel.py  # mining occupation in the multilevel models (S2)
Rscript scripts/s15_sensibilidades_sem.R            # WLSMV and split-External SEM (S4)
python scripts/s15b_external_separado_multinivel.py # split-External random slopes (S4)
python scripts/s06_multilevel.py                    # Table 6, BLUPs, Figure 2
python scripts/s14_vulnerabilidad_entre_dentro.py   # vulnerability between/within veredas
python scripts/s04c_fsqca_final.py                  # Table 5 and fsQCA grid (S3)
python scripts/s05_nca.py                           # NCA for Structural Performance, Figure S1 (S5)
python scripts/s18_suplemento.py <output.docx>      # Supplementary Material document
```

Random seed: 42 (`config.RANDOM_SEED`). Code comments are in Spanish; some refer to
the authors' internal audit log (`docs/…`), which is not part of this deposit — the
decisions themselves are documented in the comments and in the article. Figure 1 is
rendered from `figure1_interactive.html` by printing it to PDF in a browser; the
headless rendering in `s03b`/`s08` needs Edge or Chrome and may not work on every
system.

## Changes from version 1.0.0

- **Framing:** the article now centers on the territorial heterogeneity of
  governance–performance associations; the structural model is treated as
  exploratory and reported with Benjamini–Hochberg q-values and Holm-adjusted p-values.
- **Structural model (Table 4):** water-source vulnerability enters as a
  single-indicator latent variable, so its covariances with the latent factors are
  estimated rather than fixed at zero (Δχ² ≈ 96, 4 df).
- **Measurement model (Table 3):** re-estimated in lavaan with the same estimator as
  Table 4.
- **Construct label:** "Community Trust" is renamed "Perceived Value of Trust and
  Transparency", which describes its two items more accurately.
- **fsQCA:** Boolean minimization, all cases (no memberships at exactly 0.5),
  scale-based calibration anchors, PRI ≥ .70, two outcomes, and a 648-specification
  robustness grid; used as a robustness check.
- **NCA:** moved to the Supplementary Material (effect sizes are zero by construction
  for most condition–outcome pairs in these data).
- **New analyses:** mining occupation as a covariate, ordinal (WLSMV) estimation,
  External Institution Trust split into environmental authority and municipality,
  design effects of clustering, between/within decomposition of water-source
  vulnerability, and item-redundancy statistics.

## License

Code under the MIT License; tables and figures under CC BY 4.0. See `LICENSE`.

## How to cite

Please cite both this deposit and the article:

> Polanco, J.-A., Calle Gallego, J. M., & Hernández-Díaz, P. M. (2026).
> *Replication materials for: Water Governance Perceptions and Socio-Ecological
> Performance Across Gold-Mining Communities* (Version 2.0.0) [Software]. Zenodo.
> https://doi.org/10.5281/zenodo.23504943

`10.5281/zenodo.23504943` (concept DOI) always resolves to the latest version.
Zenodo assigns a version-specific DOI to each release; version 1.0.0 is
`10.5281/zenodo.23504944`. See also `CITATION.cff`.
