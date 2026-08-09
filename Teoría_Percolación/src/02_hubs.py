# ============================================================
# 02_hubs.py
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Identifica los hubs de la red propia (backbone ISP) y genera
# una visualización del grafo donde el tamaño y color de cada
# nodo refleja su grado (importancia para la conectividad).
#
# Un hub es un nodo con grado significativamente mayor al
# grado medio ⟨k⟩. En el contexto ISP representan enrutadores
# o agregadores críticos cuya falla fragmentaría la red.
#
# Salida:
#   results/files/02_hubs.csv       — ranking de nodos por grado
#   results/images/02_hubs_red.png  — grafo con nodos escalados
#
# Ejecutar desde src/:
#   python 02_hubs.py

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
import os
import sys
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from red_propia import construir_red_propia, get_posiciones

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

def identificar_hubs(G_ud: nx.Graph, umbral_percentil: float = 75.0) -> dict:
    """
    Clasifica los nodos en hubs y no-hubs según si su grado
    supera el percentil indicado de la distribución de grados.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido.
        umbral_percentil (float): percentil a partir del cual un
            nodo se considera hub (por defecto 75).

    Salida:
        dict: {
            "grados": {nodo: grado},
            "hubs": [lista de nodos hub],
            "umbral": valor de grado mínimo para ser hub (float)
        }
    """
    grados = dict(G_ud.degree())
    umbral = np.percentile(list(grados.values()), umbral_percentil)
    hubs   = [n for n, k in grados.items() if k >= umbral]
    return {"grados": grados, "hubs": hubs, "umbral": umbral}


def guardar_ranking(grados: dict, hubs: list, ruta: str) -> pd.DataFrame:
    """
    Guarda el ranking de nodos por grado en CSV, indicando si
    cada nodo es hub.

    Argumentos:
        grados (dict): {nodo: grado}.
        hubs (list): lista de nodos hub.
        ruta (str): ruta completa del CSV de salida.

    Salida:
        pd.DataFrame: tabla con columnas [nodo, grado, es_hub].
    """
    df = pd.DataFrame([
        {"nodo": n, "grado": k, "es_hub": n in hubs}
        for n, k in sorted(grados.items(), key=lambda x: -x[1])
    ])
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df.to_csv(ruta, index=False)
    return df


def graficar_hubs(G_dir: nx.DiGraph, grados: dict, hubs: list,
                  pos: dict, ruta: str) -> None:
    """
    Visualiza el grafo con nodos escalados por grado y coloreados
    según si son hubs (rojo) o nodos normales (azul claro).
    Las aristas se dibujan como el grafo dirigido original.

    Argumentos:
        G_dir (nx.DiGraph): dígrafo original (para mantener arcos).
        grados (dict): {nodo: grado} del grafo no dirigido.
        hubs (list): lista de nodos clasificados como hubs.
        pos (dict): {nodo: (x, y)} posiciones.
        ruta (str): ruta completa del PNG de salida.

    Salida:
        None (guarda imagen en disco).
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    max_k = max(grados.values())
    node_sizes  = [400 + 300 * (grados[n] / max_k) for n in G_dir.nodes()]
    node_colors = ["#c0392b" if n in hubs else "#aed6f1" for n in G_dir.nodes()]
    node_edge   = ["#922b21" if n in hubs else "#2980b9" for n in G_dir.nodes()]

    nx.draw_networkx_edges(
        G_dir, pos, ax=ax,
        edge_color="#b0b0b0", arrows=True,
        arrowsize=14, width=1.4,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=18, min_target_margin=18
    )
    nx.draw_networkx_nodes(
        G_dir, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors=node_edge, linewidths=2.0
    )
    labels = {n: f"{n}\nk={grados[n]}" for n in G_dir.nodes()}
    nx.draw_networkx_labels(G_dir, pos, labels, ax=ax, font_size=8, font_weight="bold")

    # leyenda manual
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor="#c0392b", edgecolor="#922b21", label="Hub (grado ≥ umbral)"),
        Patch(facecolor="#aed6f1", edgecolor="#2980b9", label="Nodo normal"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=10)
    ax.set_title("Identificación de hubs — Red Propia (backbone ISP)", fontsize=13)
    ax.axis("off")
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=180)
    plt.close(fig)
    print(f"  [OK] Imagen guardada en {ruta}")


# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Construir red y convertir a no dirigida.
# 2) Identificar hubs por percentil 75.
# 3) Imprimir ranking y clasificación.
# 4) Guardar CSV y visualización.

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

G_dir, s, t = construir_red_propia()
G_ud = nx.to_undirected(G_dir)
pos  = get_posiciones(G_dir)

resultado = identificar_hubs(G_ud, umbral_percentil=75.0)
grados = resultado["grados"]
hubs   = resultado["hubs"]
umbral = resultado["umbral"]

print("=" * 55)
print("IDENTIFICACIÓN DE HUBS — Red Propia (backbone ISP)")
print("=" * 55)
print(f"\nUmbral (percentil 75): k ≥ {umbral:.1f}")
print(f"\nRanking de nodos por grado:")
print(f"  {'Nodo':>6}  {'Grado':>5}  {'Tipo':>10}")
print(f"  {'-'*6}  {'-'*5}  {'-'*10}")
for n, k in sorted(grados.items(), key=lambda x: -x[1]):
    tipo = "HUB" if n in hubs else "normal"
    print(f"  {n:>6}  {k:>5}  {tipo:>10}")

print(f"\nHubs identificados: {hubs}")
print(f"\nInterpretación en contexto ISP:")
for h in sorted(hubs, key=lambda n: -grados[n]):
    print(f"  • Nodo '{h}' (k={grados[h]}): enrutador/agregador crítico.")
    print(f"    Su falla desconectaría {grados[h]} enlaces directamente.")
print("=" * 55)

df = guardar_ranking(grados, hubs, os.path.join(BASE, "results", "files", "02_hubs.csv"))
graficar_hubs(G_dir, grados, hubs, pos, os.path.join(BASE, "results", "images", "02_hubs_red.png"))
