# s11_precision_coeficientes.R — Ronda 17, paso E (medición).
#
# ¿El resultado nulo de External Institution Trust es evidencia de ausencia de
# relación o solo falta de precisión? Para cada ruta del modelo estructural
# corregido (s03e, vulnerabilidad como phantom), calcula:
#   - IC 95 % del beta estandarizado con EE cluster-robusto por vereda y
#     referencia t(14) (la misma inferencia de la Tabla 4);
#   - efecto mínimo detectable con potencia .80 y alfa .05 bilateral:
#     MDE = (t_.975(14) + t_.80(14)) * EE.
#
# Salida: outputs/tables/table_r17_precision_coeficientes.csv

suppressPackageStartupMessages(library(lavaan))
df <- read.csv("data/processed/survey_clean.csv", stringsAsFactors = FALSE)

# Mismo modelo que s03e (corregido 2026-11-10)
src <- readLines("scripts/s03e_single_estimator_heywood_fixed.R", encoding = "UTF-8")
ini <- grep("^model <- '", src); fin <- which(src == "'")[which(src == "'") > ini][1]
eval(parse(text = src[ini:fin]))

fit <- sem(model, data = df, cluster = "Vereda")
stopifnot(lavInspect(fit, "converged"))
ss <- standardizedSolution(fit)
outcomes <- c("DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia")
s <- ss[ss$op == "~" & ss$lhs %in% outcomes, c("lhs", "rhs", "est.std", "se")]
s$rhs[s$rhs == "VUL"] <- "vulnerabilidad_hidrica"

tc <- qt(.975, 14); tp <- qt(.80, 14)
s$ic_inf <- s$est.std - tc * s$se
s$ic_sup <- s$est.std + tc * s$se
s$p_t14 <- 2 * pt(-abs(s$est.std / s$se), 14)
s$MDE_80 <- (tc + tp) * s$se
s[, -(1:2)] <- round(s[, -(1:2)], 3)
names(s)[1:4] <- c("outcome", "predictor", "beta", "se_cluster")
s <- s[order(s$predictor, s$outcome), ]
write.csv(s, "outputs/tables/table_r17_precision_coeficientes.csv", row.names = FALSE)
options(width = 200); print(s, row.names = FALSE)
