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
# Ítem 2 — Ford-Fulkerson con DFS (versión clásica)
# ------------------------------------------------------------
# FUENTE: adaptado de codigo_referencia/ford-fulkerson/ford_fulkerson.jl
# (Dr. Fabián Astudillo-Salinas, Módulo 1217 — Redes Complejas).
# La implementación original en Julia usa buscar_camino_dfs() con una
# pila explícita; aquí se porta a Python manteniendo la misma lógica.

def ford_fulkerson_dfs(grafo_cap: dict, fuente: str, sumidero: str) -> dict:
    """
    Ford-Fulkerson con búsqueda DFS de caminos aumentantes.
    Complejidad: O(E · f*) donde f* es el flujo máximo (puede ser grande
    si las capacidades son altas). No garantiza caminos mínimos.

    Argumentos:
        grafo_cap (dict): {u: {v: capacidad}} — grafo de capacidades.
        fuente    (str) : nodo fuente.
        sumidero  (str) : nodo sumidero.

    Salida:
        dict:
            'flujo_maximo'  — valor del flujo máximo
            'flujo_red'     — {u: {v: flujo}} flujo en cada arco
            'n_iteraciones' — número de caminos aumentantes encontrados
            'long_caminos'  — lista de longitudes de cada camino aumentante
    """
    flujo_red: dict = {u: {v: 0 for v in grafo_cap[u]} for u in grafo_cap}
    for u in grafo_cap:
        for v in grafo_cap[u]:
            if v not in flujo_red:
                flujo_red[v] = {}
            if u not in flujo_red[v]:
                flujo_red[v][u] = 0

    flujo_total  = 0
    n_iter       = 0
    long_caminos = []

    def _dfs_camino():
        """DFS iterativo para encontrar un camino aumentante (cualquiera)."""
        visitado = {fuente}
        pila     = [(fuente, [fuente])]
        while pila:
            u, camino = pila.pop()
            for v in grafo_cap.get(u, {}):
                cap_res = grafo_cap[u][v] - flujo_red[u].get(v, 0)
                if v not in visitado and cap_res > 0:
                    visitado.add(v)
                    nuevo = camino + [v]
                    if v == sumidero:
                        return nuevo
                    pila.append((v, nuevo))
        return None

    while True:
        camino = _dfs_camino()
        if camino is None:
            break
        cuello = min(
            grafo_cap[camino[i]][camino[i+1]] - flujo_red[camino[i]].get(camino[i+1], 0)
            for i in range(len(camino)-1)
        )
        for i in range(len(camino)-1):
            u, v = camino[i], camino[i+1]
            flujo_red[u][v] = flujo_red[u].get(v, 0) + cuello
            flujo_red[v][u] = flujo_red[v].get(u, 0) - cuello
        flujo_total  += cuello
        n_iter       += 1
        long_caminos.append(len(camino) - 1)

    return {
        "flujo_maximo"  : flujo_total,
        "flujo_red"     : flujo_red,
        "n_iteraciones" : n_iter,
        "long_caminos"  : long_caminos,
    }


# ------------------------------------------------------------
# Ítem 2 — Edmonds-Karp (Ford-Fulkerson con BFS)
# ------------------------------------------------------------
# FUENTE: adaptado de codigo_referencia/edmonds-karp/edmonds_karp.jl
# (Dr. Fabián Astudillo-Salinas, Módulo 1217 — Redes Complejas).
# La implementación original registra niveles BFS y árbol de exploración
# para animación; aquí se porta a Python conservando la lógica central.

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

    # Ítem 2 + 3: comparación Ford-Fulkerson (DFS) vs Edmonds-Karp (BFS)
    print("[Ítem 2] Comparación Ford-Fulkerson (DFS) vs Edmonds-Karp (BFS)")
    print(f"  {'Campus':35s}  {'FF-DFS iter':>11}  {'EK-BFS iter':>11}  "
          f"{'Flujo (Mbps)':>12}  {'Long.media DFS':>14}  {'Long.media BFS':>14}")
    print("  " + "-"*97)

    campus_list = sorted(
        nodos_df["campus"].dropna().unique(),
        key=lambda c: len(nodos_df[nodos_df["campus"]==c]), reverse=True)

    filas_comp = []
    for campus in campus_list:
        gc, fuente, sumidero = construir_grafo_flujo(G, nodos_df, aristas_df, campus)
        if gc is None:
            continue
        res_ff  = ford_fulkerson_dfs(gc, fuente, sumidero)
        res_ek  = edmonds_karp(gc, fuente, sumidero)
        lm_ff   = round(sum(res_ff["long_caminos"]) / max(len(res_ff["long_caminos"]), 1), 2)
        lm_ek   = round(sum(res_ek["long_caminos"]) / max(len(res_ek["long_caminos"]), 1), 2)
        n_acc   = len(nodos_df[(nodos_df["campus"]==campus) & (nodos_df["capa"]=="acceso")])
        print(f"  {campus:35s}  {res_ff['n_iteraciones']:>11d}  {res_ek['n_iteraciones']:>11d}  "
              f"{res_ek['flujo_maximo']:>12.0f}  {lm_ff:>14.2f}  {lm_ek:>14.2f}")
        filas_comp.append({
            "campus": campus, "n_acceso": n_acc,
            "flujo_max_mbps": res_ek["flujo_maximo"],
            "iter_ff_dfs": res_ff["n_iteraciones"], "long_media_ff": lm_ff,
            "iter_ek_bfs": res_ek["n_iteraciones"], "long_media_ek": lm_ek,
            "sumidero": sumidero,
        })

    df_comp = pd.DataFrame(filas_comp)
    df_comp.to_csv(os.path.join(DIR_TAB, "p6_comparacion_ff_ek.csv"), index=False)
    print(f"\n  [OK] {os.path.join(DIR_TAB, 'p6_comparacion_ff_ek.csv')}")

    # Ítem 3: flujo por campus (resumen)
    print("\n[Ítem 3] Flujo máximo por campus")
    df_flujo = df_comp[["campus","n_acceso","flujo_max_mbps","iter_ek_bfs","long_media_ek","sumidero"]].copy()
    df_flujo.columns = ["campus","n_acceso","flujo_max_mbps","n_iter","long_media_camino","sumidero"]
    df_flujo.to_csv(os.path.join(DIR_TAB, "p6_flujo_por_campus.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p6_flujo_por_campus.csv')}")
    print(df_flujo.to_string(index=False))

    # Corte mínimo del campus más grande
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

    # Ítem 5: flujo de costo mínimo — dos campus, comparación con flujo máximo puro
    print("\n[Ítem 5] Flujo de costo mínimo — dos campus hacia Internet")
    print("  Campus fuente: Campus Central + Campus Balzay")
    print("  Demanda fija : 5 000 Mbps por campus (total 10 000 Mbps)")
    print("  Costo        : weight = 1 por salto (rutas cortas son más baratas)\n")

    try:
        cap_dict = capacidad_estimada(G, nodos_df, aristas_df)
        DEMANDA_POR_CAMPUS = 5_000   # Mbps
        CAMPUS_FUENTE = ["Campus Central", "Campus Balzay"]
        SUMIDERO = "INTERNET-MPLS"

        # ── Construir digrafo con capacidades y costo=1 por salto ──
        DG = nx.DiGraph()
        for u, v in G.edges():
            c = int(cap_dict.get(frozenset([u, v]), 100))
            DG.add_edge(u, v, capacity=c, weight=1)
            DG.add_edge(v, u, capacity=c, weight=1)

        # Super-nodo fuente por campus
        demanda_total = 0
        for campus in CAMPUS_FUENTE:
            super_s = f"SUPER_{campus.upper().replace(' ','_')}"
            acceso = nodos_df[
                (nodos_df["campus"] == campus) & (nodos_df["capa"] == "acceso")
            ]["id"].tolist()
            # Conectar super-nodo a todos los accesos con capacidad suficiente
            for nodo in acceso:
                DG.add_edge(super_s, nodo, capacity=DEMANDA_POR_CAMPUS, weight=0)
            DG.nodes[super_s]["demand"] = -DEMANDA_POR_CAMPUS
            demanda_total += DEMANDA_POR_CAMPUS

        # El sumidero absorbe toda la demanda
        DG.nodes[SUMIDERO]["demand"] = demanda_total

        # ── Flujo de costo mínimo ──
        flujo_mcf = nx.min_cost_flow(DG)
        costo_mcf = nx.cost_of_flow(DG, flujo_mcf)

        # Calcular longitud media de las rutas usadas (aproximación: costo/flujo)
        flujo_enviado = sum(
            flujo_mcf.get(SUMIDERO, {}).get(v, 0)
            + flujo_mcf.get(v, {}).get(SUMIDERO, 0)
            for v in DG.predecessors(SUMIDERO)
        )
        saltos_medio_mcf = costo_mcf / demanda_total if demanda_total > 0 else 0

        print(f"  [Costo Mínimo]  Flujo enviado: {demanda_total:,} Mbps  "
              f"Costo total: {costo_mcf:,} saltos·Mbps  "
              f"Saltos medio: {saltos_medio_mcf:.2f}")

        # ── Flujo máximo puro (sin restricción de demanda) ──
        # Construir grafo de capacidades para EK (mismos dos campus)
        gc_combinado: dict = {}
        for u in DG.nodes():
            gc_combinado[u] = {}
        for u, v, data in DG.edges(data=True):
            gc_combinado[u][v] = data["capacity"]

        res_fm = edmonds_karp(gc_combinado,
                              f"SUPER_CAMPUS_CENTRAL", SUMIDERO)
        flujo_maximo_cc = res_fm["flujo_maximo"]
        res_fm2 = edmonds_karp(gc_combinado,
                               f"SUPER_CAMPUS_BALZAY", SUMIDERO)
        flujo_maximo_bal = res_fm2["flujo_maximo"]

        lm_cc  = (sum(res_fm["long_caminos"]) / len(res_fm["long_caminos"])
                  if res_fm["long_caminos"] else 0)
        lm_bal = (sum(res_fm2["long_caminos"]) / len(res_fm2["long_caminos"])
                  if res_fm2["long_caminos"] else 0)

        print(f"  [Flujo Máximo]  Campus Central: {flujo_maximo_cc:,} Mbps  "
              f"Saltos medio: {lm_cc:.2f}")
        print(f"  [Flujo Máximo]  Campus Balzay : {flujo_maximo_bal:,} Mbps  "
              f"Saltos medio: {lm_bal:.2f}")

        print(f"\n  Comparación:")
        print(f"    Costo mínimo envía {demanda_total:,} Mbps con saltos medio {saltos_medio_mcf:.2f}")
        print(f"    Flujo máximo podría enviar hasta {flujo_maximo_cc+flujo_maximo_bal:,} Mbps")
        print(f"    pero lo haría con saltos medio {(lm_cc+lm_bal)/2:.2f} (rutas más largas al saturar toda la red)")

        # Guardar resumen
        resumen_item5 = (
            f"Flujo de costo mínimo\n"
            f"  Campus fuente  : {', '.join(CAMPUS_FUENTE)}\n"
            f"  Demanda total  : {demanda_total:,} Mbps\n"
            f"  Costo total    : {costo_mcf:,} saltos·Mbps\n"
            f"  Saltos medio   : {saltos_medio_mcf:.2f}\n\n"
            f"Flujo máximo puro\n"
            f"  Campus Central : {flujo_maximo_cc:,} Mbps  (saltos medio {lm_cc:.2f})\n"
            f"  Campus Balzay  : {flujo_maximo_bal:,} Mbps  (saltos medio {lm_bal:.2f})\n"
        )
        with open(os.path.join(DIR_TAB, "p6_costo_minimo.txt"), "w", encoding="utf-8") as f:
            f.write(resumen_item5)
        print(f"  [OK] {os.path.join(DIR_TAB, 'p6_costo_minimo.txt')}")

    except Exception as e:
        print(f"  Error en flujo de costo mínimo: {e}")

    print("\n=== P6 completado ===\n")
