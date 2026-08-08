"""
graficar_red.py — Visualización de la red propia (backbone ISP).

Genera una figura de alta calidad del dígrafo de flujo con:
  - Nodos fuente (s) y sumidero (t) diferenciados por color.
  - Etiquetas de capacidad sobre cada arco.
  - Par antiparalelo c <-> d resaltado en morado.
  - Cuello de botella e -> t resaltado en rojo.
  - Arcos normales en gris oscuro.

Salida: results/images/red_propia_topologia.png

Ejecutar desde la raíz del proyecto:
    python src/graficar_red.py
"""

# ============================================================
# Carga de librerías
# ============================================================
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

from red_propia import construir_red_propia, get_posiciones


# ============================================================
# Definición de funciones
# ============================================================

def clasificar_arcos(G: nx.DiGraph) -> tuple:
    """
    Separa los arcos del dígrafo en tres categorías para colorearlos.

    Arguments
    ---------
    G : nx.DiGraph
        Dígrafo de la red propia.

    Returns
    -------
    normales : list[tuple]
        Arcos que no son antiparalelos ni cuello de botella.
    antiparalelos : list[tuple]
        Par (c->d) y (d->c).
    cuello : list[tuple]
        Arco e->t (cuello de botella).
    """
    antiparalelos = [("c", "d"), ("d", "c")]
    cuello        = [("e", "t")]
    normales = [
        (u, v) for u, v in G.edges()
        if (u, v) not in antiparalelos and (u, v) not in cuello
    ]
    return normales, antiparalelos, cuello


def calcular_offset(pos: dict, u: str, v: str, delta: float = 0.08) -> tuple:
    """
    Calcula un vector de desplazamiento perpendicular al arco (u, v)
    para separar visualmente los arcos antiparalelos.

    Arguments
    ---------
    pos : dict
        Diccionario {nodo: (x, y)}.
    u : str
        Nodo origen del arco.
    v : str6
        Nodo destino del arco.
    delta : float
        Magnitud del desplazamiento perpendicular (en unidades del grafo).

    Returns
    -------
    tuple[float, float]
        Vector (dx, dy) de desplazamiento perpendicular.
    """
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    # perpendicular normalizado
    return (-dy / length * delta, dx / length * delta)


def dibujar_etiquetas_arcos(ax, G: nx.DiGraph, pos: dict,
                             lista_arcos: list, color: str,
                             curvatura: float = 0.0,
                             offset_perp: float = 0.0) -> None:
    """
    Dibuja las etiquetas de capacidad sobre un conjunto de arcos.

    Arguments
    ---------
    ax : matplotlib.axes.Axes
        Ejes donde se dibuja.
    G : nx.DiGraph
        Dígrafo de la red.
    pos : dict
        Posiciones de los nodos.
    lista_arcos : list[tuple]
        Arcos cuyas etiquetas se van a dibujar.
    color : str
        Color del texto.
    curvatura : float
        Curvatura del arco (rad), usada para desplazar la etiqueta.
    offset_perp : float
        Desplazamiento perpendicular adicional para arcos curvos.

    Returns
    -------
    None
    """
    for u, v in lista_arcos:
        cap = G[u][v]["capacity"]
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if offset_perp:
            ox, oy = calcular_offset(pos, u, v, delta=offset_perp)
            mx += ox
            my += oy
        ax.text(mx, my, str(cap),
                ha="center", va="center", fontsize=8.5,
                color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))


def graficar_red(ruta_salida: str = "../results/images/red_propia_topologia.png") -> None:
    """
    Genera y guarda la figura de la red propia.

    Arguments
    ---------
    ruta_salida : str
        Ruta del archivo PNG de salida.

    Returns
    -------
    None
        Guarda la figura en ``ruta_salida``.
    """
    # --- Construir red y clasificar arcos ---
    G, s, t = construir_red_propia()
    pos = get_posiciones(G)
    normales, antiparalelos, cuello = clasificar_arcos(G)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Red propia — Backbone ISP\n"
                 "9 nodos · 16 arcos · flujo máximo = 24 Gb/s",
                 fontsize=13, fontweight="bold", pad=14)

    # --- Colores de nodos ---
    color_nodos = []
    for n in G.nodes():
        if n == s:
            color_nodos.append("#3b82f6")   # azul — fuente
        elif n == t:
            color_nodos.append("#ef4444")   # rojo — sumidero
        else:
            color_nodos.append("#e2e8f0")   # gris claro — intermedios

    # --- Dibujar arcos normales ---
    nx.draw_networkx_edges(
        G, pos, edgelist=normales, ax=ax,
        edge_color="#475569", width=1.8,
        arrows=True, arrowsize=18,
        connectionstyle="arc3,rad=0.0",
        node_size=900,
    )

    # --- Dibujar par antiparalelo (curvados) ---
    nx.draw_networkx_edges(
        G, pos, edgelist=antiparalelos, ax=ax,
        edge_color="#7c3aed", width=2.2,
        arrows=True, arrowsize=18,
        connectionstyle="arc3,rad=0.35",
        node_size=900, style="dashed",
    )

    # --- Dibujar cuello de botella ---
    nx.draw_networkx_edges(
        G, pos, edgelist=cuello, ax=ax,
        edge_color="#dc2626", width=2.8,
        arrows=True, arrowsize=20,
        connectionstyle="arc3,rad=0.0",
        node_size=900,
    )

    # --- Dibujar nodos ---
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=color_nodos,
        node_size=900,
        linewidths=2,
        edgecolors=["white" if n in (s, t) else "#94a3b8" for n in G.nodes()],
    )

    # --- Etiquetas de nodos ---
    label_color = {n: "white" if n in (s, t) else "#1e293b" for n in G.nodes()}
    for n, (x, y) in pos.items():
        ax.text(x, y, n,
                ha="center", va="center",
                fontsize=11, fontweight="bold",
                color=label_color[n])

    # --- Etiquetas de capacidades ---
    dibujar_etiquetas_arcos(ax, G, pos, normales,      "#334155", offset_perp=0.0)
    dibujar_etiquetas_arcos(ax, G, pos, antiparalelos, "#7c3aed", offset_perp=0.18)
    dibujar_etiquetas_arcos(ax, G, pos, cuello,        "#dc2626", offset_perp=0.0)

    # --- Leyenda ---
    leyenda = [
        mpatches.Patch(color="#3b82f6", label="s — fuente (peering)"),
        mpatches.Patch(color="#ef4444", label="t — sumidero (data center)"),
        mpatches.Patch(color="#e2e8f0", label="Enrutador intermedio",
                       linewidth=1, edgecolor="#94a3b8"),
        mpatches.Patch(color="#7c3aed", label="Par antiparalelo c ⇄ d",
                       linestyle="dashed"),
        mpatches.Patch(color="#dc2626", label="Cuello de botella e→t (cap=3)"),
    ]
    ax.legend(handles=leyenda, loc="lower left", fontsize=8.5,
              framealpha=0.9, edgecolor="#cbd5e1")

    plt.tight_layout()
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    plt.savefig(ruta_salida, dpi=180, bbox_inches="tight")
    print(f"Figura guardada en: {ruta_salida}")
    plt.close(fig)


# ============================================================
# Código main
# ============================================================
if __name__ == "__main__":
    # Guardar la figura de topología en results/images/
    graficar_red("../results/images/red_propia_topologia.png")
