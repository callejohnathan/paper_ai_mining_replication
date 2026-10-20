# Replication materials — Fragmented Trust, Uneven Returns

Analysis code and results for:

> Polanco, J.-A., Calle Gallego, J. M., & Hernández-Díaz, P. M. *Fragmented
> Trust, Uneven Returns: A Mixed-Methods Analysis of Water Governance and
> Socio-Ecological System Performance in Gold-Mining Territories.* Submitted to
> *Resources Policy*.

The study combines covariance-based structural equation modelling (CB-SEM),
fuzzy-set qualitative comparative analysis (fsQCA), necessary condition
analysis (NCA) and multilevel models on a household survey (N = 980) in 15
veredas (rural districts) of a gold-mining territory in Antioquia, Colombia.

## Contents

```
config.py              Central pipeline decisions: paths, excluded items, construct mapping
scripts/               Analysis pipeline (Python + R), numbered in execution order
outputs/tables/        CSV for every table and supplementary analysis in the paper
outputs/figures/       Figures 1–3 (PNG/JPG) and figure1_interactive.html
outputs/figures/vector Figures 1–3 as vector PDF (version submitted to the journal)
DATA_DICTIONARY.md     Variables the pipeline expects in the (non-distributed) dataset
```

## Data availability

The survey microdata and the questionnaire are **not included**. They contain
information on households in small rural communities and are subject to the
confidentiality terms of the informed consent and of the agreement under which
the data were collected. Researchers who wish to replicate the analysis may
request access from the corresponding author (Jorge-Andrés Polanco,
japolanco@udemedellin.edu.co); requests will be assessed case by case.

`DATA_DICTIONARY.md` documents the structure of the analysis dataset
(variable codes, scales and derived variables) so that the pipeline can be run
once access has been granted. All results reported in the paper are available
in `outputs/`.

## Map to the paper

| Paper | File(s) | Script |
|---|---|---|
| Table 2 — Sample descriptives | `table2_sample_descriptives.csv`, `table_n_por_vereda.csv` (count of `Vereda`) | `s02b` |
| Table 3 — Measurement model | `table3_measurement_model.csv`, `table3_fit_indices.csv`, `htmt_matrix.csv` | `s02` |
| Table 4 — Structural model | `table4_single_estimator*.csv` (reported), `table4_cluster_robust_*.csv` | `s03e`, `r_cluster_robust_sem.R`, `s03c` |
| Attenuation sensitivity | `table4b_attenuation_sensitivity.csv` | `s03d` |
| Table 5 — fsQCA | `table5_fsqca_configurations.csv`, `truth_table_full.csv` | `s04` |
| Table 6 — NCA | `table6_nca_effect_sizes.csv` | `s05` |
| Table 7 — Multilevel (ICC, random slopes) | `table7a_icc.csv`, `table7b_random_slopes.csv`, `blups_*.csv` | `s06` |
| Table 8 — Synthesis by governance actor | `table8_synthesis.csv` | `s07` |
| Figure 1 — Path diagram | `figure1_path_diagram.png`, `vector/Figure_1.pdf` | `s03b`, `s03f`, `s08` |
| Figure 2 — NCA ceiling lines | `figure2_nca_ceiling_lines.png`, `vector/Figure_2.pdf` | `s05`, `s08` |
| Figure 3 — Vereda-level slopes (BLUPs) | `figure3_blups_sustainability_structural.png`, `vector/Figure_3.pdf` | `s06`, `s08` |
| Item screening, EFA | `item_diagnostics.csv`, `efa_*.csv` | `s00`, `s01` |

Files whose names end in `_PAPER.jpg` are the figures exactly as they appear in
the manuscript. Variable and construct codes are in Spanish in the code and in
English in the paper; the correspondence is in `config.py`
(`MEASUREMENT_MODEL`, `STRUCTURAL_PREDICTORS_EN`) and in `DATA_DICTIONARY.md`.

## Running the pipeline

Requirements: Python 3.13 (`pip install -r requirements.txt`) and R ≥ 4.3 with
`lavaan`. Place the dataset at `data/raw/Datos Mineria objetivo 2.xlsx` and run
from the repository root:

```
python scripts/s00_load_clean.py              # item screening -> data/processed/survey_clean.csv
python scripts/s01_efa.py                     # exploratory factor analysis
python scripts/s02_cfa_measurement.py         # CFA: loadings, CR, AVE, HTMT (Table 3)
python scripts/s02b_sample_descriptives.py    # sample descriptives (Table 2)
python scripts/s03_structural_model.py        # CB-SEM in semopy (first estimation)
Rscript scripts/r_cluster_robust_sem.R        # CB-SEM in lavaan, cluster-robust SE by vereda
python scripts/s03c_cluster_robust_t14.py     # t(G-1) reference for cluster-robust p-values
python scripts/s03d_attenuation_sensitivity.py
Rscript scripts/s03e_single_estimator_heywood_fixed.R   # Table 4 as reported (single estimator)
python scripts/s03b_figure1_html.py           # Figure 1 (SVG/HTML rendered with headless Edge/Chrome)
python scripts/s03f_regenerate_figure1.py     # Figure 1 from the Table 4 estimates
python scripts/s04_fsqca.py                   # fsQCA (Table 5)
python scripts/s05_nca.py                     # NCA + Figure 2 (Table 6)
python scripts/s06_multilevel.py              # ICC, random slopes, BLUPs + Figure 3 (Table 7)
python scripts/s07_synthesis.py               # synthesis table (Table 8)
python scripts/s08_export_vector_figures.py   # vector PDFs of Figures 1–3
```

Random seed: 42 (`config.RANDOM_SEED`). Code comments are in Spanish; some
refer to the authors' internal audit log (`docs/…`), which is not part of this
deposit — the decisions themselves are documented in the comments and in the
paper.

## License

Code under the MIT License; tables and figures under CC BY 4.0. See `LICENSE`.

## How to cite

See `CITATION.cff`. Please cite both this deposit (DOI) and the article.
