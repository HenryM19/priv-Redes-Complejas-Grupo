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
  Ítem 2 · Heurística greedy para p-Mediana con p∈{1,2,3,5}, contrastada
           con el óptimo exacto de un solver de programación entera (PuLP)
  Ítem 3 · Heurística greedy para p-Centro con p∈{1,2,3,5}, contrastada
           con el óptimo exacto (PuLP)
  Ítem 4 · Comparación de mediana/centro óptimos con centralidades (P1)
  Ítem 5 · Discusión de ventajas de c/modelo según objetivos de red

El enunciado (P7.2) pide resolver con heurística voraz "y, si les es
posible, con un solver de programación entera". Ambos modelos MIP son
lineales estándar (p-median: minimizar suma de costos de asignación;
p-center: minimizar el radio con una variable auxiliar) y con 177 nodos
CBC (el solver por defecto de PuLP) los resuelve en segundos, así que se
incluyen los dos: la heurística da una cota superior rápida y el solver
exacto certifica qué tan lejos está esa heurística del óptimo real.

Uso:
    python problema7.py

Salidas:
    results/tablas/p7_mediana.csv
    results/tablas/p7_centro.csv
    results/tablas/p7_comparacion_centralidades.csv
    results/tablas/p7_comparacion_heuristica_vs_solver.csv
    results/imagenes/p7_mediana_vs_centro.png
    results/imagenes/p7_heuristica_vs_solver.png
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

try:
    import pulp
    _PULP_DISPONIBLE = True
except ImportError:
    _PULP_DISPONIBLE = False

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
# Ítem 2b/3b — Solver exacto de programación entera (PuLP / CBC)
# ------------------------------------------------------------

def p_mediana_exacta(nodos: list, D: np.ndarray, p: int,
                     tiempo_limite: int = 120) -> dict:
    """
    Resuelve el p-Mediana de forma exacta con programación lineal entera.

    Formulación estándar (facility location):
        variables:  y_j ∈ {0,1}  — 1 si el nodo j es mediana
                    x_ij ∈ {0,1} — 1 si el nodo i se asigna a la mediana j
        minimizar   Σ_i Σ_j D[i,j] · x_ij
        sujeto a    Σ_j y_j = p                      (exactamente p medianas)
                    Σ_j x_ij = 1  ∀i                  (cada nodo asignado a una)
                    x_ij ≤ y_j    ∀i,j                (solo se asigna a medianas abiertas)
                    x_ij, y_j ∈ {0,1}

    Argumentos:
        nodos          (list)      : lista de identificadores de nodos.
        D              (np.ndarray): matriz N×N de distancias.
        p              (int)       : número de medianas.
        tiempo_limite  (int)       : límite de tiempo del solver, en segundos.

    Salida:
        dict: {'medianas', 'asignacion', 'obj', 'status', 'gap_heuristica'}
              (gap_heuristica se rellena después, al comparar con el greedy)
    """
    if not _PULP_DISPONIBLE:
        return {"medianas": None, "asignacion": None, "obj": None,
                "status": "PuLP no disponible"}

    N = len(nodos)
    idx = range(N)
    prob = pulp.LpProblem("p_mediana", pulp.LpMinimize)

    y = pulp.LpVariable.dicts("y", idx, cat="Binary")
    x = pulp.LpVariable.dicts("x", (idx, idx), cat="Binary")

    prob += pulp.lpSum(D[i][j] * x[i][j] for i in idx for j in idx)
    prob += pulp.lpSum(y[j] for j in idx) == p
    for i in idx:
        prob += pulp.lpSum(x[i][j] for j in idx) == 1
        for j in idx:
            prob += x[i][j] <= y[j]

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=tiempo_limite)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    medianas = [nodos[j] for j in idx if pulp.value(y[j]) > 0.5]
    asignacion = {}
    for i in idx:
        for j in idx:
            if pulp.value(x[i][j]) > 0.5:
                asignacion[nodos[i]] = nodos[j]
                break

    return {
        "medianas"  : medianas,
        "asignacion": asignacion,
        "obj"       : pulp.value(prob.objective),
        "status"    : status,
    }


def p_centro_exacto(nodos: list, D: np.ndarray, p: int,
                    tiempo_limite: int = 120) -> dict:
    """
    Resuelve el p-Centro de forma exacta con programación lineal entera.

    Formulación (min-max linealizado con variable auxiliar R):
        variables:  y_j ∈ {0,1}, x_ij ∈ {0,1}, R ≥ 0 (radio de cobertura)
        minimizar   R
        sujeto a    Σ_j y_j = p
                    Σ_j x_ij = 1  ∀i
                    x_ij ≤ y_j    ∀i,j
                    Σ_j D[i,j]·x_ij ≤ R  ∀i     (el radio cubre a todo nodo i)

    Argumentos: igual que p_mediana_exacta.

    Salida:
        dict: {'centros', 'asignacion', 'radio', 'status'}
    """
    if not _PULP_DISPONIBLE:
        return {"centros": None, "asignacion": None, "radio": None,
                "status": "PuLP no disponible"}

    N = len(nodos)
    idx = range(N)
    prob = pulp.LpProblem("p_centro", pulp.LpMinimize)

    y = pulp.LpVariable.dicts("y", idx, cat="Binary")
    x = pulp.LpVariable.dicts("x", (idx, idx), cat="Binary")
    R = pulp.LpVariable("R", lowBound=0)

    prob += R
    prob += pulp.lpSum(y[j] for j in idx) == p
    for i in idx:
        prob += pulp.lpSum(x[i][j] for j in idx) == 1
        prob += pulp.lpSum(D[i][j] * x[i][j] for j in idx) <= R
        for j in idx:
            prob += x[i][j] <= y[j]

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=tiempo_limite)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    centros = [nodos[j] for j in idx if pulp.value(y[j]) > 0.5]
    asignacion = {}
    for i in idx:
        for j in idx:
            if pulp.value(x[i][j]) > 0.5:
                asignacion[nodos[i]] = nodos[j]
                break

    return {
        "centros"   : centros,
        "asignacion": asignacion,
        "radio"     : pulp.value(R),
        "status"    : status,
    }


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


def graficar_heuristica_vs_solver(df_comp: pd.DataFrame) -> None:
    """
    Barras agrupadas: objetivo/radio de la heurística greedy vs el óptimo
    exacto del solver PuLP, para cada p y cada modelo (mediana/centro).
    Un gap del 0% significa que el greedy ya encontró el óptimo.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))

    df_m = df_comp[df_comp["modelo"] == "mediana"]
    x = np.arange(len(df_m))
    w = 0.35
    ax1.bar(x - w/2, df_m["valor_greedy"], w, label="Greedy", color="#2980b9")
    ax1.bar(x + w/2, df_m["valor_exacto"], w, label="Óptimo (PuLP/CBC)", color="#27ae60")
    ax1.set_xticks(x); ax1.set_xticklabels([f"p={p}" for p in df_m["p"]])
    ax1.set_ylabel("Suma de distancias (saltos)")
    ax1.set_title("p-Mediana: greedy vs óptimo exacto")
    ax1.legend(fontsize=9); ax1.grid(axis="y", alpha=0.3)
    for i, (g, e) in enumerate(zip(df_m["valor_greedy"], df_m["valor_exacto"])):
        gap = 0.0 if e == 0 else 100 * (g - e) / e
        ax1.annotate(f"+{gap:.1f}%" if gap > 0.05 else "óptimo",
                    (i, max(g, e)), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=8)

    df_c = df_comp[df_comp["modelo"] == "centro"]
    x = np.arange(len(df_c))
    ax2.bar(x - w/2, df_c["valor_greedy"], w, label="Greedy", color="#e67e22")
    ax2.bar(x + w/2, df_c["valor_exacto"], w, label="Óptimo (PuLP/CBC)", color="#27ae60")
    ax2.set_xticks(x); ax2.set_xticklabels([f"p={p}" for p in df_c["p"]])
    ax2.set_ylabel("Radio máximo (saltos)")
    ax2.set_title("p-Centro: greedy vs óptimo exacto")
    ax2.legend(fontsize=9); ax2.grid(axis="y", alpha=0.3)
    for i, (g, e) in enumerate(zip(df_c["valor_greedy"], df_c["valor_exacto"])):
        gap = 0.0 if e == 0 else 100 * (g - e) / e
        ax2.annotate(f"+{gap:.1f}%" if gap > 0.05 else "óptimo",
                    (i, max(g, e)), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=8)

    plt.suptitle("P7 · Heurística greedy vs solver exacto de programación entera",
                fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p7_heuristica_vs_solver.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P7 — p-Mediana y p-Centro ===\n")

    G = cargar_red(fuente="csv"); verificar(G)

    if not _PULP_DISPONIBLE:
        print("  [ADVERTENCIA] PuLP no está instalado: se omite el solver exacto.")
        print("  Instalar con: pip install pulp\n")

    # Ítem 1: Matriz de distancias
    print("[Ítem 1] Construyendo matriz de distancias (saltos)...")
    nodos, D = matriz_distancias(G)
    print(f"  Matriz {len(nodos)}×{len(nodos)} completada.")

    P_VALS = [1, 2, 3, 5]
    filas_med, filas_cen = [], []
    obj_med_vals, radio_vals = [], []
    filas_comp = []  # comparación heurística vs solver exacto

    for p in P_VALS:
        # Ítem 2: p-Mediana
        res_m = p_mediana_greedy(nodos, D, p)
        print(f"\n[Ítem 2] p-Mediana p={p}")
        print(f"  Medianas (greedy)    : {res_m['medianas']}")
        print(f"  Objetivo (greedy)    : {res_m['obj']:.1f} saltos·nodo")
        filas_med.append({
            "p"        : p,
            "medianas" : "; ".join(res_m["medianas"]),
            "objetivo" : round(res_m["obj"], 2),
        })
        obj_med_vals.append(res_m["obj"])

        if _PULP_DISPONIBLE:
            print(f"  Resolviendo p-Mediana p={p} con PuLP/CBC (óptimo exacto)...")
            res_m_ex = p_mediana_exacta(nodos, D, p)
            print(f"  Medianas (exacto)    : {res_m_ex['medianas']}  [{res_m_ex['status']}]")
            print(f"  Objetivo (exacto)    : {res_m_ex['obj']:.1f} saltos·nodo")
            gap = 0.0 if res_m_ex['obj'] == 0 else \
                100 * (res_m['obj'] - res_m_ex['obj']) / res_m_ex['obj']
            print(f"  Gap greedy vs óptimo : {gap:.2f}%")
            filas_comp.append({
                "modelo": "mediana", "p": p,
                "valor_greedy": round(res_m['obj'], 2),
                "valor_exacto": round(res_m_ex['obj'], 2),
                "gap_pct": round(gap, 2),
                "medianas_greedy": "; ".join(res_m["medianas"]),
                "medianas_exacto": "; ".join(res_m_ex["medianas"]) if res_m_ex["medianas"] else "",
                "status_solver": res_m_ex["status"],
            })

        # Ítem 3: p-Centro
        res_c = p_centro_greedy(nodos, D, p)
        print(f"[Ítem 3] p-Centro  p={p}")
        print(f"  Centros (greedy)     : {res_c['centros']}")
        print(f"  Radio (greedy)       : {res_c['radio']} saltos")
        filas_cen.append({
            "p"      : p,
            "centros": "; ".join(res_c["centros"]),
            "radio"  : res_c["radio"],
        })
        radio_vals.append(res_c["radio"])

        if _PULP_DISPONIBLE:
            print(f"  Resolviendo p-Centro p={p} con PuLP/CBC (óptimo exacto)...")
            res_c_ex = p_centro_exacto(nodos, D, p)
            print(f"  Centros (exacto)     : {res_c_ex['centros']}  [{res_c_ex['status']}]")
            print(f"  Radio (exacto)       : {res_c_ex['radio']:.1f} saltos")
            gap = 0.0 if res_c_ex['radio'] == 0 else \
                100 * (res_c['radio'] - res_c_ex['radio']) / res_c_ex['radio']
            print(f"  Gap greedy vs óptimo : {gap:.2f}%")
            filas_comp.append({
                "modelo": "centro", "p": p,
                "valor_greedy": round(res_c['radio'], 2),
                "valor_exacto": round(res_c_ex['radio'], 2),
                "gap_pct": round(gap, 2),
                "medianas_greedy": "; ".join(res_c["centros"]),
                "medianas_exacto": "; ".join(res_c_ex["centros"]) if res_c_ex["centros"] else "",
                "status_solver": res_c_ex["status"],
            })

    df_med = pd.DataFrame(filas_med)
    df_cen = pd.DataFrame(filas_cen)
    df_med.to_csv(os.path.join(DIR_TAB, "p7_mediana.csv"), index=False)
    df_cen.to_csv(os.path.join(DIR_TAB, "p7_centro.csv"),  index=False)
    print(f"\n  [OK] p7_mediana.csv y p7_centro.csv")

    if _PULP_DISPONIBLE and filas_comp:
        df_comp_solver = pd.DataFrame(filas_comp)
        df_comp_solver.to_csv(
            os.path.join(DIR_TAB, "p7_comparacion_heuristica_vs_solver.csv"),
            index=False)
        print(f"  [OK] p7_comparacion_heuristica_vs_solver.csv")
        print(f"\n  Resumen greedy vs óptimo exacto:")
        print(df_comp_solver[["modelo", "p", "valor_greedy", "valor_exacto", "gap_pct"]]
              .to_string(index=False))
        graficar_heuristica_vs_solver(df_comp_solver)

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
