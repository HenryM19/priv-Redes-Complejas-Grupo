"""
animate.py — Animaciones llamativas y autoexplicativas del grafo de ataque.

Genera tres productos visuales:
  1. attack_graph.png        — el grafo completo por capas, aristas coloreadas
                               por severidad CVSS.
  2. dijkstra_expansion.gif  — Dijkstra paso a paso: el frente de exploración
                               se expande desde INTERNET, los nodos visitados
                               se "queman" y las distancias se actualizan.
  3. critical_path.gif       — la ruta crítica se traza salto a salto, mostrando
                               el CVE explotado en cada paso.

Estética "command-center": fondo oscuro, acentos neón por severidad.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import imageio.v2 as imageio
import networkx as nx

from attack_graph import layered_layout, LAYER_ORDER, LAYER_LABEL
from dijkstra import path_edges

# ── Paleta command-center ───────────────────────────────────────────────────────
BG       = "#0d1320"
PANEL    = "#121a2b"
GRIDc    = "#1e2a40"
TXT      = "#e8edf6"
MUTED    = "#8a97ad"
SEV_COLOR = {            # por severidad CVSS
    "CRITICAL": "#ff3b5c",
    "HIGH":     "#ff8c42",
    "MEDIUM":   "#ffd23f",
    "LOW":      "#5ad1a0",
}
NODE_IDLE   = "#26324a"
NODE_VISIT  = "#ff8c42"   # quemado (visitado)
NODE_FRONT  = "#3fb6ff"   # frontera
NODE_CUR    = "#ffffff"   # nodo actual
NODE_TARGET = "#ff3b5c"
NODE_ENTRY  = "#5ad1a0"
PATH_GLOW   = "#3fb6ff"


def _sev(cvss):
    if cvss >= 9.0: return "CRITICAL"
    if cvss >= 7.0: return "HIGH"
    if cvss >= 4.0: return "MEDIUM"
    return "LOW"


def _base_fig():
    fig, ax = plt.subplots(figsize=(13, 7.3), dpi=110)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    return fig, ax


def _draw_layers(ax, pos):
    """Bandas verticales de capa + etiquetas, para contexto autoexplicativo."""
    xs = sorted(set(x for x, _ in pos.values()))
    for li, layer in enumerate(LAYER_ORDER):
        x = li * 2.2
        ax.axvspan(x - 1.05, x + 1.05, color=PANEL if li % 2 == 0 else BG, alpha=0.45, zorder=0)
        ax.text(x, 3.0, LAYER_LABEL[layer], ha="center", va="bottom",
                color=MUTED, fontsize=10, family="monospace", fontweight="bold")


def _node_style(G, n, source, target, visited=None, frontier=None, current=None):
    visited = visited or set()
    frontier = frontier or set()
    if n == current:               return NODE_CUR, 1500, "#ffffff"
    if n == target:                return NODE_TARGET, 1500, "#ff3b5c"
    if n == source:                return NODE_ENTRY, 1300, "#5ad1a0"
    if n in visited:               return NODE_VISIT, 1100, "#ff8c42"
    if n in frontier:              return NODE_FRONT, 1100, "#3fb6ff"
    return NODE_IDLE, 900, "#3a4760"


def _draw_edges(ax, G, pos, highlight=None, dim=False):
    highlight = highlight or set()
    for u, v, d in G.edges(data=True):
        col = SEV_COLOR[_sev(d["cvss"])]
        is_hi = (u, v) in highlight
        lw = 3.4 if is_hi else 1.3
        alpha = 0.95 if is_hi else (0.15 if dim else 0.4)
        ax.annotate("", xy=pos[v], xytext=pos[u],
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, alpha=alpha,
                                    shrinkA=18, shrinkB=18,
                                    connectionstyle="arc3,rad=0.08"),
                    zorder=2 if not is_hi else 5)


def _draw_nodes(ax, G, pos, source, target, visited=None, frontier=None, current=None, dist=None):
    for n in G.nodes:
        c, s, ec = _node_style(G, n, source, target, visited, frontier, current)
        ax.scatter(*pos[n], s=s, c=c, edgecolors=ec, linewidths=2.0, zorder=6)
        ax.text(pos[n][0], pos[n][1] - 0.34, n, ha="center", va="top",
                color=TXT, fontsize=8.5, family="monospace", zorder=7)
        if dist is not None and dist.get(n, float("inf")) < float("inf"):
            ax.text(pos[n][0], pos[n][1] + 0.30, f"{dist[n]:.1f}", ha="center", va="bottom",
                    color="#ffd23f", fontsize=9, fontweight="bold", zorder=7,
                    family="monospace")


def _legend(ax):
    items = [
        Line2D([0],[0], marker='o', color='none', markerfacecolor=NODE_ENTRY, markersize=11, label='Entrada (INTERNET)'),
        Line2D([0],[0], marker='o', color='none', markerfacecolor=NODE_CUR,   markeredgecolor='#888', markersize=11, label='Nodo actual'),
        Line2D([0],[0], marker='o', color='none', markerfacecolor=NODE_VISIT, markersize=11, label='Visitado'),
        Line2D([0],[0], marker='o', color='none', markerfacecolor=NODE_FRONT, markersize=11, label='Frontera'),
        Line2D([0],[0], marker='o', color='none', markerfacecolor=NODE_TARGET,markersize=11, label='Activo crítico'),
    ]
    leg = ax.legend(handles=items, loc="lower left", fontsize=8.5, framealpha=0.0,
                    labelcolor=TXT, ncol=5, bbox_to_anchor=(0.0, -0.02))


def _sev_legend(ax):
    items = [mpatches.Patch(color=SEV_COLOR[s], label=f"{s} (w={'bajo' if s in ('CRITICAL','HIGH') else 'alto'})")
             for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]]
    ax.legend(handles=items, loc="lower right", fontsize=8, framealpha=0.0,
              labelcolor=TXT, title="Aristas (CVE)  ·  w = 10 − CVSS",
              title_fontsize=8)


# ── 1. Grafo estático ───────────────────────────────────────────────────────────

def render_graph_png(G, source, target, out_path):
    pos = layered_layout(G)
    fig, ax = _base_fig()
    _draw_layers(ax, pos)
    _draw_edges(ax, G, pos)
    _draw_nodes(ax, G, pos, source, target)
    ax.set_title("Grafo de Ataque — hosts/servicios y CVEs explotables",
                 color=TXT, fontsize=15, fontweight="bold", pad=16, family="monospace")
    _sev_legend(ax)
    _set_lims(ax, pos)
    fig.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  PNG grafo: {out_path}")
    return out_path


def _set_lims(ax, pos):
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.4, max(xs) + 1.4)
    ax.set_ylim(min(ys) - 1.0, 3.6)


# ── 2. Expansión de Dijkstra ────────────────────────────────────────────────────

def render_dijkstra_gif(G, result, source, target, out_path, fps=1.4):
    pos = layered_layout(G)
    frames = []
    tmpdir = os.path.join(os.path.dirname(out_path), "_tmp_dij")
    os.makedirs(tmpdir, exist_ok=True)

    steps = result["steps"]
    for i, st in enumerate(steps):
        fig, ax = _base_fig()
        _draw_layers(ax, pos)
        _draw_edges(ax, G, pos, dim=True)
        # resaltar aristas ya fijadas (árbol de caminos mínimos parcial)
        tree = set()
        for v, u in result["prev"].items():
            if u is not None and v in st["visited"]:
                tree.add((u, v))
        _draw_edges(ax, G, pos, highlight=tree)
        _draw_nodes(ax, G, pos, source, target,
                    visited=st["visited"], frontier=set(st["frontier"]),
                    current=st["current"], dist=st["dist"])
        ax.set_title(f"Dijkstra · iteración {i+1}/{len(steps)}  —  fijado: {st['current']}",
                     color=TXT, fontsize=14, fontweight="bold", pad=16, family="monospace")
        ax.text(0.5, 0.965,
                "El frente de exploración avanza por el camino de MENOR resistencia (w = 10 − CVSS)",
                transform=ax.transAxes, ha="center", color=MUTED, fontsize=9.5, family="monospace")
        _legend(ax)
        _set_lims(ax, pos)
        fp = os.path.join(tmpdir, f"f{i:03d}.png")
        fig.savefig(fp, facecolor=BG)   # tamaño fijo (sin bbox tight) para GIF uniforme
        plt.close(fig)
        frames.append(fp)

    imgs = [imageio.imread(f) for f in frames]
    imgs += [imgs[-1]] * 4  # pausa final
    imageio.mimsave(out_path, imgs, fps=fps, loop=0)
    for f in frames: os.remove(f)
    os.rmdir(tmpdir)
    print(f"  GIF expansión Dijkstra: {out_path}  ({len(steps)} iteraciones)")
    return out_path


# ── 3. Ruta crítica trazada ─────────────────────────────────────────────────────

def render_critical_path_gif(G, result, source, target, out_path, fps=1.2):
    pos = layered_layout(G)
    path = result["path"]
    edges = path_edges(path)
    frames = []
    tmpdir = os.path.join(os.path.dirname(out_path), "_tmp_path")
    os.makedirs(tmpdir, exist_ok=True)

    for i in range(len(edges) + 1):
        fig, ax = _base_fig()
        _draw_layers(ax, pos)
        _draw_edges(ax, G, pos, dim=True)
        hi = set(edges[:i])
        _draw_edges(ax, G, pos, highlight=hi)
        on_path = set(n for e in edges[:i] for n in e) | {source}
        _draw_nodes(ax, G, pos, source, target, visited=on_path,
                    current=(path[i] if i < len(path) else target))
        # panel del salto actual
        if 0 < i <= len(edges):
            u, v = edges[i - 1]
            e = G[u][v]
            ax.text(0.5, 0.93,
                    f"Salto {i}: {u} → {v}   |   {e['cve']}  (CVSS {e['cvss']}, w={e['weight']})",
                    transform=ax.transAxes, ha="center", color="#ff8c42",
                    fontsize=11, family="monospace", fontweight="bold")
            ax.text(0.5, 0.885, e["product"], transform=ax.transAxes, ha="center",
                    color=MUTED, fontsize=9, family="monospace")
        title = "Ruta crítica de ataque" if i < len(edges) else \
                f"RUTA CRÍTICA COMPLETA · resistencia total = {result['cost']:.2f}"
        ax.set_title(title, color=TXT, fontsize=14, fontweight="bold", pad=22, family="monospace")
        _set_lims(ax, pos)
        fp = os.path.join(tmpdir, f"p{i:03d}.png")
        fig.savefig(fp, facecolor=BG)   # tamaño fijo para GIF uniforme
        plt.close(fig)
        frames.append(fp)

    imgs = [imageio.imread(f) for f in frames]
    imgs += [imgs[-1]] * 6
    imageio.mimsave(out_path, imgs, fps=fps, loop=0)
    for f in frames: os.remove(f)
    os.rmdir(tmpdir)
    print(f"  GIF ruta crítica: {out_path}  ({len(edges)} saltos)")
    return out_path
