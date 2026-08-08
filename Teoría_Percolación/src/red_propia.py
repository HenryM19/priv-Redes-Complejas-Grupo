"""
red_propia.py — Definición de la red de flujo usada en la actividad.

Modela el backbone de un proveedor de Internet:
  - `s`  : punto de peering (fuente de tráfico)
  - `t`  : data center (sumidero)
  - a..g : enrutadores intermedios

Topología: 9 nodos, 16 arcos dirigidos. Las capacidades están en Gb/s.

Características notables:
  * Par antiparalelo: c → d (cap=5) y d → c (cap=7).
  * Cuello de botella: e → t (cap=3).
  * Corte mínimo: S = {s, a, c, e}, capacidad total = 24 Gb/s.
  * Flujo máximo = 24 Gb/s.
"""

# ============================================================
# Carga de librerías
# ============================================================
import networkx as nx


# ============================================================
# Definición de funciones
# ============================================================

def construir_red_propia() -> tuple:
    """
    Construye la red de flujo propia (backbone ISP) como un dígrafo de NetworkX.

    Cada arco lleva el atributo ``capacity`` con la capacidad en Gb/s.
    Los nodos llevan el atributo ``pos`` con coordenadas (x, y) para la
    visualización, siguiendo la misma disposición que la versión en Julia.

    Returns
    -------
    G : nx.DiGraph
        Dígrafo con 9 nodos y 16 arcos.
    s : str
        Nombre del nodo fuente ("s").
    t : str
        Nombre del nodo sumidero ("t").
    """
    G = nx.DiGraph()

    # --- Posiciones (x, y) para visualización ---
    posiciones = {
        "s": (0.0, 1.5),
        "a": (1.3, 3.0),
        "b": (1.3, 0.0),
        "c": (2.6, 2.4),
        "d": (2.6, 0.6),
        "e": (3.9, 3.2),
        "f": (3.9, 1.5),
        "g": (3.9, 0.0),
        "t": (5.2, 1.5),
    }
    for nodo, pos in posiciones.items():
        G.add_node(nodo, pos=pos)

    # --- Arcos con sus capacidades (Gb/s) ---
    arcos = [
        # capa 1: salida de la fuente
        ("s", "a", 13),
        ("s", "b",  8),
        ("s", "c",  6),
        # capa 2: reparto interno
        ("a", "c",  8),
        ("a", "e", 15),
        ("b", "d",  6),
        ("b", "f", 13),
        # par antiparalelo c <-> d
        ("c", "d",  5),
        ("d", "c",  7),
        # capa 3: hacia los agregadores
        ("c", "e",  6),
        ("c", "f",  8),
        ("d", "f",  3),
        ("d", "g", 10),
        # capa 4: entrada al sumidero
        ("e", "t",  3),
        ("f", "t", 14),
        ("g", "t",  7),
    ]
    for u, v, cap in arcos:
        G.add_edge(u, v, capacity=cap)

    return G, "s", "t"


def get_posiciones(G: nx.DiGraph) -> dict:
    """
    Extrae el diccionario de posiciones almacenado en los atributos de los nodos.

    Arguments
    ---------
    G : nx.DiGraph
        Dígrafo construido por ``construir_red_propia()``.

    Returns
    -------
    dict
        Diccionario {nodo: (x, y)} listo para usar en ``nx.draw``.
    """
    return {n: data["pos"] for n, data in G.nodes(data=True)}
