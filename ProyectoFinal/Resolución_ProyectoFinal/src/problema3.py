"""
problema3.py — Problema P3: BFS y DFS sobre la Red (Fase 2)
============================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Implementa BFS y DFS desde cero (sin usar nx.bfs_* ni nx.dfs_*)
y los aplica sobre la red de datos UCuenca para responder preguntas
estructurales sobre jerarquía, alcanzabilidad y ciclos.

Los cinco ítems resueltos son:
  Ítem 1 · BFS y DFS desde cero — estructura de datos y complejidad
  Ítem 2 · Perfil de profundidad BFS desde el core del Campus Central
  Ítem 3 · Perfil de profundidad BFS desde la nube MPLS
  Ítem 4 · Detección de ciclos con DFS y relación con redundancia
  Ítem 5 · BFS vs DFS para inspección física de armarios

Uso:
    python problema3.py

Salidas (relativas a Resolución_ProyectoFinal/):
    results/tablas/p3_perfil_core.csv
    results/tablas/p3_perfil_mpls.csv
    results/tablas/p3_ciclos.txt
    results/imagenes/p3_perfil_profundidad.png
    results/imagenes/p3_ciclos.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os
import sys
import collections

import networkx as nx
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# --- Rutas del proyecto ---
DIR_SRC   = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL = os.path.dirname(DIR_SRC)
DIR_ROOT  = os.path.dirname(DIR_RESOL)
DIR_BASE  = os.path.join(DIR_ROOT, "codigo_base")
DIR_TAB   = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG   = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar  # noqa: E402


# ============================================================
# Definición de funciones
# ============================================================

# ------------------------------------------------------------
# Utilidades internas
# ------------------------------------------------------------

def _crear_dirs() -> None:
    """
    Crea los directorios de salida si no existen.

    Argumentos: ninguno
    Salida: None
    """
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


def _gcc(G: nx.Graph) -> nx.Graph:
    """
    Devuelve la componente conexa gigante del grafo.

    Argumentos:
        G (nx.Graph): grafo de entrada.

    Salida:
        nx.Graph: subgrafo inducido por la GCC.
    """
    gcc_nodes = max(nx.connected_components(G), key=len)
    return G.subgraph(gcc_nodes).copy()


# ------------------------------------------------------------
# Ítem 1 — BFS y DFS desde cero
# ------------------------------------------------------------

def bfs(G: nx.Graph, origen: str) -> dict:
    """
    Búsqueda en anchura (BFS) implementada desde cero con una cola FIFO.
    Complejidad temporal: O(n + m).  Complejidad espacial: O(n).

    Argumentos:
        G      (nx.Graph): grafo no dirigido.
        origen (str)     : nodo raíz del recorrido.

    Salida:
        dict con claves:
            'distancia'  — {nodo: distancia en saltos desde origen}
            'predecesor' — {nodo: nodo padre en el árbol BFS}
            'orden'      — lista de nodos en orden de visita
            'niveles'    — {distancia: [nodos a esa distancia]}
    """
    visitado   = {origen}
    distancia  = {origen: 0}
    predecesor = {origen: None}
    orden      = [origen]
    cola       = collections.deque([origen])

    while cola:
        u = cola.popleft()
        for v in G.neighbors(u):
            if v not in visitado:
                visitado.add(v)
                distancia[v]  = distancia[u] + 1
                predecesor[v] = u
                orden.append(v)
                cola.append(v)

    # Agrupar nodos por nivel (distancia)
    niveles: dict[int, list] = collections.defaultdict(list)
    for nodo, d in distancia.items():
        niveles[d].append(nodo)

    return {
        "distancia" : distancia,
        "predecesor": predecesor,
        "orden"     : orden,
        "niveles"   : dict(niveles),
    }


def dfs(G: nx.Graph, origen: str) -> dict:
    """
    Búsqueda en profundidad (DFS) implementada desde cero con una pila LIFO.
    Complejidad temporal: O(n + m).  Complejidad espacial: O(n).

    Durante el recorrido clasifica cada arista como:
      - 'árbol'   : arista usada para descubrir un nodo nuevo.
      - 'retroceso': arista que apunta a un ancestro ya visitado → ciclo.

    Argumentos:
        G      (nx.Graph): grafo no dirigido.
        origen (str)     : nodo raíz del recorrido.

    Salida:
        dict con claves:
            'orden'       — lista de nodos en orden de visita (DFS)
            'predecesor'  — {nodo: nodo padre en el árbol DFS}
            'tiempo_desc' — {nodo: tiempo de descubrimiento}
            'tiempo_fin'  — {nodo: tiempo de finalización}
            'aristas_arbol'    — lista de aristas de árbol (u, v)
            'aristas_retroceso'— lista de aristas de retroceso (u, v)
    """
    visitado       = set()
    predecesor     = {origen: None}
    tiempo_desc    = {}
    tiempo_fin     = {}
    orden          = []
    aristas_arbol  = []
    aristas_retro  = []
    tiempo         = [0]   # mutable para modificar dentro de la función auxiliar

    def _dfs_recursivo(u: str, padre: str) -> None:
        visitado.add(u)
        tiempo[0] += 1
        tiempo_desc[u] = tiempo[0]
        orden.append(u)

        for v in G.neighbors(u):
            if v not in visitado:
                predecesor[v] = u
                aristas_arbol.append((u, v))
                _dfs_recursivo(v, u)
            elif v != padre:
                # Arista de retroceso (en grafo no dirigido, excluir padre)
                aristas_retro.append((u, v))

        tiempo[0] += 1
        tiempo_fin[u] = tiempo[0]

    # Recorrer la componente del origen
    _dfs_recursivo(origen, None)

    # Manejar posibles nodos desconectados del origen
    for nodo in G.nodes():
        if nodo not in visitado:
            predecesor[nodo] = None
            _dfs_recursivo(nodo, None)

    return {
        "orden"              : orden,
        "predecesor"         : predecesor,
        "tiempo_desc"        : tiempo_desc,
        "tiempo_fin"         : tiempo_fin,
        "aristas_arbol"      : aristas_arbol,
        "aristas_retroceso"  : aristas_retro,
    }


# ------------------------------------------------------------
# Ítem 2 — Perfil de profundidad BFS desde el core
# ------------------------------------------------------------

def perfil_bfs_core(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Ejecuta BFS desde el switch de core del Campus Central con mayor grado
    y construye el perfil de profundidad: número de nodos a cada distancia.

    Argumentos:
        G        (nx.Graph)     : grafo completo.
        nodos_df (pd.DataFrame) : atributos de nodos (id, campus, capa).

    Salida:
        dict con claves:
            'origen'  — identificador del nodo origen
            'bfs'     — resultado completo de bfs()
            'perfil'  — DataFrame(distancia, n_nodos, capas_dominantes)
    """
    # Identificar switches de core del Campus Central
    mask_core_cc = (
        (nodos_df["capa"] == "core") &
        (nodos_df["campus"].str.contains("Central", case=False, na=False))
    )
    core_cc = nodos_df[mask_core_cc]["id"].tolist()
    if not core_cc:
        # Fallback: cualquier nodo de capa core
        core_cc = nodos_df[nodos_df["capa"] == "core"]["id"].tolist()

    # Elegir el de mayor grado
    origen = max(core_cc, key=lambda n: G.degree(n))
    print(f"  [BFS-core] Origen: {origen}  (grado={G.degree(origen)})")

    resultado_bfs = bfs(G, origen)

    # Construir perfil de profundidad con info de capas
    filas = []
    for dist in sorted(resultado_bfs["niveles"].keys()):
        nodos_nivel = resultado_bfs["niveles"][dist]
        capas = (
            nodos_df[nodos_df["id"].isin(nodos_nivel)]["capa"]
            .value_counts()
            .to_dict()
        )
        filas.append({
            "distancia"        : dist,
            "n_nodos"          : len(nodos_nivel),
            "capas"            : capas,
            "capa_dominante"   : max(capas, key=capas.get) if capas else "—",
        })

    perfil_df = pd.DataFrame(filas)
    return {"origen": origen, "bfs": resultado_bfs, "perfil": perfil_df}


# ------------------------------------------------------------
# Ítem 3 — Perfil de profundidad BFS desde la nube MPLS
# ------------------------------------------------------------

def perfil_bfs_mpls(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Ejecuta BFS desde el nodo de la nube MPLS (capa wan o campus MPLS)
    y compara el perfil con el BFS desde el core.

    Argumentos:
        G        (nx.Graph)     : grafo completo.
        nodos_df (pd.DataFrame) : atributos de nodos.

    Salida:
        dict con claves 'origen', 'bfs', 'perfil' (igual que perfil_bfs_core).
    """
    # Identificar nodo MPLS (campus Nube MPLS o capa wan con más conexiones)
    mask_mpls = nodos_df["campus"].str.contains("MPLS|mpls|Nube", case=False, na=False)
    mpls_nodes = nodos_df[mask_mpls]["id"].tolist()
    if not mpls_nodes:
        mask_mpls = nodos_df["capa"].str.contains("wan|interconexion", case=False, na=False)
        mpls_nodes = nodos_df[mask_mpls]["id"].tolist()

    if not mpls_nodes:
        # Buscar por nombre de nodo
        mpls_nodes = [n for n in G.nodes() if "MPLS" in str(n).upper() or "INTERNET" in str(n).upper()]

    origen = max(mpls_nodes, key=lambda n: G.degree(n)) if mpls_nodes else list(G.nodes())[0]
    print(f"  [BFS-MPLS] Origen: {origen}  (grado={G.degree(origen)})")

    resultado_bfs = bfs(G, origen)

    filas = []
    for dist in sorted(resultado_bfs["niveles"].keys()):
        nodos_nivel = resultado_bfs["niveles"][dist]
        campus_counts = (
            nodos_df[nodos_df["id"].isin(nodos_nivel)]["campus"]
            .value_counts()
            .to_dict()
        )
        filas.append({
            "distancia"    : dist,
            "n_nodos"      : len(nodos_nivel),
            "campus_counts": campus_counts,
        })

    perfil_df = pd.DataFrame(filas)
    return {"origen": origen, "bfs": resultado_bfs, "perfil": perfil_df}


# ------------------------------------------------------------
# Ítem 4 — Ciclos con DFS
# ------------------------------------------------------------

def detectar_ciclos(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Usa DFS para detectar ciclos en el grafo. En un grafo no dirigido,
    cada arista de retroceso en el DFS corresponde a un ciclo.

    Argumentos:
        G        (nx.Graph)     : grafo completo.
        nodos_df (pd.DataFrame) : atributos de nodos.

    Salida:
        dict con claves:
            'resultado_dfs'    — salida completa de dfs()
            'n_aristas_retro'  — número de aristas de retroceso (= número de ciclos independientes)
            'aristas_retro'    — lista de aristas de retroceso
            'ciclos_por_campus'— {campus: n_ciclos}
            'n_ciclos_teoria'  — m - n + 1 (número ciclomático)
    """
    # Elegir origen: core de Campus Central
    mask_core = nodos_df["capa"] == "core"
    core_nodes = nodos_df[mask_core]["id"].tolist()
    origen = max(core_nodes, key=lambda n: G.degree(n)) if core_nodes else list(G.nodes())[0]

    resultado_dfs = dfs(G, origen)

    aristas_retro = resultado_dfs["aristas_retroceso"]
    # Eliminar duplicados (u,v) y (v,u)
    aristas_unicas = list({frozenset(e) for e in aristas_retro})
    aristas_retro_clean = [tuple(sorted(e)) for e in aristas_unicas]

    # Clasificar por campus (campus del nodo u)
    id_to_campus = nodos_df.set_index("id")["campus"].to_dict()
    ciclos_por_campus: dict = collections.Counter()
    for u, v in aristas_retro_clean:
        camp = id_to_campus.get(u, "Desconocido")
        ciclos_por_campus[camp] += 1

    # Número ciclomático = m - n + componentes_conexas
    n_ciclos_teoria = G.number_of_edges() - G.number_of_nodes() + nx.number_connected_components(G)

    return {
        "resultado_dfs"    : resultado_dfs,
        "n_aristas_retro"  : len(aristas_retro_clean),
        "aristas_retro"    : aristas_retro_clean,
        "ciclos_por_campus": dict(ciclos_por_campus),
        "n_ciclos_teoria"  : n_ciclos_teoria,
    }


# ------------------------------------------------------------
# Ítem 5 — BFS vs DFS para inspección física
# ------------------------------------------------------------

def comparar_bfs_dfs_inspeccion(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Compara BFS y DFS como modelos de recorrido físico de armarios
    de red partiendo del switch de core del Campus Central.

    BFS visita nivel a nivel (primero todos los vecinos, luego sus vecinos).
    DFS profundiza por una rama hasta el final antes de retroceder.

    En inspección física de armarios esto equivale a:
      - BFS: visitar primero todos los switches de core, luego todos los de
             agregación, luego todos los de acceso → natural para "barrer por piso".
      - DFS: recorrer un edificio completo de arriba a abajo antes de pasar
             al siguiente → natural para "terminar una zona antes de moverse".

    Argumentos:
        G        (nx.Graph)     : grafo completo.
        nodos_df (pd.DataFrame) : atributos de nodos.

    Salida:
        dict con claves:
            'origen'             — nodo de inicio
            'bfs_orden_capas'    — primeros 20 nodos BFS con su capa
            'dfs_orden_capas'    — primeros 20 nodos DFS con su capa
            'conclusion'         — string con el análisis
    """
    mask_core = nodos_df["capa"] == "core"
    core_nodes = nodos_df[mask_core & nodos_df["campus"].str.contains("Central", case=False, na=False)]["id"].tolist()
    if not core_nodes:
        core_nodes = nodos_df[mask_core]["id"].tolist()
    origen = max(core_nodes, key=lambda n: G.degree(n))

    res_bfs = bfs(G, origen)
    res_dfs = dfs(G, origen)

    id_to_capa = nodos_df.set_index("id")["capa"].to_dict()
    id_to_campus = nodos_df.set_index("id")["campus"].to_dict()

    bfs_orden = [
        {"nodo": n, "capa": id_to_capa.get(n, "?"), "campus": id_to_campus.get(n, "?")}
        for n in res_bfs["orden"][:20]
    ]
    dfs_orden = [
        {"nodo": n, "capa": id_to_capa.get(n, "?"), "campus": id_to_campus.get(n, "?")}
        for n in res_dfs["orden"][:20]
    ]

    conclusion = (
        "DFS modela mejor la inspección física de armarios. "
        "Un técnico que sale del core recorre un edificio completo "
        "(core → agregación → acceso → acceso → ...) antes de pasar al "
        "siguiente, lo que minimiza desplazamientos entre edificios. "
        "BFS visita todos los switches de agregación de todos los edificios "
        "antes de bajar a la capa de acceso, obligando al técnico a moverse "
        "constantemente entre edificios."
    )

    return {
        "origen"          : origen,
        "bfs_orden_capas" : bfs_orden,
        "dfs_orden_capas" : dfs_orden,
        "conclusion"      : conclusion,
    }


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_perfiles(res_core: dict, res_mpls: dict) -> None:
    """
    Genera una figura comparativa con los perfiles de profundidad BFS
    desde el core del Campus Central y desde la nube MPLS.

    Argumentos:
        res_core (dict): resultado de perfil_bfs_core().
        res_mpls (dict): resultado de perfil_bfs_mpls().

    Salida:
        None — guarda imagen en DIR_IMG/p3_perfil_profundidad.png
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("P3 · Perfiles de Profundidad BFS — Red UCuenca",
                 fontsize=14, fontweight="bold")

    for ax, res, titulo, color in zip(
        axes,
        [res_core, res_mpls],
        [f"Desde core ({res_core['origen']})",
         f"Desde MPLS ({res_mpls['origen']})"],
        ["#2980b9", "#e67e22"]
    ):
        perfil = res["perfil"]
        ax.bar(perfil["distancia"], perfil["n_nodos"], color=color, alpha=0.85, edgecolor="white")
        ax.set_xlabel("Distancia (saltos)", fontsize=11)
        ax.set_ylabel("Número de nodos", fontsize=11)
        ax.set_title(titulo, fontsize=12)
        ax.set_xticks(perfil["distancia"])
        for x, y in zip(perfil["distancia"], perfil["n_nodos"]):
            ax.text(x, y + 0.5, str(y), ha="center", va="bottom", fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p3_perfil_profundidad.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_ciclos(G: nx.Graph, res_ciclos: dict, nodos_df: pd.DataFrame) -> None:
    """
    Visualiza el grafo con las aristas de retroceso (ciclos) resaltadas
    en rojo sobre el fondo gris de las aristas de árbol DFS.

    Argumentos:
        G          (nx.Graph)     : grafo completo.
        res_ciclos (dict)         : resultado de detectar_ciclos().
        nodos_df   (pd.DataFrame) : atributos de nodos.

    Salida:
        None — guarda imagen en DIR_IMG/p3_ciclos.png
    """
    # Colores por capa
    CAPA_COLOR = {
        "core"         : "#c0392b",
        "agregacion"   : "#2980b9",
        "acceso"       : "#27ae60",
        "wan"          : "#8e44ad",
        "interconexion": "#f39c12",
    }
    id_to_capa = nodos_df.set_index("id")["capa"].to_dict()

    retro_set = set(map(frozenset, res_ciclos["aristas_retro"]))
    edge_colors = []
    edge_widths = []
    for u, v in G.edges():
        if frozenset([u, v]) in retro_set:
            edge_colors.append("#e74c3c")
            edge_widths.append(3.0)
        else:
            edge_colors.append("#bdc3c7")
            edge_widths.append(0.8)

    node_colors = [CAPA_COLOR.get(id_to_capa.get(n, ""), "#95a5a6") for n in G.nodes()]

    pos = nx.spring_layout(G, seed=42, k=0.4)
    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=edge_widths, alpha=0.7)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=60)

    leyenda = [mpatches.Patch(color=c, label=k) for k, c in CAPA_COLOR.items()]
    leyenda.append(mpatches.Patch(color="#e74c3c", label=f"Aristas de retroceso (ciclos) — {res_ciclos['n_aristas_retro']}"))
    ax.legend(handles=leyenda, loc="upper left", fontsize=9)
    ax.set_title(
        f"P3 · Ciclos detectados por DFS — Red UCuenca\n"
        f"Número ciclomático: {res_ciclos['n_ciclos_teoria']}  |  "
        f"Aristas de retroceso: {res_ciclos['n_aristas_retro']}",
        fontsize=13, fontweight="bold"
    )
    ax.axis("off")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p3_ciclos.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================
# 1) Cargar la red y los atributos de nodos.
# 2) Ítem 1: mostrar resumen de BFS/DFS (estructura y complejidad).
# 3) Ítem 2: perfil BFS desde el core del Campus Central.
# 4) Ítem 3: perfil BFS desde la nube MPLS y comparación.
# 5) Ítem 4: detectar ciclos con DFS.
# 6) Ítem 5: análisis BFS vs DFS para inspección física.
# 7) Generar tablas y visualizaciones.

if __name__ == "__main__":
    _crear_dirs()

    # --- Carga de datos ---
    print("\n=== P3 — BFS y DFS sobre la Red UCuenca ===\n")
    G = cargar_red(fuente="csv")
    verificar(G)

    def _leer_csv(nombre: str) -> pd.DataFrame:
        return pd.read_csv(os.path.join(DIR_ROOT, nombre), dtype=str)

    nodos_df   = _leer_csv("red_ucuenca_nodes.csv")
    aristas_df = _leer_csv("red_ucuenca_edges.csv")

    # --- Ítem 1: Descripción de BFS/DFS ---
    print("\n[Ítem 1] BFS y DFS desde cero")
    print("  BFS  — cola FIFO (collections.deque). Complejidad: O(n + m).")
    print("  DFS  — pila implícita recursiva.      Complejidad: O(n + m).")
    print("  Estructura de datos extra: conjunto 'visitado' → O(n) espacio.")

    # --- Ítem 2: Perfil BFS desde core ---
    print("\n[Ítem 2] Perfil BFS desde core Campus Central")
    res_core = perfil_bfs_core(G, nodos_df)
    print(res_core["perfil"].to_string(index=False))
    res_core["perfil"].to_csv(os.path.join(DIR_TAB, "p3_perfil_core.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p3_perfil_core.csv')}")

    # --- Ítem 3: Perfil BFS desde MPLS ---
    print("\n[Ítem 3] Perfil BFS desde nube MPLS")
    res_mpls = perfil_bfs_mpls(G, nodos_df)
    print(res_mpls["perfil"].to_string(index=False))
    res_mpls["perfil"].to_csv(os.path.join(DIR_TAB, "p3_perfil_mpls.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p3_perfil_mpls.csv')}")

    # Graficar perfiles comparativos
    graficar_perfiles(res_core, res_mpls)

    # --- Ítem 4: Ciclos con DFS ---
    print("\n[Ítem 4] Detección de ciclos con DFS")
    res_ciclos = detectar_ciclos(G, nodos_df)
    print(f"  Número ciclomático (m - n + c) : {res_ciclos['n_ciclos_teoria']}")
    print(f"  Aristas de retroceso (DFS)     : {res_ciclos['n_aristas_retro']}")
    print(f"  Ciclos por campus              : {res_ciclos['ciclos_por_campus']}")

    with open(os.path.join(DIR_TAB, "p3_ciclos.txt"), "w", encoding="utf-8") as f:
        f.write(f"Número ciclomático: {res_ciclos['n_ciclos_teoria']}\n")
        f.write(f"Aristas de retroceso: {res_ciclos['n_aristas_retro']}\n\n")
        f.write("Aristas de retroceso (ciclos):\n")
        for u, v in res_ciclos["aristas_retro"]:
            f.write(f"  {u} — {v}\n")
        f.write("\nCiclos por campus:\n")
        for camp, n in sorted(res_ciclos["ciclos_por_campus"].items(), key=lambda x: -x[1]):
            f.write(f"  {camp}: {n}\n")
    print(f"  [OK] {os.path.join(DIR_TAB, 'p3_ciclos.txt')}")

    graficar_ciclos(G, res_ciclos, nodos_df)

    # --- Ítem 5: BFS vs DFS para inspección física ---
    print("\n[Ítem 5] BFS vs DFS para inspección física")
    res_comp = comparar_bfs_dfs_inspeccion(G, nodos_df)
    print(f"\n  Conclusión: {res_comp['conclusion']}")

    print("\n  Primeros 10 nodos BFS:")
    for entry in res_comp["bfs_orden_capas"][:10]:
        print(f"    {entry['nodo']:30s}  capa={entry['capa']:15s}  campus={entry['campus']}")

    print("\n  Primeros 10 nodos DFS:")
    for entry in res_comp["dfs_orden_capas"][:10]:
        print(f"    {entry['nodo']:30s}  capa={entry['capa']:15s}  campus={entry['campus']}")

    print("\n=== P3 completado ===\n")
