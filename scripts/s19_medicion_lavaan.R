# s19_medicion_lavaan.R — Ronda 21 (pendiente 4 del paso F): Tabla 3 con un solo estimador.
#
# La Tabla 3 del manuscrito (modelo de medición) venía de semopy (s02), mientras
# que la Tabla 4 se estima en lavaan. Este script estima la AFC de 8 factores en
# lavaan con el mismo estimador (ML) y la misma restricción Heywood de DES_2
# (varianza residual fijada en .05) que s03e, y calcula:
#   - ajuste: chi2, gl, CFI, TLI, RMSEA, SRMR;
#   - por constructo: número de ítems, rango de cargas estandarizadas,
#     CR = (sum lambda)^2 / ((sum lambda)^2 + sum(1 - lambda^2)) y AVE = mean(lambda^2);
#   - HTMT (Henseler et al., 2015) con correlaciones absolutas entre ítems.
#
# Salidas:
#   outputs/tables/table3_measurement_lavaan.csv
#   outputs/tables/table3_fit_lavaan.csv

suppressPackageStartupMessages(library(lavaan))
df <- read.csv("data/processed/survey_clean.csv", stringsAsFactors = FALSE)

bloques <- list(
  GOB_empresa = c("GOB_1", "GOB_6", "GOB_11", "GOB_12", "GOB_13"),
  GOB_confianza = c("GOB_9", "GOB_10"),
  GOB_externo = c("GOB_2", "GOB_7", "GOB_8"),
  SOS_ambiental = c("SOS_3", "SOS_4", "SOS_5"),
  DES_relacional = c("DES_5", "DES_6", "DES_7"),
  DES_regulacion = c("DES_12", "DES_13", "DES_14"),
  DES_estructural = c("DES_1", "DES_3"),
  DES_agencia = c("DES_2", "DES_9")
)
etiqueta <- c(GOB_empresa = "Company Trust", GOB_confianza = "Perceived Value of Trust and Transparency",
              GOB_externo = "External Institution Trust", SOS_ambiental = "Environmental Sustainability",
              DES_relacional = "Relational Performance", DES_regulacion = "Ecological Regulation",
              DES_estructural = "Structural Performance", DES_agencia = "Individual Agency")

modelo <- paste(c(sprintf("%s =~ %s", names(bloques), sapply(bloques, paste, collapse = " + ")),
                  "DES_2 ~~ 0.05*DES_2"), collapse = "\n")
fit <- sem(modelo, data = df)
stopifnot(lavInspect(fit, "converged"))

fm <- fitMeasures(fit, c("chisq", "df", "cfi", "tli", "rmsea", "srmr"))
ajuste <- data.frame(chi2 = round(fm["chisq"], 1), df = fm["df"], CFI = round(fm["cfi"], 3),
                     TLI = round(fm["tli"], 3), RMSEA = round(fm["rmsea"], 3), SRMR = round(fm["srmr"], 3))
write.csv(ajuste, "outputs/tables/table3_fit_lavaan.csv", row.names = FALSE)

ss <- standardizedSolution(fit)
cargas <- ss[ss$op == "=~", c("lhs", "rhs", "est.std")]
filas <- lapply(names(bloques), function(f) {
  l <- cargas$est.std[cargas$lhs == f]
  cr <- sum(l)^2 / (sum(l)^2 + sum(1 - l^2))
  data.frame(construct_es = f, construct_en = etiqueta[[f]], n_items = length(l),
             loading_min = round(min(l), 3), loading_max = round(max(l), 3),
             CR = round(cr, 3), AVE = round(mean(l^2), 3))
})
tabla <- do.call(rbind, filas)
tabla$below_threshold <- tabla$CR < .70 | tabla$AVE < .50

# HTMT con correlaciones absolutas entre ítems
R <- abs(cor(df[, unlist(bloques)], use = "pairwise.complete.obs"))
mono <- function(it) { if (length(it) < 2) return(1); m <- R[it, it]; mean(m[upper.tri(m)]) }
nombres <- names(bloques); htmt <- matrix(NA, length(nombres), length(nombres), dimnames = list(nombres, nombres))
for (i in seq_along(nombres)) for (j in seq_along(nombres)) if (i < j) {
  a <- bloques[[i]]; b <- bloques[[j]]
  htmt[i, j] <- mean(R[a, b]) / sqrt(mono(a) * mono(b))
}
tabla$htmt_max_con_otros <- sapply(nombres, function(f) round(max(c(htmt[f, ], htmt[, f]), na.rm = TRUE), 3))
write.csv(tabla, "outputs/tables/table3_measurement_lavaan.csv", row.names = FALSE)

options(width = 200)
cat("=== Ajuste (lavaan, ML, Heywood DES_2 fijado) ===\n"); print(ajuste, row.names = FALSE)
cat("\n=== Tabla 3 ===\n"); print(tabla, row.names = FALSE)
cat("\nHTMT máximo:", round(max(htmt, na.rm = TRUE), 3), "\n")
