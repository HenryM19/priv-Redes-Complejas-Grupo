# ============================================================
# graficar_red.py
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Visualiza la red propia (backbone ISP) como un GRAFO NO
# DIRIGIDO, que es la representación relevante para el análisis
# de percolación de sitios.
#
# Para percolación solo importa la estructura de conectividad
# (quién está conectado con quién), no las direcciones del
# flujo ni las capacidades. El par antiparalelo c⇄d se
# representa como una única arista no dirigida c–d.
#
# Salida:
#   results/images/red_propia_topologia.png
#
# Ejecutar desde src/:
#   python graficar_red.py

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
import os
import sys
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from red_propia import construir_red_propia, get_posiciones

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

def construir_no_dirigida(G_dir: nx.DiGraph) -> nx.Graph:
    """
    Convierte el dígrafo de la red propia a un grafo no dirigido.
    El par antiparalelo c⇄d queda como una sola arista c–d.

    Argumentos:
        G_dir (nx.DiGraph): dígrafo original.

    Salida:
        nx.Graph: grafo no dirigido equivalente.
    """
    return nx.to_undirected(G_dir)


def clasificar_nodos(G_ud: nx.Graph) -> dict:
    """
    Clasifica los nodos por su rol en la red ISP para asignar
    colores diferenciados en la visualización.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido.

    Salida:
        dict: {nodo: categoria} donde categoria es
              "fuente", "sumidero" o "intermedio".
    """
    categorias = {}
    for n in G_ud.nodes():
        if n == "s":
            categorias[n] = "fuente"
        elif n == "t":
            categorias[n] = "sumidero"
        else:
            categorias[n] = "intermedio"
    return categorias


def graficar_red(G_ud: nx.Graph, pos: dict, ruta: str) -> None:
    """
    Dibuja y guarda la topología no dirigida de la red propia.
    Los nodos se colorean según su rol (fuente, sumidero,
    intermedio) y el tamaño refleja el grado.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido.
        pos (dict): {nodo: (x, y)} posiciones de los nodos.
        ruta (str): ruta completa del PNG de salida.

    Salida:
        None (guarda imagen en disco).
    """
    categorias = clasificar_nodos(G_ud)
    grados = dict(G_ud.degree())

    color_map = {"fuente": "#2980b9", "sumidero": "#e74c3c",
                 "intermedio": "#d5d8dc"}
    edge_map   = {"fuente": "#1a5276", "sumidero": "#922b21",
                  "intermedio": "#717d7e"}

    node_colors  = [color_map[categorias[n]]  for n in G_ud.nodes()]
    node_edgecol = [edge_map[categorias[n]]   for n in G_ud.nodes()]
    node_sizes   = [500 + 200 * grados[n]     for n in G_ud.nodes()]

    fig, ax = plt.subplots(figsize=(10, 6))

    nx.draw_networkx_edges(
        G_ud, pos, ax=ax,
        edge_color="#7f8c8d", width=2.0, alpha=0.8
    )
    nx.draw_networkx_nodes(
        G_ud, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors=node_edgecol,
        linewidths=2.2
    )
    nx.draw_networkx_labels(
        G_ud, pos, ax=ax,
        font_size=11, font_weight="bold", font_color="white"
    )
    # Etiquetas de grado junto a cada nodo
    grado_labels = {n: f"k={grados[n]}" for n in G_ud.nodes()}
    offset_pos   = {n: (x, y - 0.28) for n, (x, y) in pos.items()}
    nx.draw_networkx_labels(
        G_ud, offset_pos, labels=grado_labels, ax=ax,
        font_size=8, font_color="#555555"
    )

    leyenda = [
        Patch(facecolor="#2980b9", edgecolor="#1a5276", label="s — fuente (peering)"),
        Patch(facecolor="#e74c3c", edgecolor="#922b21", label="t — sumidero (data center)"),
        Patch(facecolor="#d5d8dc", edgecolor="#717d7e", label="Enrutador / agregador"),
    ]
    ax.legend(handles=leyenda, loc="upper left", fontsize=10)
    ax.set_title(
        "Red propia — Backbone ISP (versión no dirigida)\n"
        f"{G_ud.number_of_nodes()} nodos · {G_ud.number_of_edges()} aristas",
        fontsize=13, fontweight="bold"
    )
    ax.axis("off")
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] Imagen guardada en {ruta}")


# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Construir el dígrafo original y convertir a no dirigido.
# 2) Extraer posiciones de los nodos.
# 3) Graficar y guardar la imagen de topología.

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

G_dir, s, t = construir_red_propia()
G_ud = construir_no_dirigida(G_dir)
pos  = get_posiciones(G_dir)

print("Red no dirigida:")
print(f"  Nodos  : {G_ud.number_of_nodes()}")
print(f"  Aristas: {G_ud.number_of_edges()}")
print(f"  Grados : { {n: k for n, k in sorted(G_ud.degree(), key=lambda x: -x[1])} }")

graficar_red(G_ud, pos,
    os.path.join(BASE, "results", "images", "red_propia_topologia.png"))
