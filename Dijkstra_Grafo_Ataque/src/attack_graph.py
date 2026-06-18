"""
attack_graph.py — Construye un grafo de ataque dirigido a partir de CVEs reales.

Modelo:
  - NODOS  = hosts/servicios de la infraestructura, organizados en capas:
       INTERNET → perimeter → web → service → host → data (ACTIVO CRÍTICO)
  - ARISTAS = vulnerabilidades explotables (CVEs). Una arista u→v significa
       "estando en u, explotar este CVE me lleva a v".
  - PESO   = w = 10 − CVSS  (CVSS inverso).
       Vulnerabilidad crítica (CVSS alto) → peso bajo → camino de MENOR
       resistencia para el atacante. Dijkstra minimiza la resistencia total.

El nodo de entrada es `INTERNET` (atacante externo). El objetivo es el activo
crítico `DB-CRITICAL` en la capa de datos.
"""

import networkx as nx

# Cadena de capas (profundidad creciente hacia el activo crítico)
LAYER_ORDER = ["internet", "perimeter", "web", "service", "host", "data"]

LAYER_LABEL = {
    "internet":  "INTERNET\n(atacante)",
    "perimeter": "Perímetro",
    "web":       "Web/App",
    "service":   "Servicios",
    "host":      "Hosts/SO",
    "data":      "Datos (CRÍTICO)",
}


def edge_weight(cvss: float) -> float:
    """w = 10 − CVSS, acotado a un mínimo positivo para que Dijkstra funcione."""
    return max(0.1, round(10.0 - cvss, 2))


def build_attack_graph(cves: list, seed: int = 42) -> nx.DiGraph:
    """
    Construye el DiGraph. Crea 1-2 nodos host por capa y conecta capas
    consecutivas usando los CVEs cuya `vector_layer` corresponde a la capa
    destino. Cada CVE = una arista explotable hacia la capa siguiente.
    """
    import random
    random.seed(seed)

    G = nx.DiGraph()

    # Nodos por capa (activos concretos de una red corporativa)
    layer_nodes = {
        "internet":  ["INTERNET"],
        "perimeter": ["FW-VPN", "GW-EDGE"],
        "web":       ["WEB-01", "APP-02"],
        "service":   ["SMB-FILES", "RDP-JUMP", "MAIL-EX"],
        "host":      ["DC-01", "WS-ADMIN"],
        "data":      ["DB-CRITICAL"],
    }
    for layer, nodes in layer_nodes.items():
        for n in nodes:
            G.add_node(n, layer=layer)

    # Agrupar CVEs por capa destino
    by_layer = {l: [] for l in LAYER_ORDER}
    for c in cves:
        by_layer.get(c["vector_layer"], by_layer["host"]).append(c)

    # Cablear capas consecutivas: src en capa i, dst en capa i+1,
    # arista etiquetada con un CVE cuya vector_layer == capa destino.
    for i in range(len(LAYER_ORDER) - 1):
        src_layer = LAYER_ORDER[i]
        dst_layer = LAYER_ORDER[i + 1]
        src_nodes = layer_nodes[src_layer]
        dst_nodes = layer_nodes[dst_layer]
        cve_pool = by_layer[dst_layer] or by_layer["host"]
        if not cve_pool:
            continue

        # Conectar cada destino desde al menos un origen, variando CVEs
        for dst in dst_nodes:
            n_links = random.randint(1, max(1, len(src_nodes)))
            chosen_src = random.sample(src_nodes, n_links)
            for src in chosen_src:
                cve = random.choice(cve_pool)
                G.add_edge(src, dst,
                           weight=edge_weight(cve["cvss"]),
                           cve=cve["id"],
                           cvss=cve["cvss"],
                           product=cve["product"],
                           severity=cve["severity"])

    # Añadir algunos "atajos" laterales realistas (mismo o salto de 2 capas)
    # para que existan rutas alternativas y los cuellos de botella tengan sentido.
    extra = [
        ("FW-VPN", "WEB-01"), ("GW-EDGE", "APP-02"),
        ("WEB-01", "SMB-FILES"), ("APP-02", "MAIL-EX"),
        ("SMB-FILES", "DC-01"), ("RDP-JUMP", "DC-01"),
        ("MAIL-EX", "WS-ADMIN"), ("DC-01", "DB-CRITICAL"),
        ("WS-ADMIN", "DB-CRITICAL"),
    ]
    all_cves = cves
    for u, v in extra:
        if G.has_node(u) and G.has_node(v) and not G.has_edge(u, v):
            cve = random.choice(all_cves)
            G.add_edge(u, v, weight=edge_weight(cve["cvss"]), cve=cve["id"],
                       cvss=cve["cvss"], product=cve["product"], severity=cve["severity"])

    return G


def layered_layout(G: nx.DiGraph) -> dict:
    """Posiciones (x,y): x = índice de capa, y = reparto vertical por capa."""
    pos = {}
    by_layer = {l: [] for l in LAYER_ORDER}
    for n, d in G.nodes(data=True):
        by_layer[d["layer"]].append(n)
    for li, layer in enumerate(LAYER_ORDER):
        nodes = by_layer[layer]
        k = len(nodes)
        for j, n in enumerate(nodes):
            y = 0.0 if k == 1 else (j - (k - 1) / 2.0)
            pos[n] = (li * 2.2, y * 1.6)
    return pos


def graph_summary(G: nx.DiGraph) -> dict:
    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "layers": LAYER_ORDER,
        "entry": "INTERNET",
        "target": "DB-CRITICAL",
    }


if __name__ == "__main__":
    from nvd_fetch import load_cves
    cves, src = load_cves(use_live=False)
    G = build_attack_graph(cves)
    print(graph_summary(G))
    for u, v, d in list(G.edges(data=True))[:6]:
        print(f"  {u:10} → {v:12}  w={d['weight']:<4} via {d['cve']} (CVSS {d['cvss']})")
