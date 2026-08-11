"""
comparar_layouts.py — Comparación de 3 algoritmos de disposición
Genera una figura con shell, spectral y BFS-radial para la red UCuenca.
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

nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))
nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))

campus_orden = [
    "Campus Central", "Campus Balzay", "Campus Paraiso",
    "Campus Yanuncay", "Campus Hospitalidad",
    "Nube MPLS", "Sede Centro Historico", "Sede Museo",
]
paleta = ["#e74c3c","#2980b9","#f39c12","#8e44ad","#27ae60",
          "#16a085","#d35400","#2c3e50"]
campus_color = {c: paleta[i % len(paleta)] for i, c in enumerate(campus_orden)}
node_colors  = [campus_color.get(nodo_campus.get(n,""), "#aaaaaa") for n in G.nodes()]
grados       = dict(G.degree())
node_size    = [max(25, 35 + grados[n]*18) for n in G.nodes()]

leyenda = [mpatches.Patch(color=campus_color[c], label=c.replace("Campus ",""))
           for c in campus_orden if c in campus_color]

fig, axes = plt.subplots(1, 3, figsize=(24, 9))
fig.suptitle("Red UCuenca — Comparación de layouts", fontsize=14, fontweight="bold")

# ── 1. SHELL LAYOUT ─────────────────────────────────────────────────────────
capas_shell = {
    "wan"          : [],
    "core"         : [],
    "interconexion": [],
    "agregacion"   : [],
    "acceso"       : [],
}
for n in G.nodes():
    c = nodo_capa.get(n, "acceso")
    capas_shell.get(c, capas_shell["acceso"]).append(n)

shells = [capas_shell["acceso"], capas_shell["agregacion"],
          capas_shell["interconexion"], capas_shell["core"],
          capas_shell["wan"]]
shells = [s for s in shells if s]   # quitar vacíos

pos_shell = nx.shell_layout(G, nlist=shells)

ax = axes[0]
ax.set_facecolor("#f4f6f8")
nx.draw_networkx_edges(G, pos_shell, ax=ax, edge_color="#c0c8d0", width=0.5, alpha=0.5)
nx.draw_networkx_nodes(G, pos_shell, ax=ax, node_color=node_colors,
                       node_size=node_size, edgecolors="#333", linewidths=0.4)
nodos_etiq = {n: n for n in G.nodes() if nodo_capa.get(n,"") in ("core","wan")}
nx.draw_networkx_labels(G, pos_shell, labels=nodos_etiq, ax=ax,
                        font_size=4.5, font_weight="bold", font_color="#1a1a2e")
ax.set_title("Shell layout\n(anillos concéntricos: acceso→core→WAN)", fontsize=10, fontweight="bold")
ax.axis("off")

# ── 2. SPECTRAL LAYOUT ──────────────────────────────────────────────────────
pos_spec = nx.spectral_layout(G)

ax = axes[1]
ax.set_facecolor("#f4f6f8")
nx.draw_networkx_edges(G, pos_spec, ax=ax, edge_color="#c0c8d0", width=0.5, alpha=0.5)
nx.draw_networkx_nodes(G, pos_spec, ax=ax, node_color=node_colors,
                       node_size=node_size, edgecolors="#333", linewidths=0.4)
nx.draw_networkx_labels(G, pos_spec, labels=nodos_etiq, ax=ax,
                        font_size=4.5, font_weight="bold", font_color="#1a1a2e")
ax.set_title("Spectral layout\n(eigenvectores del laplaciano)", fontsize=10, fontweight="bold")
ax.axis("off")

# ── 3. BFS RADIAL desde INTERNET-MPLS ───────────────────────────────────────
raiz = "INTERNET-MPLS"
if raiz not in G.nodes():
    # buscar nodo WAN alternativo
    raiz = next((n for n in G.nodes() if nodo_capa.get(n) == "wan"), list(G.nodes())[0])

pos_bfs = nx.bfs_layout(G, raiz, align="horizontal")

ax = axes[2]
ax.set_facecolor("#f4f6f8")
nx.draw_networkx_edges(G, pos_bfs, ax=ax, edge_color="#c0c8d0", width=0.5, alpha=0.5)
nx.draw_networkx_nodes(G, pos_bfs, ax=ax, node_color=node_colors,
                       node_size=node_size, edgecolors="#333", linewidths=0.4)
nx.draw_networkx_labels(G, pos_bfs, labels=nodos_etiq, ax=ax,
                        font_size=4.5, font_weight="bold", font_color="#1a1a2e")
ax.set_title(f"BFS radial (raíz: {raiz})\n(árbol de amplitud desde el gateway)", fontsize=10, fontweight="bold")
ax.axis("off")

# Leyenda compartida
fig.legend(handles=leyenda, loc="lower center", ncol=8, fontsize=8,
           framealpha=0.9, title="Campus", title_fontsize=9, bbox_to_anchor=(0.5, -0.02))

fig.tight_layout(rect=[0, 0.04, 1, 1])
out = os.path.join(DIR_IMG, "p2_comparacion_layouts.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"[OK] {out}")
