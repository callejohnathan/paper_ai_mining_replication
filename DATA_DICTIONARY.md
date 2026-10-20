# Data dictionary

The dataset is not distributed (see `README.md`, "Data availability"). This
file describes the analysis dataset `data/processed/survey_clean.csv`, which
`scripts/s00_load_clean.py` builds from the raw survey file. One row per
respondent (N = 980 households, 15 veredas).

## Survey items

All items are 5-point Likert scales (1 = lowest, 5 = highest agreement /
trust / performance). Item wording is not published; items are identified by
block and position.

| Block | Items in the raw file | Retained | Excluded (reason in `config.EXCLUDED_ITEMS`) |
|---|---|---|---|
| `GOB` — water governance / trust | `GOB_1`–`GOB_14` | 12 | `GOB_3`, `GOB_4` |
| `SOS` — environmental sustainability | `SOS_1`–`SOS_5` | 3 | `SOS_1`, `SOS_2` |
| `DES` — socio-ecological system performance | `DES_1`–`DES_15` | 13 | `DES_8`, `DES_15` |

## Constructs (measurement model)

Composite scores are the simple mean of their items (`scripts/_common.py`).

| Code | Construct in the paper | Items |
|---|---|---|
| `GOB_empresa` | Company Trust | `GOB_1`, `GOB_6`, `GOB_11`, `GOB_12`, `GOB_13` |
| `GOB_confianza` | Community Trust | `GOB_9`, `GOB_10` |
| `GOB_externo` | External Institution Trust | `GOB_2`, `GOB_7`, `GOB_8` |
| `SOS_ambiental` | Environmental Sustainability | `SOS_3`, `SOS_4`, `SOS_5` |
| `DES_relacional` | Relational Performance | `DES_5`, `DES_6`, `DES_7` |
| `DES_regulacion` | Ecological Regulation | `DES_12`, `DES_13`, `DES_14` |
| `DES_estructural` | Structural Performance | `DES_1`, `DES_3` |
| `DES_agencia` | Individual Agency | `DES_2`, `DES_9` |

Retained items not assigned to any construct after the EFA (`GOB_5`, `GOB_14`,
`DES_4`, `DES_10`, `DES_11`) are kept in the file but not used in the models.

## Context and derived variables

| Variable | Type | Values / definition |
|---|---|---|
| `Vereda` | categorical | 15 veredas (cluster variable for multilevel and cluster-robust models) |
| `Actividad` | categorical | Respondent's main activity (household, agriculture, mining, trade, sugar-cane mill, livestock, other…) |
| `Responde` | categorical | Respondent's gender: `mujer`, `hombre` |
| `Acueducto` | categorical | Household connected to an aqueduct: `si`, `no` |
| `Fuente` | text | Household water source as recorded in the field |
| `fuente_cat` | categorical | `Fuente` recoded: `segura` (own/communal spring, formal), `informal`, `comprada` (purchased), `otro` |
| `vulnerabilidad_hidrica` | ordinal 0–2 | Water-Source Vulnerability: `segura`=0, `informal`/`otro`=1, `comprada`=2 |
| `seguridad_hidrica` | ordinal 0–2 | `2 − vulnerabilidad_hidrica`; Water-Source Security condition in fsQCA/NCA |
| `acueducto_si` | binary | 1 if `Acueducto == "si"` |
