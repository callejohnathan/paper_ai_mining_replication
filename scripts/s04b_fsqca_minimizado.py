"""
s04b — fsQCA con minimización booleana (ronda 13, paso D del plan de la ronda 12).

Diferencias con s04_fsqca.py (que se deja intacto para reproducir la Tabla 5 del paper):

1. Evita membresías de exactamente 0.5. En s04 un caso con 0.5 en cualquier
   condición no pertenece a ninguna fila de la tabla de verdad; con la
   calibración del paper eso deja fuera 484 de 980 casos (los 362 con fuente
   informal, Security = 0.5, y los casos en la mediana de cada escala).
   Aquí 0.5 se desplaza a 0.5 ± 0.001 (Fiss, 2011) y el sentido del
   desplazamiento es un parámetro de robustez.
2. Tabla de verdad con umbral de frecuencia, de consistencia y de PRI.
3. Minimización Quine-McCluskey: solución compleja (sin remanentes),
   parsimoniosa (todos los remanentes) e intermedia (solo contrafácticos fáciles,
   expectativa direccional: todas las condiciones presentes contribuyen a Y).
   Condiciones núcleo = las que aparecen también en la solución parsimoniosa.
4. Métricas de solución: consistencia, PRI, cobertura bruta y única por término.
5. Análisis del resultado negado (~Y) y una grilla de robustez.

Salidas (outputs/tables/):
    table_r13_fsqca_truth_table.csv     tabla de verdad de la especificación principal
    table_r13_fsqca_solution.csv        soluciones de la especificación principal (Y y ~Y)
    table_r13_fsqca_robustness.csv      grilla de robustez
"""
import sys
from itertools import combinations, product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import config as cfg
from _common import compute_composites

CONDS = cfg.FSQCA_CONDITIONS
LABEL = {"GOB_empresa": "Company", "GOB_confianza": "Community", "GOB_externo": "External",
         "SOS_ambiental": "Sustainability", "seguridad_hidrica": "Security"}
OUTCOMES = ["DES_estructural", "DES_regulacion", "DES_relacional", "DES_agencia"]

# Especificación principal
MAIN = dict(calib="p10-50-90", empuje=+1, cons=0.80, pri=0.70, freq=10)


# ---------------------------------------------------------------------------
# Calibración
# ---------------------------------------------------------------------------
def sigmoide(xv, out, cross, inn):
    z = np.where(xv >= cross, (xv - cross) / (inn - cross) * 3.0,
                 (xv - cross) / (cross - out) * 3.0)
    return np.exp(z) / (1 + np.exp(z))


def calibrar(x: pd.Series, calib: str) -> np.ndarray:
    xv = x.values.astype(float)
    if calib == "teorica":
        # Anclas sobre la escala Likert 1-5: 2 = fuera, 3.25 = cruce (no alcanzable
        # por promedios de 2, 3 o 5 ítems), 4.5 = dentro.
        out, cross, inn = 2.0, 3.25, 4.5
    else:
        lo, hi = {"p10-50-90": (10, 90), "p20-50-80": (20, 80)}[calib]
        out, cross, inn = np.percentile(xv, [lo, 50, hi])
    if inn <= cross or out >= cross:
        return None  # calibración degenerada (efecto techo/piso)
    return sigmoide(xv, out, cross, inn)


def calibrar_todo(df, calib, empuje):
    fs = {}
    for c in CONDS:
        if c == "seguridad_hidrica":
            m = df[c].map({0: 0.05, 1: 0.50, 2: 0.95}).values.astype(float)
        else:
            m = calibrar(df[c], calib)
        m = np.where(np.isclose(m, 0.5), 0.5 + 0.001 * empuje, m)
        fs[c] = m
    for y in OUTCOMES:
        fs[y] = calibrar(df[y], calib)
    return fs


# ---------------------------------------------------------------------------
# Métricas difusas
# ---------------------------------------------------------------------------
def metricas(x, y):
    sx, sxy = x.sum(), np.minimum(x, y).sum()
    amb = np.minimum(x, np.minimum(y, 1 - y)).sum()
    cons = sxy / sx if sx > 0 else np.nan
    pri = (sxy - amb) / (sx - amb) if sx - amb > 1e-9 else np.nan
    cov = sxy / y.sum()
    return cons, pri, cov


def membresia_termino(term, fs):
    """term: tupla con 1 (presente), 0 (ausente) o None (irrelevante) por condición."""
    m = np.ones(len(fs[CONDS[0]]))
    for c, v in zip(CONDS, term):
        if v is not None:
            m = np.minimum(m, fs[c] if v == 1 else 1 - fs[c])
    return m


def nombre(term):
    partes = [LABEL[c] if v == 1 else "~" + LABEL[c] for c, v in zip(CONDS, term) if v is not None]
    return "*".join(partes) if partes else "(tautología)"


# ---------------------------------------------------------------------------
# Tabla de verdad
# ---------------------------------------------------------------------------
def tabla_verdad(fs, y):
    filas = []
    for combo in product([1, 0], repeat=len(CONDS)):
        m = membresia_termino(combo, fs)
        n = int((m > 0.5).sum())
        cons, pri, _ = metricas(m, y)
        filas.append({"fila": combo, "n": n, "consistencia": cons, "PRI": pri})
    return filas


def clasificar(filas, cons, pri, freq):
    pos, neg, rem = [], [], []
    for f in filas:
        if f["n"] < freq:
            rem.append(f["fila"])
        elif f["consistencia"] >= cons and f["PRI"] >= pri:
            pos.append(f["fila"])
        else:
            neg.append(f["fila"])
    return pos, neg, rem


# ---------------------------------------------------------------------------
# Quine-McCluskey
# ---------------------------------------------------------------------------
def cubre(term, fila):
    return all(t is None or t == f for t, f in zip(term, fila))


def implicantes_primos(on, dc):
    actuales = {tuple(r) for r in on} | {tuple(r) for r in dc}
    primos = set()
    while actuales:
        usados, siguientes = set(), set()
        lista = list(actuales)
        for a, b in combinations(lista, 2):
            dif = [i for i, (p, q) in enumerate(zip(a, b)) if p != q]
            if len(dif) == 1 and a[dif[0]] is not None and b[dif[0]] is not None:
                nuevo = list(a)
                nuevo[dif[0]] = None
                siguientes.add(tuple(nuevo))
                usados.update([a, b])
        primos |= actuales - usados
        actuales = siguientes
    # solo los que cubren al menos una fila positiva
    return [p for p in primos if any(cubre(p, r) for r in on)]


def coberturas_minimas(primos, on):
    """Todas las coberturas de mínimo número de términos (y, entre ellas, mínimo de literales)."""
    if not on:
        return [[]]
    for k in range(1, len(primos) + 1):
        sols = [list(s) for s in combinations(primos, k)
                if all(any(cubre(p, r) for p in s) for r in on)]
        if sols:
            lit = lambda s: sum(v is not None for t in s for v in t)
            mejor = min(lit(s) for s in sols)
            return [s for s in sols if lit(s) == mejor]
    return [[]]


def minimizar(on, dc):
    return coberturas_minimas(implicantes_primos(on, dc), on)


def solucion_intermedia(complejas, parsimoniosas, on, rem, expectativa):
    """Ragin y Sonnett: de cada término complejo se eliminan los literales contrarios a la
    expectativa direccional que no están en un término parsimonioso que lo contenga.
    Luego se minimiza usando como remanentes solo los contrafácticos fáciles resultantes."""
    pars = {t for s in parsimoniosas for t in s}
    faciles = set()
    for sol in complejas:
        for c in sol:
            for p in pars:
                if not all(pv is None or pv == cv for pv, cv in zip(p, c)):
                    continue  # p no contiene a c
                inter = tuple(cv if (cv is not None and (pv is not None or cv == expectativa))
                              else None for cv, pv in zip(c, p))
                faciles |= {r for r in rem if cubre(inter, r)}
    return minimizar(on, list(faciles))


# ---------------------------------------------------------------------------
# Análisis completo de una especificación
# ---------------------------------------------------------------------------
def analizar(fs, y, cons, pri, freq, expectativa=1):
    filas = tabla_verdad(fs, y)
    pos, neg, rem = clasificar(filas, cons, pri, freq)
    if not pos:
        return filas, None
    compleja = minimizar(pos, [])
    pars = minimizar(pos, rem)
    inter = solucion_intermedia(compleja, pars, pos, rem, expectativa)
    return filas, {"compleja": compleja, "parsimoniosa": pars, "intermedia": inter,
                   "n_pos": len(pos), "casos_tabla": sum(f["n"] for f in filas if f["n"] >= freq)}


def metricas_solucion(sol, fs, y):
    ms = [membresia_termino(t, fs) for t in sol]
    filas = []
    for i, (t, m) in enumerate(zip(sol, ms)):
        cons, pri, cov = metricas(m, y)
        otros = np.max([ms[j] for j in range(len(ms)) if j != i], axis=0) if len(ms) > 1 else np.zeros_like(m)
        cov_resto = metricas(otros, y)[2] if len(ms) > 1 else 0.0
        unica = metricas(np.max(ms, axis=0), y)[2] - cov_resto
        filas.append({"termino": nombre(t), "consistencia": cons, "PRI": pri,
                      "cobertura_bruta": cov, "cobertura_unica": unica})
    cons, pri, cov = metricas(np.max(ms, axis=0), y)
    return filas, {"consistencia": cons, "PRI": pri, "cobertura": cov}


def nucleo(term_inter, parsimoniosa):
    """Literales del término intermedio presentes en algún término parsimonioso que lo contiene."""
    out = {}
    for c, v in zip(CONDS, term_inter):
        if v is None:
            continue
        es_nucleo = any(p[CONDS.index(c)] == v and all(pv is None or pv == iv for pv, iv in zip(p, term_inter))
                        for p in parsimoniosa)
        out[c] = ("núcleo" if es_nucleo else "periférica", v)
    return out


# ---------------------------------------------------------------------------
def main():
    df = compute_composites(pd.read_csv(cfg.DATA_PROCESSED / "survey_clean.csv"))

    # --- especificación principal ---------------------------------------
    fs = calibrar_todo(df, MAIN["calib"], MAIN["empuje"])
    sol_rows, tt_rows = [], []
    for y_name in ["DES_estructural", "DES_regulacion"]:
        for negado in (False, True):
            y = 1 - fs[y_name] if negado else fs[y_name]
            etiqueta = ("~" if negado else "") + y_name
            filas, res = analizar(fs, y, MAIN["cons"], MAIN["pri"], MAIN["freq"],
                                  expectativa=0 if negado else 1)
            for f in filas:
                tt_rows.append({"resultado": etiqueta, "fila": nombre(f["fila"]), "n": f["n"],
                                "consistencia": round(f["consistencia"], 3), "PRI": round(f["PRI"], 3),
                                "Y": int(f["n"] >= MAIN["freq"] and f["consistencia"] >= MAIN["cons"]
                                         and f["PRI"] >= MAIN["pri"]) if f["n"] >= MAIN["freq"] else "R"})
            if res is None:
                sol_rows.append({"resultado": etiqueta, "solucion": "ninguna fila supera los umbrales"})
                continue
            for tipo in ("compleja", "parsimoniosa", "intermedia"):
                for k, sol in enumerate(res[tipo]):
                    terms, glob = metricas_solucion(sol, fs, y)
                    for t, tr in zip(sol, terms):
                        nuc = nucleo(t, res["parsimoniosa"][0]) if tipo == "intermedia" else {}
                        sol_rows.append({"resultado": etiqueta, "solucion": tipo, "modelo": k + 1, **tr,
                                         "nucleo": "; ".join(f"{'~' if v == 0 else ''}{LABEL[c]}={e}"
                                                             for c, (e, v) in nuc.items()),
                                         "sol_consistencia": glob["consistencia"], "sol_PRI": glob["PRI"],
                                         "sol_cobertura": glob["cobertura"]})
    pd.DataFrame(tt_rows).to_csv(cfg.OUT_TABLES / "table_r13_fsqca_truth_table.csv", index=False)
    sol = pd.DataFrame(sol_rows).round(3)
    sol.to_csv(cfg.OUT_TABLES / "table_r13_fsqca_solution.csv", index=False)

    # --- grilla de robustez ---------------------------------------------
    rob = []
    for calib, empuje in [("p10-50-90", +1), ("p10-50-90", -1), ("p20-50-80", +1),
                          ("teorica", +1), ("teorica", -1)]:
        fs = calibrar_todo(df, calib, empuje)
        for y_name in OUTCOMES:
            if fs[y_name] is None:
                continue
            for negado in (False, True):
                y = 1 - fs[y_name] if negado else fs[y_name]
                for cons_t, pri_t, freq in product([0.75, 0.80, 0.85], [0.50, 0.65, 0.70], [5, 10, 20]):
                    _, res = analizar(fs, y, cons_t, pri_t, freq, expectativa=0 if negado else 1)
                    reg = {"calibracion": calib, "empuje_0.5": empuje,
                           "resultado": ("~" if negado else "") + y_name,
                           "cons": cons_t, "PRI_min": pri_t, "freq": freq}
                    if res is None:
                        rob.append({**reg, "filas_positivas": 0})
                        continue
                    inter = res["intermedia"][0]
                    _, glob = metricas_solucion(inter, fs, y)
                    nuc = [nucleo(t, res["parsimoniosa"][0]) for t in inter]
                    for c in CONDS:
                        pres = sum(1 for t in inter if t[CONDS.index(c)] == 1)
                        aus = sum(1 for t in inter if t[CONDS.index(c)] == 0)
                        core = sum(1 for n in nuc if c in n and n[c][0] == "núcleo")
                        reg[f"{LABEL[c]}"] = f"{pres}+/{aus}-/{core}n"
                    rob.append({**reg, "filas_positivas": res["n_pos"], "casos_en_tabla": res["casos_tabla"],
                                "terminos": len(inter), "modelos_alternativos": len(res["intermedia"]),
                                "solucion": " + ".join(nombre(t) for t in inter),
                                "parsimoniosa": " + ".join(nombre(t) for t in res["parsimoniosa"][0]),
                                "sol_consistencia": round(glob["consistencia"], 3),
                                "sol_PRI": round(glob["PRI"], 3), "sol_cobertura": round(glob["cobertura"], 3)})
    pd.DataFrame(rob).to_csv(cfg.OUT_TABLES / "table_r13_fsqca_robustness.csv", index=False)

    # --- sensibilidad a las anclas teóricas (cons .80, PRI .70, freq 10) ---
    anc = []
    for anclas in [(2, 3.25, 4.5), (1.5, 3.25, 4.5), (2, 3.1, 4.5), (2.5, 3.75, 4.75), (2, 3.4, 4.8)]:
        for empuje in (+1, -1):
            fs = {}
            for c in CONDS:
                if c == "seguridad_hidrica":
                    m = df[c].map({0: 0.05, 1: 0.50, 2: 0.95}).values.astype(float)
                else:
                    m = sigmoide(df[c].values.astype(float), *anclas)
                fs[c] = np.where(np.isclose(m, 0.5), 0.5 + 0.001 * empuje, m)
            for y_name in ["DES_estructural", "DES_regulacion"]:
                y = sigmoide(df[y_name].values.astype(float), *anclas)
                _, res = analizar(fs, y, 0.80, 0.70, 10)
                reg = {"anclas": "/".join(map(str, anclas)), "empuje_0.5": empuje, "resultado": y_name,
                       "prop_Y_dentro": round(float((y > 0.5).mean()), 2)}
                if res is None:
                    anc.append({**reg, "solucion": "sin solución"})
                    continue
                inter = res["intermedia"][0]
                _, glob = metricas_solucion(inter, fs, y)
                anc.append({**reg, "solucion": " + ".join(nombre(t) for t in inter),
                            "parsimoniosa": " + ".join(nombre(t) for t in res["parsimoniosa"][0]),
                            "sol_consistencia": round(glob["consistencia"], 3),
                            "sol_PRI": round(glob["PRI"], 3), "sol_cobertura": round(glob["cobertura"], 3)})
    pd.DataFrame(anc).to_csv(cfg.OUT_TABLES / "table_r13_fsqca_anclas.csv", index=False)

    pd.set_option("display.width", 250, "display.max_colwidth", 120)
    print(sol.to_string(index=False))


if __name__ == "__main__":
    main()
