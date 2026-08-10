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
  Ítem 2 · Fracción de nodos fallidos vs tolerancia α
  Ítem 3 · Modelo SIR sobre la red; umbral crítico τ_c ≈ ⟨k⟩/⟨k²⟩
  Ítem 4 · Estrategias de inmunización
  Ítem 5 · Nodo más crítico (mayor cascada y mayor propagación)

Uso:
    python problema9.py

Salidas:
    results/tablas/p9_cascada_tolerancia.csv
    results/tablas/p9_sir_promedio.csv
    results/tablas/p9_inmunizacion.csv
    results/imagenes/p9_cascada.png
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

def inmunizacion(G: nx.Graph, beta: float, gamma: float,
                 fraccion: float, estrategia: str,
                 semilla_inf: str, semilla: int = 42) -> dict:
    """
    Simula el SIR luego de inmunizar una fracción de nodos.

    Argumentos:
        G           (nx.Graph): grafo original.
        beta, gamma (float)   : parámetros SIR.
        fraccion    (float)   : fracción de nodos a inmunizar.
        estrategia  (str)     : 'aleatorio'|'grado'|'betweenness'|'vecino'.
        semilla_inf (str)     : nodo de infección.
        semilla     (int)     : semilla RNG.

    Salida:
        dict: {estrategia, fraccion, R_final, fraccion_afectada}.
    """
    rng = random.Random(semilla)
    nodos = list(G.nodes())
    n_inm = max(1, int(fraccion * len(nodos)))
    Gc = G.copy()

    if estrategia == "aleatorio":
        inmunes = rng.sample(nodos, n_inm)
    elif estrategia == "grado":
        inmunes = sorted(nodos, key=lambda v: G.degree(v), reverse=True)[:n_inm]
    elif estrategia == "betweenness":
        btw = nx.betweenness_centrality(G)
        inmunes = sorted(nodos, key=lambda v: btw[v], reverse=True)[:n_inm]
    elif estrategia == "vecino":
        # Estrategia de vecino: seleccionar nodos aleatorios y vacunar a un vecino aleatorio
        candidatos = set()
        while len(candidatos) < n_inm:
            v = rng.choice(nodos)
            vecinos = list(G.neighbors(v))
            if vecinos:
                candidatos.add(rng.choice(vecinos))
        inmunes = list(candidatos)[:n_inm]
    else:
        inmunes = []

    Gc.remove_nodes_from([v for v in inmunes if v in Gc and v != semilla_inf])

    if semilla_inf not in Gc:
        return {"estrategia": estrategia, "fraccion": fraccion,
                "R_final": 0, "fraccion_afectada": 0.0}

    df_sir = sir_discreto(Gc, beta, gamma, semilla_inf, semilla=semilla)
    R_final = df_sir["R"].iloc[-1]
    return {
        "estrategia"       : estrategia,
        "fraccion_inm"     : fraccion,
        "R_final"          : R_final,
        "fraccion_afectada": R_final / len(nodos),
    }


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_cascada(df: pd.DataFrame, nodo: str) -> None:
    """Fracción de nodos fallidos vs α."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["alpha"], df["fraccion"] * 100, "ro-", linewidth=2, markersize=7)
    ax.set_xlabel("Tolerancia α")
    ax.set_ylabel("Nodos fallidos (%)")
    ax.set_title(f"P9 · Cascada de fallos — nodo inicial: {nodo}", fontweight="bold")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p9_cascada.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_sir(df_sub: pd.DataFrame, df_sup: pd.DataFrame,
                 tau_c: float) -> None:
    """Curvas SIR sub-crítico y sobre-crítico."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))
    for ax, df, titulo in [(ax1, df_sub, f"β < τ_c={tau_c:.3f} (sub-crítico)"),
                            (ax2, df_sup, f"β > τ_c={tau_c:.3f} (epidemia)")]:
        ax.plot(df["t"], df["S"], "b-", label="S", linewidth=2)
        ax.plot(df["t"], df["I"], "r-", label="I", linewidth=2)
        ax.plot(df["t"], df["R"], "g-", label="R", linewidth=2)
        ax.set_xlabel("Tiempo (pasos)")
        ax.set_ylabel("Número de nodos")
        ax.set_title(titulo)
        ax.legend(); ax.grid(alpha=0.3)
    plt.suptitle("P9 · Modelo SIR — Red UCuenca", fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p9_sir.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_inmunizacion(filas: list) -> None:
    """Comparativa de estrategias de inmunización."""
    df = pd.DataFrame(filas)
    fig, ax = plt.subplots(figsize=(8, 4))
    colores = {"aleatorio": "steelblue", "grado": "red",
               "betweenness": "darkorange", "vecino": "green"}
    for est in df["estrategia"].unique():
        sub = df[df["estrategia"] == est]
        ax.plot(sub["fraccion_inm"], sub["fraccion_afectada"] * 100,
                "o-", color=colores.get(est, "gray"), label=est, linewidth=2)
    ax.set_xlabel("Fracción inmunizada")
    ax.set_ylabel("Fracción afectada final (%)")
    ax.set_title("P9 · Estrategias de inmunización", fontweight="bold")
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

    G = cargar_red(fuente="csv"); verificar(G)

    # Nodo de mayor betweenness (más crítico para cascada)
    btw = nx.betweenness_centrality(G, normalized=False)
    nodo_critico = max(btw, key=btw.get)
    print(f"  Nodo de mayor betweenness: {nodo_critico} ({btw[nodo_critico]:.0f})\n")

    # Ítem 1 & 2: cascada con barrido de α
    print("[Ítem 1-2] Cascada de fallos — barrido de tolerancia α")
    alphas = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    df_casc = barrido_tolerancia(G, nodo_critico, alphas)
    df_casc["nodo_inicial"] = nodo_critico
    df_casc.to_csv(os.path.join(DIR_TAB, "p9_cascada_tolerancia.csv"), index=False)
    print(df_casc.to_string(index=False))
    graficar_cascada(df_casc, nodo_critico)

    # Ítem 3: umbral crítico y modelo SIR
    tau_c = umbral_critico(G)
    print(f"\n[Ítem 3] Umbral crítico τ_c = ⟨k⟩/⟨k²⟩ = {tau_c:.4f}")

    nodo_inf = nodo_critico  # infección empieza en el nodo más central
    beta_sub  = round(tau_c * 0.5, 4)
    beta_sup  = round(tau_c * 2.0, 4)
    gamma_val = 0.1

    df_sub = sir_discreto(G, beta_sub, gamma_val, nodo_inf)
    df_sup = sir_discreto(G, beta_sup, gamma_val, nodo_inf)

    df_sir_all = pd.concat([df_sub.assign(caso="sub_critico", beta=beta_sub),
                             df_sup.assign(caso="sobre_critico", beta=beta_sup)])
    df_sir_all.to_csv(os.path.join(DIR_TAB, "p9_sir_promedio.csv"), index=False)

    R_sub = df_sub["R"].iloc[-1]
    R_sup = df_sup["R"].iloc[-1]
    print(f"  β={beta_sub} (sub-crítico): R_final={R_sub}/{G.number_of_nodes()}")
    print(f"  β={beta_sup} (sobre-crítico): R_final={R_sup}/{G.number_of_nodes()}")
    graficar_sir(df_sub, df_sup, tau_c)

    # Ítem 4: estrategias de inmunización
    print("\n[Ítem 4] Estrategias de inmunización")
    fracciones = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]
    estrategias = ["aleatorio", "grado", "betweenness", "vecino"]
    filas_inm = []
    for est in estrategias:
        for f in fracciones:
            res = inmunizacion(G, beta_sup, gamma_val, f, est, nodo_inf)
            filas_inm.append(res)
            print(f"  {est:15s}  f={f:.2f}  afectados={res['R_final']:>3d}  "
                  f"({res['fraccion_afectada']*100:.1f}%)")

    pd.DataFrame(filas_inm).to_csv(
        os.path.join(DIR_TAB, "p9_inmunizacion.csv"), index=False)
    graficar_inmunizacion(filas_inm)

    # Ítem 5: nodo más crítico
    print(f"\n[Ítem 5] Nodo más crítico:")
    print(f"  Mayor cascada (α=0.1): {nodo_critico}")
    res_cascada0 = cascada_fallos(G, nodo_critico, alpha=0.1)
    print(f"    Nodos fallidos: {res_cascada0['n_fallidos']} ({res_cascada0['fraccion']*100:.1f}%)")
    print(f"    Propagación SIR (β=τ_c×2): R_final={R_sup}")

    print("\n=== P9 completado ===\n")
