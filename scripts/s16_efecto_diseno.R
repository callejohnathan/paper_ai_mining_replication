# s16_efecto_diseno.R — Ronda 20 (F-a, verificación de la auditoría §3.2).
#
# Compara, para cada ruta del modelo estructural corregido (s03e), el error
# estándar del beta estandarizado sin y con agrupamiento por vereda. La razón
# (efecto de diseño) muestra qué parte de la imprecisión viene de la
# variación entre comunidades y no de la medición.
#
# Salida: outputs/tables/tableS_efecto_diseno.csv

suppressPackageStartupMessages(library(lavaan))
df <- read.csv("data/processed/survey_clean.csv")
src <- readLines("scripts/s03e_single_estimator_heywood_fixed.R", encoding="UTF-8")
ini <- grep("^model <- '", src); fin <- which(src=="'"); fin <- fin[fin>ini][1]
eval(parse(text=src[ini:fin]))
a <- standardizedSolution(suppressWarnings(sem(model, df))); b <- standardizedSolution(suppressWarnings(sem(model, df, cluster="Vereda")))
a<-a[a$op=="~",c("lhs","rhs","est.std","se")]; b<-b[b$op=="~",c("lhs","rhs","se")]; r<-merge(a,b,by=c("lhs","rhs"),suffixes=c("_n","_c")); r$beta<-round(r$est.std,3); r$se_n<-round(r$se_n,3); r$se_c<-round(r$se_c,3); r$est.std<-NULL
r$deff <- round(r$se_c/r$se_n,2); r$ci_n <- paste0("[",round(r$beta-1.96*r$se_n,2),", ",round(r$beta+1.96*r$se_n,2),"]")
r$rhs[r$rhs == "VUL"] <- "vulnerabilidad_hidrica"
r <- r[order(r$rhs, r$lhs), ]
write.csv(r, "outputs/tables/tableS_efecto_diseno.csv", row.names = FALSE)
print(r, row.names = FALSE)
