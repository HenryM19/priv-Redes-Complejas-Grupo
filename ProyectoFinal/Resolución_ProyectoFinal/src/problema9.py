"""
problema9.py — Problema P9: Fallas en Cascada y Epidemias SIR (Fase 4)
=======================================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Modela fenómenos dinámicos sobre la red:
  1. Modelo de carga-capacidad (fallas en cascada): un nodo falla si su
     carga supera su capacidad; distribuye carga extra a vecinos y puede
     desencadenar más fallas.
  2. Modelo SIR discreto (epidemia): simula propagación de un fallo lógico
     (virus, misconfiguration) con tasa de infección β y recuperación γ.
  3. Estrategias de inmunización: aleatoria, por grado, por betweenness,
     por vecino de nodo aleatorio (aproximación práctica).

Los cinco ítems resueltos son:
  Ítem 1 · Modelo de carga-capacidad; fallas en cascada
  Ítem 2 · Margen crítico τ_c por nodo disparador (top-5 por betweenness) y
           fracción de nodos fallidos vs tolerancia α
  Ítem 3 · Modelo SIR sobre la red (30 realizaciones, media ± std);
           umbral crítico τ_c ≈ ⟨k⟩/⟨k²⟩
  Ítem 4 · Estrategias de inmunización (30 realizaciones, media ± std)
  Ítem 5 · Nodo(s) más crítico(s) (mayor cascada y mayor propagación)

El modelo SIR y la inmunización son procesos estocásticos: una sola
realización puede no ser representativa. Todo lo que depende de ellos se
promedia sobre N_REALIZ corridas con semillas distintas y se reporta con
desviación estándar.

Uso:
    python problema9.py

Salidas:
    results/tablas/p9_cascada_tolerancia.csv
    results/tablas/p9_margen_critico.csv
    results/tablas/p9_sir_promedio.csv
    results/tablas/p9_inmunizacion.csv
    results/imagenes/p9_cascada.png
    results/imagenes/p9_margen_critico.png
    results/imagenes/p9_sir.png
    results/imagenes/p9_inmunizacion.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, random, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

DIR_SRC   = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL = os.path.dirname(DIR_SRC)
DIR_ROOT  = os.path.dirname(DIR_RESOL)
DIR_BASE  = os.path.join(DIR_ROOT, "codigo_base")
DIR_TAB   = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG   = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar  # noqa


def _crear_dirs():
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


# ============================================================
# Definición de funciones
# ============================================================

# ------------------------------------------------------------
# Ítem 1 — Modelo de carga-capacidad (fallas en cascada)
# ------------------------------------------------------------

def cascada_fallos(G: nx.Graph, nodo_inicial: str,
                   alpha: float = 0.1) -> dict:
    """
    Modelo de carga-capacidad de Motter-Lai (2002).
    Cada nodo i tiene:
      carga(i) = betweenness(i)   (proporcional al tráfico de paso)
      capacidad(i) = (1 + α) · carga(i)
    Al fallar el nodo_inicial, el betweenness se redistribuye.
    Proceso iterativo hasta que no haya nuevas fallas.

    Argumentos:
        G             (nx.Graph): grafo original.
        nodo_inicial  (str)     : nodo que falla primero.
        alpha         (float)   : tolerancia α ≥ 0.

    Salida:
        dict:
            'nodos_fallidos'  — lista de nodos que fallaron en cascada
            'n_fallidos'      — cantidad total
            'fraccion'        — fracción n_fallidos / n_total
            'pasos'           — número de rondas de cascada
    """
    n = G.number_of_nodes()
    Gc = G.copy()

    # Capacidad inicial (fija al inicio de la simulación)
    btw0 = nx.betweenness_centrality(G, normalized=False)
    capacidad = {v: (1 + alpha) * max(btw0[v], 1.0) for v in G.nodes()}

    # Falla inicial
    fallidos = []
    if nodo_inicial in Gc:
        Gc.remove_node(nodo_inicial)
        fallidos.append(nodo_inicial)

    pasos = 0
    while True:
        if Gc.number_of_nodes() == 0:
            break
        btw_actual = nx.betweenness_centrality(Gc, normalized=False)
        nuevos_fallidos = [v for v in Gc.nodes()
                           if btw_actual.get(v, 0) > capacidad.get(v, float("inf"))]
        if not nuevos_fallidos:
            break
        for v in nuevos_fallidos:
            Gc.remove_node(v)
            fallidos.append(v)
        pasos += 1

    return {
        "nodos_fallidos": fallidos,
        "n_fallidos"    : len(fallidos),
        "fraccion"      : len(fallidos) / n,
        "pasos"         : pasos,
    }


def barrido_tolerancia(G: nx.Graph, nodo: str,
                        alphas: list) -> pd.DataFrame:
    """
    Ejecuta la cascada para un nodo inicial con distintos valores de α.

    Argumentos:
        G      (nx.Graph): grafo.
        nodo   (str)     : nodo detonador.
        alphas (list)    : lista de valores α a explorar.

    Salida:
        pd.DataFrame [alpha, n_fallidos, fraccion, pasos].
    """
    filas = []
    for a in alphas:
        res = cascada_fallos(G, nodo, alpha=a)
        filas.append({"alpha": a, "n_fallidos": res["n_fallidos"],
                      "fraccion": res["fraccion"], "pasos": res["pasos"]})
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Ítem 2 — Margen crítico τ_c por nodo disparador (multi-nodo)
# ------------------------------------------------------------

def margen_critico_multinodo(G: nx.Graph, nodos_candidatos: list,
                              alphas: list, umbral_fraccion: float = 0.2
                              ) -> pd.DataFrame:
    """
    Para cada nodo candidato, determina el margen crítico α_c: el mayor
    valor de α en el barrido para el cual la cascada iniciada en ese nodo
    todavía afecta a más del `umbral_fraccion` de la red (por defecto 20%,
    como pide el enunciado P9.2). Por debajo de α_c la falla de ese único
    nodo dispara una cascada "grande"; por encima, el resto de la red
    absorbe la sobrecarga sin colapsar.

    Barriendo varios nodos candidatos (no solo el de mayor betweenness) se
    puede identificar cuáles son realmente "los nodos disparadores más
    peligrosos" en plural, tal como pide el enunciado.

    Argumentos:
        G                (nx.Graph): grafo.
        nodos_candidatos (list)    : nodos a evaluar como disparador.
        alphas           (list)    : valores de α a barrer (ordenados asc.).
        umbral_fraccion  (float)   : fracción de la red que define "cascada
                                     grande" (0.2 = 20%, según enunciado).

    Salida:
        pd.DataFrame [nodo, alpha_critico, fraccion_en_alpha_critico,
                      fraccion_max_observada], ordenado por peligrosidad
        (alpha_critico descendente = más peligroso primero).
    """
    alphas_ord = sorted(alphas)
    filas = []
    for nodo in nodos_candidatos:
        alpha_c = None
        frac_en_alpha_c = 0.0
        frac_max = 0.0
        for a in alphas_ord:
            res = cascada_fallos(G, nodo, alpha=a)
            frac_max = max(frac_max, res["fraccion"])
            if res["fraccion"] > umbral_fraccion:
                alpha_c = a
                frac_en_alpha_c = res["fraccion"]
        filas.append({
            "nodo"                      : nodo,
            # NaN (no 0.0) cuando el nodo nunca dispara una cascada grande
            # en el rango de α probado: 0.0 confundiría "α_c=0" (dispara
            # incluso sin margen) con "no aplica" (nunca dispara).
            "alpha_critico"             : alpha_c if alpha_c is not None else np.nan,
            "fraccion_en_alpha_critico" : round(frac_en_alpha_c, 4) if alpha_c is not None else np.nan,
            "fraccion_max_observada"    : round(frac_max, 4),
            "dispara_cascada_grande"    : alpha_c is not None,
        })
    df = pd.DataFrame(filas).sort_values(
        # Los que sí disparan van primero (ordenados por α_c: mayor margen
        # tolerado y aun así colapsa = más peligroso). Entre los que no
        # disparan, se ordenan por qué tan cerca estuvieron del umbral.
        ["dispara_cascada_grande", "alpha_critico", "fraccion_max_observada"],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    return df


# ------------------------------------------------------------
# Ítem 3 — Modelo SIR discreto
# ------------------------------------------------------------

def sir_discreto(G: nx.Graph, beta: float, gamma: float,
                 semilla_inf: str, semilla: int = 42,
                 t_max: int = 50) -> pd.DataFrame:
    """
    Simula el modelo SIR en tiempo discreto sobre G.
    S → I con probabilidad β por cada vecino infectado.
    I → R con probabilidad γ en cada paso.

    Argumentos:
        G          (nx.Graph): grafo.
        beta       (float)   : tasa de infección por contacto ∈ [0,1].
        gamma      (float)   : tasa de recuperación ∈ [0,1].
        semilla_inf (str)    : nodo donde inicia la infección.
        semilla    (int)     : semilla RNG.
        t_max      (int)     : pasos máximos.

    Salida:
        pd.DataFrame [t, S, I, R].
    """
    rng = random.Random(semilla)
    nodos = list(G.nodes())
    n = len(nodos)

    estado = {v: "S" for v in nodos}
    estado[semilla_inf] = "I"

    filas = []
    for t in range(t_max + 1):
        S = sum(1 for v in nodos if estado[v] == "S")
        I = sum(1 for v in nodos if estado[v] == "I")
        R = sum(1 for v in nodos if estado[v] == "R")
        filas.append({"t": t, "S": S, "I": I, "R": R})
        if I == 0:
            break

        nuevo_estado = dict(estado)
        for v in nodos:
            if estado[v] == "S":
                vecinos_inf = [u for u in G.neighbors(v) if estado[u] == "I"]
                p_inf = 1 - (1 - beta) ** len(vecinos_inf)
                if rng.random() < p_inf:
                    nuevo_estado[v] = "I"
            elif estado[v] == "I":
                if rng.random() < gamma:
                    nuevo_estado[v] = "R"
        estado = nuevo_estado

    return pd.DataFrame(filas)


def sir_promedio(G: nx.Graph, beta: float, gamma: float, semilla_inf: str,
                  n_realiz: int = 30, t_max: int = 50) -> dict:
    """
    Promedia n_realiz corridas del SIR estocástico (semillas 0..n_realiz-1)
    y devuelve la trayectoria media ± std de S, I, R alineada en el tiempo,
    más la distribución del tamaño final del brote R_final.

    El SIR discreto es estocástico (cada contagio y cada recuperación es
    un sorteo aleatorio): una sola corrida puede sobre- o sub-estimar el
    alcance real de la epidemia. Promediar sobre varias semillas da una
    trayectoria representativa y permite reportar la variabilidad.

    Argumentos:
        G           (nx.Graph): grafo.
        beta, gamma (float)   : parámetros SIR.
        semilla_inf (str)     : nodo donde inicia la infección.
        n_realiz    (int)     : número de realizaciones a promediar.
        t_max       (int)     : pasos máximos por realización.

    Salida:
        dict:
            'df_media'   — pd.DataFrame [t, S, I, R] (media, series alineadas
                            por longitud máxima, rellenando con el último
                            estado tras la extinción).
            'df_std'     — pd.DataFrame [t, S, I, R] (desviación estándar).
            'R_finales'  — list[int] con el tamaño final del brote por corrida.
            'R_final_media', 'R_final_std' — resumen escalar.
    """
    corridas = []
    r_finales = []
    for s in range(n_realiz):
        df = sir_discreto(G, beta, gamma, semilla_inf, semilla=s, t_max=t_max)
        r_finales.append(int(df["R"].iloc[-1]))
        corridas.append(df)

    largo_max = max(len(df) for df in corridas)
    n = G.number_of_nodes()
    # Extender cada corrida hasta largo_max repitiendo el último estado
    # (la epidemia ya se extinguió: I=0, S y R quedan constantes).
    mats = {"S": [], "I": [], "R": []}
    for df in corridas:
        for col in ("S", "I", "R"):
            serie = df[col].tolist()
            serie += [serie[-1]] * (largo_max - len(serie))
            mats[col].append(serie)

    df_media = pd.DataFrame({
        "t": range(largo_max),
        "S": np.mean(mats["S"], axis=0),
        "I": np.mean(mats["I"], axis=0),
        "R": np.mean(mats["R"], axis=0),
    })
    df_std = pd.DataFrame({
        "t": range(largo_max),
        "S": np.std(mats["S"], axis=0),
        "I": np.std(mats["I"], axis=0),
        "R": np.std(mats["R"], axis=0),
    })

    return {
        "df_media"      : df_media,
        "df_std"        : df_std,
        "R_finales"     : r_finales,
        "R_final_media" : float(np.mean(r_finales)),
        "R_final_std"   : float(np.std(r_finales)),
    }


def umbral_critico(G: nx.Graph) -> float:
    """
    Calcula el umbral crítico de infección τ_c ≈ ⟨k⟩/⟨k²⟩.
    Para β > τ_c hay una epidemia global.

    Argumentos:
        G (nx.Graph): grafo.

    Salida:
        float: τ_c.
    """
    grados = [d for _, d in G.degree()]
    k_mean  = np.mean(grados)
    k2_mean = np.mean([k**2 for k in grados])
    if k2_mean == 0:
        return float("inf")
    return k_mean / k2_mean


# ------------------------------------------------------------
# Ítem 4 — Estrategias de inmunización
# ------------------------------------------------------------

def _seleccionar_inmunes(G: nx.Graph, nodos: list, n_inm: int,
                          estrategia: str, rng: random.Random) -> list:
    """Selecciona los n_inm nodos a inmunizar según la estrategia dada."""
    if estrategia == "aleatorio":
        return rng.sample(nodos, n_inm)
    elif estrategia == "grado":
        return sorted(nodos, key=lambda v: G.degree(v), reverse=True)[:n_inm]
    elif estrategia == "betweenness":
        btw = nx.betweenness_centrality(G)
        return sorted(nodos, key=lambda v: btw[v], reverse=True)[:n_inm]
    elif estrategia == "vecino":
        # Vacunar al vecino de un nodo aleatorio (acquaintance immunization):
        # tiende a encontrar hubs sin necesitar conocer la topología completa.
        candidatos = set()
        intentos = 0
        while len(candidatos) < n_inm and intentos < 50 * n_inm:
            v = rng.choice(nodos)
            vecinos = list(G.neighbors(v))
            if vecinos:
                candidatos.add(rng.choice(vecinos))
            intentos += 1
        return list(candidatos)[:n_inm]
    return []


def inmunizacion(G: nx.Graph, beta: float, gamma: float,
                 fraccion: float, estrategia: str,
                 semilla_inf: str, n_realiz: int = 30) -> dict:
    """
    Simula el SIR luego de inmunizar una fracción de nodos, promediando
    sobre n_realiz realizaciones independientes (semillas 0..n_realiz-1)
    tanto para la selección de inmunes (en 'aleatorio' y 'vecino', que son
    estocásticas) como para la propagación SIR.

    Se promedia porque tanto la elección de inmunes al azar como el
    contagio son procesos estocásticos: una sola corrida puede sub- o
    sobre-estimar la efectividad real de la estrategia.

    Argumentos:
        G           (nx.Graph): grafo original.
        beta, gamma (float)   : parámetros SIR.
        fraccion    (float)   : fracción de nodos a inmunizar.
        estrategia  (str)     : 'aleatorio'|'grado'|'betweenness'|'vecino'.
        semilla_inf (str)     : nodo de infección.
        n_realiz    (int)     : número de realizaciones a promediar.

    Salida:
        dict: {estrategia, fraccion_inm, R_final (media), R_final_std,
               fraccion_afectada (media), fraccion_afectada_std}.
    """
    nodos = list(G.nodes())
    n_inm = max(1, int(fraccion * len(nodos)))
    r_finales = []

    for s in range(n_realiz):
        rng = random.Random(s)
        inmunes = _seleccionar_inmunes(G, nodos, n_inm, estrategia, rng)
        Gc = G.copy()
        Gc.remove_nodes_from([v for v in inmunes if v in Gc and v != semilla_inf])

        if semilla_inf not in Gc:
            r_finales.append(0)
            continue

        df_sir = sir_discreto(Gc, beta, gamma, semilla_inf, semilla=s)
        r_finales.append(int(df_sir["R"].iloc[-1]))

    r_media = float(np.mean(r_finales))
    r_std   = float(np.std(r_finales))
    return {
        "estrategia"            : estrategia,
        "fraccion_inm"          : fraccion,
        "R_final"               : round(r_media, 2),
        "R_final_std"           : round(r_std, 2),
        "fraccion_afectada"     : r_media / len(nodos),
        "fraccion_afectada_std" : r_std / len(nodos),
    }


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_cascada(df: pd.DataFrame, nodo: str, alpha_c: float = None) -> None:
    """Fracción de nodos fallidos vs α, con marcador en el margen crítico."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["alpha"], df["fraccion"] * 100, "ro-", linewidth=2, markersize=7)
    ax.axhline(20, color="gray", linestyle=":", linewidth=1.3,
               label="Umbral de cascada grande (20%)")
    if alpha_c is not None:
        ax.axvline(alpha_c, color="darkred", linestyle="--", linewidth=1.5,
                   label=f"α_c ≈ {alpha_c:.2f}")
    ax.set_xlabel("Tolerancia α")
    ax.set_ylabel("Nodos fallidos (%)")
    ax.set_title(f"P9 · Cascada de fallos — nodo inicial: {nodo}", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p9_cascada.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_margen_critico(df_margen: pd.DataFrame) -> None:
    """
    Barras horizontales por nodo candidato. Si el nodo dispara una cascada
    > 20% en algún α del barrido, la barra muestra α_c (mayor α_c = más
    peligroso: tolera más margen y aun así colapsa la red). Si ningún α
    del barrido dispara esa cascada grande, la barra muestra en su lugar
    la fracción máxima observada, para no confundir "no llegó a colapsar
    en este rango de α" con "colapsa apenas se elimina el nodo".
    """
    df = df_margen.sort_values(
        ["dispara_cascada_grande", "alpha_critico", "fraccion_max_observada"]
    )
    fig, ax = plt.subplots(figsize=(9, max(3.5, 0.5 * len(df))))
    colores = ["#c0392b" if d else "#95a5a6"
               for d in df["dispara_cascada_grande"]]
    nodos_cortos = [n[-22:] if len(n) > 22 else n for n in df["nodo"]]
    # Barra: α_c si dispara, fracción_max (escalada ×10 para visibilidad) si no.
    valores_barra = [
        a if d else f * 10
        for a, f, d in zip(df["alpha_critico"], df["fraccion_max_observada"],
                           df["dispara_cascada_grande"])
    ]
    bars = ax.barh(nodos_cortos, valores_barra, color=colores,
                   edgecolor="white", linewidth=0.6)
    for bar, a, f, disparo in zip(bars, df["alpha_critico"],
                                   df["fraccion_max_observada"],
                                   df["dispara_cascada_grande"]):
        etiqueta = f"α_c={a:.2f}" if disparo else f"máx {f*100:.1f}% (no llega a 20%)"
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                etiqueta, va="center", fontsize=8)
    ax.set_xlabel("α_c (rojo, dispara ≥20%)  ·  fracción máx. × 10 (gris, no dispara)")
    ax.set_title("P9 · Margen crítico por nodo disparador\n"
                  "(umbral: cascada afecta > 20% de la red)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p9_margen_critico.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_sir(res_sub: dict, res_sup: dict, tau_c: float,
                 n_realiz: int) -> None:
    """
    Curvas SIR sub-crítico y sobre-crítico: trayectoria media de N_REALIZ
    realizaciones, con banda ±1 std para mostrar la variabilidad estocástica.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))
    for ax, res, titulo in [
        (ax1, res_sub, f"β < τ_c={tau_c:.3f} (sub-crítico)"),
        (ax2, res_sup, f"β > τ_c={tau_c:.3f} (epidemia)"),
    ]:
        dfm, dfs = res["df_media"], res["df_std"]
        for col, color, etiqueta in [("S", "b", "S"), ("I", "r", "I"), ("R", "g", "R")]:
            ax.plot(dfm["t"], dfm[col], color=color, label=etiqueta, linewidth=2)
            ax.fill_between(dfm["t"], dfm[col] - dfs[col], dfm[col] + dfs[col],
                            color=color, alpha=0.15)
        ax.set_xlabel("Tiempo (pasos)")
        ax.set_ylabel("Número de nodos")
        ax.set_title(titulo)
        ax.legend(); ax.grid(alpha=0.3)
    plt.suptitle(f"P9 · Modelo SIR — Red UCuenca (media ± std, {n_realiz} realizaciones)",
                fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p9_sir.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_inmunizacion(filas: list, n_realiz: int) -> None:
    """Comparativa de estrategias de inmunización, con barras de error ±std."""
    df = pd.DataFrame(filas)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colores = {"aleatorio": "steelblue", "grado": "red",
               "betweenness": "darkorange", "vecino": "green"}
    for est in df["estrategia"].unique():
        sub = df[df["estrategia"] == est].sort_values("fraccion_inm")
        ax.errorbar(sub["fraccion_inm"], sub["fraccion_afectada"] * 100,
                    yerr=sub["fraccion_afectada_std"] * 100,
                    fmt="o-", color=colores.get(est, "gray"), label=est,
                    linewidth=2, capsize=3)
    ax.set_xlabel("Fracción inmunizada")
    ax.set_ylabel("Fracción afectada final (%)")
    ax.set_title(f"P9 · Estrategias de inmunización (media ± std, {n_realiz} realiz.)",
                fontweight="bold")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p9_inmunizacion.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P9 — Fallas en Cascada y Epidemias SIR ===\n")

    N_REALIZ = 30  # realizaciones para promediar procesos estocásticos (SIR, inmunización)

    G = cargar_red(fuente="csv"); verificar(G)

    # Top-5 nodos por betweenness: candidatos a disparador de cascada.
    # No asumimos de antemano que el de mayor betweenness es "el" más
    # peligroso — el enunciado pide identificar los disparadores más
    # peligrosos en plural, así que se comparan varios.
    btw = nx.betweenness_centrality(G, normalized=False)
    top5_btw = [n for n, _ in sorted(btw.items(), key=lambda x: -x[1])[:5]]
    nodo_critico = top5_btw[0]
    print(f"  Top-5 candidatos por betweenness: {top5_btw}\n")

    # Ítem 1: cascada con barrido de α (nodo de referencia = mayor betweenness)
    print("[Ítem 1] Cascada de fallos — barrido de tolerancia α (nodo de referencia)")
    alphas = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    df_casc = barrido_tolerancia(G, nodo_critico, alphas)
    df_casc["nodo_inicial"] = nodo_critico
    df_casc.to_csv(os.path.join(DIR_TAB, "p9_cascada_tolerancia.csv"), index=False)
    print(df_casc.to_string(index=False))

    # Ítem 2: margen crítico multi-nodo — ¿cuáles son los disparadores
    # más peligrosos, no solo el de mayor betweenness?
    print("\n[Ítem 2] Margen crítico α_c por nodo disparador (top-5 betweenness)")
    df_margen = margen_critico_multinodo(G, top5_btw, alphas, umbral_fraccion=0.2)
    df_margen.to_csv(os.path.join(DIR_TAB, "p9_margen_critico.csv"), index=False)
    print(df_margen.to_string(index=False))
    fila_ref = df_margen.loc[df_margen["nodo"] == nodo_critico].iloc[0]
    alpha_c_ref = float(fila_ref["alpha_critico"]) if fila_ref["dispara_cascada_grande"] else None
    graficar_cascada(df_casc, nodo_critico, alpha_c_ref)
    graficar_margen_critico(df_margen)

    fila_top = df_margen.iloc[0]
    nodo_mas_peligroso = fila_top["nodo"]
    if fila_top["dispara_cascada_grande"]:
        print(f"\n  Nodo disparador más peligroso: {nodo_mas_peligroso} "
              f"(α_c={fila_top['alpha_critico']:.2f} — dispara cascada >20% "
              f"incluso con ese margen de tolerancia)")
    else:
        print(f"\n  Ningún nodo del top-5 dispara una cascada >20% en el rango "
              f"de α probado ({alphas[0]}–{alphas[-1]}).")
        print(f"  El más cercano al umbral: {nodo_mas_peligroso} "
              f"(máximo {fila_top['fraccion_max_observada']*100:.1f}% de la red afectada).")

    # Ítem 3: umbral crítico y modelo SIR (promediado)
    tau_c = umbral_critico(G)
    print(f"\n[Ítem 3] Umbral crítico τ_c = ⟨k⟩/⟨k²⟩ = {tau_c:.4f}")

    nodo_inf = nodo_critico  # infección empieza en el nodo más central
    beta_sub  = round(tau_c * 0.5, 4)
    beta_sup  = round(tau_c * 2.0, 4)
    gamma_val = 0.1

    print(f"  Promediando SIR sobre {N_REALIZ} realizaciones (β_sub={beta_sub}, β_sup={beta_sup})...")
    res_sub = sir_promedio(G, beta_sub, gamma_val, nodo_inf, n_realiz=N_REALIZ)
    res_sup = sir_promedio(G, beta_sup, gamma_val, nodo_inf, n_realiz=N_REALIZ)

    df_sir_all = pd.concat([
        res_sub["df_media"].assign(caso="sub_critico", beta=beta_sub, tipo="media"),
        res_sub["df_std"].assign(caso="sub_critico", beta=beta_sub, tipo="std"),
        res_sup["df_media"].assign(caso="sobre_critico", beta=beta_sup, tipo="media"),
        res_sup["df_std"].assign(caso="sobre_critico", beta=beta_sup, tipo="std"),
    ])
    df_sir_all.to_csv(os.path.join(DIR_TAB, "p9_sir_promedio.csv"), index=False)

    print(f"  β={beta_sub} (sub-crítico): R_final={res_sub['R_final_media']:.1f}"
          f"±{res_sub['R_final_std']:.1f} / {G.number_of_nodes()}")
    print(f"  β={beta_sup} (sobre-crítico): R_final={res_sup['R_final_media']:.1f}"
          f"±{res_sup['R_final_std']:.1f} / {G.number_of_nodes()}")
    graficar_sir(res_sub, res_sup, tau_c, N_REALIZ)

    # Ítem 4: estrategias de inmunización (promediado)
    print(f"\n[Ítem 4] Estrategias de inmunización ({N_REALIZ} realizaciones c/u)")
    fracciones = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
    estrategias = ["aleatorio", "grado", "betweenness", "vecino"]
    filas_inm = []
    for est in estrategias:
        for f in fracciones:
            res = inmunizacion(G, beta_sup, gamma_val, f, est, nodo_inf, n_realiz=N_REALIZ)
            filas_inm.append(res)
            print(f"  {est:15s}  f={f:.2f}  afectados={res['R_final']:>6.1f}±{res['R_final_std']:<5.1f}  "
                  f"({res['fraccion_afectada']*100:.1f}%)")

    pd.DataFrame(filas_inm).to_csv(
        os.path.join(DIR_TAB, "p9_inmunizacion.csv"), index=False)
    graficar_inmunizacion(filas_inm, N_REALIZ)

    # Ítem 5: nodo(s) más crítico(s) — síntesis de cascada (determinista) y
    # propagación SIR (estocástica, promediada)
    print(f"\n[Ítem 5] Nodo(s) más crítico(s):")
    if fila_top["dispara_cascada_grande"]:
        print(f"  Mayor margen crítico de cascada (α_c más alto): {nodo_mas_peligroso}")
        print(f"    α_c = {fila_top['alpha_critico']:.2f}  "
              f"(fracción afectada en ese punto: {fila_top['fraccion_en_alpha_critico']*100:.1f}%)")
    else:
        print(f"  Ningún nodo del top-5 dispara cascada >20% con este modelo de "
              f"capacidad-carga. El más cercano: {nodo_mas_peligroso} "
              f"(máx. {fila_top['fraccion_max_observada']*100:.1f}%).")
    res_cascada0 = cascada_fallos(G, nodo_critico, alpha=0.1)
    print(f"  Cascada del nodo de referencia (α=0.1, {nodo_critico}): "
          f"{res_cascada0['n_fallidos']} nodos fallidos ({res_cascada0['fraccion']*100:.1f}%)")
    print(f"  Propagación SIR (β=τ_c×2, promedio {N_REALIZ} realiz.): "
          f"R_final={res_sup['R_final_media']:.1f}±{res_sup['R_final_std']:.1f}")

    print("\n=== P9 completado ===\n")
