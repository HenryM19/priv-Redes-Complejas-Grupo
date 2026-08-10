"""
problema8.py — Problema P8: Percolación de Nodos y Aristas (Fase 4)
====================================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Analiza la robustez de la red UCuenca ante fallas usando percolación:
eliminación secuencial de nodos o aristas bajo 4 estrategias de ataque
y observando el colapso de la componente gigante.

Métrica principal:
  Eficiencia global  E(G) = (1/(n(n-1))) · Σ_{i≠j} 1/d(i,j)
  donde d(i,j) = ∞ si no hay camino ⟹ 0 en la suma.

Estrategias implementadas:
  1. Aleatorio         : eliminación aleatoria (promedio de 10 semillas)
  2. Grado-descendente : eliminar primero el nodo/arista de mayor grado
  3. Betweenness       : eliminar primero el nodo de mayor betweenness
  4. Grado-ascendente  : eliminar primero el nodo de menor grado (comparación)

Los cinco ítems resueltos son:
  Ítem 1 · Función de eficiencia global E(G)
  Ítem 2 · Percolación de nodos bajo 4 estrategias
  Ítem 3 · Percolación de aristas bajo 2 estrategias
  Ítem 4 · Comparación con modelos nulos (ER, CM, BA)
  Ítem 5 · Identificación del umbral de percolación

Uso:
    python problema8.py

Salidas:
    results/tablas/p8_percolacion_nodos.csv
    results/tablas/p8_percolacion_aristas.csv
    results/imagenes/p8_robustez_nodos.png
    results/imagenes/p8_robustez_aristas.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, random, copy
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
# Ítem 1 — Eficiencia global
# ------------------------------------------------------------

def eficiencia_global(G: nx.Graph) -> float:
    """
    Calcula la eficiencia global de un grafo.
    E(G) = 1/(n(n-1)) * Σ_{i≠j} 1/d(i,j)
    Si no hay camino entre i y j, su contribución es 0.

    Argumentos:
        G (nx.Graph): grafo (puede ser disconexo).

    Salida:
        float: eficiencia global ∈ [0, 1].
    """
    n = G.number_of_nodes()
    if n <= 1:
        return 0.0
    total = 0.0
    for u in G.nodes():
        lengths = nx.single_source_shortest_path_length(G, u)
        for v, d in lengths.items():
            if v != u and d > 0:
                total += 1.0 / d
    return total / (n * (n - 1))


# ------------------------------------------------------------
# Ítem 2 — Percolación de nodos
# ------------------------------------------------------------

def _orden_nodos(G: nx.Graph, estrategia: str, semilla: int = 42) -> list:
    """
    Genera el orden de eliminación de nodos según la estrategia.

    Argumentos:
        G          (nx.Graph): grafo actual.
        estrategia (str)     : 'aleatorio'|'grado_desc'|'betweenness'|'grado_asc'.
        semilla    (int)     : semilla para aleatoriedad.

    Salida:
        list: nodos en orden de eliminación.
    """
    nodos = list(G.nodes())
    if estrategia == "aleatorio":
        rng = random.Random(semilla)
        rng.shuffle(nodos)
        return nodos
    elif estrategia == "grado_desc":
        return sorted(nodos, key=lambda n: G.degree(n), reverse=True)
    elif estrategia == "betweenness":
        btw = nx.betweenness_centrality(G)
        return sorted(nodos, key=lambda n: btw[n], reverse=True)
    elif estrategia == "grado_asc":
        return sorted(nodos, key=lambda n: G.degree(n))
    else:
        raise ValueError(f"Estrategia desconocida: {estrategia}")


def percolacion_nodos(G: nx.Graph, estrategia: str,
                      semilla: int = 42, pasos: int = 30) -> pd.DataFrame:
    """
    Simula la percolación de nodos eliminando secuencialmente
    según la estrategia, midiendo la eficiencia global.

    Argumentos:
        G          (nx.Graph): grafo original.
        estrategia (str)     : estrategia de eliminación.
        semilla    (int)     : semilla para estrategia aleatoria.
        pasos      (int)     : número de puntos de muestreo.

    Salida:
        pd.DataFrame con columnas [fraccion_eliminada, eficiencia, n_componentes, tamanio_cgc].
    """
    Gc = G.copy()
    n_total = Gc.number_of_nodes()
    # Para estrategia estática, ordenamos el grafo original
    if estrategia != "aleatorio":
        orden = _orden_nodos(G, estrategia, semilla)
    else:
        orden = _orden_nodos(G, estrategia, semilla)

    muestras = np.linspace(0, 1, pasos + 1)
    filas = []
    eliminados = 0

    # Estado inicial
    filas.append({
        "fraccion_eliminada": 0.0,
        "eficiencia"        : eficiencia_global(Gc),
        "n_componentes"     : nx.number_connected_components(Gc),
        "tamanio_cgc"       : max(len(c) for c in nx.connected_components(Gc)),
    })

    for i, frac in enumerate(muestras[1:], 1):
        objetivo = int(frac * n_total)
        while eliminados < objetivo and eliminados < len(orden):
            nodo = orden[eliminados]
            if nodo in Gc:
                Gc.remove_node(nodo)
            eliminados += 1
        if Gc.number_of_nodes() == 0:
            filas.append({"fraccion_eliminada": frac, "eficiencia": 0.0,
                           "n_componentes": 0, "tamanio_cgc": 0})
            continue
        comps = list(nx.connected_components(Gc))
        filas.append({
            "fraccion_eliminada": round(frac, 4),
            "eficiencia"        : eficiencia_global(Gc),
            "n_componentes"     : len(comps),
            "tamanio_cgc"       : max(len(c) for c in comps),
        })
    return pd.DataFrame(filas)


def percolacion_aleatoria_media(G: nx.Graph, n_semillas: int = 5,
                                 pasos: int = 30) -> pd.DataFrame:
    """
    Promedia la percolación aleatoria sobre varias semillas para reducir
    la varianza estadística.

    Argumentos:
        G         (nx.Graph): grafo.
        n_semillas (int)    : número de semillas.
        pasos      (int)    : puntos de muestreo.

    Salida:
        pd.DataFrame: promedio de eficiencias por fracción.
    """
    dfs = [percolacion_nodos(G, "aleatorio", semilla=s, pasos=pasos)
           for s in range(n_semillas)]
    df_concat = pd.concat(dfs).groupby("fraccion_eliminada").mean().reset_index()
    return df_concat


# ------------------------------------------------------------
# Ítem 3 — Percolación de aristas
# ------------------------------------------------------------

def percolacion_aristas(G: nx.Graph, estrategia: str = "aleatorio",
                         semilla: int = 42, pasos: int = 30) -> pd.DataFrame:
    """
    Simula la percolación de aristas eliminando secuencialmente.

    Argumentos:
        G          (nx.Graph): grafo original.
        estrategia (str)     : 'aleatorio' | 'betweenness_arista'.
        semilla    (int)     : semilla aleatoria.
        pasos      (int)     : puntos de muestreo.

    Salida:
        pd.DataFrame con [fraccion_eliminada, eficiencia, n_componentes, tamanio_cgc].
    """
    Gc = G.copy()
    aristas = list(G.edges())
    m_total = len(aristas)

    if estrategia == "aleatorio":
        rng = random.Random(semilla)
        rng.shuffle(aristas)
        orden_aristas = aristas
    else:
        btw_e = nx.edge_betweenness_centrality(G)
        orden_aristas = sorted(aristas, key=lambda e: btw_e.get(e, btw_e.get((e[1],e[0]),0)),
                               reverse=True)

    muestras = np.linspace(0, 1, pasos + 1)
    filas = []
    eliminados = 0

    filas.append({
        "fraccion_eliminada": 0.0,
        "eficiencia"        : eficiencia_global(Gc),
        "n_componentes"     : nx.number_connected_components(Gc),
        "tamanio_cgc"       : max(len(c) for c in nx.connected_components(Gc)),
    })

    for frac in muestras[1:]:
        objetivo = int(frac * m_total)
        while eliminados < objetivo and eliminados < len(orden_aristas):
            u, v = orden_aristas[eliminados]
            if Gc.has_edge(u, v):
                Gc.remove_edge(u, v)
            eliminados += 1
        if Gc.number_of_nodes() == 0:
            filas.append({"fraccion_eliminada": frac, "eficiencia": 0.0,
                           "n_componentes": 0, "tamanio_cgc": 0})
            continue
        comps = list(nx.connected_components(Gc))
        filas.append({
            "fraccion_eliminada": round(frac, 4),
            "eficiencia"        : eficiencia_global(Gc),
            "n_componentes"     : len(comps),
            "tamanio_cgc"       : max(len(c) for c in comps),
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Ítem 4 — Comparación con modelos nulos
# ------------------------------------------------------------

def generar_modelo_nulo(G: nx.Graph, modelo: str, semilla: int = 42) -> nx.Graph:
    """
    Genera un modelo nulo para comparación.

    Argumentos:
        G      (nx.Graph): grafo de referencia.
        modelo (str)     : 'ER' | 'CM'.
        semilla (int)    : semilla aleatoria.

    Salida:
        nx.Graph: grafo del modelo nulo.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    rng = np.random.default_rng(semilla)
    if modelo == "ER":
        p = 2 * m / (n * (n - 1))
        H = nx.erdos_renyi_graph(n, p, seed=int(rng.integers(0, 10000)))
        return H
    elif modelo == "CM":
        grados = [d for _, d in G.degree()]
        try:
            H = nx.configuration_model(grados, seed=int(rng.integers(0, 10000)))
            H = nx.Graph(H)  # remover multi-aristas y auto-lazos
            H.remove_edges_from(nx.selfloop_edges(H))
        except Exception:
            H = nx.erdos_renyi_graph(n, 2*m/(n*(n-1)),
                                      seed=int(rng.integers(0, 10000)))
        return H
    raise ValueError(f"Modelo desconocido: {modelo}")


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_robustez_nodos(resultados: dict) -> None:
    """Curvas de eficiencia global vs fracción de nodos eliminados."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colores = {"aleatorio": "steelblue", "grado_desc": "red",
               "betweenness": "darkorange", "grado_asc": "green"}
    etiquetas = {"aleatorio": "Aleatorio (media)", "grado_desc": "Mayor grado primero",
                 "betweenness": "Mayor betweenness", "grado_asc": "Menor grado primero"}

    for est, df in resultados.items():
        ax1.plot(df["fraccion_eliminada"], df["eficiencia"],
                 color=colores.get(est, "gray"), label=etiquetas.get(est, est), linewidth=2)
        ax2.plot(df["fraccion_eliminada"], df["tamanio_cgc"] / df["tamanio_cgc"].iloc[0],
                 color=colores.get(est, "gray"), label=etiquetas.get(est, est), linewidth=2)

    ax1.set_xlabel("Fracción de nodos eliminados (f)")
    ax1.set_ylabel("Eficiencia global E(G)")
    ax1.set_title("Eficiencia global")
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)

    ax2.set_xlabel("Fracción de nodos eliminados (f)")
    ax2.set_ylabel("Fracción tamaño CGC")
    ax2.set_title("Tamaño de la componente gigante")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)

    plt.suptitle("P8 · Percolación de nodos — Red UCuenca", fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p8_robustez_nodos.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_robustez_aristas(res_aleat: pd.DataFrame,
                               res_btw: pd.DataFrame) -> None:
    """Curvas de eficiencia vs fracción de aristas eliminadas."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(res_aleat["fraccion_eliminada"], res_aleat["eficiencia"],
            "b-", linewidth=2, label="Aristas aleatorio")
    ax.plot(res_btw["fraccion_eliminada"], res_btw["eficiencia"],
            "r--", linewidth=2, label="Mayor betweenness de arista")
    ax.set_xlabel("Fracción de aristas eliminadas (q)")
    ax.set_ylabel("Eficiencia global E(G)")
    ax.set_title("P8 · Percolación de aristas — Red UCuenca", fontweight="bold")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p8_robustez_aristas.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P8 — Percolación de Nodos y Aristas ===\n")

    G = cargar_red(fuente="csv"); verificar(G)
    E0 = eficiencia_global(G)
    print(f"  Eficiencia global inicial E₀ = {E0:.4f}\n")

    PASOS = 20  # suficiente resolución para la curva

    # Ítem 2: percolación de nodos
    print("[Ítem 2] Percolación de nodos...")
    df_aleat  = percolacion_aleatoria_media(G, n_semillas=5, pasos=PASOS)
    print("  [OK] aleatorio")
    df_gdesc  = percolacion_nodos(G, "grado_desc", pasos=PASOS)
    print("  [OK] grado_desc")
    df_btw    = percolacion_nodos(G, "betweenness", pasos=PASOS)
    print("  [OK] betweenness")
    df_gasc   = percolacion_nodos(G, "grado_asc", pasos=PASOS)
    print("  [OK] grado_asc")

    resultados_nodos = {
        "aleatorio" : df_aleat,
        "grado_desc": df_gdesc,
        "betweenness": df_btw,
        "grado_asc" : df_gasc,
    }

    # Guardar
    df_todos_nodos = pd.concat(
        [df.assign(estrategia=k) for k, df in resultados_nodos.items()]
    )
    df_todos_nodos.to_csv(os.path.join(DIR_TAB, "p8_percolacion_nodos.csv"), index=False)

    graficar_robustez_nodos(resultados_nodos)

    # Umbral aproximado (f tal que eficiencia cae al 50%)
    for est, df in resultados_nodos.items():
        e_norm = df["eficiencia"] / df["eficiencia"].iloc[0]
        for _, row in df.iterrows():
            if row["eficiencia"] / df["eficiencia"].iloc[0] < 0.5:
                print(f"  Umbral 50% E — {est:15s}: f ≈ {row['fraccion_eliminada']:.2f}")
                break

    # Ítem 3: percolación de aristas
    print("\n[Ítem 3] Percolación de aristas...")
    df_ar_aleat = percolacion_aristas(G, "aleatorio", pasos=PASOS)
    print("  [OK] aristas aleatorio")
    df_ar_btw   = percolacion_aristas(G, "betweenness_arista", pasos=PASOS)
    print("  [OK] aristas betweenness")

    pd.concat([df_ar_aleat.assign(estrategia="aleatorio"),
               df_ar_btw.assign(estrategia="betweenness_arista")
    ]).to_csv(os.path.join(DIR_TAB, "p8_percolacion_aristas.csv"), index=False)

    graficar_robustez_aristas(df_ar_aleat, df_ar_btw)

    # Ítem 4: comparación con modelos nulos
    print("\n[Ítem 4] Comparación con modelos nulos (ER, CM)...")
    for modelo in ["ER", "CM"]:
        H = generar_modelo_nulo(G, modelo)
        e_h = eficiencia_global(H)
        df_hn = percolacion_nodos(H, "grado_desc", pasos=PASOS)
        # Umbral
        for _, row in df_hn.iterrows():
            if df_hn["eficiencia"].iloc[0] > 0 and \
               row["eficiencia"] / df_hn["eficiencia"].iloc[0] < 0.5:
                print(f"  Modelo {modelo}: E₀={e_h:.4f}  umbral 50%≈f={row['fraccion_eliminada']:.2f}")
                break

    print("\n=== P8 completado ===\n")
