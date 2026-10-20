# r_cluster_robust_sem.R
#
# Reajusta el CB-SEM completo (modelo de medida + estructural) con errores
# estandar robustos al cluster (vereda) usando el sandwich estimator nativo
# de lavaan (cluster=). Esto es la verificacion "gold standard" del hallazgo
# de la ronda 8 (bootstrap por cluster + correccion de Kish en Python), que
# sugeria que la mayoria de los paths del CB-SEM pierden significancia bajo
# ajuste por cluster.
#
# Salida: outputs/tables/table4_cluster_robust_lavaan.csv

library(lavaan)

df <- read.csv("data/processed/survey_clean.csv", stringsAsFactors = FALSE)

model <- '
  GOB_empresa =~ GOB_1 + GOB_6 + GOB_11 + GOB_12 + GOB_13
  GOB_confianza =~ GOB_9 + GOB_10
  GOB_externo =~ GOB_2 + GOB_7 + GOB_8
  SOS_ambiental =~ SOS_3 + SOS_4 + SOS_5
  DES_relacional =~ DES_5 + DES_6 + DES_7
  DES_regulacion =~ DES_12 + DES_13 + DES_14
  DES_estructural =~ DES_1 + DES_3
  DES_agencia =~ DES_2 + DES_9

  DES_relacional ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
  DES_regulacion ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
  DES_estructural ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
  DES_agencia ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
'

# --- 1) Ajuste naive (sin cluster) para comparar contra semopy/Python ---
fit_naive <- sem(model, data = df, std.lv = FALSE)
cat("=== Ajuste naive (lavaan, sin cluster) ===\n")
print(fitMeasures(fit_naive, c("chi.square", "df", "cfi", "tli", "rmsea", "srmr")))

# --- 2) Ajuste con errores estandar robustos al cluster (sandwich estimator) ---
fit_cluster <- sem(model, data = df, cluster = "Vereda", std.lv = FALSE)
cat("\n=== Ajuste con errores estandar robustos al cluster (Vereda) ===\n")
print(fitMeasures(fit_cluster, c("chi.square", "df", "cfi", "tli", "rmsea", "srmr")))

# --- 3) Comparacion de coeficientes estructurales, SE y p-valores ---
pe_naive <- parameterEstimates(fit_naive, standardized = TRUE)
pe_cluster <- parameterEstimates(fit_cluster, standardized = TRUE)

outcomes <- c("DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia")
predictors <- c("GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental", "vulnerabilidad_hidrica")

struct_naive <- pe_naive[pe_naive$op == "~" & pe_naive$lhs %in% outcomes & pe_naive$rhs %in% predictors, ]
struct_cluster <- pe_cluster[pe_cluster$op == "~" & pe_cluster$lhs %in% outcomes & pe_cluster$rhs %in% predictors, ]

merged <- merge(struct_naive[, c("lhs", "rhs", "std.all", "se", "pvalue")],
                 struct_cluster[, c("lhs", "rhs", "se", "pvalue")],
                 by = c("lhs", "rhs"), suffixes = c("_naive", "_cluster"))
merged$sig_naive <- merged$pvalue_naive < 0.05
merged$sig_cluster <- merged$pvalue_cluster < 0.05
merged$cambia <- merged$sig_naive & !merged$sig_cluster
merged <- merged[order(-merged$cambia, merged$pvalue_cluster), ]

cat("\n=== Comparacion final: naive vs. robusto al cluster (lavaan, sandwich estimator) ===\n")
print(merged, row.names = FALSE)

write.csv(merged, "outputs/tables/table4_cluster_robust_lavaan.csv", row.names = FALSE)
cat("\nPaths donde la significancia CAMBIA (naive sig, cluster-robusto no):",
    sum(merged$cambia), "de", nrow(merged), "\n")

# --- 4) Nota (docs/decisiones_auditoria_20261015.md, punto 2) ---------------
# lavaan reporta pvalue_cluster con referencia NORMAL (z = est/se, sin importar
# cuantos clusteres haya). Con solo 15 clusteres (veredas) eso es anticonservador
# -- ver scripts/s03c_cluster_robust_t14.py, que recupera el z exacto desde este
# CSV y aplica una referencia t(14) (Cameron & Miller 2015) sin necesitar volver
# a correr lavaan. Si se corre este script en una maquina con R, el equivalente
# nativo es ajustar con `lavTestScore`/`parameterEstimates(..., )` pasando un
# objeto con grados de libertad t(G-1) en vez de usar el z por defecto -- lavaan
# no expone esa opcion directamente para el sandwich estimator, por eso se usa
# la correccion post-hoc del script s03c.
