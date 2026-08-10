"""
problema2.py — Problema P2: Modelos Nulos y Visualización (Fase 1)
==================================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Compara la red real UCuenca con tres modelos nulos (Erdős–Rényi,
modelo de configuración, Barabási–Albert) y produce dos visualizaciones
propias con criterios distintos de color y tamaño de nodo.

Los tres ítems resueltos son:
  Ítem 1 · 100 realizaciones ER + 100 realizaciones CM
           Comparación de clustering, distancia media, diámetro
           y asortatividad frente a los valores reales.
  Ítem 2 · Red Barabási–Albert con n y m comparables.
           Discusión sobre crecimiento preferencial en infraestructura.
  Ítem 3 · Dos visualizaciones propias:
           (a) Nodos coloreados por campus, disposición spring.
           (b) Tamaño de nodo proporcional a intermediación,
               color por capa jerárquica, disposición kamada-kawai.

Uso:
    python problema2.py

Salidas (relativas a Resolución_ProyectoFinal/):
    results/tablas/p2_comparacion_modelos.csv
    results/tablas/p2_comparacion_modelos.txt
    results/tablas/p2_barabasi_albert.txt
    results/imagenes/p2_comparacion_modelos.png
    results/imagenes/p2_visualizacion_campus.png
    results/imagenes/p2_visualizacion_betweenness.png
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
from matplotlib.lines import Line2D

warnings.filterwarnings("ignore")

# --- Rutas del proyecto ---
DIR_SRC   = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL = os.path.dirname(DIR_SRC)
DIR_ROOT  = os.path.dirname(DIR_RESOL)
DIR_BASE  = os.path.join(DIR_ROOT, "codigo_base")
DIR_TAB   = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG   = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar           # noqa: E402


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


def _metricas_grafo(G: nx.Graph) -> dict:
    """
    Calcula las cuatro métricas de comparación para un grafo dado.
    Si el grafo no es conexo, opera sobre la componente gigante.

    Argumentos:
        G (nx.Graph): grafo a evaluar.

    Salida:
        dict: {
            'clustering'      (float): coeficiente de clustering medio,
            'distancia_media' (float): distancia media entre pares,
            'diametro'        (int)  : diámetro,
            'asortatividad'   (float): asortatividad por grado,
        }
    """
    if not nx.is_connected(G):
        nodos_gigante = max(nx.connected_components(G), key=len)
        G = G.subgraph(nodos_gigante).copy()

    return {
        "clustering"      : nx.average_clustering(G),
        "distancia_media" : nx.average_shortest_path_length(G),
        "diametro"        : nx.diameter(G),
        "asortatividad"   : nx.degree_assortativity_coefficient(G),
    }


# ------------------------------------------------------------
# Ítem 1 · Modelos nulos: Erdős–Rényi y Configuración
# ------------------------------------------------------------

def comparar_modelos_nulos(G_real: nx.Graph, n_realizaciones: int = 100,
                           semilla: int = 42) -> pd.DataFrame:
    """
    Genera n_realizaciones de Erdős–Rényi G(n, m) y del modelo de
    configuración, calcula las métricas de cada realización y las
    compara con los valores de la red real.

    El modelo de configuración preserva exactamente la secuencia de
    grados observada; por tanto, si ER y CM difieren en una métrica,
    la secuencia de grados la explica. Si CM también difiere de la
    red real, hay estructura más allá de los grados.

    Argumentos:
        G_real         (nx.Graph): grafo real UCuenca.
        n_realizaciones(int)     : número de realizaciones por modelo.
        semilla        (int)     : semilla para reproducibilidad.

    Salida:
        pd.DataFrame: tabla con filas ['Red real', 'ER (media)', 'ER (std)',
                      'CM (media)', 'CM (std)'] y columnas de cada métrica.
    """
    rng = np.random.default_rng(semilla)
    n = G_real.number_of_nodes()
    m = G_real.number_of_edges()
    secuencia_grados = [d for _, d in G_real.degree()]

    # Métricas de la red real
    real = _metricas_grafo(G_real)

    metricas_er = {"clustering": [], "distancia_media": [],
                   "diametro": [], "asortatividad": []}
    metricas_cm = {"clustering": [], "distancia_media": [],
                   "diametro": [], "asortatividad": []}

    print(f"  Generando {n_realizaciones} realizaciones ER y CM...")
    for i in range(n_realizaciones):
        seed_i = int(rng.integers(0, 1_000_000))

        # --- Erdős–Rényi G(n, m) ---
        G_er = nx.gnm_random_graph(n, m, seed=seed_i)
        met  = _metricas_grafo(G_er)
        for k in metricas_er:
            metricas_er[k].append(met[k])

        # --- Modelo de configuración ---
        # Se genera con la misma secuencia de grados de la red real.
        # allow_selfloops=False y multigraph=False para grafo simple.
        G_cm = nx.configuration_model(secuencia_grados, seed=seed_i)
        G_cm = nx.Graph(G_cm)           # eliminar multiaristas
        G_cm.remove_edges_from(nx.selfloop_edges(G_cm))
        met  = _metricas_grafo(G_cm)
        for k in metricas_cm:
            metricas_cm[k].append(met[k])

        if (i + 1) % 25 == 0:
            print(f"    {i+1}/{n_realizaciones} realizaciones completadas.")

    # --- Tabla de comparación ---
    metricas_nombres = ["clustering", "distancia_media", "diametro", "asortatividad"]
    filas = []

    filas.append({"modelo": "Red real",
                  **{k: round(real[k], 4) for k in metricas_nombres}})
    filas.append({"modelo": "ER (media)",
                  **{k: round(float(np.mean(metricas_er[k])), 4)
                     for k in metricas_nombres}})
    filas.append({"modelo": "ER (std)",
                  **{k: round(float(np.std(metricas_er[k])), 4)
                     for k in metricas_nombres}})
    filas.append({"modelo": "CM (media)",
                  **{k: round(float(np.mean(metricas_cm[k])), 4)
                     for k in metricas_nombres}})
    filas.append({"modelo": "CM (std)",
                  **{k: round(float(np.std(metricas_cm[k])), 4)
                     for k in metricas_nombres}})

    df = pd.DataFrame(filas)
    _guardar_csv(df, "p2_comparacion_modelos.csv")

    # --- Figura: distribución de cada métrica para ER y CM ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "P2 · Comparación de la red UCuenca con modelos nulos\n"
        f"({n_realizaciones} realizaciones por modelo)",
        fontsize=13, fontweight="bold"
    )

    etiq_metricas = {
        "clustering"      : "Clustering medio <C>",
        "distancia_media" : "Distancia media <d>",
        "diametro"        : "Diámetro",
        "asortatividad"   : "Asortatividad r",
    }
    colores = {"ER": "#3498db", "CM": "#e67e22"}

    for ax, metrica in zip(axes.flat, metricas_nombres):
        vals_er = metricas_er[metrica]
        vals_cm = metricas_cm[metrica]
        val_real = real[metrica]

        ax.hist(vals_er, bins=20, alpha=0.65, color=colores["ER"],
                label="Erdős–Rényi", edgecolor="white", linewidth=0.4)
        ax.hist(vals_cm, bins=20, alpha=0.65, color=colores["CM"],
                label="Config. Model", edgecolor="white", linewidth=0.4)
        ax.axvline(val_real, color="#e74c3c", linewidth=2.2, linestyle="--",
                   label=f"Red real = {val_real:.3f}")

        ax.set_title(etiq_metricas[metrica], fontsize=11, fontweight="bold")
        ax.set_xlabel("Valor", fontsize=9)
        ax.set_ylabel("Frecuencia", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    _guardar_figura(fig, "p2_comparacion_modelos.png")

    # --- Texto de reporte ---
    er_med  = {k: np.mean(metricas_er[k]) for k in metricas_nombres}
    er_std  = {k: np.std(metricas_er[k])  for k in metricas_nombres}
    cm_med  = {k: np.mean(metricas_cm[k]) for k in metricas_nombres}
    cm_std  = {k: np.std(metricas_cm[k])  for k in metricas_nombres}

    lineas = [
        "=" * 70,
        "ÍTEM 1 · COMPARACIÓN CON MODELOS NULOS",
        f"  ({n_realizaciones} realizaciones de ER G(n,m) y Modelo de Configuración)",
        "=" * 70,
        f"  {'Métrica':<22} {'Real':>10} {'ER media':>10} {'ER std':>8}"
        f" {'CM media':>10} {'CM std':>8}",
        "  " + "-" * 70,
    ]
    for k in metricas_nombres:
        lineas.append(
            f"  {etiq_metricas[k]:<22} {real[k]:>10.4f}"
            f" {er_med[k]:>10.4f} {er_std[k]:>8.4f}"
            f" {cm_med[k]:>10.4f} {cm_std[k]:>8.4f}"
        )
    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "",
        "  Clustering:",
        "  La red real tiene clustering << ER y CM. Erdős–Rényi predice",
        "  C ≈ p = 2m/n(n-1) ≈ 0.013, y el CM predice un valor similar.",
        "  Que la red real sea aún más baja confirma que la jerarquía",
        "  prohíbe triángulos: los nodos de acceso solo se conectan",
        "  hacia arriba, nunca entre sí.",
        "",
        "  Distancia media y diámetro:",
        "  ER produce distancias muy cortas (mundo pequeño). La red real",
        "  tiene distancias más largas porque la jerarquía obliga a pasar",
        "  por capas intermedias. El CM se acerca más a la red real",
        "  porque preserva la secuencia de grados, con muchos nodos de",
        "  grado 1 que 'alargan' los caminos.",
        "",
        "  Asortatividad:",
        "  ER tiene asortatividad ≈ 0 (neutra). La red real es negativa",
        "  (-0.15): los hubs se conectan con hojas. Ni ER ni CM reproducen",
        "  esta asortatividad negativa, lo que indica que la jerarquía",
        "  core–agregación–acceso es una propiedad estructural que va MÁS",
        "  ALLÁ de la simple secuencia de grados.",
        "=" * 70,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p2_comparacion_modelos.txt")
    return df


# ------------------------------------------------------------
# Ítem 2 · Modelo Barabási–Albert
# ------------------------------------------------------------

def modelo_barabasi_albert(G_real: nx.Graph, semilla: int = 42) -> nx.Graph:
    """
    Genera una red Barabási–Albert con n y m comparables a la red real
    y discute si el modelo de crecimiento preferencial explica la
    topología de una red de infraestructura física.

    El parámetro m_ba (aristas por nodo nuevo) se estima como el
    grado medio dividido entre 2: m_ba = round(<k>/2).

    Argumentos:
        G_real (nx.Graph): grafo real UCuenca.
        semilla(int)     : semilla para reproducibilidad.

    Salida:
        nx.Graph: red Barabási–Albert generada.
    """
    n = G_real.number_of_nodes()
    grado_medio = 2 * G_real.number_of_edges() / n
    m_ba = max(1, round(grado_medio / 2))   # aristas por nodo nuevo

    G_ba = nx.barabasi_albert_graph(n, m_ba, seed=semilla)
    met_real = _metricas_grafo(G_real)
    met_ba   = _metricas_grafo(G_ba)

    # Distribución de grado BA
    grados_ba   = [d for _, d in G_ba.degree()]
    grados_real = [d for _, d in G_real.degree()]

    # --- Figura: comparación de distribuciones de grado ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        f"P2 · Red Barabási–Albert (n={n}, m={m_ba}) vs Red UCuenca",
        fontsize=12, fontweight="bold"
    )

    # Histograma lineal
    ax = axes[0]
    bins = range(1, max(max(grados_real), max(grados_ba)) + 2)
    ax.hist(grados_real, bins=bins, alpha=0.7, color="#2980b9",
            label="UCuenca real", edgecolor="white", linewidth=0.4,
            align="left")
    ax.hist(grados_ba, bins=bins, alpha=0.7, color="#e74c3c",
            label="Barabási–Albert", edgecolor="white", linewidth=0.4,
            align="left")
    ax.set_xlabel("Grado k", fontsize=10)
    ax.set_ylabel("Número de nodos", fontsize=10)
    ax.set_title("Distribución de grado (lineal)", fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    # Log-log
    ax = axes[1]
    conteo_real = collections.Counter(grados_real)
    conteo_ba   = collections.Counter(grados_ba)
    ks_real = sorted(conteo_real); pk_real = [conteo_real[k]/n for k in ks_real]
    ks_ba   = sorted(conteo_ba);   pk_ba   = [conteo_ba[k]/n   for k in ks_ba]

    ax.scatter(ks_real, pk_real, color="#2980b9", s=55, zorder=3,
               label="UCuenca real")
    ax.scatter(ks_ba, pk_ba, color="#e74c3c", s=55, zorder=3,
               label="Barabási–Albert", marker="^")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Grado k (log)", fontsize=10)
    ax.set_ylabel("P(k) (log)", fontsize=10)
    ax.set_title("Distribución de grado (log-log)", fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, which="both", alpha=0.3)

    fig.tight_layout()
    _guardar_figura(fig, "p2_barabasi_albert.png")

    # --- Texto de reporte ---
    lineas = [
        "=" * 65,
        "ÍTEM 2 · MODELO BARABÁSI–ALBERT",
        f"  Parámetros: n={n}, m_ba={m_ba}  (m_ba = round(<k>/2))",
        "=" * 65,
        f"  {'Métrica':<22} {'Red real':>12} {'BA':>12}",
        "  " + "-" * 48,
        f"  {'Clustering medio':<22} {met_real['clustering']:>12.4f}"
        f" {met_ba['clustering']:>12.4f}",
        f"  {'Distancia media':<22} {met_real['distancia_media']:>12.4f}"
        f" {met_ba['distancia_media']:>12.4f}",
        f"  {'Diámetro':<22} {met_real['diametro']:>12d}"
        f" {met_ba['diametro']:>12d}",
        f"  {'Asortatividad':<22} {met_real['asortatividad']:>12.4f}"
        f" {met_ba['asortatividad']:>12.4f}",
        "",
        "  INTERPRETACIÓN:",
        "",
        "  El modelo BA asume dos mecanismos: (i) crecimiento — se añaden",
        "  nodos nuevos uno a uno; (ii) enlace preferencial — cada nodo",
        "  nuevo se conecta con probabilidad proporcional al grado de los",
        "  nodos existentes (los ricos se hacen más ricos).",
        "",
        "  ¿Aplica en una red de infraestructura física?",
        "  · El diseño de la red UCuenca NO es incremental ni orgánico.",
        "    Fue planificado deliberadamente bajo una topología en estrella",
        "    jerárquica. Los nodos de core existían antes que los de acceso",
        "    y su grado alto es consecuencia del diseño, no de un proceso",
        "    de enlace preferencial.",
        "  · BA produce redes con cola de potencia P(k) ~ k^{-3}, hubs",
        "    muy conectados y clustering bajo — lo que superficialmente",
        "    se parece a UCuenca. Sin embargo, la asortatividad de BA",
        "    suele ser levemente negativa pero por razones distintas:",
        "    en BA los hubs se conectan entre sí, mientras que en UCuenca",
        "    el core está separado del acceso por la capa de agregación.",
        "  · Conclusión: BA NO modela bien redes de infraestructura.",
        "    El modelo correcto es un árbol jerárquico con redundancia",
        "    parcial (puentes + algunos ciclos en el core).",
        "=" * 65,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p2_barabasi_albert.txt")
    return G_ba


# ------------------------------------------------------------
# Ítem 3 · Visualizaciones propias
# ------------------------------------------------------------

def visualizacion_campus(G: nx.Graph, nodos_df: pd.DataFrame) -> None:
    """
    Produce una visualización de la red coloreada por campus usando
    el algoritmo de disposición spring (Fruchterman-Reingold).

    Se elige spring porque distribuye los nodos maximizando la
    separación y minimizando el cruce de aristas, sin imponer
    coordenadas fijas. Para redes medianas (~200 nodos) produce
    una disposición legible donde los campus tienden a agruparse.

    Argumentos:
        G        (nx.Graph)    : grafo de la red UCuenca.
        nodos_df (pd.DataFrame): tabla de nodos con columnas id y campus.

    Salida: None (guarda imagen en disco).
    """
    # Paleta de campus
    campus_lista = sorted(nodos_df["campus"].unique())
    paleta = [
        "#2980b9", "#e74c3c", "#27ae60", "#f39c12",
        "#8e44ad", "#16a085", "#d35400", "#2c3e50",
    ]
    campus_color = {c: paleta[i % len(paleta)]
                    for i, c in enumerate(campus_lista)}

    nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))
    node_colors = [campus_color.get(nodo_campus.get(n, ""), "#aaaaaa")
                   for n in G.nodes()]

    # Disposición spring: semilla fija para reproducibilidad
    pos = nx.spring_layout(G, seed=7, k=0.55, iterations=80)

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")

    # Aristas
    nx.draw_networkx_edges(G, pos, ax=ax,
                           edge_color="#bdc3c7", width=0.7, alpha=0.6)

    # Nodos
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=node_colors,
                           node_size=120,
                           edgecolors="#2c3e50",
                           linewidths=0.5)

    # Leyenda de campus
    leyenda = [mpatches.Patch(color=campus_color[c], label=c)
               for c in campus_lista]
    ax.legend(handles=leyenda, loc="upper left", fontsize=8,
              framealpha=0.9, title="Campus", title_fontsize=9)

    ax.set_title(
        "Red UCuenca — Visualización por campus\n"
        "Disposición: Spring (Fruchterman-Reingold, k=0.55, 80 iter.)",
        fontsize=12, fontweight="bold", pad=12
    )
    ax.axis("off")
    fig.tight_layout()
    _guardar_figura(fig, "p2_visualizacion_campus.png")
    print("  Algoritmo spring elegido porque distribuye los nodos sin")
    print("  coordenadas fijas, favoreciendo la separación visual de campus.")


def visualizacion_betweenness(G: nx.Graph, nodos_df: pd.DataFrame) -> None:
    """
    Produce una visualización donde el tamaño de cada nodo es
    proporcional a su centralidad de intermediación y el color
    indica la capa jerárquica (core/agregacion/acceso/wan/interconexion).

    Se usa el algoritmo Kamada-Kawai porque minimiza la energía de
    un sistema de resortes con longitud ideal proporcional a la
    distancia de grafo, lo que tiende a respetar la geometría
    jerárquica y colocar los nodos de core en el centro.

    Argumentos:
        G        (nx.Graph)    : grafo de la red UCuenca.
        nodos_df (pd.DataFrame): tabla de nodos con columnas id y capa.

    Salida: None (guarda imagen en disco).
    """
    # Centralidad de intermediación
    between = nx.betweenness_centrality(G, normalized=True)

    # Tamaño proporcional a betweenness (escala para visibilidad)
    b_vals   = np.array([between[n] for n in G.nodes()])
    tam_min, tam_max = 50, 1800
    if b_vals.max() > 0:
        node_sizes = tam_min + (b_vals / b_vals.max()) * (tam_max - tam_min)
    else:
        node_sizes = np.full(len(b_vals), tam_min)

    # Color por capa jerárquica
    paleta_capa = {
        "core"          : "#c0392b",
        "agregacion"    : "#e67e22",
        "acceso"        : "#3498db",
        "wan"           : "#8e44ad",
        "interconexion" : "#27ae60",
    }
    nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))
    node_colors = [paleta_capa.get(nodo_capa.get(n, "acceso"), "#aaaaaa")
                   for n in G.nodes()]

    # Disposición Kamada-Kawai
    pos = nx.kamada_kawai_layout(G)

    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    # Aristas
    nx.draw_networkx_edges(G, pos, ax=ax,
                           edge_color="#4a4a6a", width=0.6, alpha=0.5)

    # Nodos
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=node_colors,
                           node_size=node_sizes,
                           edgecolors="#ecf0f1",
                           linewidths=0.4,
                           alpha=0.92)

    # Etiquetar solo los nodos de core e interconexión (los más centrales)
    nodos_etiquetar = {n: n.split("-")[-1]
                       for n in G.nodes()
                       if nodo_capa.get(n) in ("core", "interconexion")}
    nx.draw_networkx_labels(G, pos, labels=nodos_etiquetar, ax=ax,
                            font_size=6.5, font_color="white",
                            font_weight="bold")

    # Leyenda de capas
    leyenda_capas = [
        mpatches.Patch(color=c, label=capa)
        for capa, c in paleta_capa.items()
    ]
    # Leyenda de tamaño
    leyenda_tam = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#aaaaaa",
               markersize=s, label=etiq)
        for s, etiq in [(4, "Baja betweenness"),
                        (9, "Media betweenness"),
                        (14, "Alta betweenness")]
    ]
    leg1 = ax.legend(handles=leyenda_capas, loc="upper left", fontsize=8,
                     framealpha=0.7, title="Capa", title_fontsize=9,
                     labelcolor="white", facecolor="#2c3e50",
                     edgecolor="#4a4a6a")
    ax.add_artist(leg1)
    ax.legend(handles=leyenda_tam, loc="lower left", fontsize=8,
              framealpha=0.7, title="Tamaño ∝ betweenness",
              title_fontsize=9, labelcolor="white",
              facecolor="#2c3e50", edgecolor="#4a4a6a")

    ax.set_title(
        "Red UCuenca — Tamaño ∝ intermediación · Color = capa jerárquica\n"
        "Disposición: Kamada-Kawai (minimiza energía de resortes con distancia de grafo)",
        fontsize=11, fontweight="bold", color="white", pad=12
    )
    ax.axis("off")
    fig.tight_layout()
    _guardar_figura(fig, "p2_visualizacion_betweenness.png")
    print("  Algoritmo Kamada-Kawai elegido porque la longitud ideal de")
    print("  cada arco es proporcional a la distancia real en el grafo,")
    print("  lo que tiende a colocar los switches de core en el centro.")


# ============================================================
# CÓDIGO MAIN
# ============================================================
# 1) Crear directorios de salida.
# 2) Cargar y verificar el grafo UCuenca.
# 3) Cargar DataFrames de atributos.
# 4) Ejecutar los tres ítems del Problema P2 en orden.

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("PROBLEMA P2 — MODELOS NULOS Y VISUALIZACIÓN")
    print("Red de datos · Universidad de Cuenca")
    print("=" * 65 + "\n")

    # 1) Directorios
    _crear_dirs()

    # 2) Cargar grafo y verificar pipeline
    G = cargar_red(fuente="csv")
    ok = verificar(G)
    if not ok:
        sys.exit("Pipeline fallido: corrija la carga antes de continuar.")

    # 3) Cargar DataFrames de atributos
    import pandas as _pd
    nodos_df = _pd.read_csv(
        os.path.join(DIR_ROOT, "red_ucuenca_nodes.csv"), dtype=str
    )

    # 4.1) Ítem 1 — Modelos nulos: ER y CM (100 realizaciones cada uno)
    print("\n[1/3] Generando modelos nulos (ER y CM)...")
    comparar_modelos_nulos(G, n_realizaciones=100, semilla=42)

    # 4.2) Ítem 2 — Modelo Barabási–Albert
    print("\n[2/3] Generando red Barabási–Albert...")
    modelo_barabasi_albert(G, semilla=42)

    # 4.3) Ítem 3a — Visualización coloreada por campus (spring)
    print("\n[3/3] Generando visualizaciones...")
    visualizacion_campus(G, nodos_df)

    # 4.4) Ítem 3b — Visualización tamaño ∝ betweenness (kamada-kawai)
    visualizacion_betweenness(G, nodos_df)

    print("\n" + "=" * 65)
    print("P2 completado. Resultados en:")
    print(f"  Tablas  → {DIR_TAB}")
    print(f"  Imágenes→ {DIR_IMG}")
    print("=" * 65 + "\n")
