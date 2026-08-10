"""
problema7.py — Problema P7: p-Mediana y p-Centro (Fase 3)
==========================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Modela el problema de localización óptima de p servidores/repetidores:
  - p-Mediana  : minimiza la suma total de distancias desde cada nodo al
                  servidor asignado. ⟹ optimiza la latencia promedio.
  - p-Centro   : minimiza la máxima distancia de cualquier nodo al servidor
                  más cercano. ⟹ garantiza cobertura equitativa (min-max).

Los cinco ítems resueltos son:
  Ítem 1 · Matriz de distancias mínimas (Dijkstra con pesos por saltos)
  Ítem 2 · Heurística greedy para p-Mediana con p∈{1,2,3,5}
  Ítem 3 · Heurística greedy para p-Centro con p∈{1,2,3,5}
  Ítem 4 · Comparación de mediana/centro óptimos con centralidades (P1)
  Ítem 5 · Discusión de ventajas de c/modelo según objetivos de red

Uso:
    python problema7.py

Salidas:
    results/tablas/p7_mediana.csv
    results/tablas/p7_centro.csv
    results/tablas/p7_comparacion_centralidades.csv
    results/imagenes/p7_mediana_vs_centro.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, heapq
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
# Ítem 1 — Dijkstra y construcción de matriz de distancias
# ------------------------------------------------------------

def dijkstra_saltos(G: nx.Graph, origen: str) -> dict:
    """
    Dijkstra con peso uniforme (saltos) desde 'origen'.
    Complejidad: O((n+m) log n).

    Argumentos:
        G      (nx.Graph): grafo.
        origen (str)     : nodo de origen.

    Salida:
        dict {nodo: distancia_saltos}
    """
    dist = {n: float("inf") for n in G.nodes()}
    dist[origen] = 0
    heap = [(0, origen)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v in G.neighbors(u):
            nd = dist[u] + 1
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def matriz_distancias(G: nx.Graph) -> tuple:
    """
    Construye la matriz de distancias (saltos) N×N entre todos los pares.

    Argumentos:
        G (nx.Graph): grafo.

    Salida:
        tuple: (nodos_lista, D) donde D es np.ndarray N×N.
    """
    nodos = list(G.nodes())
    N = len(nodos)
    idx = {n: i for i, n in enumerate(nodos)}
    D = np.full((N, N), np.inf)
    for n in nodos:
        dists = dijkstra_saltos(G, n)
        for m, d in dists.items():
            D[idx[n]][idx[m]] = d
    return nodos, D


# ------------------------------------------------------------
# Ítem 2 — p-Mediana (greedy)
# ------------------------------------------------------------

def p_mediana_greedy(nodos: list, D: np.ndarray, p: int) -> dict:
    """
    Heurística greedy para p-Mediana.
    Paso 1: elige el nodo que minimiza la suma total de distancias.
    Paso 2: añade sucesivamente el nodo que más reduce la función objetivo.

    Argumentos:
        nodos (list)     : lista de identificadores de nodos.
        D     (np.ndarray): matriz N×N de distancias.
        p     (int)      : número de medianas.

    Salida:
        dict:
            'medianas'       — lista de p nodos seleccionados
            'asignacion'     — {nodo: mediana_asignada}
            'obj'            — valor de la función objetivo Σ min_j d(i,j)
    """
    N = len(nodos)
    seleccionados = []
    dist_min = np.full(N, np.inf)

    for _ in range(p):
        mejor_cand = None
        mejor_red  = -np.inf
        for j in range(N):
            if nodos[j] in seleccionados:
                continue
            nueva_dist = np.minimum(dist_min, D[:, j])
            red = np.sum(dist_min[dist_min < np.inf]) - np.sum(nueva_dist[nueva_dist < np.inf])
            if red > mejor_red:
                mejor_red  = red
                mejor_cand = j
        dist_min = np.minimum(dist_min, D[:, mejor_cand])
        seleccionados.append(nodos[mejor_cand])

    # Asignación de cada nodo a su mediana más cercana
    asignacion = {}
    for i, n in enumerate(nodos):
        dists_sel = {s: D[i][nodos.index(s)] for s in seleccionados}
        asignacion[n] = min(dists_sel, key=dists_sel.get)

    obj = sum(D[i][nodos.index(asignacion[nodos[i]])]
              for i in range(N) if D[i][nodos.index(asignacion[nodos[i]])] < np.inf)

    return {"medianas": seleccionados, "asignacion": asignacion, "obj": obj}


# ------------------------------------------------------------
# Ítem 3 — p-Centro (greedy)
# ------------------------------------------------------------

def p_centro_greedy(nodos: list, D: np.ndarray, p: int) -> dict:
    """
    Heurística greedy para p-Centro.
    Selecciona el nodo que más reduce la distancia máxima de cobertura.

    Argumentos:
        nodos (list)     : lista de identificadores de nodos.
        D     (np.ndarray): matriz N×N de distancias.
        p     (int)      : número de centros.

    Salida:
        dict:
            'centros'    — lista de p nodos seleccionados
            'asignacion' — {nodo: centro_asignado}
            'radio'      — radio de cobertura máximo (minimax)
    """
    N = len(nodos)
    seleccionados = []
    dist_min = np.full(N, np.inf)

    for _ in range(p):
        mejor_cand = None
        mejor_radio = np.inf
        for j in range(N):
            if nodos[j] in seleccionados:
                continue
            nueva_dist = np.minimum(dist_min, D[:, j])
            radio = np.max(nueva_dist[nueva_dist < np.inf])
            if radio < mejor_radio:
                mejor_radio = radio
                mejor_cand  = j
        dist_min = np.minimum(dist_min, D[:, mejor_cand])
        seleccionados.append(nodos[mejor_cand])

    asignacion = {}
    for i, n in enumerate(nodos):
        dists_sel = {s: D[i][nodos.index(s)] for s in seleccionados}
        asignacion[n] = min(dists_sel, key=dists_sel.get)

    radio = max(D[i][nodos.index(asignacion[nodos[i]])]
                for i in range(N) if D[i][nodos.index(asignacion[nodos[i]])] < np.inf)

    return {"centros": seleccionados, "asignacion": asignacion, "radio": radio}


# ------------------------------------------------------------
# Ítem 4 — Comparación con centralidades
# ------------------------------------------------------------

def comparar_con_centralidades(G: nx.Graph, nodos: list,
                                mediana1: str, centro1: str) -> pd.DataFrame:
    """
    Compara la 1-mediana y el 1-centro con el ranking por centralidades.

    Argumentos:
        G        (nx.Graph): grafo.
        nodos    (list)    : todos los nodos.
        mediana1 (str)     : nodo óptimo de la 1-mediana.
        centro1  (str)     : nodo óptimo del 1-centro.

    Salida:
        pd.DataFrame con el ranking de cada nodo por cada métrica.
    """
    deg_c  = nx.degree_centrality(G)
    btw_c  = nx.betweenness_centrality(G, normalized=True)
    clo_c  = nx.closeness_centrality(G)
    # Eigenvector puede fallar en no conexos; usar try/except
    try:
        eig_c = nx.eigenvector_centrality(G, max_iter=500)
    except Exception:
        eig_c = {n: 0 for n in G.nodes()}

    data = []
    for n in G.nodes():
        data.append({
            "nodo"        : n,
            "deg_c"       : round(deg_c.get(n, 0), 4),
            "btw_c"       : round(btw_c.get(n, 0), 4),
            "clo_c"       : round(clo_c.get(n, 0), 4),
            "eig_c"       : round(eig_c.get(n, 0), 4),
            "es_mediana1" : (n == mediana1),
            "es_centro1"  : (n == centro1),
        })
    df = pd.DataFrame(data)
    df["rank_deg"] = df["deg_c"].rank(ascending=False).astype(int)
    df["rank_btw"] = df["btw_c"].rank(ascending=False).astype(int)
    df["rank_clo"] = df["clo_c"].rank(ascending=False).astype(int)
    df["rank_eig"] = df["eig_c"].rank(ascending=False).astype(int)
    return df.sort_values("rank_clo")


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_mediana_centro(p_vals: list, obj_med: list, radios: list) -> None:
    """Comparativa de objetivo de p-Mediana y radio de p-Centro vs p."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(p_vals, obj_med, "bo-", linewidth=2, markersize=8)
    ax1.set_xlabel("p (número de servidores)")
    ax1.set_ylabel("Suma total de distancias (saltos)")
    ax1.set_title("p-Mediana: función objetivo")
    ax1.grid(alpha=0.3)
    for p, v in zip(p_vals, obj_med):
        ax1.annotate(f"{v:.0f}", (p, v), textcoords="offset points",
                     xytext=(5, 5), fontsize=9)

    ax2.plot(p_vals, radios, "rs-", linewidth=2, markersize=8)
    ax2.set_xlabel("p (número de servidores)")
    ax2.set_ylabel("Radio máximo de cobertura (saltos)")
    ax2.set_title("p-Centro: minimax radio")
    ax2.grid(alpha=0.3)
    for p, v in zip(p_vals, radios):
        ax2.annotate(f"{v:.0f}", (p, v), textcoords="offset points",
                     xytext=(5, 5), fontsize=9)

    plt.suptitle("P7 · p-Mediana y p-Centro — Red UCuenca", fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p7_mediana_vs_centro.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P7 — p-Mediana y p-Centro ===\n")

    G = cargar_red(fuente="csv"); verificar(G)

    # Ítem 1: Matriz de distancias
    print("[Ítem 1] Construyendo matriz de distancias (saltos)...")
    nodos, D = matriz_distancias(G)
    print(f"  Matriz {len(nodos)}×{len(nodos)} completada.")

    P_VALS = [1, 2, 3, 5]
    filas_med, filas_cen = [], []
    obj_med_vals, radio_vals = [], []

    for p in P_VALS:
        # Ítem 2: p-Mediana
        res_m = p_mediana_greedy(nodos, D, p)
        print(f"\n[Ítem 2] p-Mediana p={p}")
        print(f"  Medianas    : {res_m['medianas']}")
        print(f"  Objetivo    : {res_m['obj']:.1f} saltos·nodo")
        filas_med.append({
            "p"        : p,
            "medianas" : "; ".join(res_m["medianas"]),
            "objetivo" : round(res_m["obj"], 2),
        })
        obj_med_vals.append(res_m["obj"])

        # Ítem 3: p-Centro
        res_c = p_centro_greedy(nodos, D, p)
        print(f"[Ítem 3] p-Centro  p={p}")
        print(f"  Centros     : {res_c['centros']}")
        print(f"  Radio       : {res_c['radio']} saltos")
        filas_cen.append({
            "p"      : p,
            "centros": "; ".join(res_c["centros"]),
            "radio"  : res_c["radio"],
        })
        radio_vals.append(res_c["radio"])

    df_med = pd.DataFrame(filas_med)
    df_cen = pd.DataFrame(filas_cen)
    df_med.to_csv(os.path.join(DIR_TAB, "p7_mediana.csv"), index=False)
    df_cen.to_csv(os.path.join(DIR_TAB, "p7_centro.csv"),  index=False)
    print(f"\n  [OK] p7_mediana.csv y p7_centro.csv")

    # Ítem 4: comparar con centralidades (p=1)
    print("\n[Ítem 4] Comparación con centralidades (p=1)")
    res_m1 = p_mediana_greedy(nodos, D, 1)
    res_c1 = p_centro_greedy(nodos, D, 1)
    print(f"  1-Mediana: {res_m1['medianas'][0]}")
    print(f"  1-Centro : {res_c1['centros'][0]}")

    df_comp = comparar_con_centralidades(G, nodos,
                                          res_m1["medianas"][0],
                                          res_c1["centros"][0])
    df_comp.to_csv(os.path.join(DIR_TAB, "p7_comparacion_centralidades.csv"), index=False)
    print(f"\n  Top-10 por closeness:")
    cols = ["nodo","clo_c","rank_clo","rank_btw","es_mediana1","es_centro1"]
    print(df_comp[cols].head(10).to_string(index=False))

    # Mostrar posición de la mediana y centro en rankings
    row_m = df_comp[df_comp["nodo"] == res_m1["medianas"][0]].iloc[0]
    row_c = df_comp[df_comp["nodo"] == res_c1["centros"][0]].iloc[0]
    print(f"\n  1-Mediana '{row_m['nodo']}': rank_clo={row_m['rank_clo']}, rank_btw={row_m['rank_btw']}")
    print(f"  1-Centro  '{row_c['nodo']}': rank_clo={row_c['rank_clo']}, rank_btw={row_c['rank_btw']}")

    # Visualización
    graficar_mediana_centro(P_VALS, obj_med_vals, radio_vals)

    print("\n=== P7 completado ===\n")
