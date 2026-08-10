"""
problema1.py — Problema P1: Medidas Fundamentales (Fase 1)
===========================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Calcula e interpreta las medidas estructurales fundamentales de la red
de datos de la Universidad de Cuenca (177 nodos, 209 aristas).

Los seis ítems resueltos son:
  Ítem 1 · Métricas básicas del grafo
  Ítem 2 · Distribución de grado (histograma + log-log)
  Ítem 3 · Centralidades: grado, betweenness, closeness, eigenvector
  Ítem 4 · Clustering, diámetro, distancia media y asortatividad
  Ítem 5 · Puntos de articulación y puentes (por campus y capa)
  Ítem 6 · Contraste con el informe técnico (redundancia core–agregación)

Uso:
    python problema1.py

Salidas (relativas a Resolución_ProyectoFinal/):
    results/tablas/p1_metricas_basicas.txt
    results/tablas/p1_centralidades_top10.csv
    results/tablas/p1_articulacion_campus.csv
    results/tablas/p1_articulacion_capa.csv
    results/tablas/p1_puentes_campus.csv
    results/tablas/p1_redundancia.txt
    results/imagenes/p1_distribucion_grado.png
    results/imagenes/p1_centralidades_top10.png
    results/imagenes/p1_articulacion_puentes.png
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
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

warnings.filterwarnings("ignore")

# --- Rutas del proyecto ---
DIR_SRC    = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL  = os.path.dirname(DIR_SRC)                      # Resolución_ProyectoFinal/
DIR_ROOT   = os.path.dirname(DIR_RESOL)                    # ProyectoFinal/
DIR_BASE   = os.path.join(DIR_ROOT, "codigo_base")         # codigo_base/
DIR_TAB    = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG    = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar           # noqa: E402  (importación local)


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
    for d in (DIR_TAB, DIR_IMG):
        os.makedirs(d, exist_ok=True)


def _guardar_tabla(texto: str, nombre: str) -> None:
    """
    Escribe un bloque de texto como archivo .txt en results/tablas/.

    Argumentos:
        texto  (str): contenido a guardar.
        nombre (str): nombre del archivo, sin ruta.

    Salida: None
    """
    ruta = os.path.join(DIR_TAB, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"  [OK] {ruta}")


def _guardar_csv(df: pd.DataFrame, nombre: str) -> None:
    """
    Guarda un DataFrame como CSV en results/tablas/.

    Argumentos:
        df     (pd.DataFrame): tabla a guardar.
        nombre (str): nombre del archivo, sin ruta.

    Salida: None
    """
    ruta = os.path.join(DIR_TAB, nombre)
    df.to_csv(ruta, index=False, encoding="utf-8")
    print(f"  [OK] {ruta}")


def _guardar_figura(fig: plt.Figure, nombre: str) -> None:
    """
    Guarda una figura matplotlib en results/imagenes/.

    Argumentos:
        fig    (plt.Figure): figura a guardar.
        nombre (str): nombre del archivo, sin ruta.

    Salida: None
    """
    ruta = os.path.join(DIR_IMG, nombre)
    fig.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


# ------------------------------------------------------------
# Ítem 1 · Métricas básicas
# ------------------------------------------------------------

def metricas_basicas(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Calcula las métricas básicas del grafo: nodos, aristas, densidad,
    componentes conexas y tamaño de la mayor.

    Argumentos:
        G        (nx.Graph)    : grafo de la red UCuenca.
        nodos_df (pd.DataFrame): tabla de nodos con columnas campus y capa.

    Salida:
        dict: {
            'n'              (int)  : número de nodos,
            'm'              (int)  : número de aristas,
            'densidad'       (float): densidad del grafo 2m / n(n-1),
            'n_componentes'  (int)  : número de componentes conexas,
            'tam_mayor'      (int)  : tamaño de la componente más grande,
        }
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    componentes = list(nx.connected_components(G))

    resultado = {
        "n"             : n,
        "m"             : m,
        "densidad"      : nx.density(G),
        "n_componentes" : len(componentes),
        "tam_mayor"     : max(len(c) for c in componentes),
    }

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 1 · MÉTRICAS BÁSICAS",
        "=" * 60,
        f"  Nodos (n)                     : {resultado['n']}",
        f"  Aristas (m)                   : {resultado['m']}",
        f"  Densidad                      : {resultado['densidad']:.6f}",
        f"  Componentes conexas           : {resultado['n_componentes']}",
        f"  Tamaño de la mayor componente : {resultado['tam_mayor']}",
        "",
        "  INTERPRETACIÓN:",
        "  La densidad es muy baja (~0.013), lo que es esperable en una",
        "  red de infraestructura jerárquica: cada equipo se conecta solo",
        "  a sus vecinos inmediatos en la jerarquía (core → agregación →",
        "  acceso), no a todos los demás. Una red completa tendría",
        f"  densidad 1.0 y requeriría {n*(n-1)//2} aristas.",
        "  El grafo es conexo (1 componente), confirmando que todos los",
        "  campus tienen al menos un camino hacia el resto de la red.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_metricas_basicas.txt")
    return resultado


# ------------------------------------------------------------
# Ítem 2 · Distribución de grado
# ------------------------------------------------------------

def distribucion_grado(G: nx.Graph) -> dict:
    """
    Calcula la distribución de grado y genera el histograma más el
    gráfico log-log para discutir si la red tiene cola pesada.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca.

    Salida:
        dict: {
            'grados'     (list[int])  : lista de grados de todos los nodos,
            'grado_medio'(float)      : grado medio <k>,
            'grado_max'  (int)        : grado máximo,
            'grado_min'  (int)        : grado mínimo,
            'conteo'     (dict)       : {grado: frecuencia},
        }
    """
    grados = [d for _, d in G.degree()]
    conteo = collections.Counter(grados)

    resultado = {
        "grados"      : grados,
        "grado_medio" : float(np.mean(grados)),
        "grado_max"   : max(grados),
        "grado_min"   : min(grados),
        "conteo"      : dict(conteo),
    }

    # --- Figura: histograma (izq) + log-log (der) ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "P1 · Distribución de grado — Red UCuenca",
        fontsize=13, fontweight="bold"
    )

    # Panel izquierdo: histograma lineal
    ax = axes[0]
    bins = range(resultado["grado_min"], resultado["grado_max"] + 2)
    ax.hist(grados, bins=bins, color="#2980b9", edgecolor="white",
            linewidth=0.6, align="left")
    ax.axvline(resultado["grado_medio"], color="#e74c3c", linestyle="--",
               linewidth=1.8, label=f"<k> = {resultado['grado_medio']:.2f}")
    ax.set_xlabel("Grado k", fontsize=11)
    ax.set_ylabel("Número de nodos", fontsize=11)
    ax.set_title("Histograma lineal", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.4)

    # Panel derecho: gráfico log-log (P(k) vs k)
    ax = axes[1]
    ks = sorted(conteo.keys())
    pk = [conteo[k] / len(grados) for k in ks]
    ax.scatter(ks, pk, color="#2980b9", s=60, zorder=3, label="P(k) observada")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Grado k (escala log)", fontsize=11)
    ax.set_ylabel("P(k) (escala log)", fontsize=11)
    ax.set_title("Gráfico log-log", fontsize=11)
    ax.grid(True, which="both", alpha=0.3)

    # Anotación sobre cola pesada
    ax.text(
        0.05, 0.10,
        "¿Cola pesada?\nCon n=177 es difícil\nconcluir ley de potencia\nsin test estadístico.",
        transform=ax.transAxes, fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fef9e7", alpha=0.85)
    )
    ax.legend(fontsize=10)

    fig.tight_layout()
    _guardar_figura(fig, "p1_distribucion_grado.png")

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 2 · DISTRIBUCIÓN DE GRADO",
        "=" * 60,
        f"  Grado medio <k>  : {resultado['grado_medio']:.4f}",
        f"  Grado máximo     : {resultado['grado_max']}",
        f"  Grado mínimo     : {resultado['grado_min']}",
        "",
        "  Frecuencias por grado:",
    ]
    for k in sorted(conteo):
        lineas.append(f"    k={k:2d} → {conteo[k]:3d} nodos")
    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "  La distribución muestra una cola derecha: unos pocos nodos",
        "  (switches de core y agregación) concentran la mayoría de",
        "  conexiones. Sin embargo, con solo 177 nodos, el rango de",
        "  grados (1–" + str(resultado['grado_max']) + ") es insuficiente",
        "  para ajustar una ley de potencia P(k) ~ k^{-γ} con rigor.",
        "  Un test Kolmogorov-Smirnov o powerlaw (Clauset et al. 2009)",
        "  sería necesario antes de proclamar 'red libre de escala'.",
        "  Lo que sí se observa: nodos de grado 1 (hojas de acceso) son",
        "  la mayoría, y el nodo de mayor grado es un switch de core.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_distribucion_grado.txt")
    return resultado


# ------------------------------------------------------------
# Ítem 3 · Centralidades
# ------------------------------------------------------------

def centralidades(G: nx.Graph) -> pd.DataFrame:
    """
    Calcula las cuatro centralidades principales y devuelve una tabla
    con el top-10 de cada una, alineadas en columnas comparativas.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca.

    Salida:
        pd.DataFrame: tabla con columnas
            ['rank', 'nodo_grado', 'grado', 'nodo_between', 'betweenness',
             'nodo_close', 'closeness', 'nodo_eigen', 'eigenvector']
    """
    # Cálculo de las cuatro centralidades
    c_grado     = nx.degree_centrality(G)
    c_between   = nx.betweenness_centrality(G, normalized=True)
    c_close     = nx.closeness_centrality(G)
    c_eigen     = nx.eigenvector_centrality(G, max_iter=1000)

    top_n = 10

    def _top(d: dict, n: int = top_n) -> list:
        return sorted(d.items(), key=lambda x: -x[1])[:n]

    top_g = _top(c_grado)
    top_b = _top(c_between)
    top_c = _top(c_close)
    top_e = _top(c_eigen)

    # Tabla comparativa
    filas = []
    for i in range(top_n):
        filas.append({
            "rank"         : i + 1,
            "nodo_grado"   : top_g[i][0],
            "grado"        : round(top_g[i][1], 4),
            "nodo_between" : top_b[i][0],
            "betweenness"  : round(top_b[i][1], 4),
            "nodo_close"   : top_c[i][0],
            "closeness"    : round(top_c[i][1], 4),
            "nodo_eigen"   : top_e[i][0],
            "eigenvector"  : round(top_e[i][1], 4),
        })
    df = pd.DataFrame(filas)
    _guardar_csv(df, "p1_centralidades_top10.csv")

    # --- Figura: gráfico de barras horizontal por centralidad ---
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "P1 · Top-10 nodos por centralidad — Red UCuenca",
        fontsize=13, fontweight="bold"
    )

    configs = [
        (axes[0, 0], top_g, "Centralidad de Grado",           "#2980b9"),
        (axes[0, 1], top_b, "Centralidad de Intermediación",   "#e67e22"),
        (axes[1, 0], top_c, "Centralidad de Cercanía",         "#27ae60"),
        (axes[1, 1], top_e, "Centralidad de Vector Propio",    "#8e44ad"),
    ]

    for ax, top, titulo, color in configs:
        nodos  = [t[0] for t in reversed(top)]
        valores = [t[1] for t in reversed(top)]
        # Nombres cortos para legibilidad
        nodos_cortos = [n[-14:] if len(n) > 14 else n for n in nodos]
        bars = ax.barh(nodos_cortos, valores, color=color, alpha=0.85,
                       edgecolor="white", linewidth=0.5)
        ax.set_title(titulo, fontsize=11, fontweight="bold")
        ax.set_xlabel("Valor normalizado", fontsize=9)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", alpha=0.3)
        # Etiqueta de valor al final de cada barra
        for bar, val in zip(bars, valores):
            ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", fontsize=7.5)

    fig.tight_layout()
    _guardar_figura(fig, "p1_centralidades_top10.png")

    # --- Texto de reporte ---
    print("\n" + "=" * 60)
    print("ÍTEM 3 · CENTRALIDADES — TOP-10 COMPARATIVO")
    print("=" * 60)
    print(df.to_string(index=False))
    print()
    print("  INTERPRETACIÓN:")
    print("  Los nodos de mayor grado suelen ser switches de core o")
    print("  agregación. La intermediación (betweenness) identifica los")
    print("  cuellos de botella del enrutamiento: si un nodo con alta")
    print("  intermediación falla, muchos caminos quedan interrumpidos.")
    print("  La cercanía (closeness) señala qué nodo puede alcanzar")
    print("  cualquier otro en menos saltos: útil para ubicar servicios")
    print("  centralizados (DNS, NTP). El vector propio pondera la")
    print("  calidad de los vecinos: un nodo de acceso conectado a un")
    print("  core potente tiene alta centralidad de vector propio.")
    print("=" * 60)
    return df


# ------------------------------------------------------------
# Ítem 4 · Clustering, diámetro, distancia media y asortatividad
# ------------------------------------------------------------

def metricas_cohesion(G: nx.Graph) -> dict:
    """
    Calcula el coeficiente de clustering medio, el diámetro, la
    distancia media entre pares y la asortatividad por grado.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca (debe ser conexo).

    Salida:
        dict: {
            'clustering_medio' (float): coeficiente de clustering promedio,
            'diametro'         (int)  : máxima distancia más corta,
            'distancia_media'  (float): promedio de todas las distancias,
            'asortatividad'    (float): correlación de Pearson de grados,
        }
    """
    resultado = {
        "clustering_medio" : nx.average_clustering(G),
        "diametro"         : nx.diameter(G),
        "distancia_media"  : nx.average_shortest_path_length(G),
        "asortatividad"    : nx.degree_assortativity_coefficient(G),
    }

    lineas = [
        "=" * 60,
        "ÍTEM 4 · CLUSTERING, DIÁMETRO, DISTANCIA MEDIA Y ASORTATIVIDAD",
        "=" * 60,
        f"  Clustering medio <C>          : {resultado['clustering_medio']:.6f}",
        f"  Diámetro                      : {resultado['diametro']}",
        f"  Distancia media               : {resultado['distancia_media']:.4f}",
        f"  Asortatividad por grado (r)   : {resultado['asortatividad']:.4f}",
        "",
        "  INTERPRETACIÓN:",
        "  El clustering medio es muy bajo: en una red jerárquica los",
        "  equipos de acceso se conectan solo hacia arriba (a su switch",
        "  de agregación), no entre sí, por lo que hay muy pocos",
        "  triángulos. Las redes sociales, en cambio, tienen clustering",
        "  alto porque 'los amigos de mis amigos son mis amigos'.",
        "",
        "  La asortatividad negativa es la firma de una red jerárquica:",
        "  los nodos de alto grado (core) se conectan con nodos de bajo",
        "  grado (acceso), no entre sí. Esto implica que los hubs son",
        "  resistentes a fallos aleatorios pero vulnerables si se ataca",
        "  específicamente un switch de core o agregación.",
        "",
        "  El diámetro y la distancia media son relativamente bajos",
        "  gracias a la jerarquía: cualquier equipo llega a cualquier",
        "  otro en pocos saltos atravesando la cadena acceso→agg→core.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_cohesion.txt")
    return resultado


# ------------------------------------------------------------
# Ítem 5 · Puntos de articulación y puentes
# ------------------------------------------------------------

def articulacion_y_puentes(G: nx.Graph, nodos_df: pd.DataFrame,
                            aristas_df: pd.DataFrame) -> dict:
    """
    Identifica los puntos de articulación (nodos cuya eliminación
    desconecta el grafo) y los puentes (aristas equivalentes), y
    los contabiliza por campus y por capa.

    Argumentos:
        G         (nx.Graph)    : grafo de la red UCuenca.
        nodos_df  (pd.DataFrame): tabla de nodos con columnas id, campus, capa.
        aristas_df(pd.DataFrame): tabla de aristas con columnas source, target.

    Salida:
        dict: {
            'articulacion'       (list[str])          : nodos de articulación,
            'puentes'            (list[tuple])         : aristas puente (u, v),
            'art_por_campus'     (pd.DataFrame)        : conteo por campus,
            'art_por_capa'       (pd.DataFrame)        : conteo por capa,
            'puentes_por_campus' (pd.DataFrame)        : conteo puentes por campus,
        }
    """
    # Puntos de articulación
    art_set = set(nx.articulation_points(G))
    art_lista = sorted(art_set)

    # Puentes
    puentes = list(nx.bridges(G))

    # Mapa nodo → campus/capa
    nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))
    nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))

    # Conteo de articulación por campus y capa
    campus_art = collections.Counter(nodo_campus.get(n, "?") for n in art_lista)
    capa_art   = collections.Counter(nodo_capa.get(n, "?")   for n in art_lista)

    df_art_campus = pd.DataFrame(
        sorted(campus_art.items(), key=lambda x: -x[1]),
        columns=["campus", "puntos_articulacion"]
    )
    df_art_capa = pd.DataFrame(
        sorted(capa_art.items(), key=lambda x: -x[1]),
        columns=["capa", "puntos_articulacion"]
    )

    # Puentes: asignar a campus del nodo de menor capa jerárquica
    jerarquia = {"core": 0, "wan": 1, "interconexion": 1,
                 "agregacion": 2, "acceso": 3}
    campus_puentes = []
    for u, v in puentes:
        # El puente se asigna al campus del nodo más «alto» en la jerarquía
        j_u = jerarquia.get(nodo_capa.get(u, "acceso"), 3)
        j_v = jerarquia.get(nodo_capa.get(v, "acceso"), 3)
        nodo_ref = u if j_u <= j_v else v
        campus_puentes.append(nodo_campus.get(nodo_ref, "?"))

    df_puentes_campus = pd.DataFrame(
        sorted(collections.Counter(campus_puentes).items(), key=lambda x: -x[1]),
        columns=["campus", "puentes"]
    )

    _guardar_csv(df_art_campus,    "p1_articulacion_campus.csv")
    _guardar_csv(df_art_capa,      "p1_articulacion_capa.csv")
    _guardar_csv(df_puentes_campus,"p1_puentes_campus.csv")

    # --- Figura: visualización de articulaciones y puentes ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "P1 · Puntos de articulación y puentes — Red UCuenca",
        fontsize=12, fontweight="bold"
    )

    # Subgráfico izquierdo: articulaciones por capa
    ax = axes[0]
    df_art_capa_plot = df_art_capa.sort_values("puntos_articulacion")
    ax.barh(df_art_capa_plot["capa"], df_art_capa_plot["puntos_articulacion"],
            color="#e74c3c", edgecolor="white", linewidth=0.6)
    ax.set_title(f"Puntos de articulación por capa\n(total: {len(art_lista)})",
                 fontsize=10)
    ax.set_xlabel("Cantidad", fontsize=9)
    ax.grid(axis="x", alpha=0.3)

    # Subgráfico derecho: puentes por campus
    ax = axes[1]
    df_p_plot = df_puentes_campus.sort_values("puentes")
    ax.barh(df_p_plot["campus"], df_p_plot["puentes"],
            color="#e67e22", edgecolor="white", linewidth=0.6)
    ax.set_title(f"Puentes por campus\n(total: {len(puentes)})", fontsize=10)
    ax.set_xlabel("Cantidad", fontsize=9)
    ax.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    _guardar_figura(fig, "p1_articulacion_puentes.png")

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 5 · PUNTOS DE ARTICULACIÓN Y PUENTES",
        "=" * 60,
        f"  Total puntos de articulación  : {len(art_lista)}",
        f"  Total puentes                 : {len(puentes)}",
        "",
        "  Articulaciones por campus:",
    ]
    for _, fila in df_art_campus.iterrows():
        lineas.append(f"    {fila['campus']:<42} {fila['puntos_articulacion']:>4}")
    lineas += ["", "  Articulaciones por capa:"]
    for _, fila in df_art_capa.iterrows():
        lineas.append(f"    {fila['capa']:<20} {fila['puntos_articulacion']:>4}")
    lineas += ["", "  Puentes por campus:"]
    for _, fila in df_puentes_campus.iterrows():
        lineas.append(f"    {fila['campus']:<42} {fila['puentes']:>4}")
    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "  Un punto de articulación es un nodo cuya falla desconecta",
        "  al menos a un subconjunto de la red. En una jerarquía sin",
        "  redundancia (un solo switch de agregación por edificio) ese",
        "  switch ES un punto de articulación. Los puentes son la",
        "  versión de arista: un único enlace que, si falla, aísla a",
        "  un segmento. Campus con muchos puentes carecen de caminos",
        "  alternativos y son más vulnerables a fallos de enlace.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_articulacion_puentes.txt")

    return {
        "articulacion"       : art_lista,
        "puentes"            : puentes,
        "art_por_campus"     : df_art_campus,
        "art_por_capa"       : df_art_capa,
        "puentes_por_campus" : df_puentes_campus,
    }


# ------------------------------------------------------------
# Ítem 6 · Contraste con el informe técnico (redundancia)
# ------------------------------------------------------------

def contraste_redundancia(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Verifica empíricamente si cada campus tiene redundancia
    core–agregación usando el atributo capa del grafo.

    La redundancia core–agregación existe cuando un switch de
    agregación está conectado a MÁS DE UN switch de core del
    mismo campus. Si todos los switches de agregación de un campus
    solo tienen un vecino de capa core, el campus NO tiene
    redundancia de núcleo — contradiga o confirme lo que afirma
    el informe técnico.

    Argumentos:
        G        (nx.Graph)    : grafo de la red UCuenca.
        nodos_df (pd.DataFrame): tabla con columnas id, campus, capa.

    Salida:
        dict: {campus: {'agg_nodes': list, 'con_redundancia': int,
                        'sin_redundancia': int, 'tiene_redundancia': bool}}
    """
    # Mapas de apoyo
    nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))
    nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))

    # Para cada campus, analizar sus switches de agregación
    campus_unicos = [c for c in nodos_df["campus"].unique()
                     if c != "Nube MPLS"]

    resultado = {}
    for campus in sorted(campus_unicos):
        nodos_agg = [n for n in G.nodes()
                     if nodo_campus.get(n) == campus
                     and nodo_capa.get(n) == "agregacion"]

        con_red = 0
        sin_red = 0
        for agg in nodos_agg:
            vecinos_core = [v for v in G.neighbors(agg)
                            if nodo_capa.get(v) == "core"]
            if len(vecinos_core) > 1:
                con_red += 1
            else:
                sin_red += 1

        resultado[campus] = {
            "agg_nodes"        : nodos_agg,
            "con_redundancia"  : con_red,
            "sin_redundancia"  : sin_red,
            "tiene_redundancia": con_red > 0,
        }

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 6 · CONTRASTE CON EL INFORME TÉCNICO",
        "         Redundancia core–agregación por campus",
        "=" * 60,
        f"  {'Campus':<42} {'Nodos agg':>9} {'Con red.':>8} {'Sin red.':>8} {'Redundancia':>11}",
        "  " + "-" * 80,
    ]
    for campus, datos in resultado.items():
        n_agg = len(datos["agg_nodes"])
        con   = datos["con_redundancia"]
        sin   = datos["sin_redundancia"]
        tiene = "SÍ ✓" if datos["tiene_redundancia"] else "NO ✗"
        lineas.append(
            f"  {campus:<42} {n_agg:>9} {con:>8} {sin:>8} {tiene:>11}"
        )

    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "  Balzay: el informe afirma redundancia core–agregación. Los",
        "  datos deben confirmarla (switches de agregación conectados a",
        "  DT-0A-C12 Y DT-0A-C13 simultáneamente).",
        "",
        "  Paraíso: el informe también afirma redundancia, pero los",
        "  datos revelan un solo switch de core (CPAR-C10). Los dobles",
        "  enlaces de sus switches de agregación van ambos al MISMO",
        "  core → es agregación de puertos (LAG), no redundancia de",
        "  núcleo. La afirmación del informe es incorrecta.",
        "",
        "  Campus Central: el informe describe enlaces simples agg–core,",
        "  pero los datos muestran que los 13 switches CC-* están",
        "  doblemente conectados a DATCC-2A-C2 y DATCC-2A-C3.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_redundancia.txt")
    return resultado


# ============================================================
# CÓDIGO MAIN
# ============================================================
# 1) Crear directorios de salida.
# 2) Cargar y verificar el grafo UCuenca.
# 3) Cargar los DataFrames de nodos y aristas para atributos.
# 4) Ejecutar los seis ítems del Problema P1 en orden.

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PROBLEMA P1 — MEDIDAS FUNDAMENTALES")
    print("Red de datos · Universidad de Cuenca")
    print("=" * 60 + "\n")

    # 1) Directorios
    _crear_dirs()

    # 2) Cargar grafo y verificar pipeline
    G = cargar_red(fuente="csv")
    ok = verificar(G)
    if not ok:
        sys.exit("Pipeline fallido: corrija la carga antes de continuar.")

    # 3) Cargar DataFrames de atributos desde los CSV
    import csv as _csv

    def _leer_csv(nombre: str) -> pd.DataFrame:
        ruta = os.path.join(DIR_ROOT, nombre)
        return pd.read_csv(ruta, dtype=str)

    nodos_df   = _leer_csv("red_ucuenca_nodes.csv")
    aristas_df = _leer_csv("red_ucuenca_edges.csv")

    # 4.1) Ítem 1 — Métricas básicas
    print("\n[1/6] Métricas básicas...")
    metricas_basicas(G, nodos_df)

    # 4.2) Ítem 2 — Distribución de grado
    print("\n[2/6] Distribución de grado...")
    distribucion_grado(G)

    # 4.3) Ítem 3 — Centralidades
    print("\n[3/6] Centralidades...")
    centralidades(G)

    # 4.4) Ítem 4 — Clustering, diámetro, distancia media, asortatividad
    print("\n[4/6] Métricas de cohesión...")
    metricas_cohesion(G)

    # 4.5) Ítem 5 — Puntos de articulación y puentes
    print("\n[5/6] Puntos de articulación y puentes...")
    articulacion_y_puentes(G, nodos_df, aristas_df)

    # 4.6) Ítem 6 — Contraste con el informe técnico
    print("\n[6/6] Contraste con el informe técnico...")
    contraste_redundancia(G, nodos_df)

    print("\n" + "=" * 60)
    print("P1 completado. Resultados en:")
    print(f"  Tablas  → {DIR_TAB}")
    print(f"  Imágenes→ {DIR_IMG}")
    print("=" * 60 + "\n")
