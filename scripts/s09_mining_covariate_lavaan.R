# s09_mining_covariate_lavaan.R — Ronda 14, paso C del plan de la ronda 12.
#
# Ocupación minera como covariable en el modelo estructural definitivo (lavaan,
# Heywood de DES_2 fijado, p cluster-robusto con referencia t(14), como s03e).
#
# Hallazgo previo al paso C: en lavaan, un predictor OBSERVADO exógeno no se
# correlaciona con los factores LATENTES exógenos; esa covarianza queda fijada
# en 0 sin aviso. En s03e eso le pasa a `vulnerabilidad_hidrica`: la Tabla 4
# supone que la vulnerabilidad de la fuente no está correlacionada con Company,
# Community, External ni Sustainability. Para controlar de verdad, cada
# predictor observado se convierte en latente de un solo indicador (phantom:
# carga 1, varianza residual 0), y así lavaan libera sus covarianzas.
#
# Modelos:
#   M0  = s03e tal cual (reproduce la Tabla 4)
#   M0b = M0 con vulnerabilidad como phantom (covarianzas libres)
#   M1  = M0b + minería (Actividad == "mineria") como phantom sobre los 4 resultados
#
# Advertencia esperada: lavaan avisa que la vcov "no parece definida positiva"
# con un autovalor mínimo del orden de -1e-13. Es cero numérico, producto de
# fijar en 0 la varianza residual de los indicadores phantom; no es un problema
# de identificación.
#
# Salidas:
#   outputs/tables/table_r14_mining_lavaan.csv      coeficientes de M0, M0b y M1
#   outputs/tables/table_r14_mining_lavaan_fit.csv  ajuste y R2 por modelo
#   outputs/tables/table_r14_mining_lavaan_cor.csv  correlaciones de minería y vulnerabilidad con los factores (M1)

suppressPackageStartupMessages(library(lavaan))

df <- read.csv("data/processed/survey_clean.csv", stringsAsFactors = FALSE)
df$mining <- as.integer(df$Actividad == "mineria")

medicion <- '
  GOB_empresa =~ GOB_1 + GOB_6 + GOB_11 + GOB_12 + GOB_13
  GOB_confianza =~ GOB_9 + GOB_10
  GOB_externo =~ GOB_2 + GOB_7 + GOB_8
  SOS_ambiental =~ SOS_3 + SOS_4 + SOS_5
  DES_relacional =~ DES_5 + DES_6 + DES_7
  DES_regulacion =~ DES_12 + DES_13 + DES_14
  DES_estructural =~ DES_1 + DES_3
  DES_agencia =~ DES_2 + DES_9
  DES_2 ~~ 0.05*DES_2
'
phantom_vul <- '
  VUL =~ 1*vulnerabilidad_hidrica
  vulnerabilidad_hidrica ~~ 0*vulnerabilidad_hidrica
'
phantom_min <- '
  MIN =~ 1*mining
  mining ~~ 0*mining
'
outcomes <- c("DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia")
estructural <- function(preds) {
  paste(sprintf("%s ~ %s", outcomes, paste(preds, collapse = " + ")), collapse = "\n")
}

base <- c("GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental")
modelos <- list(
  M0  = paste(medicion, estructural(c(base, "vulnerabilidad_hidrica"))),
  M0b = paste(medicion, phantom_vul, estructural(c(base, "VUL"))),
  M1  = paste(medicion, phantom_vul, phantom_min, estructural(c(base, "VUL", "MIN")))
)

renombrar <- c(VUL = "vulnerabilidad_hidrica", MIN = "mining")

coefs <- list(); ajustes <- list(); fits <- list()
for (nm in names(modelos)) {
  f_n <- sem(modelos[[nm]], data = df)
  f_c <- sem(modelos[[nm]], data = df, cluster = "Vereda")
  stopifnot(lavInspect(f_n, "converged"), lavInspect(f_c, "converged"))
  fits[[nm]] <- f_n
  pn <- parameterEstimates(f_n, standardized = TRUE)
  pc <- parameterEstimates(f_c, standardized = TRUE)
  sel <- function(p) p[p$op == "~" & p$lhs %in% outcomes, ]
  a <- sel(pn); b <- sel(pc)
  stopifnot(all(a$lhs == b$lhs), all(a$rhs == b$rhs))
  z <- qnorm(1 - b$pvalue / 2)
  coefs[[nm]] <- data.frame(modelo = nm, outcome = a$lhs,
                            predictor = ifelse(a$rhs %in% names(renombrar), renombrar[a$rhs], a$rhs),
                            beta = round(a$std.all, 3),
                            p_t14 = signif(2 * pt(-abs(z), df = 14), 3))
  r2 <- lavInspect(f_n, "rsquare")[outcomes]
  fm <- fitMeasures(f_n, c("chisq", "df", "cfi", "tli", "rmsea", "srmr"))
  ajustes[[nm]] <- data.frame(modelo = nm, as.list(round(fm, 3)),
                              as.list(setNames(round(r2, 3), paste0("R2_", outcomes))))
}

largo <- do.call(rbind, coefs)
ancho <- reshape(largo, idvar = c("outcome", "predictor"), timevar = "modelo", direction = "wide")
ancho$cambio_M0b_M1 <- round(ancho$beta.M1 - ancho$beta.M0b, 3)
ancho <- ancho[order(ancho$outcome, ancho$predictor), ]
write.csv(ancho, "outputs/tables/table_r14_mining_lavaan.csv", row.names = FALSE)
write.csv(do.call(rbind, ajustes), "outputs/tables/table_r14_mining_lavaan_fit.csv", row.names = FALSE)

# Correlaciones latentes de minería y vulnerabilidad con los factores (M1)
cl <- lavInspect(fits$M1, "cor.lv")
cors <- data.frame(factor = c(base, outcomes),
                   r_mining = round(cl["MIN", c(base, outcomes)], 3),
                   r_vulnerabilidad = round(cl["VUL", c(base, outcomes)], 3))
write.csv(cors, "outputs/tables/table_r14_mining_lavaan_cor.csv", row.names = FALSE)

options(width = 200)
cat("=== Coeficientes estandarizados y p cluster-robusto t(14) ===\n"); print(ancho, row.names = FALSE)
cat("\n=== Ajuste y R2 ===\n"); print(do.call(rbind, ajustes), row.names = FALSE)
cat("\n=== Correlaciones latentes (M1) ===\n"); print(cors, row.names = FALSE)
