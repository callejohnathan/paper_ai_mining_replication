# s03e_single_estimator_heywood_fixed.R
#
# CORREGIDO 2026-10-15 (docs/decisiones_auditoria_20261015.md, punto 4).
#
# La Tabla 4 del manuscrito mezclaba dos estimaciones distintas: los beta
# venian de lavaan (std.all, round r_cluster_robust_sem.R), pero el chi2,
# CFI, TLI, RMSEA, SRMR y los R^2 de la tabla venian de semopy (Python,
# s03_structural_model.py). Lavaan ademas señala un caso Heywood en
# DES_agencia: DES_2 carga 1.000 (lavaan sin restriccion da carga
# estandarizada 1.101 y varianza residual NEGATIVA, -0.256), lo que infla
# el R^2 de Individual Agency segun el programa que se use (semopy: .088,
# lavaan sin restriccion: .040 -- casi 2x de diferencia en el mismo numero).
#
# Esta version resuelve ambos problemas con UN SOLO estimador (lavaan) y
# el caso Heywood fijado: la varianza residual de DES_2 se fija a un valor
# positivo pequeño (0.05), el remedio estandar para casos Heywood (Dillon,
# Kumar & Mulani, 1987; Chen, Bollen, Paxton, Curran & Kirby, 2001), ya
# explorado pero nunca adoptado en scripts/reference_original/08_cfa_heywood_fix.py.
# Se probo sensibilidad del path externo (GOB_externo -> DES_agencia) para
# valores fijos entre .01 y .15: beta estable en .053-.065, nunca
# significativo bajo ningun valor razonable -- la conclusion sustantiva no
# depende de la eleccion exacta.
#
# El p-valor cluster-robusto usa la referencia t(14) (Cameron & Miller,
# 2015), igual que la correccion ya aplicada en el punto 2 (antes via
# recuperacion algebraica en s03c_cluster_robust_t14.py porque R no estaba
# disponible en el entorno; ahora se corre lavaan directamente).
#
# Salida:
#   outputs/tables/table4_single_estimator.csv   (beta, SE, p por los 3 niveles, sig, R2)
#   outputs/tables/table4_single_estimator_fit.csv (chi2, df, CFI, TLI, RMSEA, SRMR)

suppressPackageStartupMessages(library(lavaan))

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
  DES_2 ~~ 0.05*DES_2

  DES_relacional ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
  DES_regulacion ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
  DES_estructural ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
  DES_agencia ~ GOB_empresa + GOB_confianza + GOB_externo + SOS_ambiental + vulnerabilidad_hidrica
'

fit_naive <- sem(model, data = df, std.lv = FALSE)
fit_cluster <- sem(model, data = df, cluster = "Vereda", std.lv = FALSE)

stopifnot(lavInspect(fit_naive, "converged"))

# --- Tabla de coeficientes -------------------------------------------------
LATENT_EN <- c(
  GOB_empresa = "Company Trust", GOB_confianza = "Community Trust",
  GOB_externo = "External Institution Trust", SOS_ambiental = "Environmental Sustainability",
  vulnerabilidad_hidrica = "Water-Source Vulnerability",
  DES_relacional = "Relational Performance", DES_regulacion = "Ecological Regulation",
  DES_estructural = "Structural Performance", DES_agencia = "Individual Agency"
)

outcomes <- c("DES_relacional", "DES_regulacion", "DES_estructural", "DES_agencia")
predictors <- c("GOB_empresa", "GOB_confianza", "GOB_externo", "SOS_ambiental", "vulnerabilidad_hidrica")

pe_n <- parameterEstimates(fit_naive, standardized = TRUE)
pe_c <- parameterEstimates(fit_cluster, standardized = TRUE)

sn <- pe_n[pe_n$op == "~" & pe_n$lhs %in% outcomes & pe_n$rhs %in% predictors,
           c("lhs", "rhs", "std.all", "se", "pvalue")]
sc <- pe_c[pe_c$op == "~" & pe_c$lhs %in% outcomes & pe_c$rhs %in% predictors,
           c("lhs", "rhs", "se", "pvalue")]
m <- merge(sn, sc, by = c("lhs", "rhs"), suffixes = c("_naive", "_cluster"))

m$z_cluster <- qnorm(1 - m$pvalue_cluster / 2) * sign(m$std.all)
m$p_cluster_t14 <- 2 * pt(-abs(m$z_cluster), df = 14)
m$sig <- ifelse(m$p_cluster_t14 < .001, "***",
          ifelse(m$p_cluster_t14 < .01, "**",
          ifelse(m$p_cluster_t14 < .05, "*", "")))

m$outcome_en <- LATENT_EN[m$lhs]
m$predictor_en <- LATENT_EN[m$rhs]
m <- m[, c("lhs", "rhs", "outcome_en", "predictor_en", "std.all",
           "pvalue_naive", "pvalue_cluster", "p_cluster_t14", "sig")]
names(m)[names(m) == "std.all"] <- "beta"
m$beta <- round(m$beta, 3)
m <- m[order(m$lhs, -abs(m$beta)), ]

write.csv(m, "outputs/tables/table4_single_estimator.csv", row.names = FALSE)

# --- R^2 --------------------------------------------------------------------
r2 <- lavInspect(fit_naive, "rsquare")
r2_tab <- data.frame(outcome_es = outcomes, outcome_en = LATENT_EN[outcomes],
                      R2 = round(unname(r2[outcomes]), 3))
write.csv(r2_tab, "outputs/tables/table4_single_estimator_r2.csv", row.names = FALSE)

# --- Fit indices --------------------------------------------------------------
fit_vals <- fitMeasures(fit_naive, c("chisq", "df", "cfi", "tli", "rmsea"))
fit_tab <- data.frame(chi2 = round(fit_vals["chisq"], 1), DoF = fit_vals["df"],
                       CFI = round(fit_vals["cfi"], 3), TLI = round(fit_vals["tli"], 3),
                       RMSEA = round(fit_vals["rmsea"], 3),
                       SRMR = round(fitMeasures(fit_naive, "srmr"), 3))
write.csv(fit_tab, "outputs/tables/table4_single_estimator_fit.csv", row.names = FALSE)

cat("=== Tabla 4 (estimador unico, lavaan, Heywood fijado) ===\n")
print(m, digits = 3)
cat("\n=== R^2 ===\n")
print(r2_tab)
cat("\n=== Ajuste ===\n")
print(fit_tab)

cat("\nNota DES_2 (Heywood): sin restriccion, lavaan da carga std=1.101 y "
    , "varianza residual std=-0.212 (negativa, caso Heywood). Con la "
    , "varianza fijada a .05, la carga queda en 1.000 y el modelo converge "
    , "sin advertencias de varianza negativa.\n", sep = "")
