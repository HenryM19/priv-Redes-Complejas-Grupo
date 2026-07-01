"""
recomendaciones_defensivas.py — Priorizacion de mitigaciones por impacto en el grafo.

Para cada tecnica de la ruta critica y top-5 betweenness:
  1. Simula "bloqueo" del nodo (elimina del grafo)
  2. Recalcula costo Dijkstra ATTACKER->IMPACT
  3. Mide: delta_costo = nuevo_costo - costo_original
     (cuanto sube el costo del atacante si se mitiga esa tecnica)
  4. Si no hay ruta tras el bloqueo: impacto = infinito (bloqueo total)

Salida: results/real/recomendaciones_defensivas.json
"""

import json
from pathlib import Path

import networkx as nx

from dataset_real import (
    download_mitre,
    extract_campaign,
    build_attack_graph,
    TARGET_CAMPAIGN_NAME,
    ENTRY_NODE,
    TARGET_NODE,
)
from analisis_real import dijkstra, reconstruct_path

RESULTS_DIR = Path("results/real")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def simulate_block(G: nx.DiGraph, node: str) -> tuple[float, list[str]]:
    """
    Simula bloqueo del nodo: elimina todos sus arcos entrantes y salientes.
    Recalcula Dijkstra en el grafo modificado.
    Retorna (nuevo_costo, nueva_ruta).
    """
    G2 = G.copy()
    G2.remove_node(node)
    dist, prev = dijkstra(G2, ENTRY_NODE)
    new_cost = dist.get(TARGET_NODE, float("inf"))
    new_path = reconstruct_path(prev, ENTRY_NODE, TARGET_NODE)
    return new_cost, new_path


def mitigation_priority(G: nx.DiGraph, candidates: list[str], base_cost: float, base_path: list[str]) -> list[dict]:
    """
    Para cada nodo candidato, simula bloqueo y calcula impacto defensivo.
    Candidatos = union de ruta critica y top-betweenness.
    """
    results = []
    for node in candidates:
        if node in (ENTRY_NODE, TARGET_NODE):
            continue

        new_cost, new_path = simulate_block(G, node)
        blocked = new_cost == float("inf") or not new_path

        if blocked:
            delta = float("inf")
            delta_pct = float("inf")
            new_cost_display = None
        else:
            delta = round(new_cost - base_cost, 4)
            delta_pct = round(100 * delta / base_cost, 2) if base_cost > 0 else 0
            new_cost_display = round(new_cost, 4)

        # Nodos en la nueva ruta que no estaban en la original (ruta alternativa)
        orig_set = set(base_path) - {ENTRY_NODE, TARGET_NODE}
        new_set  = set(new_path) - {ENTRY_NODE, TARGET_NODE}
        ruta_alternativa_nodos = sorted(new_set - orig_set)

        results.append({
            "node": node,
            "name": G.nodes[node].get("name", ""),
            "tactics": G.nodes[node].get("tactics", []),
            "weight": round(G.nodes[node].get("weight", 0), 3),
            "weight_source": G.nodes[node].get("weight_source", ""),
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
            "en_ruta_critica": node in base_path,
            "bloqueo_total": blocked,
            "costo_original": round(base_cost, 4),
            "costo_tras_bloqueo": new_cost_display,
            "delta_costo": round(delta, 4) if delta != float("inf") else None,
            "delta_porcentaje": delta_pct if delta_pct != float("inf") else None,
            "nueva_ruta": new_path if not blocked else [],
            "ruta_alternativa_nodos_nuevos": ruta_alternativa_nodos,
        })

    # Ordenar: bloqueos totales primero, luego por delta descendente
    results.sort(key=lambda x: (
        0 if x["bloqueo_total"] else 1,
        -(x["delta_costo"] or 0)
    ))
    return results


def run(edge_mode: str = "cartesian", weight_mode: str = "mitigations"):
    suffix = "" if (edge_mode == "cartesian" and weight_mode == "mitigations") \
        else f"_{edge_mode}_{weight_mode}"

    print("\n" + "="*65)
    print("  RECOMENDACIONES DEFENSIVAS — SolarWinds Compromise")
    print("  Priorizacion por impacto en costo del atacante")
    print("="*65)

    print("\n[1/3] Cargando dataset y construyendo grafo...")
    bundle = download_mitre()
    campaign_obj, techniques = extract_campaign(bundle, TARGET_CAMPAIGN_NAME)
    G, tech_by_id, by_tactic = build_attack_graph(
        bundle, techniques, campaign=campaign_obj,
        edge_mode=edge_mode, weight_mode=weight_mode,
    )

    print("\n[2/3] Dijkstra base y FW-betweenness...")
    dist, prev = dijkstra(G, ENTRY_NODE)
    base_path = reconstruct_path(prev, ENTRY_NODE, TARGET_NODE)
    base_cost = round(dist.get(TARGET_NODE, float("inf")), 4)

    # Cargar betweenness pre-calculado (mismo modo, debe existir de un run previo de analisis_real.py)
    with open(RESULTS_DIR / f"fw_betweenness_solarwinds{suffix}.json", encoding="utf-8") as f:
        betw_data = json.load(f)
    top_betw = [b["node"] for b in betw_data[:10]]

    # Candidatos = union ruta critica + top-10 betweenness
    candidates_set = (set(base_path) | set(top_betw)) - {ENTRY_NODE, TARGET_NODE}
    candidates = sorted(candidates_set)
    print(f"     Base: costo={base_cost}, pasos={len(base_path)}")
    print(f"     Candidatos a evaluar: {len(candidates)} nodos")

    print("\n[3/3] Simulando bloqueos...")
    priority = mitigation_priority(G, candidates, base_cost, base_path)

    print(f"\n  {'Rk':<4} {'ID':<14} {'Bloqueo':<9} {'Delta costo':<14} {'Delta %':<10} Nombre")
    print(f"  {'-'*75}")
    for i, p in enumerate(priority[:15]):
        blk = "TOTAL" if p["bloqueo_total"] else ""
        delta = "inf" if p["delta_costo"] is None else f"+{p['delta_costo']:.4f}"
        pct   = "inf" if p["delta_porcentaje"] is None else f"+{p['delta_porcentaje']:.1f}%"
        print(f"  {i+1:<4} {p['node']:<14} {blk:<9} {delta:<14} {pct:<10} {p['name'][:30]}")

    # Generar recomendaciones priorizadas en lenguaje natural
    recomendaciones = []
    for i, p in enumerate(priority):
        if p["bloqueo_total"]:
            accion = f"Bloquear {p['node']} elimina toda ruta ATTACKER->IMPACT. Impacto maxximo."
            prioridad = "CRITICA"
        elif p["delta_costo"] and p["delta_costo"] > 0.5:
            accion = f"Mitigar {p['node']} sube el costo en +{p['delta_costo']:.3f} ({p['delta_porcentaje']:.1f}%). Ruta alternativa pasa por: {', '.join(p['ruta_alternativa_nodos_nuevos'][:3]) or 'ninguno nuevo'}."
            prioridad = "ALTA"
        elif p["delta_costo"] and p["delta_costo"] > 0.1:
            accion = f"Mitigar {p['node']} incrementa resistencia en +{p['delta_costo']:.3f} ({p['delta_porcentaje']:.1f}%)."
            prioridad = "MEDIA"
        else:
            accion = f"Impacto bajo: el atacante re-enruta con costo similar."
            prioridad = "BAJA"

        recomendaciones.append({
            "ranking": i + 1,
            "prioridad": prioridad,
            "node": p["node"],
            "name": p["name"],
            "tactics": p["tactics"],
            "accion_recomendada": accion,
            "metricas": {
                "costo_original": p["costo_original"],
                "costo_tras_bloqueo": p["costo_tras_bloqueo"],
                "delta_costo": p["delta_costo"],
                "delta_porcentaje": p["delta_porcentaje"],
                "bloqueo_total": p["bloqueo_total"],
                "en_ruta_critica": p["en_ruta_critica"],
                "in_degree": p["in_degree"],
                "out_degree": p["out_degree"],
                "weight": p["weight"],
                "weight_source": p["weight_source"],
            },
            "ruta_alternativa_tras_bloqueo": p["nueva_ruta"],
        })

    output = {
        "campana": TARGET_CAMPAIGN_NAME,
        "costo_base": base_cost,
        "ruta_critica_base": base_path,
        "n_candidatos_evaluados": len(candidates),
        "recomendaciones": recomendaciones,
        "resumen_ejecutivo": {
            "bloqueos_totales": sum(1 for r in recomendaciones if r["metricas"]["bloqueo_total"]),
            "impacto_alto": sum(1 for r in recomendaciones if r["prioridad"] == "ALTA"),
            "impacto_medio": sum(1 for r in recomendaciones if r["prioridad"] == "MEDIA"),
            "top3_recomendados": [r["node"] for r in recomendaciones[:3]],
            "metodologia": (
                "Para cada tecnica candidata, se elimina del grafo y se recalcula "
                "Dijkstra. El delta de costo mide cuanto mas caro se vuelve el ataque "
                "para el adversario. Bloqueo total = no existe ruta ATTACKER->IMPACT."
            )
        }
    }

    out_path = RESULTS_DIR / f"recomendaciones_defensivas{suffix}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*65}")
    print(f"  Bloqueos totales: {output['resumen_ejecutivo']['bloqueos_totales']}")
    print(f"  Top-3 a mitigar: {output['resumen_ejecutivo']['top3_recomendados']}")
    print(f"  Guardado: {out_path}")
    print("="*65)

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--edge-mode", choices=["cartesian", "cooccurrence"], default="cartesian")
    parser.add_argument("--weight-mode", choices=["mitigations", "combined"], default="mitigations")
    args = parser.parse_args()
    run(edge_mode=args.edge_mode, weight_mode=args.weight_mode)
