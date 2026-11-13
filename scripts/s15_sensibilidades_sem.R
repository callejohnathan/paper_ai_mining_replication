# s15_sensibilidades_sem.R — Ronda 20, pasos F-a4 y F-a5 (S1: ambos análisis).
#
# Dos sensibilidades del modelo estructural corregido (s03e), para el suplemento:
#
# A. WLSMV: los ítems Likert se tratan como ordinales (correlaciones
#    policóricas). La vulnerabilidad sigue como phantom continuo. Sin la
#    restricción Heywood de DES_2 (bajo WLSMV las varianzas residuales de los
#    ítems ordinales no son parámetros libres). Errores estándar cluster-robustos
#    cluster-robustos por vereda si lavaan los admite con este estimador; si no,
#    se reportan los ingenuos y se indica en la columna `se_tipo`.
#
# B. External separado: autoridad ambiental (GOB_2 POMCA de Cornare, GOB_7
#    acciones de Cornare) y municipio (GOB_8, un solo ítem, como phantom con
#    varianza residual 0, es decir, sin error de medición modelado). Mismo
#    estimador (ML), restricción Heywood y p cluster-robusto t(14) que s03e.
#
# Salidas:
#   outputs/tables/tableS_sem_wlsmv.csv
#   outputs/tables/tableS_sem_external_separado.csv

suppressPackageStartupMessages(library(lavaan))
df <- read.csv("data/processed/survey_clean.csv", stringsAsFactors = FALSE)

outcomes <- c("DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia")
medicion_base <- '
  GOB_empresa =~ GOB_1 + GOB_6 + GOB_11 + GOB_12 + GOB_13
  GOB_confianza =~ GOB_9 + GOB_10
  SOS_ambiental =~ SOS_3 + SOS_4 + SOS_5
  DES_relacional =~ DES_5 + DES_6 + DES_7
  DES_regulacion =~ DES_12 + DES_13 + DES_14
  DES_estructural =~ DES_1 + DES_3
  DES_agencia =~ DES_2 + DES_9
  VUL =~ 1*vulnerabilidad_hidrica
  vulnerabilidad_hidrica ~~ 0*vulnerabilidad_hidrica
'
estr <- function(preds) paste(sprintf("%s ~ %s", outcomes, paste(preds, collapse = " + ")), collapse = "\n")

tabla <- function(fit_n, fit_c, preds) {
  pn <- parameterEstimates(fit_n, standardized = TRUE)
  sel <- pn$op == "~" & pn$lhs %in% outcomes
  out <- data.frame(outcome = pn$lhs[sel], predictor = pn$rhs[sel], beta = round(pn$std.all[sel], 3),
                    p_ingenuo = signif(pn$pvalue[sel], 3))
  if (!is.null(fit_c)) {
    pc <- parameterEstimates(fit_c, standardized = TRUE)
    selc <- pc$op == "~" & pc$lhs %in% outcomes
    stopifnot(all(pc$lhs[selc] == out$outcome), all(pc$rhs[selc] == out$predictor))
    z <- qnorm(1 - pc$pvalue[selc] / 2)
    out$p_cluster_t14 <- signif(2 * pt(-abs(z), 14), 3)
    out$q_bh <- signif(p.adjust(out$p_cluster_t14, "BH"), 3)
  }
  out$predictor[out$predictor == "VUL"] <- "vulnerabilidad_hidrica"
  out
}

# --- A. WLSMV ---------------------------------------------------------------
items <- c("GOB_1","GOB_6","GOB_11","GOB_12","GOB_13","GOB_9","GOB_10","GOB_2","GOB_7","GOB_8",
           "SOS_3","SOS_4","SOS_5","DES_5","DES_6","DES_7","DES_12","DES_13","DES_14",
           "DES_1","DES_3","DES_2","DES_9")
mA <- paste(medicion_base, "GOB_externo =~ GOB_2 + GOB_7 + GOB_8\n",
            estr(c("GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental", "VUL")))
avisos_A <- character(0)
fitA <- withCallingHandlers(sem(mA, data = df, ordered = items, estimator = "WLSMV"),
                            warning = function(w) { avisos_A <<- c(avisos_A, conditionMessage(w)); invokeRestart("muffleWarning") })
# CORREGIDO 2026-11-13 (ronda 21, H1): antes, tryCatch(..., warning = function(w) NULL)
# descartaba el ajuste cluster-robusto ante cualquier advertencia, y el modelo
# ordinal siempre advierte (correlación ~1 entre DES_5 y DES_6). Ahora las
# advertencias se registran sin descartar el ajuste; solo un error lo descarta.
avisos_Ac <- character(0)
fitAc <- tryCatch(
  withCallingHandlers(sem(mA, data = df, ordered = items, estimator = "WLSMV", cluster = "Vereda"),
                      warning = function(w) { avisos_Ac <<- c(avisos_Ac, conditionMessage(w)); invokeRestart("muffleWarning") }),
  error = function(e) NULL)
if (!is.null(fitAc) && !lavInspect(fitAc, "converged")) fitAc <- NULL
tA <- tabla(fitA, fitAc)
tA$se_tipo <- if (is.null(fitAc)) "ingenuo (el ajuste cluster-robusto no convergió)" else "cluster-robusto t(14)"
tA$converge <- lavInspect(fitA, "converged")
tA$avisos <- paste(unique(gsub("\\s+", " ", sub("^lavaan->[^:]*:\\s*", "", c(avisos_A, avisos_Ac)))), collapse = " | ")
write.csv(tA, "outputs/tables/tableS_sem_wlsmv.csv", row.names = FALSE)
cat("=== A. WLSMV ===\n"); print(tA, row.names = FALSE)
cat("\nAvisos de lavaan (WLSMV):\n"); print(unique(substr(avisos_A, 1, 200)))
fmA <- fitMeasures(fitA, c("chisq.scaled", "df.scaled", "cfi.scaled", "tli.scaled", "rmsea.scaled", "srmr"))
print(round(fmA, 3))

# --- B. External separado ---------------------------------------------------
mB <- paste(medicion_base, '
  DES_2 ~~ 0.05*DES_2
  EXT_autoridad =~ GOB_2 + GOB_7
  EXT_municipio =~ 1*GOB_8
  GOB_8 ~~ 0*GOB_8
', estr(c("GOB_empresa", "GOB_confianza", "EXT_autoridad", "EXT_municipio", "SOS_ambiental", "VUL")))
fitB <- suppressWarnings(sem(mB, data = df))
fitBc <- suppressWarnings(sem(mB, data = df, cluster = "Vereda"))
stopifnot(lavInspect(fitB, "converged"), lavInspect(fitBc, "converged"))
tB <- tabla(fitB, fitBc)
write.csv(tB, "outputs/tables/tableS_sem_external_separado.csv", row.names = FALSE)
cat("\n=== B. External separado ===\n"); print(tB[tB$predictor %in% c("EXT_autoridad", "EXT_municipio"), ], row.names = FALSE)
cl <- lavInspect(fitB, "cor.lv")
cat("\nCorrelación latente autoridad ambiental - municipio:", round(cl["EXT_autoridad", "EXT_municipio"], 3), "\n")
print(round(fitMeasures(fitB, c("chisq", "df", "cfi", "tli", "rmsea", "srmr")), 3))
