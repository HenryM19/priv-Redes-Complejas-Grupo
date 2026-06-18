"""
dijkstra.py — Algoritmo de Dijkstra implementado desde cero, instrumentado
para animar la expansión paso a paso.

Sobre el grafo de ataque, Dijkstra encuentra el camino de MENOR resistencia
(suma mínima de w = 10−CVSS) desde el nodo externo hasta el activo crítico.
Ese camino = la secuencia de explotación más probable.

`dijkstra_steps` devuelve, además del resultado, una traza de cada iteración
(nodo extraído, frontera relajada, distancias) para el GIF.
"""

import heapq


def dijkstra_steps(graph, source, target):
    """
    Dijkstra con min-heap. Devuelve dict con:
      dist, prev, order (orden de finalización de nodos),
      steps (lista de snapshots para animación),
      path (lista de nodos source→target), cost (resistencia total).
    """
    dist = {n: float("inf") for n in graph.nodes}
    prev = {n: None for n in graph.nodes}
    dist[source] = 0.0
    visited = set()
    order = []
    steps = []

    pq = [(0.0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        order.append(u)

        relaxed = []
        for v in graph.successors(u):
            w = graph[u][v]["weight"]
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
                relaxed.append(v)

        steps.append({
            "current": u,
            "visited": set(visited),
            "frontier": [n for _, n in pq if n not in visited],
            "relaxed": relaxed,
            "dist": dict(dist),
        })

        if u == target:
            break

    # Reconstruir camino
    path = []
    if dist[target] < float("inf"):
        node = target
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()

    return {
        "dist": dist,
        "prev": prev,
        "order": order,
        "steps": steps,
        "path": path,
        "cost": dist[target],
    }


def path_edges(path):
    """Lista de aristas (u,v) del camino."""
    return list(zip(path[:-1], path[1:]))


def bottleneck_nodes(graph, source, target, top_k=3):
    """
    Nodos cuello de botella: por cuántos de los caminos más cortos pasan.
    Heurística: contar apariciones de cada nodo intermedio en los k caminos
    de menor costo (usando shortest simple paths por peso).
    """
    import networkx as nx
    counts = {}
    try:
        # generador de caminos simples ordenados aproximadamente por longitud;
        # los re-puntuamos por peso real y tomamos los mejores.
        paths = list(nx.shortest_simple_paths(graph, source, target, weight="weight"))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

    scored = []
    for p in paths[:12]:
        cost = sum(graph[u][v]["weight"] for u, v in zip(p[:-1], p[1:]))
        scored.append((cost, p))
    scored.sort(key=lambda x: x[0])

    k_paths = scored[: max(3, top_k * 2)]
    for _, p in k_paths:
        for n in p[1:-1]:  # excluir source y target
            counts[n] = counts.get(n, 0) + 1

    ranked = sorted(counts.items(), key=lambda x: -x[1])
    return ranked[:top_k]


def critical_path_report(graph, result):
    """Texto + tabla de la ruta crítica: cada salto con su CVE y CVSS."""
    rows = []
    for u, v in path_edges(result["path"]):
        e = graph[u][v]
        rows.append({
            "from": u, "to": v,
            "cve": e["cve"], "cvss": e["cvss"],
            "weight": e["weight"], "product": e["product"],
            "severity": e["severity"],
        })
    return rows


if __name__ == "__main__":
    from nvd_fetch import load_cves
    from attack_graph import build_attack_graph
    cves, _ = load_cves(use_live=False)
    G = build_attack_graph(cves)
    r = dijkstra_steps(G, "INTERNET", "DB-CRITICAL")
    print("Ruta crítica:", " → ".join(r["path"]))
    print("Resistencia total:", round(r["cost"], 2))
    print("Iteraciones Dijkstra:", len(r["steps"]))
    print("Cuellos de botella:", bottleneck_nodes(G, "INTERNET", "DB-CRITICAL"))
