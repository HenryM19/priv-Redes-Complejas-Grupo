"""
analisis_real.py — Dijkstra + Floyd-Warshall: caso de estudio SolarWinds Compromise.

Pregunta de investigacion:
  En la campana SolarWinds Compromise (2019-2020, documentada por MITRE ATT&CK),
  ¿cual es la secuencia de tecnicas de menor resistencia desde el acceso inicial
  hasta el impacto, segun Dijkstra?
  ¿Y que tecnicas son cuellos de botella universales segun Floyd-Warshall?

Datos: 100% MITRE ATT&CK Enterprise STIX 2.1 (enterprise-attack.json)
       Pesos: n_mitigaciones reales del bundle + CVSS real de CVEs NVD
"""

import json
import heapq
from pathlib import Path

import networkx as nx
import numpy as np

from dataset_real import (
    download_mitre,
    extract_campaign,
    build_attack_graph,
    graph_summary,
    TARGET_CAMPAIGN_NAME,
    ENTRY_NODE,
    TARGET_NODE,
    TACTIC_ORDER,
)

RESULTS_DIR = Path("results/real")


# ── Dijkstra propio (desde cero) ─────────────────────────────────────────────

def dijkstra(G: nx.DiGraph, source: str) -> tuple[dict, dict]:
    """
    Dijkstra con heap binario (implementacion propia).
    Retorna (dist, prev): dist[v]=costo minimo desde source; prev[v]=predecesor.
    """
    dist = {n: float("inf") for n in G.nodes()}
    prev = {n: None for n in G.nodes()}
    dist[source] = 0.0
    heap = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, data in G[u].items():
            w = data.get("weight", 1.0)
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    return dist, prev


def reconstruct_path(prev: dict, source: str, target: str) -> list[str]:
    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    if path and path[0] == source:
        return path
    return []


# ── Floyd-Warshall ────────────────────────────────────────────────────────────

def floyd_warshall(G: nx.DiGraph) -> tuple[np.ndarray, list]:
    """
    Floyd-Warshall sobre el grafo completo de la campana.
    Con 73 nodos (71 tecnicas + 2 fronteras) es O(73^3) = 389k ops, trivial.
    Retorna (dist_matrix, node_list).
    """
    nodes = list(G.nodes())
    n = len(nodes)
    idx = {node: i for i, node in enumerate(nodes)}

    INF = float("inf")
    dist = np.full((n, n), INF)
    np.fill_diagonal(dist, 0.0)

    for u, v, data in G.edges(data=True):
        i, j = idx[u], idx[v]
        w = data.get("weight", 1.0)
        if w < dist[i][j]:
            dist[i][j] = w

    print(f"  [FW] Floyd-Warshall sobre {n} nodos (campana completa)...")
    for k in range(n):
        dist = np.minimum(dist, dist[:, k:k+1] + dist[k:k+1, :])

    return dist, nodes, idx


def fw_betweenness(dist: np.ndarray, nodes: list, idx: dict, G: nx.DiGraph) -> list[dict]:
    """
    Betweenness por caminos minimos (Floyd-Warshall):
    Para nodo k: cuenta pares (i,j) donde d(i,k)+d(k,j) == d(i,j).
    Identifica tecnicas que aparecen en la mayor cantidad de rutas optimas.
    """
    n = len(nodes)
    INF = float("inf")
    scores = np.zeros(n)

    for k in range(n):
        d_ik = dist[:, k]
        d_kj = dist[k, :]
        with np.errstate(invalid="ignore"):  # inf-inf=nan en pares no alcanzables, esperado
            through_k = np.abs((d_ik[:, None] + d_kj[None, :]) - dist) < 1e-9
        through_k[k, :] = False
        through_k[:, k] = False
        reachable = dist < INF
        # Evitar inf-inf = nan
        valid = np.isfinite(d_ik[:, None]) & np.isfinite(d_kj[None, :])
        scores[k] = np.sum(through_k & reachable & valid)

    results = []
    for i, node in enumerate(nodes):
        if node in (ENTRY_NODE, TARGET_NODE):
            continue
        tacs = G.nodes[node].get("tactics", [])
        results.append({
            "node": node,
            "name": G.nodes[node].get("name", ""),
            "fw_betweenness": int(max(0, scores[i])),
            "tactics": tacs,
            "weight": round(G.nodes[node].get("weight", 0), 3),
            "weight_source": G.nodes[node].get("weight_source", ""),
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
        })

    results.sort(key=lambda x: x["fw_betweenness"], reverse=True)
    return results


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run(force_download: bool = False, campaign_name: str = TARGET_CAMPAIGN_NAME):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Dataset real
    print(f"\n[1/4] Cargando dataset MITRE ATT&CK Enterprise...")
    bundle = download_mitre(force=force_download)
    campaign_obj, techniques = extract_campaign(bundle, campaign_name)
    G, tech_by_id, by_tactic = build_attack_graph(bundle, techniques)
    s = graph_summary(G, campaign_name)
    print(f"      Grafo: {s['n_nodes']} nodos, {s['n_edges']} aristas, densidad={s['density']}")

    # 2. Dijkstra
    print(f"\n[2/4] Dijkstra: ruta de menor resistencia ATTACKER -> IMPACT...")
    dist, prev = dijkstra(G, ENTRY_NODE)
    ruta = reconstruct_path(prev, ENTRY_NODE, TARGET_NODE)
    costo_total = dist.get(TARGET_NODE, float("inf"))

    print(f"\n  PREGUNTA DE INVESTIGACION:")
    print(f"  En SolarWinds Compromise, ¿cual es la secuencia de tecnicas")
    print(f"  de menor resistencia segun Dijkstra?")
    print(f"\n  RESPUESTA (Dijkstra):")
    if ruta:
        print(f"  Costo minimo total: {costo_total:.4f}")
        print(f"  Pasos: {len(ruta)} ({len(ruta)-2} tecnicas reales)")
        print(f"\n  Ruta critica:")
        print(f"  {'Paso':<5} {'ID ATT&CK':<14} {'Costo acum.':<13} {'Fuente peso':<40} Nombre tecnica")
        print(f"  {'-'*100}")
        for i, node in enumerate(ruta):
            name = G.nodes[node].get("name", node)
            d = round(dist.get(node, 0), 4)
            w_src = G.nodes[node].get("weight_source", "")
            tactics = G.nodes[node].get("tactics", [])
            tac = tactics[0] if tactics else ""
            print(f"  {i:<5} {node:<14} {d:<13} {w_src:<40} {name[:40]}")
    else:
        print("  [WARN] No se encontro ruta ATTACKER->IMPACT")

    # Guardar
    ruta_data = [
        {
            "step": i,
            "node": node,
            "name": G.nodes[node].get("name", ""),
            "tactics": G.nodes[node].get("tactics", []),
            "weight": round(G.nodes[node].get("weight", 0), 4),
            "weight_source": G.nodes[node].get("weight_source", ""),
            "dist_acumulada": round(dist.get(node, 0), 4),
        }
        for i, node in enumerate(ruta)
    ]
    with open(RESULTS_DIR / "ruta_critica_solarwinds.json", "w", encoding="utf-8") as f:
        json.dump(ruta_data, f, indent=2, ensure_ascii=False)

    # 3. Floyd-Warshall
    print(f"\n[3/4] Floyd-Warshall: betweenness de tecnicas en rutas optimas...")
    fw_dist, fw_nodes, fw_idx = floyd_warshall(G)
    betweenness = fw_betweenness(fw_dist, fw_nodes, fw_idx, G)

    print(f"\n  Top-15 tecnicas puente (mayor presencia en rutas optimas):")
    print(f"  {'Rk':<4} {'ID':<14} {'FW-Betw':<10} {'Peso':<7} {'Tactica':<25} {'Fuente peso':<30} Nombre")
    print(f"  {'-'*115}")
    for i, b in enumerate(betweenness[:15]):
        tac = b["tactics"][0] if b["tactics"] else "-"
        print(f"  {i+1:<4} {b['node']:<14} {b['fw_betweenness']:<10} {b['weight']:<7} {tac:<25} {b['weight_source']:<30} {b['name'][:30]}")

    with open(RESULTS_DIR / "fw_betweenness_solarwinds.json", "w", encoding="utf-8") as f:
        json.dump(betweenness, f, indent=2, ensure_ascii=False)

    # 4. Cuellos de botella
    print(f"\n[4/4] Cuellos de botella: tecnicas en ruta critica con mayor in-degree...")
    cuellos = []
    for node in ruta:
        if node in (ENTRY_NODE, TARGET_NODE):
            continue
        cuellos.append({
            "node": node,
            "name": G.nodes[node].get("name", ""),
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
            "weight": round(G.nodes[node].get("weight", 0), 4),
            "weight_source": G.nodes[node].get("weight_source", ""),
            "tactics": G.nodes[node].get("tactics", []),
            "dist_acumulada": round(dist.get(node, 0), 4),
            "fw_betweenness": next(
                (b["fw_betweenness"] for b in betweenness if b["node"] == node), 0
            ),
        })
    cuellos.sort(key=lambda x: x["in_degree"], reverse=True)

    print(f"\n  {'ID':<14} {'in-deg':<8} {'FW-Betw':<10} {'Peso':<7} {'Fuente peso':<35} Nombre")
    print(f"  {'-'*100}")
    for c in cuellos:
        print(f"  {c['node']:<14} {c['in_degree']:<8} {c['fw_betweenness']:<10} {c['weight']:<7} {c['weight_source']:<35} {c['name'][:30]}")

    with open(RESULTS_DIR / "cuellos_solarwinds.json", "w", encoding="utf-8") as f:
        json.dump(cuellos, f, indent=2, ensure_ascii=False)

    # Resumen tecnicas por tactica
    print(f"\n  Tecnicas SolarWinds por tactica:")
    for tac in TACTIC_ORDER:
        nodes = by_tactic.get(tac, [])
        if nodes:
            print(f"    {tac:<25} {len(nodes):2}")

    print(f"\n{'='*65}")
    print(f"  Resultados en {RESULTS_DIR}/")
    print(f"    ruta_critica_solarwinds.json    {len(ruta_data)} pasos")
    print(f"    fw_betweenness_solarwinds.json  {len(betweenness)} tecnicas")
    print(f"    cuellos_solarwinds.json         {len(cuellos)} cuellos")
    print(f"{'='*65}")

    return G, ruta, betweenness, cuellos


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--campaign", default=TARGET_CAMPAIGN_NAME)
    args = parser.parse_args()
    run(force_download=args.force, campaign_name=args.campaign)
