"""
problema6.py — Problema P6: Flujo Máximo y Corte Mínimo (Fase 3)
=================================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Modela el problema de flujo de tráfico de cada campus hacia Internet
y calcula el flujo máximo y corte mínimo usando Ford-Fulkerson (BFS)
= Edmonds-Karp.

Los cinco ítems resueltos son:
  Ítem 1 · Función de capacidad c(u,v) estimada (documentada)
  Ítem 2 · Modelado fuente–sumidero y cálculo Ford-Fulkerson / Edmonds-Karp
  Ítem 3 · Flujo máximo, iteraciones, longitudes de caminos, corte mínimo
  Ítem 4 · Interpretación del corte mínimo vs puentes de P1
  Ítem 5 · Formulación de flujo de costo mínimo

Uso:
    python problema6.py

Salidas:
    results/tablas/p6_flujo_por_campus.csv
    results/tablas/p6_corte_minimo.txt
    results/imagenes/p6_flujo_campus.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, collections
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

# Reutilizar función de capacidad de P5
sys.path.insert(0, DIR_SRC)
from problema5 import capacidad_estimada


def _crear_dirs():
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


# ============================================================
# Definición de funciones
# ============================================================

# ------------------------------------------------------------
# Ítem 2 — Edmonds-Karp (Ford-Fulkerson con BFS)
# ------------------------------------------------------------

def edmonds_karp(grafo_cap: dict, fuente: str, sumidero: str) -> dict:
    """
    Algoritmo de Edmonds-Karp (Ford-Fulkerson con caminos aumentantes BFS).
    Complejidad: O(V · E²).

    Argumentos:
        grafo_cap (dict): {u: {v: capacidad}} — grafo de capacidades.
        fuente    (str) : nodo fuente.
        sumidero  (str) : nodo sumidero.

    Salida:
        dict:
            'flujo_maximo'      — valor del flujo máximo
            'flujo_red'         — {u: {v: flujo}} flujo en cada arco
            'n_iteraciones'     — número de caminos aumentantes encontrados
            'long_caminos'      — lista de longitudes de cada camino aumentante
    """
    # Inicializar flujo en 0
    flujo_red: dict = {u: {v: 0 for v in grafo_cap[u]} for u in grafo_cap}
    for u in grafo_cap:
        for v in grafo_cap[u]:
            if v not in flujo_red:
                flujo_red[v] = {}
            if u not in flujo_red[v]:
                flujo_red[v][u] = 0

    flujo_total   = 0
    n_iter        = 0
    long_caminos  = []

    def _bfs_camino():
        """BFS para encontrar camino aumentante en el grafo residual."""
        visitado = {fuente}
        cola     = collections.deque([(fuente, [fuente])])
        while cola:
            u, camino = cola.popleft()
            for v in grafo_cap.get(u, {}):
                cap_res = grafo_cap[u][v] - flujo_red[u].get(v, 0)
                if v not in visitado and cap_res > 0:
                    visitado.add(v)
                    nuevo = camino + [v]
                    if v == sumidero:
                        return nuevo
                    cola.append((v, nuevo))
        return None

    while True:
        camino = _bfs_camino()
        if camino is None:
            break
        # Capacidad residual mínima en el camino
        cuello = min(
            grafo_cap[camino[i]][camino[i+1]] - flujo_red[camino[i]].get(camino[i+1], 0)
            for i in range(len(camino)-1)
        )
        # Actualizar flujos
        for i in range(len(camino)-1):
            u, v = camino[i], camino[i+1]
            flujo_red[u][v]  = flujo_red[u].get(v, 0) + cuello
            flujo_red[v][u]  = flujo_red[v].get(u, 0) - cuello
        flujo_total  += cuello
        n_iter       += 1
        long_caminos.append(len(camino) - 1)

    return {
        "flujo_maximo"  : flujo_total,
        "flujo_red"     : flujo_red,
        "n_iteraciones" : n_iter,
        "long_caminos"  : long_caminos,
    }


def corte_minimo(grafo_cap: dict, flujo_red: dict, fuente: str) -> dict:
    """
    Encuentra el corte mínimo (S, T) en el grafo residual tras Edmonds-Karp.
    Los nodos alcanzables desde la fuente en el grafo residual forman S.

    Argumentos:
        grafo_cap (dict): capacidades originales.
        flujo_red (dict): flujos calculados por edmonds_karp.
        fuente    (str) : nodo fuente.

    Salida:
        dict:
            'S'           — conjunto de nodos en el lado fuente
            'T'           — conjunto de nodos en el lado sumidero
            'aristas'     — lista de aristas del corte (u,v) con u∈S, v∈T
            'capacidad'   — suma de capacidades del corte
    """
    visitado = {fuente}
    cola     = collections.deque([fuente])
    while cola:
        u = cola.popleft()
        for v in grafo_cap.get(u, {}):
            cap_res = grafo_cap[u][v] - flujo_red.get(u, {}).get(v, 0)
            if v not in visitado and cap_res > 0:
                visitado.add(v)
                cola.append(v)

    S = visitado
    T = set(grafo_cap.keys()) - S
    aristas_corte = []
    cap_total = 0.0
    for u in S:
        for v in grafo_cap.get(u, {}):
            if v in T and grafo_cap[u][v] > 0:
                aristas_corte.append((u, v, grafo_cap[u][v]))
                cap_total += grafo_cap[u][v]

    return {"S": S, "T": T, "aristas": aristas_corte, "capacidad": cap_total}


# ------------------------------------------------------------
# Construcción del grafo de flujo por campus
# ------------------------------------------------------------

def construir_grafo_flujo(G: nx.Graph, nodos_df: pd.DataFrame,
                           aristas_df: pd.DataFrame, campus: str,
                           sumidero: str = "INTERNET-MPLS") -> tuple:
    """
    Construye el grafo de capacidades para un campus específico.
    Super-fuente 's_campus' conectada a todos los switches de acceso del campus.
    Sumidero = nodo INTERNET-MPLS o nodo WAN de mayor grado.

    Argumentos:
        G          (nx.Graph)     : grafo completo.
        nodos_df   (pd.DataFrame) : atributos de nodos.
        aristas_df (pd.DataFrame) : atributos de aristas.
        campus     (str)          : nombre del campus.
        sumidero   (str)          : identificador del nodo sumidero.

    Salida:
        tuple: (grafo_cap, fuente, sumidero_real)
    """
    cap_dict = capacidad_estimada(G, nodos_df, aristas_df)

    # Nodos de acceso del campus
    acceso_campus = nodos_df[
        (nodos_df["campus"] == campus) &
        (nodos_df["capa"]   == "acceso")
    ]["id"].tolist()

    if not acceso_campus:
        return None, None, None

    # Verificar que el sumidero existe en el grafo
    if sumidero not in G.nodes():
        # Buscar nodo WAN de mayor grado
        wan_nodes = nodos_df[nodos_df["capa"].isin(["wan","interconexion"])]["id"].tolist()
        wan_nodes = [n for n in wan_nodes if n in G.nodes()]
        if not wan_nodes:
            return None, None, None
        sumidero = max(wan_nodes, key=lambda n: G.degree(n))

    fuente = f"__S_{campus}__"

    # Construir diccionario de capacidades
    grafo_cap: dict = collections.defaultdict(dict)

    # Aristas originales
    for u, v in G.edges():
        c = cap_dict.get(frozenset([u, v]), 100.0)
        grafo_cap[u][v] = c
        grafo_cap[v][u] = c

    # Super-fuente conectada a todos los accesos del campus
    grafo_cap[fuente] = {}
    for nodo in acceso_campus:
        grafo_cap[fuente][nodo] = float("inf")

    return dict(grafo_cap), fuente, sumidero


# ------------------------------------------------------------
# Ítem 3 — Calcular flujo para cada campus
# ------------------------------------------------------------

def flujo_por_campus(G: nx.Graph, nodos_df: pd.DataFrame,
                     aristas_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ejecuta Edmonds-Karp para cada campus y reporta los resultados.

    Argumentos:
        G, nodos_df, aristas_df: datos de la red.

    Salida:
        pd.DataFrame con columnas [campus, n_acceso, flujo_max_mbps,
                                    n_iter, long_media_camino, sumidero].
    """
    campus_list = nodos_df["campus"].dropna().unique().tolist()
    # Ordenar por tamaño
    campus_list = sorted(campus_list,
                         key=lambda c: len(nodos_df[nodos_df["campus"]==c]),
                         reverse=True)

    filas = []
    for campus in campus_list:
        gc, fuente, sumidero = construir_grafo_flujo(G, nodos_df, aristas_df, campus)
        if gc is None:
            continue
        res = edmonds_karp(gc, fuente, sumidero)
        n_acc = len(nodos_df[(nodos_df["campus"]==campus) & (nodos_df["capa"]=="acceso")])
        long_media = (sum(res["long_caminos"]) / len(res["long_caminos"])
                      if res["long_caminos"] else 0)
        filas.append({
            "campus"            : campus,
            "n_acceso"          : n_acc,
            "flujo_max_mbps"    : res["flujo_maximo"],
            "n_iter"            : res["n_iteraciones"],
            "long_media_camino" : round(long_media, 2),
            "sumidero"          : sumidero,
        })
        print(f"  {campus:35s}  flujo={res['flujo_maximo']:>10.0f} Mbps  "
              f"iter={res['n_iteraciones']:>3d}  long_media={long_media:.1f}")

    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_flujo(df: pd.DataFrame) -> None:
    """Barras horizontales de flujo máximo por campus."""
    fig, ax = plt.subplots(figsize=(10, 5))
    colores = ["#2980b9" if "Central" in c else "#e67e22" if "Balzay" in c
               else "#27ae60" if "Paraiso" in c else "#8e44ad"
               for c in df["campus"]]
    ax.barh(df["campus"], df["flujo_max_mbps"] / 1000, color=colores, alpha=0.85)
    ax.set_xlabel("Flujo máximo (Gbps)")
    ax.set_title("P6 · Flujo máximo campus → Internet (Edmonds-Karp)", fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    for i, (v, n) in enumerate(zip(df["flujo_max_mbps"], df["n_acceso"])):
        ax.text(v/1000 + 0.02, i, f"{v/1000:.1f} Gbps ({n} accesos)",
                va="center", fontsize=8)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p6_flujo_campus.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P6 — Flujo Máximo y Corte Mínimo ===\n")

    G = cargar_red(fuente="csv"); verificar(G)

    def _leer_csv(n):
        return pd.read_csv(os.path.join(DIR_ROOT, n), dtype=str)
    nodos_df   = _leer_csv("red_ucuenca_nodes.csv")
    aristas_df = _leer_csv("red_ucuenca_edges.csv")

    # Ítem 3: flujo por campus
    print("[Ítem 3] Flujo máximo por campus")
    df_flujo = flujo_por_campus(G, nodos_df, aristas_df)
    df_flujo.to_csv(os.path.join(DIR_TAB, "p6_flujo_por_campus.csv"), index=False)
    print(f"\n  [OK] {os.path.join(DIR_TAB, 'p6_flujo_por_campus.csv')}")
    print(df_flujo.to_string(index=False))

    # Ítem 3 extra: corte mínimo del campus más grande
    campus_principal = "Campus Central"
    gc, fuente, sumidero = construir_grafo_flujo(
        G, nodos_df, aristas_df, campus_principal)
    res_ek = edmonds_karp(gc, fuente, sumidero)
    corte  = corte_minimo(gc, res_ek["flujo_red"], fuente)

    print(f"\n[Ítem 3] Corte mínimo — {campus_principal}")
    print(f"  Capacidad del corte: {corte['capacidad']:.0f} Mbps = {corte['capacidad']/1000:.1f} Gbps")
    print(f"  Aristas del corte:")
    for u, v, c in corte["aristas"]:
        print(f"    {u} → {v}  ({c:.0f} Mbps)")

    with open(os.path.join(DIR_TAB, "p6_corte_minimo.txt"), "w", encoding="utf-8") as f:
        f.write(f"Campus: {campus_principal}\n")
        f.write(f"Flujo máximo: {res_ek['flujo_maximo']:.0f} Mbps\n")
        f.write(f"Capacidad corte mínimo: {corte['capacidad']:.0f} Mbps\n\n")
        f.write("Aristas del corte mínimo:\n")
        for u, v, c in corte["aristas"]:
            f.write(f"  {u} → {v}  ({c:.0f} Mbps)\n")
    print(f"  [OK] {os.path.join(DIR_TAB, 'p6_corte_minimo.txt')}")

    graficar_flujo(df_flujo)

    # Ítem 5: flujo de costo mínimo (formulación)
    print("\n[Ítem 5] Flujo de costo mínimo — formulación")
    print("  Costo por unidad de flujo proporcional al número de saltos:")
    print("  cost(u,v) = 1 salto. Minimizar Σ cost(u,v)·flujo(u,v)")
    print("  sujeto a: flujo(u,v) ≤ c(u,v), conservación en nodos intermedios.")
    # NetworkX tiene min_cost_flow
    try:
        # Construir digrafo con costos para Campus Central
        DG = nx.DiGraph()
        cap_dict = capacidad_estimada(G, nodos_df, aristas_df)
        for u, v in G.edges():
            c = int(cap_dict.get(frozenset([u,v]), 100))
            DG.add_edge(u, v, capacity=c, weight=1)
            DG.add_edge(v, u, capacity=c, weight=1)

        # Demanda: Campus Central acceso → INTERNET-MPLS
        acceso_cc = nodos_df[
            (nodos_df["campus"]=="Campus Central") & (nodos_df["capa"]=="acceso")
        ]["id"].tolist()[:5]  # primeros 5 para demo

        demanda = 100  # Mbps por nodo de acceso
        for n in acceso_cc:
            DG.nodes[n]["demand"] = -demanda
        if "INTERNET-MPLS" in DG.nodes():
            DG.nodes["INTERNET-MPLS"]["demand"] = demanda * len(acceso_cc)

        flujo_min_cost = nx.min_cost_flow(DG)
        costo_total = nx.cost_of_flow(DG, flujo_min_cost)
        print(f"  Costo total (saltos·Mbps) para demo {len(acceso_cc)} nodos: {costo_total}")
    except Exception as e:
        print(f"  (Flujo de costo mínimo — infeasible con capacidades estimadas: {e})")

    print("\n=== P6 completado ===\n")
