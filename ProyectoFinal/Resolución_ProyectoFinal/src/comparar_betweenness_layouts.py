"""
comparar_betweenness_layouts.py
Compara BFS radial, Shell y Spring para la visualización de betweenness.
"""
import os, sys, collections
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.join("..", "..", "codigo_base"))
from cargar_red import cargar_red

DIR_IMG = "../results/imagenes"
os.makedirs(DIR_IMG, exist_ok=True)

G        = cargar_red(fuente="csv")
nodos_df = pd.read_csv("../../red_ucuenca_nodes.csv", dtype=str)

nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))
nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))

# Betweenness y colores por capa
betweenness = nx.betweenness_centrality(G, normalized=False)
capa_color  = {"wan":"#8e44ad","core":"#e74c3c","interconexion":"#e67e22",
               "agregacion":"#2980b9","acceso":"#27ae60"}
node_colors = [capa_color.get(nodo_capa.get(n,"acceso"),"#aaaaaa") for n in G.nodes()]

# Tamaño proporcional a betweenness (con mínimo visible)
b_vals = np.array([betweenness[n] for n in G.nodes()])
b_norm = (b_vals / b_vals.max())   # 0–1
node_size = (50 + b_norm * 900).tolist()

rng = np.random.default_rng(42)

fig, axes = plt.subplots(1, 3, figsize=(26, 10))
fig.suptitle("Visualización betweenness — comparación de layouts\ntamaño ∝ betweenness · color = capa jerárquica",
             fontsize=13, fontweight="bold")

# ── Etiquetas solo top-8 betweenness ────────────────────────────────────────
top8 = sorted(betweenness, key=betweenness.get, reverse=True)[:8]
etiq = {n: (n[:14]+"…" if len(n)>14 else n) for n in top8}

# ── 1. BFS RADIAL ────────────────────────────────────────────────────────────
raiz = "INTERNET-MPLS"
bfs_depth  = nx.single_source_shortest_path_length(G, raiz)
depth_nodes = {}
for n, d in bfs_depth.items():
    depth_nodes.setdefault(d, []).append(n)

W, H_NIV = 22.0, 2.6
pos_bfs = {}
for depth, nodos_niv in depth_nodes.items():
    y = depth * H_NIV
    nodos_s = sorted(nodos_niv, key=lambda n: (nodo_capa.get(n,""), n))
    paso = W / (len(nodos_s) + 1)
    for i, nd in enumerate(nodos_s):
        x = (i+1)*paso + rng.uniform(-paso*0.2, paso*0.2)
        pos_bfs[nd] = (x, y + rng.uniform(-0.2, 0.2))

ax = axes[0]
ax.set_facecolor("#f4f6f8")
nx.draw_networkx_edges(G, pos_bfs, ax=ax, edge_color="#c5cdd5", width=0.5, alpha=0.4)
nx.draw_networkx_nodes(G, pos_bfs, ax=ax, node_color=node_colors,
                       node_size=node_size, edgecolors="#333", linewidths=0.4, alpha=0.85)
nx.draw_networkx_labels(G, pos_bfs, labels=etiq, ax=ax,
                        font_size=6, font_weight="bold", font_color="#1a1a2e")
ax.set_title("BFS radial\n(profundidad desde INTERNET-MPLS)", fontsize=10, fontweight="bold")
ax.axis("off")

# ── 2. SHELL LAYOUT ──────────────────────────────────────────────────────────
capas_shell = {"wan":[],"core":[],"interconexion":[],"agregacion":[],"acceso":[]}
for n in G.nodes():
    capas_shell.get(nodo_capa.get(n,"acceso"), capas_shell["acceso"]).append(n)
shells = [capas_shell["acceso"], capas_shell["agregacion"],
          capas_shell["interconexion"], capas_shell["core"], capas_shell["wan"]]
shells = [s for s in shells if s]
pos_shell = nx.shell_layout(G, nlist=shells)

ax = axes[1]
ax.set_facecolor("#f4f6f8")
nx.draw_networkx_edges(G, pos_shell, ax=ax, edge_color="#c5cdd5", width=0.5, alpha=0.4)
nx.draw_networkx_nodes(G, pos_shell, ax=ax, node_color=node_colors,
                       node_size=node_size, edgecolors="#333", linewidths=0.4, alpha=0.85)
nx.draw_networkx_labels(G, pos_shell, labels=etiq, ax=ax,
                        font_size=6, font_weight="bold", font_color="#1a1a2e")
ax.set_title("Shell (anillos concéntricos)\nacceso exterior → WAN centro", fontsize=10, fontweight="bold")
ax.axis("off")

# ── 3. SPRING con k grande ───────────────────────────────────────────────────
pos_spring = nx.spring_layout(G, seed=42, k=2.5, iterations=120)

ax = axes[2]
ax.set_facecolor("#f4f6f8")
nx.draw_networkx_edges(G, pos_spring, ax=ax, edge_color="#c5cdd5", width=0.5, alpha=0.4)
nx.draw_networkx_nodes(G, pos_spring, ax=ax, node_color=node_colors,
                       node_size=node_size, edgecolors="#333", linewidths=0.4, alpha=0.85)
nx.draw_networkx_labels(G, pos_spring, labels=etiq, ax=ax,
                        font_size=6, font_weight="bold", font_color="#1a1a2e")
ax.set_title("Spring (k=2.5, repulsión alta)\nnodos separados por fuerzas", fontsize=10, fontweight="bold")
ax.axis("off")

# Leyenda compartida de capas
leyenda = [mpatches.Patch(color=c, label=l)
           for l, c in capa_color.items()]
fig.legend(handles=leyenda, loc="lower center", ncol=5, fontsize=9,
           framealpha=0.9, title="Capa jerárquica", title_fontsize=10,
           bbox_to_anchor=(0.5, -0.02))

fig.tight_layout(rect=[0, 0.05, 1, 1])
out = os.path.join(DIR_IMG, "p2_comparacion_betweenness_layouts.png")
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"[OK] {out}")
