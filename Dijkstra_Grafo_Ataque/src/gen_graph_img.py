"""
gen_graph_img.py — Genera la imagen del grafo de ataque SolarWinds.

Lee los resultados ya calculados (ruta_critica_solarwinds.json,
fw_betweenness_solarwinds.json) y produce:

  diapositivas/assets/img/attack_graph_solarwinds.png
    OK: grafo completo (capas de tácticas + ruta crítica resaltada)

  diapositivas/assets/img/critical_path_solarwinds.png
    OK: solo la ruta crítica, limpio para diapositivas

No necesita descargar ATT&CK de nuevo.
"""

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import networkx as nx

ROOT      = Path(__file__).resolve().parent.parent
REAL_DIR  = ROOT / "results" / "real"
OUT_DIR   = ROOT / "diapositivas" / "assets" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Paleta del deck ───────────────────────────────────────────────────────────
BG      = "#0d1320"
PANEL   = "#121a2b"
LINE    = "#1e2a40"
TXT     = "#e8edf6"
MUTED   = "#8a97ad"
CRIT    = "#ff3b5c"
HIGH    = "#ff8c42"
CYAN    = "#3fb6ff"
GREEN   = "#5ad1a0"
AMBER   = "#ffd23f"
PURPLE  = "#c084fc"

TACTIC_ORDER = [
    "reconnaissance", "resource-development", "initial-access", "execution",
    "persistence", "privilege-escalation", "defense-impairment", "stealth",
    "credential-access", "discovery", "lateral-movement", "collection",
    "command-and-control", "exfiltration",
]
TACTIC_SHORT = {
    "reconnaissance":      "Recon",
    "resource-development":"Res.Dev",
    "initial-access":      "Init.Acc",
    "execution":           "Exec",
    "persistence":         "Persist",
    "privilege-escalation":"PrivEsc",
    "defense-impairment":  "Def.Imp",
    "stealth":             "Stealth",
    "credential-access":   "Cred.Acc",
    "discovery":           "Discovery",
    "lateral-movement":    "Lat.Mov",
    "collection":          "Collect",
    "command-and-control": "C2",
    "exfiltration":        "Exfil",
}


# ── Carga de datos ────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── 1. Imagen de la ruta crítica ─────────────────────────────────────────────

def render_critical_path(ruta: list, out: Path):
    nodes = ruta  # lista de dicts con step, node, name, weight, tactics, dist_acumulada

    fig, ax = plt.subplots(figsize=(22, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")

    n = len(nodes)
    xs = [i / (n - 1) * 0.92 + 0.04 for i in range(n)]
    y  = 0.50

    # Colores por rango de weight
    def node_color(w):
        if w <= 0.1:  return CRIT
        if w <= 0.2:  return HIGH
        if w <= 0.5:  return AMBER
        return CYAN

    # Aristas
    for i in range(n - 1):
        x0, x1 = xs[i], xs[i + 1]
        ax.annotate("", xy=(x1 - 0.01, y), xytext=(x0 + 0.01, y),
                    xycoords="axes fraction", textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color=MUTED,
                                   lw=2.2, mutation_scale=20,
                                   connectionstyle="arc3,rad=0"))

    # Nodos
    for i, nd in enumerate(nodes):
        x = xs[i]
        col = node_color(nd.get("weight", 0))

        is_border = nd["node"] in ("ATTACKER", "IMPACT")
        radius = 0.038 if is_border else 0.034
        circle = plt.Circle((x, y), radius, color=col, alpha=0.18,
                             transform=ax.transAxes, zorder=4)
        ax.add_patch(circle)
        ring = plt.Circle((x, y), radius, fill=False, edgecolor=col,
                          linewidth=2.8 if not is_border else 3.5,
                          transform=ax.transAxes, zorder=5)
        ax.add_patch(ring)

        # ID del nodo
        label = nd["node"] if nd["node"] not in ("ATTACKER","IMPACT") else ("⚠" if nd["node"]=="ATTACKER" else "✓")
        ax.text(x, y, label, ha="center", va="center", fontsize=9.5,
                color=col, fontweight="bold",
                transform=ax.transAxes, zorder=6, fontfamily="monospace")

        # Nombre debajo
        name = nd.get("name", nd["node"])
        if len(name) > 22:
            name = name[:20] + "…"
        ax.text(x, y - 0.16, name, ha="center", va="top", fontsize=8.5,
                color=TXT, transform=ax.transAxes, zorder=6,
                wrap=True)

        # Táctica sobre el nodo
        tacs = nd.get("tactics", [])
        tac_label = TACTIC_SHORT.get(tacs[0], tacs[0]) if tacs else ""
        ax.text(x, y + 0.15, tac_label, ha="center", va="bottom", fontsize=7.5,
                color=MUTED, transform=ax.transAxes, zorder=6, fontfamily="monospace")

        # Peso (w=) en la arista
        w = nd.get("weight", 0)
        dist = nd.get("dist_acumulada", 0)
        if nd["node"] not in ("ATTACKER",):
            ax.text(x, y - 0.32, f"w={w:.3f}\nΣ={dist:.3f}",
                    ha="center", va="top", fontsize=7.5, color=col,
                    transform=ax.transAxes, zorder=6, fontfamily="monospace",
                    linespacing=1.4)

    # Título
    ax.text(0.5, 0.97, "Ruta critica SolarWinds · Dijkstra · resistencia total = 1.535",
            ha="center", va="top", fontsize=13, color=AMBER, fontweight="bold",
            transform=ax.transAxes)

    plt.tight_layout(pad=0.3)
    fig.savefig(out, dpi=160, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  OK: {out}")


# ── 2. Grafo completo por capas ───────────────────────────────────────────────

def render_full_graph(ruta: list, betweenness: list, out: Path):
    """
    Grafo simplificado: 14 columnas (tácticas) con nodos representativos.
    Resalta la ruta crítica en rojo. Muestra los top-7 nodos de betweenness.
    """
    # Construir grafo de la ruta crítica solamente (para el visual de slide)
    G = nx.DiGraph()
    path_nodes = set(nd["node"] for nd in ruta)
    path_edges = [(ruta[i]["node"], ruta[i+1]["node"]) for i in range(len(ruta)-1)]

    for nd in ruta:
        G.add_node(nd["node"],
                   name=nd.get("name",""),
                   weight=nd.get("weight",0),
                   tactics=nd.get("tactics",[]),
                   dist=nd.get("dist_acumulada",0))
    for u, v in path_edges:
        G.add_edge(u, v)

    # Posiciones: eje x = orden en la ruta crítica
    pos = {}
    for i, nd in enumerate(ruta):
        pos[nd["node"]] = (i, 0)

    fig, ax = plt.subplots(figsize=(22, 7), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")

    # Colores de nodos
    def nc(w, node):
        if node == "ATTACKER": return GREEN
        if node == "IMPACT":   return CRIT
        if w <= 0.1: return CRIT
        if w <= 0.2: return HIGH
        if w <= 0.5: return AMBER
        return CYAN

    node_colors = [nc(G.nodes[n].get("weight",0), n) for n in G.nodes()]
    node_sizes  = [2800 if n in ("ATTACKER","IMPACT") else 2200 for n in G.nodes()]

    # Dibujar aristas
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=CRIT, width=3.0,
                           arrows=True, arrowsize=22, arrowstyle="-|>",
                           connectionstyle="arc3,rad=0.05",
                           min_source_margin=28, min_target_margin=28)

    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, alpha=0.85)

    # Labels
    labels = {}
    for nd in ruta:
        n = nd["node"]
        name = nd.get("name","")
        if n in ("ATTACKER","IMPACT"):
            labels[n] = n
        else:
            short = name[:14] + "…" if len(name) > 14 else name
            labels[n] = f"{n}\n{short}"

    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=8,
                            font_color=BG, font_weight="bold")

    # Pesos en aristas
    edge_labels = {}
    for i in range(len(ruta)-1):
        u, v = ruta[i]["node"], ruta[i+1]["node"]
        w = ruta[i+1].get("weight", 0)
        edge_labels[(u,v)] = f"w={w:.2f}"
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                 font_size=8, font_color=AMBER,
                                 font_family="monospace",
                                 bbox=dict(boxstyle="round,pad=0.2",
                                           fc=BG, ec=LINE, alpha=0.85))

    # Táctica debajo de cada nodo
    for nd in ruta:
        n = nd["node"]
        x, y = pos[n]
        tacs = nd.get("tactics",[])
        tac = TACTIC_SHORT.get(tacs[0], "") if tacs else ""
        dist = nd.get("dist_acumulada", 0)
        ax.text(x, -0.75, f"{tac}\nΣ={dist:.3f}",
                ha="center", va="top", fontsize=8,
                color=MUTED, fontfamily="monospace")

    # Título
    ax.set_title("Grafo de ataque SolarWinds Compromise · Ruta crítica (Dijkstra) · resistencia = 1.635",
                 color=AMBER, fontsize=14, fontweight="bold", pad=20)

    # Leyenda
    patches = [
        mpatches.Patch(color=CRIT,  label="w ≤ 0.1 · CRÍTICO"),
        mpatches.Patch(color=HIGH,  label="w ≤ 0.2 · ALTO"),
        mpatches.Patch(color=AMBER, label="w ≤ 0.5 · MEDIO"),
        mpatches.Patch(color=CYAN,  label="w > 0.5 · BAJO"),
    ]
    ax.legend(handles=patches, loc="lower right", facecolor=PANEL,
              edgecolor=LINE, labelcolor=TXT, fontsize=9)

    plt.tight_layout(pad=0.5)
    fig.savefig(out, dpi=160, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  OK: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nGenerando imágenes del grafo SolarWinds…")

    ruta        = load_json(REAL_DIR / "ruta_critica_solarwinds.json")
    betweenness = load_json(REAL_DIR / "fw_betweenness_solarwinds.json")

    print("\n[1/2] Ruta crítica (lineal)…")
    render_critical_path(ruta, OUT_DIR / "critical_path_solarwinds.png")

    print("[2/2] Grafo completo de la ruta crítica…")
    render_full_graph(ruta, betweenness, OUT_DIR / "attack_graph_solarwinds.png")

    print("\n✓ Imágenes guardadas en:", OUT_DIR)
