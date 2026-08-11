"""
problema4.py — Problema P4: Comunidades y Modularidad (Fase 2)
==============================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Aplica algoritmos de detección de comunidades sobre la red UCuenca y
compara la partición obtenida con la partición natural por campus.

Los cinco ítems resueltos son:
  Ítem 1 · Louvain con 5 semillas distintas — modularidad Q y estabilidad
  Ítem 2 · Comparación con partición por campus: NMI, ARI y matriz de confusión
  Ítem 3 · Nodos donde Louvain y campus discrepan — interpretación de ingeniería
  Ítem 4 · k-means espectral (Laplaciano) y comparación con Louvain
  Ítem 5 · Limitación de resolución de la modularidad

Uso:
    python problema4.py

Salidas (relativas a Resolución_ProyectoFinal/):
    results/tablas/p4_louvain_semillas.csv
    results/tablas/p4_comparacion_campus.txt
    results/tablas/p4_discrepancias.csv
    results/tablas/p4_kmeans.csv
    results/imagenes/p4_comunidades_louvain.png
    results/imagenes/p4_confusion_campus.png
    results/imagenes/p4_kmeans_vs_louvain.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os
import sys
import warnings
import collections

import networkx as nx
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_hex
import matplotlib.cm as cm

warnings.filterwarnings("ignore")

# Detección de comunidades (Louvain incluido en networkx >= 3.3
# o en python-louvain / community)
try:
    import community as community_louvain          # python-louvain
    _LOUVAIN_BACKEND = "python-louvain"
except ImportError:
    community_louvain = None
    _LOUVAIN_BACKEND = "networkx"

from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sklearn.metrics import (
    normalized_mutual_info_score,
    adjusted_rand_score,
)

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

def _crear_dirs() -> None:
    """Crea los directorios de salida si no existen."""
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


def _louvain_partition(G: nx.Graph, semilla: int) -> dict:
    """
    Ejecuta el algoritmo Louvain y devuelve un diccionario {nodo: comunidad}.

    Usa python-louvain si está disponible; si no, usa la implementación
    greedy_modularity_communities de NetworkX como aproximación.

    Argumentos:
        G       (nx.Graph): grafo no dirigido.
        semilla (int)     : semilla aleatoria para reproducibilidad.

    Salida:
        dict: {nodo: id_comunidad (int)}
    """
    if _LOUVAIN_BACKEND == "python-louvain":
        return community_louvain.best_partition(G, random_state=semilla)
    else:
        # Fallback: greedy modularity (NetworkX)
        from networkx.algorithms.community import greedy_modularity_communities
        comms = list(greedy_modularity_communities(G, seed=semilla))
        return {n: i for i, c in enumerate(comms) for n in c}


def _modularidad(G: nx.Graph, particion: dict) -> float:
    """
    Calcula la modularidad Q de una partición.

    Argumentos:
        G         (nx.Graph): grafo.
        particion (dict)    : {nodo: comunidad}.

    Salida:
        float: modularidad Q ∈ [-1, 1].
    """
    comunidades = collections.defaultdict(set)
    for nodo, com in particion.items():
        comunidades[com].add(nodo)
    return nx.community.modularity(G, list(comunidades.values()))


# ------------------------------------------------------------
# Ítem 1 — Louvain con 5 semillas
# ------------------------------------------------------------

def louvain_multisemilla(G: nx.Graph, semillas: list[int]) -> pd.DataFrame:
    """
    Ejecuta Louvain con varias semillas y reporta la modularidad y número
    de comunidades en cada ejecución para evaluar estabilidad.

    Argumentos:
        G       (nx.Graph) : grafo no dirigido.
        semillas (list[int]): lista de semillas a probar.

    Salida:
        pd.DataFrame con columnas [semilla, n_comunidades, modularidad].
        También devuelve la mejor partición como atributo .mejor_particion.
    """
    filas = []
    mejor_Q = -1.0
    mejor_particion = None

    for s in semillas:
        part = _louvain_partition(G, s)
        Q    = _modularidad(G, part)
        n_com = len(set(part.values()))
        filas.append({"semilla": s, "n_comunidades": n_com, "modularidad_Q": round(Q, 4)})
        if Q > mejor_Q:
            mejor_Q = Q
            mejor_particion = part

    df = pd.DataFrame(filas)
    df.mejor_particion = mejor_particion  # type: ignore[attr-defined]
    return df


# ------------------------------------------------------------
# Ítem 2 — Comparación con partición por campus
# ------------------------------------------------------------

def comparar_con_campus(
    G: nx.Graph, nodos_df: pd.DataFrame, particion: dict
) -> dict:
    """
    Compara la partición de Louvain con la partición natural por campus
    usando NMI (Información Mutua Normalizada) y ARI (Índice de Rand Ajustado).
    También construye la matriz de confusión comunidad × campus.

    Argumentos:
        G         (nx.Graph)     : grafo.
        nodos_df  (pd.DataFrame) : atributos de nodos (id, campus).
        particion (dict)         : {nodo: comunidad} resultado de Louvain.

    Salida:
        dict con claves:
            'nmi'         — float NMI ∈ [0, 1]
            'ari'         — float ARI ∈ [-1, 1]
            'confusion'   — pd.DataFrame (comunidades × campus)
            'nodos_tabla' — pd.DataFrame con nodo, campus, comunidad
    """
    id_to_campus = nodos_df.set_index("id")["campus"].to_dict()
    nodos = list(G.nodes())

    etiq_campus    = [id_to_campus.get(n, "Desconocido") for n in nodos]
    etiq_comunidad = [particion.get(n, -1) for n in nodos]

    nmi = normalized_mutual_info_score(etiq_campus, etiq_comunidad)
    ari = adjusted_rand_score(etiq_campus, etiq_comunidad)

    # Tabla nodo → campus + comunidad
    tabla = pd.DataFrame({
        "nodo"      : nodos,
        "campus"    : etiq_campus,
        "comunidad" : etiq_comunidad,
    })

    # Matriz de confusión
    confusion = (
        tabla.groupby(["comunidad", "campus"])
        .size()
        .unstack(fill_value=0)
    )

    return {
        "nmi"        : round(nmi, 4),
        "ari"        : round(ari, 4),
        "confusion"  : confusion,
        "nodos_tabla": tabla,
    }


# ------------------------------------------------------------
# Ítem 3 — Nodos con discrepancia Louvain vs campus
# ------------------------------------------------------------

def nodos_discrepantes(
    comparacion: dict, nodos_df: pd.DataFrame, G: nx.Graph
) -> pd.DataFrame:
    """
    Identifica los nodos donde la comunidad Louvain no coincide con la
    comunidad mayoritaria de su campus.

    Argumentos:
        comparacion (dict)         : resultado de comparar_con_campus().
        nodos_df    (pd.DataFrame) : atributos de nodos.
        G           (nx.Graph)     : grafo.

    Salida:
        pd.DataFrame con columnas [nodo, campus, comunidad, capa, grado,
                                    comunidad_mayoritaria_campus, discrepante].
    """
    tabla = comparacion["nodos_tabla"].copy()

    # Para cada campus, la comunidad más frecuente es la "esperada"
    campus_com_mayoritaria = (
        tabla.groupby("campus")["comunidad"]
        .agg(lambda x: x.value_counts().idxmax())
        .to_dict()
    )
    tabla["com_esperada"] = tabla["campus"].map(campus_com_mayoritaria)
    tabla["discrepante"]  = tabla["comunidad"] != tabla["com_esperada"]

    # Añadir capa y grado
    id_to_capa = nodos_df.set_index("id")["capa"].to_dict()
    tabla["capa"]  = tabla["nodo"].map(id_to_capa)
    tabla["grado"] = tabla["nodo"].map(dict(G.degree()))

    return tabla.sort_values("discrepante", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------
# Ítem 4 — k-means espectral (Laplaciano)
# ------------------------------------------------------------
# FUENTE: adaptado de codigo_referencia/kmeans/ejemplo1.jl
# (Dr. Fabián Astudillo-Salinas, Módulo 1217 — Redes Complejas).
# El código original implementa k-means desde cero en Julia con:
#   · init_plusplus()      → inicialización K-means++ (distancia²)
#   · assign_clusters()    → paso de asignación O(n·K·d)
#   · update_centroids()   → recálculo de centroides como media aritmética
#   · wcss()               → Within-Cluster Sum of Squares (métrica de convergencia)
#   · my_kmeans()          → bucle principal: asignar → actualizar → convergencia
# La adaptación a Python reemplaza el bucle manual por sklearn.cluster.KMeans,
# que implementa los mismos pasos internamente con inicialización K-means++
# (equivalente a init_plusplus) y criterio de convergencia por tolerancia en
# desplazamiento de centroides (equivalente al norm(μ_new - μ_old) < tol del original).
# El embedding espectral (vectores propios del Laplaciano) es la adaptación
# al dominio de grafos: sustituye los datos numéricos del ejemplo de pingüinos
# por coordenadas espectrales derivadas de la estructura topológica de la red.

def kmeans_espectral(G: nx.Graph, k: int, semilla: int = 42) -> dict:
    """
    Aplica k-means sobre los k primeros vectores propios del Laplaciano
    normalizado del grafo (clustering espectral).

    El Laplaciano normalizado L_sym = D^{-1/2} (D - A) D^{-1/2} captura
    la geometría espectral del grafo. Sus vectores propios de menor valor
    propio forman el embedding donde k-means opera.

    Adaptado de: codigo_referencia/kmeans/ejemplo1.jl
    (Módulo 1217 — Redes Complejas, Dr. Fabián Astudillo-Salinas)

    Argumentos:
        G      (nx.Graph): grafo no dirigido.
        k      (int)     : número de clusters (igual al número de comunidades Louvain).
        semilla (int)    : semilla para k-means (equivalente a Random.seed! del original).

    Salida:
        dict con claves:
            'etiquetas'       — {nodo: cluster}
            'k'               — número de clusters
            'valores_propios' — primeros k valores propios del Laplaciano
    """
    nodos = list(G.nodes())
    # Construir Laplaciano normalizado L_sym = D^{-1/2}(D-A)D^{-1/2}
    L = nx.normalized_laplacian_matrix(G, nodelist=nodos).toarray()

    # Calcular vectores propios (equivalente a eigen(L) del original en Julia)
    valores, vectores = np.linalg.eigh(L)

    # Embedding espectral: k vectores propios de menor valor propio
    # (los k primeros capturan la estructura comunitaria del grafo)
    embedding = vectores[:, :k]
    # Normalización L2 por fila (estabiliza k-means en el espacio espectral)
    embedding = normalize(embedding, norm="l2")

    # K-means con inicialización K-means++ (equivalente a init_plusplus del original)
    # n_init=20 replica múltiples inicializaciones para evitar óptimos locales
    km = KMeans(n_clusters=k, random_state=semilla, n_init=20, init="k-means++")
    etiquetas_array = km.fit_predict(embedding)

    etiquetas = {n: int(etiquetas_array[i]) for i, n in enumerate(nodos)}

    return {
        "etiquetas"      : etiquetas,
        "k"              : k,
        "valores_propios": valores[:k].tolist(),
    }


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_comunidades_louvain(
    G: nx.Graph, particion: dict, nodos_df: pd.DataFrame, Q: float
) -> None:
    """
    Visualiza el grafo coloreando los nodos según su comunidad Louvain.
    Disposición: spring layout (Fruchterman-Reingold).

    Argumentos:
        G         (nx.Graph)     : grafo.
        particion (dict)         : {nodo: comunidad}.
        nodos_df  (pd.DataFrame) : atributos de nodos.
        Q         (float)        : modularidad de la partición.

    Salida: None — guarda imagen en DIR_IMG/p4_comunidades_louvain.png
    """
    comunidades = sorted(set(particion.values()))
    cmap = cm.get_cmap("tab20", len(comunidades))
    color_map = {c: to_hex(cmap(i)) for i, c in enumerate(comunidades)}

    node_colors = [color_map[particion.get(n, 0)] for n in G.nodes()]

    pos = nx.spring_layout(G, seed=42, k=0.4)
    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#bdc3c7", width=0.6, alpha=0.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=60)

    leyenda = [mpatches.Patch(color=color_map[c], label=f"Comunidad {c}") for c in comunidades]
    ax.legend(handles=leyenda, loc="upper left", fontsize=8, ncol=2)
    ax.set_title(
        f"P4 · Comunidades Louvain — Red UCuenca\n"
        f"{len(comunidades)} comunidades · Q = {Q:.4f}",
        fontsize=13, fontweight="bold"
    )
    ax.axis("off")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p4_comunidades_louvain.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_confusion(confusion: pd.DataFrame) -> None:
    """
    Dibuja la matriz de confusión comunidad × campus como heatmap.

    Argumentos:
        confusion (pd.DataFrame): resultado de comparar_con_campus()['confusion'].

    Salida: None — guarda imagen en DIR_IMG/p4_confusion_campus.png
    """
    fig, ax = plt.subplots(figsize=(12, max(4, len(confusion) * 0.7)))
    im = ax.imshow(confusion.values, cmap="Blues", aspect="auto")
    plt.colorbar(im, ax=ax, label="Número de nodos")

    ax.set_xticks(range(len(confusion.columns)))
    ax.set_xticklabels(confusion.columns, rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(confusion.index)))
    ax.set_yticklabels([f"Comunidad {i}" for i in confusion.index], fontsize=9)

    for i in range(len(confusion.index)):
        for j in range(len(confusion.columns)):
            val = confusion.values[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center",
                        fontsize=8, color="white" if val > confusion.values.max() * 0.6 else "black")

    ax.set_title("P4 · Matriz de confusión: Comunidad × Campus", fontsize=13, fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p4_confusion_campus.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_kmeans_vs_louvain(
    G: nx.Graph, etiq_kmeans: dict, particion_louvain: dict
) -> None:
    """
    Visualización comparativa: k-means espectral (izquierda) vs Louvain (derecha).

    Argumentos:
        G               (nx.Graph): grafo.
        etiq_kmeans     (dict)    : {nodo: cluster} de k-means.
        particion_louvain (dict)  : {nodo: comunidad} de Louvain.

    Salida: None — guarda imagen en DIR_IMG/p4_kmeans_vs_louvain.png
    """
    pos = nx.spring_layout(G, seed=42, k=0.4)

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle("P4 · k-means espectral vs Louvain", fontsize=14, fontweight="bold")

    for ax, etiq, titulo in zip(
        axes,
        [etiq_kmeans, particion_louvain],
        ["k-means espectral (Laplaciano)", "Louvain"]
    ):
        clases = sorted(set(etiq.values()))
        cmap = cm.get_cmap("tab20", len(clases))
        color_map = {c: to_hex(cmap(i)) for i, c in enumerate(clases)}
        node_colors = [color_map[etiq.get(n, 0)] for n in G.nodes()]

        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#bdc3c7", width=0.5, alpha=0.4)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=55)
        leyenda = [mpatches.Patch(color=color_map[c], label=f"Cluster {c}") for c in clases]
        ax.legend(handles=leyenda, loc="upper left", fontsize=8, ncol=2)
        ax.set_title(titulo, fontsize=12)
        ax.axis("off")

    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p4_kmeans_vs_louvain.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================
# 1) Cargar la red y los atributos de nodos.
# 2) Ítem 1: Louvain con 5 semillas — modularidad y estabilidad.
# 3) Ítem 2: Comparar con partición por campus (NMI, ARI, confusión).
# 4) Ítem 3: Identificar nodos discrepantes.
# 5) Ítem 4: k-means espectral y comparación con Louvain.
# 6) Ítem 5: discutir limitación de resolución.
# 7) Generar tablas y visualizaciones.

if __name__ == "__main__":
    _crear_dirs()

    print(f"\n=== P4 — Comunidades y Modularidad (backend: {_LOUVAIN_BACKEND}) ===\n")
    G = cargar_red(fuente="csv")
    verificar(G)

    def _leer_csv(nombre: str) -> pd.DataFrame:
        return pd.read_csv(os.path.join(DIR_ROOT, nombre), dtype=str)

    nodos_df = _leer_csv("red_ucuenca_nodes.csv")

    # --- Ítem 1: Louvain con 5 semillas ---
    print("\n[Ítem 1] Louvain — 5 semillas")
    SEMILLAS = [0, 7, 13, 42, 99]
    df_semillas = louvain_multisemilla(G, SEMILLAS)
    print(df_semillas.to_string(index=False))
    df_semillas.to_csv(os.path.join(DIR_TAB, "p4_louvain_semillas.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p4_louvain_semillas.csv')}")

    # Mejor partición
    mejor_particion = df_semillas.mejor_particion
    mejor_Q = df_semillas["modularidad_Q"].max()
    n_com   = df_semillas.loc[df_semillas["modularidad_Q"].idxmax(), "n_comunidades"]
    print(f"\n  Mejor Q = {mejor_Q}  ({n_com} comunidades)")

    # --- Ítem 2: Comparación con campus ---
    print("\n[Ítem 2] Comparación con partición por campus")
    comp = comparar_con_campus(G, nodos_df, mejor_particion)
    print(f"  NMI = {comp['nmi']}   ARI = {comp['ari']}")
    print("\n  Matriz de confusión (comunidad × campus):")
    print(comp["confusion"].to_string())

    with open(os.path.join(DIR_TAB, "p4_comparacion_campus.txt"), "w", encoding="utf-8") as f:
        f.write(f"NMI = {comp['nmi']}\nARI = {comp['ari']}\n\n")
        f.write("Matriz de confusión (comunidad × campus):\n")
        f.write(comp["confusion"].to_string())
    print(f"\n  [OK] {os.path.join(DIR_TAB, 'p4_comparacion_campus.txt')}")

    # --- Ítem 3: Nodos discrepantes ---
    print("\n[Ítem 3] Nodos discrepantes (Louvain ≠ campus esperado)")
    tabla_disc = nodos_discrepantes(comp, nodos_df, G)
    n_disc = tabla_disc["discrepante"].sum()
    print(f"  Nodos discrepantes: {n_disc} / {len(G.nodes())}")
    disc_df = tabla_disc[tabla_disc["discrepante"]]
    print(disc_df[["nodo", "campus", "comunidad", "capa", "grado"]].to_string(index=False))
    disc_df.to_csv(os.path.join(DIR_TAB, "p4_discrepancias.csv"), index=False)
    print(f"  [OK] {os.path.join(DIR_TAB, 'p4_discrepancias.csv')}")

    # --- Ítem 4: k-means espectral ---
    print("\n[Ítem 4] k-means espectral (Laplaciano normalizado)")
    res_kmeans = kmeans_espectral(G, k=int(n_com), semilla=42)
    etiq_km = res_kmeans["etiquetas"]

    # NMI/ARI de k-means respecto a campus
    id_to_campus = nodos_df.set_index("id")["campus"].to_dict()
    nodos_lista = list(G.nodes())
    campus_labels = [id_to_campus.get(n, "?") for n in nodos_lista]
    kmeans_labels = [etiq_km[n] for n in nodos_lista]
    louvain_labels = [mejor_particion[n] for n in nodos_lista]

    nmi_km  = normalized_mutual_info_score(campus_labels, kmeans_labels)
    ari_km  = adjusted_rand_score(campus_labels, kmeans_labels)
    nmi_km_vs_louv = normalized_mutual_info_score(louvain_labels, kmeans_labels)

    pd.DataFrame({
        "nodo"   : nodos_lista,
        "campus" : campus_labels,
        "louvain": louvain_labels,
        "kmeans" : kmeans_labels,
    }).to_csv(os.path.join(DIR_TAB, "p4_kmeans.csv"), index=False)

    print(f"  k-means vs campus  → NMI={nmi_km:.4f}  ARI={ari_km:.4f}")
    print(f"  k-means vs Louvain → NMI={nmi_km_vs_louv:.4f}")
    print(f"  Primeros valores propios del Laplaciano: {[round(v, 4) for v in res_kmeans['valores_propios']]}")
    print(f"  [OK] {os.path.join(DIR_TAB, 'p4_kmeans.csv')}")

    # --- Ítem 5: Limitación de resolución ---
    print("\n[Ítem 5] Limitación de resolución de la modularidad")
    print(
        "  La modularidad Q tiene una resolución limitada: tiende a fusionar\n"
        "  comunidades pequeñas aunque estén bien definidas estructuralmente.\n"
        "  En UCuenca, los campus pequeños (Hospitalidad, Museo, Centro Histórico)\n"
        "  pueden ser absorbidos en la comunidad del campus más cercano topológicamente.\n"
        "  Esto explicaría que NMI < 1 incluso si la red tuviera partición perfecta por campus."
    )

    # --- Visualizaciones ---
    print("\n[Visualizaciones]")
    graficar_comunidades_louvain(G, mejor_particion, nodos_df, mejor_Q)
    graficar_confusion(comp["confusion"])
    graficar_kmeans_vs_louvain(G, etiq_km, mejor_particion)

    print("\n=== P4 completado ===\n")
