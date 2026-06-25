"""
gen_full_graph.py — Genera imagen del grafo COMPLETO de la campana SolarWinds.

Reconstruye los 73 nodos (71 tecnicas + ATTACKER + IMPACT) y las aristas
usando los mismos datos y reglas que dataset_real.py, sin necesitar el bundle MITRE.

Fuente: results/real/fw_betweenness_solarwinds.json
        results/real/ruta_critica_solarwinds.json

Salida: diapositivas/assets/img/full_graph_solarwinds.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

ROOT     = Path(__file__).resolve().parent.parent
REAL_DIR = ROOT / "results" / "real"
OUT_DIR  = ROOT / "diapositivas" / "assets" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BG    = "#ffffff"
PANEL = "#f0f2f5"
LINE  = "#ccd0d8"
TXT   = "#1a1a2e"
MUTED = "#555e70"
CRIT  = "#ff3b5c"
HIGH  = "#ff8c42"
CYAN  = "#3fb6ff"
GREEN = "#5ad1a0"
AMBER = "#ffd23f"
PURPLE= "#c084fc"

TACTIC_ORDER = [
    "reconnaissance", "resource-development", "initial-access",
    "execution", "persistence", "privilege-escalation",
    "defense-impairment", "stealth", "credential-access",
    "discovery", "lateral-movement", "collection",
    "command-and-control", "exfiltration",
]
TACTIC_SHORT = {
    "reconnaissance":      "Recon",
    "resource-development":"Res.Dev",
    "initial-access":      "Init.",
    "execution":           "Exec",
    "persistence":         "Persist",
    "privilege-escalation":"PrivEsc",
    "defense-impairment":  "Def.Imp",
    "stealth":             "Stealth",
    "credential-access":   "Cred.",
    "discovery":           "Discov.",
    "lateral-movement":    "Lat.Mov",
    "collection":          "Collect",
    "command-and-control": "C2",
    "exfiltration":        "Exfil",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def node_color(w, node, critical_set):
    if node == "ATTACKER": return GREEN
    if node == "IMPACT":   return CRIT
    if node in critical_set:
        if w <= 0.1:  return CRIT
        if w <= 0.2:  return HIGH
        return AMBER
    # nodos fuera de la ruta critica: mas apagados
    if w <= 0.1:  return "#e8a0aa"
    if w <= 0.3:  return "#e8c4a0"
    if w <= 0.6:  return "#d4c87a"
    return "#a0b4c8"


def build_graph(nodes_data, critical_path_ids):
    """
    Construye el DiGraph con los mismos nodos y reglas de aristas
    que dataset_real.py: conecta tacticas consecutivas entre si
    (todas las combinaciones de nodos src_tac -> dst_tac).
    """
    G = nx.DiGraph()

    # Agregar todos los nodos de tecnicas
    by_tactic = {t: [] for t in TACTIC_ORDER}
    for nd in nodes_data:
        node_id = nd["node"]
        G.add_node(node_id,
                   name=nd.get("name", ""),
                   weight=nd.get("weight", 0.5),
                   tactics=nd.get("tactics", []),
                   fw_betweenness=nd.get("fw_betweenness", 0))
        for tac in nd.get("tactics", []):
            if tac in by_tactic:
                by_tactic[tac].append(node_id)

    # Nodos frontera
    G.add_node("ATTACKER", name="Atacante", tactics=["entry"], weight=0.0)
    G.add_node("IMPACT",   name="Impacto",  tactics=["target"], weight=0.0)

    # Aristas: ATTACKER -> primera tactica
    for tac in ["reconnaissance", "resource-development", "initial-access"]:
        for nid in by_tactic.get(tac, []):
            G.add_edge("ATTACKER", nid, weight=G.nodes[nid]["weight"])

    # Aristas: ultima tactica -> IMPACT
    for nid in by_tactic.get("exfiltration", []):
        G.add_edge(nid, "IMPACT", weight=0.01)

    # Aristas: tacticas consecutivas (todas las combinaciones)
    for i in range(len(TACTIC_ORDER) - 1):
        src_tac = TACTIC_ORDER[i]
        dst_tac = TACTIC_ORDER[i + 1]
        for src in by_tactic.get(src_tac, []):
            for dst in by_tactic.get(dst_tac, []):
                if not G.has_edge(src, dst):
                    G.add_edge(src, dst, weight=G.nodes[dst]["weight"])

    return G, by_tactic


def layered_positions(G, by_tactic):
    """
    Layout en capas: x = indice de tactica, y = distribucion vertical.
    ATTACKER a la izquierda, IMPACT a la derecha.
    """
    pos = {}
    all_tactics = ["_entry"] + TACTIC_ORDER + ["_exit"]
    col_map = {t: i for i, t in enumerate(all_tactics)}

    # Nodos frontera
    n_cols = len(all_tactics)
    pos["ATTACKER"] = (0, 0)
    pos["IMPACT"]   = (n_cols - 1, 0)

    for tac in TACTIC_ORDER:
        nodes = by_tactic.get(tac, [])
        k = len(nodes)
        col_x = col_map[tac]
        for j, nid in enumerate(nodes):
            y = (j - (k - 1) / 2.0) * 1.1
            pos[nid] = (col_x, y)

    return pos


def render_full_graph(G, pos, by_tactic, critical_ids, out: Path):
    fig, ax = plt.subplots(figsize=(32, 18), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")

    # --- Columnas de fondo (una por tactica) ---
    for i, tac in enumerate(["_entry"] + TACTIC_ORDER + ["_exit"]):
        col_x = i
        nodes_in_col = by_tactic.get(tac, [])
        if not nodes_in_col and tac not in ("_entry", "_exit"):
            continue
        ax.axvline(x=col_x, color=LINE, linewidth=0.4, alpha=0.4, zorder=0)
        label = TACTIC_SHORT.get(tac, "")
        if label:
            ax.text(col_x, ax.get_ylim()[1] if ax.get_ylim()[1] != 0 else 9,
                    label, ha="center", va="bottom",
                    fontsize=7, color=MUTED, fontfamily="monospace")

    # --- Aristas fuera de la ruta critica (primero, debajo) ---
    critical_edges = set()
    crit_list = list(critical_ids)
    for k in range(len(crit_list) - 1):
        critical_edges.add((crit_list[k], crit_list[k+1]))

    non_crit_edges = [(u, v) for u, v in G.edges()
                      if (u, v) not in critical_edges]
    crit_edges     = [(u, v) for u, v in G.edges()
                      if (u, v) in critical_edges]

    nx.draw_networkx_edges(G, pos, ax=ax,
                           edgelist=non_crit_edges,
                           edge_color=LINE, width=0.35,
                           alpha=0.55, arrows=False)

    # --- Aristas de la ruta critica (encima, destacadas) ---
    nx.draw_networkx_edges(G, pos, ax=ax,
                           edgelist=crit_edges,
                           edge_color=CRIT, width=3.5,
                           alpha=0.95, arrows=True,
                           arrowsize=18, arrowstyle="-|>",
                           min_source_margin=14, min_target_margin=14)

    # --- Nodos ---
    all_nodes = list(G.nodes())
    colors = [node_color(G.nodes[n].get("weight", 0.5), n, critical_ids)
              for n in all_nodes]
    sizes  = []
    for n in all_nodes:
        if n in ("ATTACKER", "IMPACT"):
            sizes.append(900)
        elif n in critical_ids:
            sizes.append(420)
        else:
            bw = G.nodes[n].get("fw_betweenness", 0)
            sizes.append(max(80, min(350, 80 + bw * 0.12)))

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           nodelist=all_nodes,
                           node_color=colors,
                           node_size=sizes,
                           alpha=0.92, linewidths=0)

    # --- Labels solo para nodos importantes ---
    labels_main = {}
    for n in all_nodes:
        if n in ("ATTACKER", "IMPACT"):
            labels_main[n] = n
        elif n in critical_ids:
            labels_main[n] = n

    nx.draw_networkx_labels(G, pos, labels=labels_main, ax=ax,
                            font_size=7.5, font_color=TXT,
                            font_weight="bold")

    # --- Etiquetas de tactica en parte superior ---
    y_max = max(y for x, y in pos.values()) + 1.2
    for i, tac in enumerate(TACTIC_ORDER):
        col_x = i + 1   # +1 por el _entry
        label = TACTIC_SHORT.get(tac, tac)
        n_tec = len(by_tactic.get(tac, []))
        ax.text(col_x, y_max, f"{label}\n({n_tec})",
                ha="center", va="bottom",
                fontsize=8, color=MUTED, fontfamily="monospace",
                linespacing=1.3)

    # --- Leyenda ---
    patches = [
        mpatches.Patch(color=CRIT,   label="Ruta critica (Dijkstra)"),
        mpatches.Patch(color=HIGH,   label="Nodo critico · w<=0.2"),
        mpatches.Patch(color="#a0b4c8", label="Resto de tecnicas"),
        mpatches.Patch(color=GREEN,  label="ATTACKER"),
        mpatches.Patch(color=MUTED,  label=f"Aristas totales: {G.number_of_edges()}"),
    ]
    ax.legend(handles=patches, loc="lower right",
              facecolor=PANEL, edgecolor=LINE,
              labelcolor=TXT, fontsize=11, framealpha=0.9)

    # --- Titulo ---
    ax.set_title(
        f"Grafo de ataque SolarWinds Compromise · ATT&CK Enterprise · "
        f"{G.number_of_nodes()} nodos · {G.number_of_edges()} aristas · "
        f"Ruta critica Dijkstra resaltada (resistencia = 1.635)",
        color=AMBER, fontsize=14, fontweight="bold", pad=18
    )

    plt.tight_layout(pad=0.4)
    fig.savefig(out, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: {out}")


if __name__ == "__main__":
    print("Cargando datos...")
    nodes_data  = load_json(REAL_DIR / "fw_betweenness_solarwinds.json")
    ruta        = load_json(REAL_DIR / "ruta_critica_solarwinds.json")

    critical_ids = {nd["node"] for nd in ruta}

    print(f"  Tecnicas: {len(nodes_data)}")
    print(f"  Nodos ruta critica: {len(critical_ids)}")

    print("Construyendo grafo completo...")
    G, by_tactic = build_graph(nodes_data, critical_ids)
    print(f"  Nodos totales: {G.number_of_nodes()}")
    print(f"  Aristas totales: {G.number_of_edges()}")

    print("Calculando layout...")
    pos = layered_positions(G, by_tactic)

    print("Renderizando imagen...")
    render_full_graph(G, pos, by_tactic, critical_ids,
                      OUT_DIR / "full_graph_solarwinds.png")

    print("Listo.")
