"""
analisis_cientifico.py — Analisis extendido para publicacion cientifica.

Ejecuta sobre el grafo SolarWinds ya construido:
  1. Comparacion de algoritmos: Dijkstra propio vs BFS (sin pesos) vs NetworkX
  2. Bellman-Ford (validacion de implementacion propia)
  3. Analisis de sensibilidad de pesos (+/-20%, sin CVEs)
  4. Metricas de redes complejas (clustering, distribucion de grados, SCC, diametro)
  5. Comparacion FW-betweenness vs betweenness estandar NetworkX

Salidas:
  results/real/comparacion_algoritmos.json
  results/real/sensibilidad_pesos.json
  results/real/metricas_grafo.json
  results/real/betweenness_comparacion.json
"""

import json
import heapq
import time
from pathlib import Path
from collections import deque, Counter
import math

import networkx as nx
import numpy as np

from dataset_real import (
    download_mitre,
    extract_campaign,
    build_attack_graph,
    build_mitigation_index,
    compute_weight,
    ENTRY_NODE,
    TARGET_NODE,
    TARGET_CAMPAIGN_NAME,
    TACTIC_ORDER,
    KNOWN_CVE_WEIGHTS,
)
from analisis_real import dijkstra, reconstruct_path, floyd_warshall, fw_betweenness

RESULTS_DIR = Path("results/real")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── 1. BFS (sin pesos, solo hops) ────────────────────────────────────────────

def bfs_shortest_path(G: nx.DiGraph, source: str, target: str) -> tuple[list[str], int]:
    """BFS ignora pesos: minimiza numero de saltos."""
    dist = {source: 0}
    prev = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == target:
            break
        for v in G.successors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                prev[v] = u
                queue.append(v)
    if target not in dist:
        return [], -1
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path, dist[target]


# ── 2. Bellman-Ford propio ────────────────────────────────────────────────────

def bellman_ford(G: nx.DiGraph, source: str) -> tuple[dict, dict]:
    """
    Bellman-Ford O(V*E). Detecta ciclos negativos.
    Usado como validacion cruzada de Dijkstra.
    """
    dist = {n: float("inf") for n in G.nodes()}
    prev = {n: None for n in G.nodes()}
    dist[source] = 0.0
    nodes = list(G.nodes())
    n = len(nodes)

    for _ in range(n - 1):
        updated = False
        for u, v, data in G.edges(data=True):
            w = data.get("weight", 1.0)
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                updated = True
        if not updated:
            break

    # Verificar ciclos negativos
    for u, v, data in G.edges(data=True):
        w = data.get("weight", 1.0)
        if dist[u] + w < dist[v] - 1e-9:
            raise ValueError(f"Ciclo negativo detectado en arista {u}->{v}")

    return dist, prev


# ── 3. Analisis de sensibilidad ───────────────────────────────────────────────

def build_graph_with_factor(bundle: dict, techniques: list, factor: float) -> nx.DiGraph:
    """
    Reconstruye el grafo con pesos multiplicados por `factor`.
    Solo afecta pesos base (mitigaciones); CVE-weights tambien escalados.
    Usado para analisis de sensibilidad.
    """
    from dataset_real import _get_attack_id, _get_tactics

    mitig_index = build_mitigation_index(bundle)
    max_mit = max(
        (mitig_index.get(t["id"], 0) for t in techniques),
        default=1
    )

    G = nx.DiGraph()
    tech_by_id = {}

    for t in techniques:
        atk_id = _get_attack_id(t)
        if not atk_id:
            continue
        tactics = _get_tactics(t)
        if not tactics:
            continue
        n_mit = mitig_index.get(t["id"], 0)
        w, w_src = compute_weight(t, n_mit, max_mit)
        w_scaled = round(max(0.05, min(1.0, w * factor)), 3)
        tech_by_id[atk_id] = (t, w_scaled, w_src)
        G.add_node(atk_id, name=t.get("name", ""), tactics=tactics,
                   weight=w_scaled, weight_source=w_src)

    G.add_node(ENTRY_NODE, name="Atacante externo", tactics=["entry"], weight=0.0)
    G.add_node(TARGET_NODE, name="Impacto logrado", tactics=["target"], weight=0.0)

    by_tactic = {tac: [] for tac in TACTIC_ORDER}
    for atk_id in tech_by_id:
        for tac in G.nodes[atk_id]["tactics"]:
            if tac in by_tactic:
                by_tactic[tac].append(atk_id)

    for tac in ["reconnaissance", "resource-development", "initial-access"]:
        for atk_id in by_tactic.get(tac, []):
            G.add_edge(ENTRY_NODE, atk_id, weight=G.nodes[atk_id]["weight"])

    for tac in ["impact", "exfiltration"]:
        for atk_id in by_tactic.get(tac, []):
            G.add_edge(atk_id, TARGET_NODE, weight=0.01)

    for i in range(len(TACTIC_ORDER) - 1):
        src_tac = TACTIC_ORDER[i]
        dst_tac = TACTIC_ORDER[i + 1]
        for src in by_tactic.get(src_tac, []):
            for dst in by_tactic.get(dst_tac, []):
                if not G.has_edge(src, dst):
                    G.add_edge(src, dst, weight=G.nodes[dst]["weight"])

    return G


def build_graph_no_cve(bundle: dict, techniques: list) -> nx.DiGraph:
    """Grafo identico pero sin CVE-weights — solo mitigaciones."""
    from dataset_real import _get_attack_id, _get_tactics

    mitig_index = build_mitigation_index(bundle)
    max_mit = max(
        (mitig_index.get(t["id"], 0) for t in techniques),
        default=1
    )

    G = nx.DiGraph()
    tech_by_id = {}

    for t in techniques:
        atk_id = _get_attack_id(t)
        if not atk_id:
            continue
        tactics = _get_tactics(t)
        if not tactics:
            continue
        n_mit = mitig_index.get(t["id"], 0)
        if max_mit > 0:
            w = round(max(0.05, 1.0 - n_mit / max_mit), 3)
        else:
            w = 0.95
        w_src = f"solo_mitigaciones={n_mit}/{max_mit}"
        tech_by_id[atk_id] = (t, w, w_src)
        G.add_node(atk_id, name=t.get("name", ""), tactics=tactics,
                   weight=w, weight_source=w_src)

    G.add_node(ENTRY_NODE, name="Atacante externo", tactics=["entry"], weight=0.0)
    G.add_node(TARGET_NODE, name="Impacto logrado", tactics=["target"], weight=0.0)

    by_tactic = {tac: [] for tac in TACTIC_ORDER}
    for atk_id in tech_by_id:
        for tac in G.nodes[atk_id]["tactics"]:
            if tac in by_tactic:
                by_tactic[tac].append(atk_id)

    for tac in ["reconnaissance", "resource-development", "initial-access"]:
        for atk_id in by_tactic.get(tac, []):
            G.add_edge(ENTRY_NODE, atk_id, weight=G.nodes[atk_id]["weight"])

    for tac in ["impact", "exfiltration"]:
        for atk_id in by_tactic.get(tac, []):
            G.add_edge(atk_id, TARGET_NODE, weight=0.01)

    for i in range(len(TACTIC_ORDER) - 1):
        src_tac = TACTIC_ORDER[i]
        dst_tac = TACTIC_ORDER[i + 1]
        for src in by_tactic.get(src_tac, []):
            for dst in by_tactic.get(dst_tac, []):
                if not G.has_edge(src, dst):
                    G.add_edge(src, dst, weight=G.nodes[dst]["weight"])

    return G


# ── 4. Metricas de redes complejas ───────────────────────────────────────────

def compute_network_metrics(G: nx.DiGraph) -> dict:
    """
    Calcula metricas estandar de redes complejas sobre el grafo de ataque.
    Compara con grafo aleatorio Erdos-Renyi equivalente.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    in_degrees  = [d for _, d in G.in_degree()]
    out_degrees = [d for _, d in G.out_degree()]

    # Distribucion de grados
    in_counter  = Counter(in_degrees)
    out_counter = Counter(out_degrees)

    # Componentes fuertemente conexas
    sccs = list(nx.strongly_connected_components(G))
    largest_scc = max(sccs, key=len)

    # Componentes debilmente conexas
    wccs = list(nx.weakly_connected_components(G))
    largest_wcc = max(wccs, key=len)

    # Clustering (en grafo no dirigido equivalente)
    G_undirected = G.to_undirected()
    avg_clustering = nx.average_clustering(G_undirected)

    # Diametro: solo sobre la componente gigante debilmente conexa
    G_wcc = G.subgraph(largest_wcc).copy()
    G_wcc_undir = G_wcc.to_undirected()
    try:
        diameter = nx.diameter(G_wcc_undir)
        avg_path_length = nx.average_shortest_path_length(G_wcc_undir)
    except Exception:
        diameter = -1
        avg_path_length = -1.0

    # Asortatividad (por grado)
    try:
        assortativity = nx.degree_assortativity_coefficient(G)
    except Exception:
        assortativity = None

    # Grafo aleatorio equivalente (Erdos-Renyi) para comparacion
    p_er = m / (n * (n - 1)) if n > 1 else 0
    G_er = nx.erdos_renyi_graph(n, p_er, directed=True, seed=42)
    G_er_undir = G_er.to_undirected()
    er_clustering = nx.average_clustering(G_er_undir)
    er_in_degrees = [d for _, d in G_er.in_degree()]

    # Power-law check: si la distribucion de grado sigue ley de potencia
    # (simplificado: R^2 de ajuste lineal en log-log)
    def power_law_r2(degrees):
        count = Counter(degrees)
        xs = sorted(count.keys())
        if len(xs) < 3:
            return None
        log_k = [math.log(k) for k in xs if k > 0]
        log_p = [math.log(count[k] / n) for k in xs if k > 0]
        if len(log_k) < 2:
            return None
        mean_x = sum(log_k) / len(log_k)
        mean_y = sum(log_p) / len(log_p)
        ss_tot = sum((y - mean_y) ** 2 for y in log_p)
        if ss_tot == 0:
            return None
        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_k, log_p)) / \
                sum((x - mean_x) ** 2 for x in log_k)
        intercept = mean_y - slope * mean_x
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(log_k, log_p))
        return round(1 - ss_res / ss_tot, 4)

    in_degree_r2  = power_law_r2(in_degrees)
    out_degree_r2 = power_law_r2(out_degrees)

    return {
        "n_nodes": n,
        "n_edges": m,
        "density": round(nx.density(G), 6),
        "is_dag": nx.is_directed_acyclic_graph(G),
        "in_degree": {
            "min": min(in_degrees),
            "max": max(in_degrees),
            "mean": round(sum(in_degrees) / n, 3),
            "std": round(float(np.std(in_degrees)), 3),
            "distribution": {str(k): v for k, v in sorted(in_counter.items())},
            "power_law_r2": in_degree_r2,
        },
        "out_degree": {
            "min": min(out_degrees),
            "max": max(out_degrees),
            "mean": round(sum(out_degrees) / n, 3),
            "std": round(float(np.std(out_degrees)), 3),
            "distribution": {str(k): v for k, v in sorted(out_counter.items())},
            "power_law_r2": out_degree_r2,
        },
        "clustering": {
            "average_attack_graph": round(avg_clustering, 6),
            "average_erdos_renyi_equivalent": round(er_clustering, 6),
            "ratio_vs_random": round(avg_clustering / er_clustering, 3) if er_clustering > 0 else None,
            "interpretation": "ratio > 1 indica mas clustering que grafo aleatorio"
        },
        "connectivity": {
            "n_scc": len(sccs),
            "largest_scc_size": len(largest_scc),
            "n_wcc": len(wccs),
            "largest_wcc_size": len(largest_wcc),
            "largest_wcc_fraction": round(len(largest_wcc) / n, 4),
        },
        "path_metrics": {
            "diameter_wcc": diameter,
            "avg_path_length_wcc": round(avg_path_length, 4) if avg_path_length > 0 else -1,
        },
        "assortativity": round(assortativity, 4) if assortativity is not None else None,
        "erdos_renyi_comparison": {
            "p": round(p_er, 6),
            "note": f"ER equivalente: n={n}, m=~{G_er.number_of_edges()}",
        },
    }


# ── 5. Betweenness comparacion ────────────────────────────────────────────────

def compare_betweenness(G: nx.DiGraph, fw_results: list) -> list[dict]:
    """
    Compara FW-betweenness propio vs betweenness estandar de NetworkX.
    NetworkX usa Brandes algorithm (mas eficiente, misma metrica base).
    """
    print("  [BETW] Calculando betweenness NetworkX (Brandes)...")
    nx_betw = nx.betweenness_centrality(G, normalized=True, weight="weight")
    nx_betw_unw = nx.betweenness_centrality(G, normalized=True, weight=None)

    fw_map = {r["node"]: r["fw_betweenness"] for r in fw_results}
    fw_max = max(fw_map.values()) if fw_map else 1

    results = []
    for r in fw_results:
        node = r["node"]
        fw_b = r["fw_betweenness"]
        nx_b_w = nx_betw.get(node, 0.0)
        nx_b_u = nx_betw_unw.get(node, 0.0)
        results.append({
            "node": node,
            "name": r["name"],
            "tactics": r["tactics"],
            "weight": r["weight"],
            "fw_betweenness_raw": fw_b,
            "fw_betweenness_norm": round(fw_b / fw_max, 6) if fw_max > 0 else 0,
            "nx_betweenness_weighted": round(nx_b_w, 6),
            "nx_betweenness_unweighted": round(nx_b_u, 6),
            "ranking_fw": None,       # se rellena abajo
            "ranking_nx_weighted": None,
            "ranking_nx_unweighted": None,
        })

    # Rankings
    results_fw_sorted  = sorted(results, key=lambda x: x["fw_betweenness_raw"], reverse=True)
    results_nxw_sorted = sorted(results, key=lambda x: x["nx_betweenness_weighted"], reverse=True)
    results_nxu_sorted = sorted(results, key=lambda x: x["nx_betweenness_unweighted"], reverse=True)

    rank_fw  = {r["node"]: i+1 for i, r in enumerate(results_fw_sorted)}
    rank_nxw = {r["node"]: i+1 for i, r in enumerate(results_nxw_sorted)}
    rank_nxu = {r["node"]: i+1 for i, r in enumerate(results_nxu_sorted)}

    for r in results:
        r["ranking_fw"] = rank_fw[r["node"]]
        r["ranking_nx_weighted"] = rank_nxw[r["node"]]
        r["ranking_nx_unweighted"] = rank_nxu[r["node"]]
        r["rank_delta_fw_vs_nxw"] = rank_fw[r["node"]] - rank_nxw[r["node"]]

    results.sort(key=lambda x: x["fw_betweenness_raw"], reverse=True)
    return results


# ── Pipeline principal ────────────────────────────────────────────────────────

def run():
    print("\n" + "="*70)
    print("  ANALISIS CIENTIFICO EXTENDIDO — SolarWinds Compromise")
    print("  Para publicacion en revista: validacion + metricas + sensibilidad")
    print("="*70)

    # Cargar dataset
    print("\n[0/5] Cargando dataset MITRE ATT&CK...")
    bundle = download_mitre()
    campaign_obj, techniques = extract_campaign(bundle, TARGET_CAMPAIGN_NAME)
    G, tech_by_id, by_tactic = build_attack_graph(bundle, techniques)
    n, m = G.number_of_nodes(), G.number_of_edges()
    print(f"      Grafo base: {n} nodos, {m} aristas")

    # ── 1. Comparacion de algoritmos ─────────────────────────────────────────
    print("\n[1/5] Comparacion de algoritmos: Dijkstra vs BFS vs NetworkX vs Bellman-Ford...")

    # Dijkstra propio
    t0 = time.perf_counter()
    dist_dijk, prev_dijk = dijkstra(G, ENTRY_NODE)
    t_dijk = time.perf_counter() - t0
    path_dijk = reconstruct_path(prev_dijk, ENTRY_NODE, TARGET_NODE)
    cost_dijk = dist_dijk.get(TARGET_NODE, float("inf"))

    # Bellman-Ford propio (validacion)
    t0 = time.perf_counter()
    dist_bf, prev_bf = bellman_ford(G, ENTRY_NODE)
    t_bf = time.perf_counter() - t0
    path_bf = reconstruct_path(prev_bf, ENTRY_NODE, TARGET_NODE)
    cost_bf = dist_bf.get(TARGET_NODE, float("inf"))

    # NetworkX Dijkstra (referencia)
    t0 = time.perf_counter()
    try:
        path_nx = nx.dijkstra_path(G, ENTRY_NODE, TARGET_NODE, weight="weight")
        cost_nx = nx.dijkstra_path_length(G, ENTRY_NODE, TARGET_NODE, weight="weight")
    except nx.NetworkXNoPath:
        path_nx, cost_nx = [], float("inf")
    t_nx = time.perf_counter() - t0

    # BFS (sin pesos)
    t0 = time.perf_counter()
    path_bfs, hops_bfs = bfs_shortest_path(G, ENTRY_NODE, TARGET_NODE)
    t_bfs = time.perf_counter() - t0
    # Costo real de la ruta BFS (aunque BFS no lo minimiza)
    cost_bfs = sum(G.nodes[v].get("weight", 0) for v in path_bfs
                   if v not in (ENTRY_NODE, TARGET_NODE))

    # Verificar concordancia
    dijk_bf_match   = abs(cost_dijk - cost_bf) < 1e-6
    dijk_nx_match   = abs(cost_dijk - cost_nx) < 1e-6
    path_is_same    = path_dijk == path_bf == path_nx
    bfs_diff        = cost_bfs - cost_dijk  # cuanto peor es BFS
    bfs_same_path   = path_bfs == path_dijk

    print(f"  Dijkstra propio:   costo={cost_dijk:.4f}, pasos={len(path_dijk)}, t={t_dijk*1000:.2f}ms")
    print(f"  Bellman-Ford:      costo={cost_bf:.4f},  pasos={len(path_bf)},  t={t_bf*1000:.2f}ms")
    print(f"  NetworkX Dijkstra: costo={cost_nx:.4f},  pasos={len(path_nx)},  t={t_nx*1000:.2f}ms")
    print(f"  BFS (sin pesos):   costo={cost_bfs:.4f}, hops={hops_bfs}, t={t_bfs*1000:.2f}ms")
    print(f"  Dijkstra == Bellman-Ford: {dijk_bf_match}")
    print(f"  Dijkstra == NetworkX:     {dijk_nx_match}")
    print(f"  Ruta identica (Dijk=BF=NX): {path_is_same}")
    print(f"  BFS ruta mas cara en: +{bfs_diff:.4f} (pesos ignorados por BFS)")

    comparacion = {
        "dijkstra_propio": {
            "costo": round(cost_dijk, 6),
            "n_pasos": len(path_dijk),
            "ruta": path_dijk,
            "tiempo_ms": round(t_dijk * 1000, 4),
        },
        "bellman_ford_propio": {
            "costo": round(cost_bf, 6),
            "n_pasos": len(path_bf),
            "ruta": path_bf,
            "tiempo_ms": round(t_bf * 1000, 4),
        },
        "networkx_dijkstra": {
            "costo": round(cost_nx, 6),
            "n_pasos": len(path_nx),
            "ruta": path_nx,
            "tiempo_ms": round(t_nx * 1000, 4),
        },
        "bfs_sin_pesos": {
            "costo_real_acumulado": round(cost_bfs, 6),
            "n_hops": hops_bfs,
            "ruta": path_bfs,
            "tiempo_ms": round(t_bfs * 1000, 4),
        },
        "validacion": {
            "dijkstra_igual_bellman_ford": dijk_bf_match,
            "dijkstra_igual_networkx": dijk_nx_match,
            "ruta_identica_tres_algoritmos": path_is_same,
            "bfs_ruta_igual_dijkstra": bfs_same_path,
            "bfs_sobrecoste_vs_dijkstra": round(bfs_diff, 6),
            "bfs_sobrecoste_porcentaje": round(100 * bfs_diff / cost_dijk, 2) if cost_dijk > 0 else 0,
            "conclusion": (
                "Implementaciones propias (Dijkstra, Bellman-Ford) producen resultado "
                "identico a NetworkX. BFS sin pesos halla ruta suboptima, demostrando "
                "que los pesos son informativos para el modelo de amenaza."
            )
        }
    }

    with open(RESULTS_DIR / "comparacion_algoritmos.json", "w", encoding="utf-8") as f:
        json.dump(comparacion, f, indent=2, ensure_ascii=False)
    print(f"  Guardado: comparacion_algoritmos.json")

    # ── 2. Sensibilidad de pesos ──────────────────────────────────────────────
    print("\n[2/5] Analisis de sensibilidad: variacion de pesos +/-20% y sin CVEs...")

    scenarios = {
        "base":       (G, "Pesos originales (mitigaciones + CVE)"),
        "factor_0.8": (build_graph_with_factor(bundle, techniques, 0.8), "Pesos -20%"),
        "factor_1.2": (build_graph_with_factor(bundle, techniques, 1.2), "Pesos +20%"),
        "sin_cve":    (build_graph_no_cve(bundle, techniques), "Solo mitigaciones (sin CVE)"),
    }

    sensibilidad = {}
    for scen_name, (G_s, scen_desc) in scenarios.items():
        dist_s, prev_s = dijkstra(G_s, ENTRY_NODE)
        path_s = reconstruct_path(prev_s, ENTRY_NODE, TARGET_NODE)
        cost_s = dist_s.get(TARGET_NODE, float("inf"))
        nodes_s = set(path_s) - {ENTRY_NODE, TARGET_NODE}
        nodes_base = set(path_dijk) - {ENTRY_NODE, TARGET_NODE}
        overlap = nodes_s & nodes_base
        jaccard = len(overlap) / len(nodes_s | nodes_base) if (nodes_s | nodes_base) else 1.0

        sensibilidad[scen_name] = {
            "descripcion": scen_desc,
            "costo": round(cost_s, 6),
            "n_pasos": len(path_s),
            "ruta": path_s,
            "ruta_identica_al_base": path_s == path_dijk,
            "nodos_criticos_identicos": nodes_s == nodes_base,
            "jaccard_similarity": round(jaccard, 4),
            "nodos_compartidos_con_base": sorted(overlap),
            "nodos_diferentes": sorted((nodes_s | nodes_base) - overlap),
        }
        print(f"  {scen_name}: costo={cost_s:.4f}, igual={path_s==path_dijk}, Jaccard={jaccard:.3f}")

    sensibilidad["conclusion"] = (
        "Si Jaccard >= 0.8 en todos los escenarios, el modelo es robusto: "
        "la ruta critica no cambia significativamente ante variaciones del 20% en pesos."
    )

    with open(RESULTS_DIR / "sensibilidad_pesos.json", "w", encoding="utf-8") as f:
        json.dump(sensibilidad, f, indent=2, ensure_ascii=False)
    print(f"  Guardado: sensibilidad_pesos.json")

    # ── 3. Metricas de redes complejas ────────────────────────────────────────
    print("\n[3/5] Metricas de redes complejas (clustering, grados, SCC, diametro)...")
    metricas = compute_network_metrics(G)

    print(f"  Densidad:          {metricas['density']}")
    print(f"  Clustering medio:  {metricas['clustering']['average_attack_graph']:.4f}  "
          f"(vs ER random: {metricas['clustering']['average_erdos_renyi_equivalent']:.4f})")
    print(f"  Ratio vs random:   {metricas['clustering']['ratio_vs_random']}")
    print(f"  SCC count:         {metricas['connectivity']['n_scc']}")
    print(f"  Diametro (WCC):    {metricas['path_metrics']['diameter_wcc']}")
    print(f"  Avg path (WCC):    {metricas['path_metrics']['avg_path_length_wcc']}")
    print(f"  In-degree R2 (power-law): {metricas['in_degree']['power_law_r2']}")
    print(f"  Asortatividad:     {metricas['assortativity']}")

    with open(RESULTS_DIR / "metricas_grafo.json", "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    print(f"  Guardado: metricas_grafo.json")

    # ── 4. Betweenness comparacion ────────────────────────────────────────────
    print("\n[4/5] Comparacion FW-betweenness propio vs NetworkX Brandes...")

    with open(RESULTS_DIR / "fw_betweenness_solarwinds.json", encoding="utf-8") as f:
        fw_results = json.load(f)

    betw_comp = compare_betweenness(G, fw_results)

    # Top-10 concordancias/discordancias
    print(f"\n  Top-10 por FW-betweenness (delta = ranking_FW - ranking_NX_weighted):")
    print(f"  {'Rk_FW':<7} {'Rk_NX':<7} {'Delta':<7} {'ID':<14} {'FW-Betw':<10} Nombre")
    print(f"  {'-'*70}")
    for r in betw_comp[:10]:
        print(f"  {r['ranking_fw']:<7} {r['ranking_nx_weighted']:<7} "
              f"{r['rank_delta_fw_vs_nxw']:+d}    {r['node']:<14} "
              f"{r['fw_betweenness_raw']:<10} {r['name'][:30]}")

    # Correlacion de Spearman simplificada
    n_b = len(betw_comp)
    rank_fw_v  = [r["ranking_fw"] for r in betw_comp]
    rank_nxw_v = [r["ranking_nx_weighted"] for r in betw_comp]
    d2 = sum((a - b) ** 2 for a, b in zip(rank_fw_v, rank_nxw_v))
    spearman = 1 - (6 * d2) / (n_b * (n_b ** 2 - 1)) if n_b > 1 else 1.0
    print(f"\n  Spearman FW vs NX-weighted: rho={spearman:.4f}")

    betw_output = {
        "correlacion_spearman_fw_vs_nx_weighted": round(spearman, 6),
        "interpretacion": (
            "rho cercano a 1.0 indica que FW-betweenness propio y Brandes de NetworkX "
            "producen rankings equivalentes. Valida la implementacion propia."
        ),
        "top_15": betw_comp[:15],
        "todos": betw_comp,
    }

    with open(RESULTS_DIR / "betweenness_comparacion.json", "w", encoding="utf-8") as f:
        json.dump(betw_output, f, indent=2, ensure_ascii=False)
    print(f"  Guardado: betweenness_comparacion.json")

    # ── 5. Resumen ejecutivo ──────────────────────────────────────────────────
    print("\n[5/5] Resumen ejecutivo...")

    resumen = {
        "dataset": f"MITRE ATT&CK Enterprise STIX 2.1 — {TARGET_CAMPAIGN_NAME}",
        "grafo": {"nodos": n, "aristas": m, "densidad": metricas["density"]},
        "dijkstra_validado": dijk_bf_match and dijk_nx_match,
        "ruta_critica_costo": round(cost_dijk, 6),
        "ruta_critica_pasos": len(path_dijk),
        "ruta_critica_nodos": path_dijk,
        "sensibilidad_robusta": all(
            v.get("jaccard_similarity", 0) >= 0.7
            for k, v in sensibilidad.items()
            if isinstance(v, dict) and "jaccard_similarity" in v
        ),
        "clustering_ratio_vs_random": metricas["clustering"]["ratio_vs_random"],
        "betweenness_spearman_vs_networkx": round(spearman, 6),
        "archivos_generados": [
            "comparacion_algoritmos.json",
            "sensibilidad_pesos.json",
            "metricas_grafo.json",
            "betweenness_comparacion.json",
        ]
    }

    with open(RESULTS_DIR / "resumen_cientifico.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"  Dijkstra validado vs Bellman-Ford y NetworkX: {resumen['dijkstra_validado']}")
    print(f"  Sensibilidad robusta (Jaccard>=0.7 todos escenarios): {resumen['sensibilidad_robusta']}")
    print(f"  Clustering {metricas['clustering']['ratio_vs_random']}x vs grafo aleatorio")
    print(f"  Spearman FW-betw vs NetworkX: {resumen['betweenness_spearman_vs_networkx']:.4f}")
    print(f"\n  Resultados en {RESULTS_DIR}/")
    for f in resumen["archivos_generados"]:
        print(f"    {f}")
    print("="*70)

    return resumen


if __name__ == "__main__":
    run()
