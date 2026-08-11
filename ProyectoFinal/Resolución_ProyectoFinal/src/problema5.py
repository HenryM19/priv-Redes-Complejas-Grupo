"""
problema5.py — Problema P5: Caminos más Cortos (Fase 3)
========================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Implementa Dijkstra (con cola de prioridad) y Floyd-Warshall desde cero
y los aplica sobre la red UCuenca con tres modelos de peso.

Los cinco ítems resueltos son:
  Ítem 1 · Dijkstra (heapq) y Floyd-Warshall implementados desde cero
  Ítem 2 · Verificación de coincidencia en 20 pares aleatorios
  Ítem 3 · Comparación empírica de tiempos vs complejidades teóricas
  Ítem 4 · Matriz de distancias con 3 modelos; top-10 closeness por modelo
  Ítem 5 · Par de acceso más distante por modelo + discusión OSPF/IS-IS

Modelos de peso:
    w_saltos(u,v)   = 1
    w_latencia(u,v) = α + β / c(u,v)     con α=0.1 ms, β=1000 Mbps·ms
    w_carga(u,v)    = b(u,v) / c(u,v)    ratio tráfico/capacidad

Uso:
    python problema5.py

Salidas (relativas a Resolución_ProyectoFinal/):
    results/tablas/p5_verificacion.csv
    results/tablas/p5_closeness_modelos.csv
    results/tablas/p5_par_mas_distante.csv
    results/imagenes/p5_tiempos.png
    results/imagenes/p5_closeness_comparativo.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, time, random, heapq, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DIR_SRC   = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL = os.path.dirname(DIR_SRC)
DIR_ROOT  = os.path.dirname(DIR_RESOL)
DIR_BASE  = os.path.join(DIR_ROOT, "codigo_base")
DIR_TAB   = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG   = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar  # noqa

import networkx as nx


# ============================================================
# Definición de funciones
# ============================================================

def _crear_dirs():
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


# ------------------------------------------------------------
# Función de capacidad estimada c(u,v) en Mbps
# ------------------------------------------------------------

def capacidad_estimada(G: nx.Graph, nodos_df: pd.DataFrame,
                       aristas_df: pd.DataFrame) -> dict:
    """
    Estima la capacidad en Mbps de cada arista siguiendo las reglas:
      - Si capacidad_mbps está definida en aristas_df → usarla.
      - Si rol == 'wan' → 10 000 Mbps (10 Gbps MPLS).
      - Si ambos extremos son core o core–agregacion → 10 000 Mbps.
      - Si uno es agregacion y otro acceso → 1 000 Mbps.
      - Resto (acceso–acceso, respaldo, etc.) → 100 Mbps.

    Argumentos:
        G          (nx.Graph)     : grafo.
        nodos_df   (pd.DataFrame) : atributos de nodos (id, capa).
        aristas_df (pd.DataFrame) : atributos de aristas.

    Salida:
        dict: {frozenset({u,v}): capacidad_mbps (float)}
    """
    id_to_capa = nodos_df.set_index("id")["capa"].to_dict()
    cap = {}

    # Pre-cargar capacidades explícitas y roles desde aristas_df
    aristas_df["_key"] = aristas_df.apply(
        lambda r: frozenset([r["source"], r["target"]]), axis=1)

    explicit = {}
    roles    = {}
    for _, row in aristas_df.iterrows():
        k = row["_key"]
        c_str = str(row.get("capacidad_mbps", "")).strip()
        if c_str and c_str not in ("nan", "None", ""):
            try:
                explicit[k] = float(c_str)
            except ValueError:
                pass
        r = str(row.get("rol", "")).strip()
        if r:
            roles[k] = r

    for u, v in G.edges():
        k = frozenset([u, v])
        if k in explicit:
            cap[k] = explicit[k]
            continue
        rol = roles.get(k, "principal")
        if rol == "wan":
            cap[k] = 10_000.0
            continue
        capa_u = id_to_capa.get(u, "acceso")
        capa_v = id_to_capa.get(v, "acceso")
        capas  = {capa_u, capa_v}
        if "core" in capas:
            cap[k] = 10_000.0
        elif "agregacion" in capas:
            cap[k] = 1_000.0
        else:
            cap[k] = 100.0

    return cap


def _get_cap(cap_dict: dict, u: str, v: str) -> float:
    return cap_dict.get(frozenset([u, v]), 100.0)


def construir_grafos_pesados(G: nx.Graph, nodos_df: pd.DataFrame,
                              aristas_df: pd.DataFrame,
                              alpha: float = 0.1, beta: float = 1000.0
                              ) -> dict:
    """
    Construye tres grafos NetworkX con distintos pesos de arista.

    Modelos:
        saltos   : w = 1
        latencia : w = alpha + beta / c(u,v)
        carga    : w = b(u,v) / c(u,v)  (si b=0 → w=0.001 para evitar 0)

    Argumentos:
        G          (nx.Graph)     : grafo base.
        nodos_df   (pd.DataFrame) : atributos de nodos.
        aristas_df (pd.DataFrame) : atributos de aristas (trafico_mbps).
        alpha      (float)        : retardo de propagación base (ms).
        beta       (float)        : constante de serialización (Mbps·ms).

    Salida:
        dict {'saltos': nx.Graph, 'latencia': nx.Graph, 'carga': nx.Graph}
    """
    cap_dict = capacidad_estimada(G, nodos_df, aristas_df)

    # Tráfico medido por arista
    trafico: dict = {}
    aristas_df["_key"] = aristas_df.apply(
        lambda r: frozenset([r["source"], r["target"]]), axis=1)
    for _, row in aristas_df.iterrows():
        t_str = str(row.get("trafico_mbps", "")).strip()
        if t_str and t_str not in ("nan", "None", ""):
            try:
                trafico[row["_key"]] = float(t_str)
            except ValueError:
                pass

    grafos = {m: G.copy() for m in ("saltos", "latencia", "carga")}
    for u, v in G.edges():
        k   = frozenset([u, v])
        c   = _get_cap(cap_dict, u, v)
        b   = trafico.get(k, 0.0)
        grafos["saltos"][u][v]["weight"]   = 1.0
        grafos["latencia"][u][v]["weight"] = alpha + beta / c
        grafos["carga"][u][v]["weight"]    = max(b / c, 1e-6)

    return grafos


# ------------------------------------------------------------
# Ítem 1 — Dijkstra desde cero
# ------------------------------------------------------------

def dijkstra(G: nx.Graph, origen: str, peso: str = "weight") -> dict:
    """
    Dijkstra con cola de prioridad (heapq). Complejidad: O((n+m) log n).

    Argumentos:
        G      (nx.Graph): grafo con atributo de peso 'peso' en cada arista.
        origen (str)     : nodo fuente.
        peso   (str)     : nombre del atributo de peso.

    Salida:
        dict:
            'dist'  — {nodo: distancia mínima desde origen}
            'prev'  — {nodo: predecesor en el camino óptimo}
    """
    dist = {n: math.inf for n in G.nodes()}
    prev = {n: None    for n in G.nodes()}
    dist[origen] = 0.0
    heap = [(0.0, origen)]

    while heap:
        d_u, u = heapq.heappop(heap)
        if d_u > dist[u]:
            continue
        for v in G.neighbors(u):
            w = G[u][v].get(peso, 1.0)
            d_v = dist[u] + w
            if d_v < dist[v]:
                dist[v] = d_v
                prev[v] = u
                heapq.heappush(heap, (d_v, v))

    return {"dist": dist, "prev": prev}


# ------------------------------------------------------------
# Ítem 1 — Floyd-Warshall desde cero
# ------------------------------------------------------------

def floyd_warshall(G: nx.Graph, peso: str = "weight") -> dict:
    """
    Floyd-Warshall: distancias mínimas entre todos los pares. O(n³).

    Argumentos:
        G    (nx.Graph): grafo con atributo de peso.
        peso (str)     : nombre del atributo.

    Salida:
        dict:
            'dist'  — np.ndarray (n×n) con distancias mínimas
            'nodos' — lista de nodos (índice de filas/columnas)
    """
    nodos  = list(G.nodes())
    n      = len(nodos)
    idx    = {v: i for i, v in enumerate(nodos)}
    dist   = np.full((n, n), np.inf)
    np.fill_diagonal(dist, 0.0)

    for u, v, data in G.edges(data=True):
        w = data.get(peso, 1.0)
        dist[idx[u], idx[v]] = w
        dist[idx[v], idx[u]] = w  # no dirigido

    for k in range(n):
        for i in range(n):
            if dist[i, k] == np.inf:
                continue
            for j in range(n):
                nueva = dist[i, k] + dist[k, j]
                if nueva < dist[i, j]:
                    dist[i, j] = nueva

    return {"dist": dist, "nodos": nodos}


# ------------------------------------------------------------
# Ítem 2 — Verificación en 20 pares aleatorios
# ------------------------------------------------------------

def verificar_coincidencia(G: nx.Graph, peso: str = "weight",
                           n_pares: int = 20, semilla: int = 42) -> pd.DataFrame:
    """
    Compara Dijkstra vs Floyd-Warshall en n_pares aleatorios y verifica
    que las distancias coincidan (diferencia relativa < 1e-9).

    Argumentos:
        G       (nx.Graph): grafo pesado.
        peso    (str)     : atributo de peso.
        n_pares (int)     : número de pares a verificar.
        semilla (int)     : semilla aleatoria.

    Salida:
        pd.DataFrame con columnas [origen, destino, d_dijkstra, d_fw, coincide].
    """
    nodos = list(G.nodes())
    rng   = random.Random(semilla)
    pares = [(rng.choice(nodos), rng.choice(nodos)) for _ in range(n_pares)]

    fw = floyd_warshall(G, peso)
    idx_fw = {v: i for i, v in enumerate(fw["nodos"])}

    filas = []
    for u, v in pares:
        res_dij = dijkstra(G, u, peso)
        d_dij   = res_dij["dist"][v]
        d_fw    = fw["dist"][idx_fw[u], idx_fw[v]]
        ok = abs(d_dij - d_fw) < 1e-9 or (math.isinf(d_dij) and math.isinf(d_fw))
        filas.append({"origen": u, "destino": v,
                      "d_dijkstra": round(d_dij, 6),
                      "d_fw"      : round(d_fw,  6),
                      "coincide"  : ok})
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Ítem 3 — Comparación de tiempos
# ------------------------------------------------------------

def comparar_tiempos(G: nx.Graph, peso: str = "weight") -> dict:
    """
    Mide el tiempo real de Dijkstra (todos los orígenes) y Floyd-Warshall.

    Argumentos:
        G    (nx.Graph): grafo pesado.
        peso (str)     : atributo de peso.

    Salida:
        dict con 't_dijkstra_total', 't_fw', 'n', 'm'.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    nodos = list(G.nodes())

    t0 = time.perf_counter()
    for v in nodos:
        dijkstra(G, v, peso)
    t_dij = time.perf_counter() - t0

    t0 = time.perf_counter()
    floyd_warshall(G, peso)
    t_fw = time.perf_counter() - t0

    return {"t_dijkstra_total": round(t_dij, 4),
            "t_fw"            : round(t_fw, 4),
            "n": n, "m": m}


# ------------------------------------------------------------
# Ítem 4 — Closeness por modelo de peso
# ------------------------------------------------------------

def closeness_por_modelo(grafos: dict, nodos_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la centralidad de cercanía bajo cada modelo de peso y devuelve
    el top-10 de cada modelo en una tabla comparativa.

    Argumentos:
        grafos   (dict)          : {'saltos': G, 'latencia': G, 'carga': G}.
        nodos_df (pd.DataFrame)  : atributos de nodos.

    Salida:
        pd.DataFrame con top-10 de cada modelo (columnas rank, nodo_X, closeness_X).
    """
    id_to_capa   = nodos_df.set_index("id")["capa"].to_dict()
    id_to_campus = nodos_df.set_index("id")["campus"].to_dict()
    resultados   = {}

    for modelo, G in grafos.items():
        fw  = floyd_warshall(G, "weight")
        idx = {v: i for i, v in enumerate(fw["nodos"])}
        n   = len(fw["nodos"])
        cls = {}
        for nodo in fw["nodos"]:
            i        = idx[nodo]
            suma_inv = np.sum(np.where(fw["dist"][i] > 0, 1.0 / fw["dist"][i], 0.0))
            cls[nodo] = suma_inv / (n - 1)
        resultados[modelo] = sorted(cls.items(), key=lambda x: -x[1])[:10]

    filas = []
    for rank in range(10):
        fila = {"rank": rank + 1}
        for modelo in ("saltos", "latencia", "carga"):
            nodo, val = resultados[modelo][rank]
            fila[f"nodo_{modelo}"]  = nodo
            fila[f"close_{modelo}"] = round(val, 4)
            fila[f"capa_{modelo}"]  = id_to_capa.get(nodo, "?")
        filas.append(fila)

    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Ítem 5 — Par más distante (nodos de acceso)
# ------------------------------------------------------------

def par_mas_distante(grafos: dict, nodos_df: pd.DataFrame) -> pd.DataFrame:
    """
    Encuentra el par de switches de acceso con mayor distancia
    bajo cada modelo de peso y describe la ruta salto a salto.

    Argumentos:
        grafos   (dict)         : {'saltos': G, 'latencia': G, 'carga': G}.
        nodos_df (pd.DataFrame) : atributos de nodos.

    Salida:
        pd.DataFrame con columnas [modelo, nodo_a, nodo_b, distancia, ruta].
    """
    acceso = nodos_df[nodos_df["capa"] == "acceso"]["id"].tolist()
    filas  = []

    for modelo, G in grafos.items():
        fw    = floyd_warshall(G, "weight")
        nodos = fw["nodos"]
        idx   = {v: i for i, v in enumerate(nodos)}
        # Sub-matriz solo de nodos de acceso
        acc_idx = [idx[n] for n in acceso if n in idx]
        sub_a   = np.array(acc_idx)
        sub_m   = fw["dist"][np.ix_(sub_a, sub_a)]
        np.fill_diagonal(sub_m, -np.inf)
        pos = np.unravel_index(np.argmax(sub_m), sub_m.shape)
        na  = acceso[pos[0]]
        nb  = acceso[pos[1]]
        d   = sub_m[pos]

        # Reconstruir ruta con Dijkstra
        res = dijkstra(G, na, "weight")
        ruta = []
        cur  = nb
        while cur is not None:
            ruta.append(cur)
            cur = res["prev"][cur]
        ruta.reverse()

        filas.append({"modelo": modelo, "nodo_a": na, "nodo_b": nb,
                      "distancia": round(d, 4),
                      "ruta": " → ".join(ruta[:8]) + (" ..." if len(ruta) > 8 else "")})

    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_tiempos(t_saltos: dict, t_latencia: dict, t_carga: dict) -> None:
    """Barras comparativas de tiempo Dijkstra vs Floyd-Warshall por modelo."""
    fig, ax = plt.subplots(figsize=(10, 5))
    modelos = ["saltos", "latencia", "carga"]
    t_dij   = [t_saltos["t_dijkstra_total"], t_latencia["t_dijkstra_total"],
               t_carga["t_dijkstra_total"]]
    t_fw    = [t_saltos["t_fw"], t_latencia["t_fw"], t_carga["t_fw"]]
    x = range(len(modelos))
    ax.bar([i - 0.2 for i in x], t_dij, 0.35, label="Dijkstra × n orígenes", color="#2980b9")
    ax.bar([i + 0.2 for i in x], t_fw,  0.35, label="Floyd-Warshall",         color="#e74c3c")
    ax.set_xticks(list(x)); ax.set_xticklabels(modelos)
    ax.set_ylabel("Tiempo (s)"); ax.set_title("P5 · Comparación de tiempos: Dijkstra vs Floyd-Warshall")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p5_tiempos.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_closeness(df_close: pd.DataFrame) -> None:
    """Top-10 closeness side-by-side para los 3 modelos."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("P5 · Top-10 Closeness por modelo de peso", fontsize=13, fontweight="bold")
    for ax, modelo in zip(axes, ("saltos", "latencia", "carga")):
        nodos = df_close[f"nodo_{modelo}"].str[-20:]
        vals  = df_close[f"close_{modelo}"]
        ax.barh(nodos[::-1], vals[::-1], color="#2980b9", alpha=0.85)
        ax.set_title(f"Modelo: {modelo}"); ax.set_xlabel("Closeness")
        ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p5_closeness_comparativo.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P5 — Caminos más Cortos: Dijkstra y Floyd-Warshall ===\n")

    G = cargar_red(fuente="csv"); verificar(G)

    def _leer_csv(n):
        return pd.read_csv(os.path.join(DIR_ROOT, n), dtype=str)
    nodos_df   = _leer_csv("red_ucuenca_nodes.csv")
    aristas_df = _leer_csv("red_ucuenca_edges.csv")

    # Construcción de grafos pesados
    grafos = construir_grafos_pesados(G, nodos_df, aristas_df)
    print(f"  Grafos construidos: {list(grafos.keys())}")

    # Verificación: pesos no negativos (requisito de Dijkstra)
    for modelo, Gm in grafos.items():
        pesos_neg = [(u, v, Gm[u][v]["weight"])
                     for u, v in Gm.edges() if Gm[u][v]["weight"] < 0]
        if pesos_neg:
            print(f"  [ADVERTENCIA] Modelo '{modelo}': {len(pesos_neg)} aristas con peso negativo")
            for u, v, w in pesos_neg[:5]:
                print(f"    {u} — {v} : {w:.6f}")
        else:
            print(f"  [OK] Modelo '{modelo}': no se encontraron pesos negativos "
                  f"(Dijkstra puede aplicarse)")

    # Ítem 2: verificación 20 pares
    print("\n[Ítem 2] Verificación 20 pares aleatorios (modelo saltos)")
    df_ver = verificar_coincidencia(grafos["saltos"])
    n_ok   = df_ver["coincide"].sum()
    print(f"  {n_ok}/20 pares coinciden exactamente")
    df_ver.to_csv(os.path.join(DIR_TAB, "p5_verificacion.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p5_verificacion.csv')}")

    # Ítem 3: comparación de tiempos
    print("\n[Ítem 3] Comparación de tiempos")
    t_resultados = {}
    for modelo in ("saltos", "latencia", "carga"):
        t = comparar_tiempos(grafos[modelo])
        t_resultados[modelo] = t
        print(f"  {modelo:10s}  Dijkstra×n={t['t_dijkstra_total']:.4f}s  FW={t['t_fw']:.4f}s")
    graficar_tiempos(t_resultados["saltos"], t_resultados["latencia"], t_resultados["carga"])

    # Ítem 4: closeness por modelo
    print("\n[Ítem 4] Top-10 Closeness por modelo")
    df_close = closeness_por_modelo(grafos, nodos_df)
    print(df_close[["rank","nodo_saltos","close_saltos",
                     "nodo_latencia","close_latencia",
                     "nodo_carga","close_carga"]].to_string(index=False))
    df_close.to_csv(os.path.join(DIR_TAB, "p5_closeness_modelos.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p5_closeness_modelos.csv')}")
    graficar_closeness(df_close)

    # Ítem 5: par más distante
    print("\n[Ítem 5] Par de acceso más distante por modelo")
    df_dist = par_mas_distante(grafos, nodos_df)
    print(df_dist.to_string(index=False))
    df_dist.to_csv(os.path.join(DIR_TAB, "p5_par_mas_distante.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p5_par_mas_distante.csv')}")

    print("\n=== P5 completado ===\n")
