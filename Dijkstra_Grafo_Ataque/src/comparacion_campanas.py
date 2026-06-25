"""
comparacion_campanas.py — Generalización del método: múltiples campañas ATT&CK.

Ejecuta el mismo pipeline Dijkstra + Floyd-Warshall sobre 3 campañas:
  1. SolarWinds Compromise  (APT29, 71 técnicas) — caso de estudio principal
  2. Operation Wocao        (APT20, 70 técnicas) — espionaje chino
  3. Operation Dream Job    (Lazarus, 55 técnicas) — cibercrimen / espionaje NK

Pregunta de investigación extendida:
  ¿La metodología produce resultados consistentes y diferenciados entre campañas
  de actores distintos con objetivos distintos?

Salida: results/real/comparacion_campanas.json
"""

import json
import time
from pathlib import Path

import networkx as nx

from dataset_real import (
    download_mitre,
    extract_campaign,
    build_attack_graph,
    graph_summary,
    ENTRY_NODE,
    TARGET_NODE,
    TACTIC_ORDER,
)
from analisis_real import dijkstra, reconstruct_path, floyd_warshall, fw_betweenness

RESULTS_DIR = Path("results/real")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CAMPAIGNS = [
    ("SolarWinds Compromise",  "APT29",   "Espionaje EEUU — cadena suministro"),
    ("Operation Wocao",        "APT20",   "Espionaje Europa/Asia — sectores estratégicos"),
    ("Operation Dream Job",    "Lazarus", "Espionaje/cibercrimen — sector aeroespacial/defensa"),
]


def run_campaign(bundle: dict, campaign_name: str) -> dict:
    """Pipeline completo para una campaña. Retorna dict con todos los resultados."""
    print(f"\n  [{campaign_name}]")

    t0 = time.perf_counter()
    campaign_obj, techniques = extract_campaign(bundle, campaign_name)
    G, tech_by_id, by_tactic = build_attack_graph(bundle, techniques)
    s = graph_summary(G, campaign_name)
    print(f"     Nodos={s['n_nodes']}, Aristas={s['n_edges']}, DAG={s['is_dag']}")

    # Dijkstra
    dist, prev = dijkstra(G, ENTRY_NODE)
    ruta = reconstruct_path(prev, ENTRY_NODE, TARGET_NODE)
    costo = round(dist.get(TARGET_NODE, float("inf")), 4)

    # Floyd-Warshall + betweenness
    import numpy as np
    fw_dist, fw_nodes, fw_idx = floyd_warshall(G)
    betw = fw_betweenness(fw_dist, fw_nodes, fw_idx, G)

    # Tácticas en la ruta crítica
    ruta_tactics = []
    for node in ruta:
        if node in (ENTRY_NODE, TARGET_NODE):
            continue
        tacs = G.nodes[node].get("tactics", [])
        ruta_tactics.append({"node": node, "name": G.nodes[node].get("name",""), "tactics": tacs, "weight": round(G.nodes[node].get("weight",0),3)})

    # Técnicas por táctica
    by_tac_counts = {tac: len(nodes) for tac, nodes in by_tactic.items() if nodes}

    # Peso medio
    weights = [G.nodes[n].get("weight",0) for n in G.nodes() if n not in (ENTRY_NODE, TARGET_NODE)]
    avg_weight = round(sum(weights)/len(weights),4) if weights else 0

    elapsed = round((time.perf_counter() - t0)*1000, 2)

    print(f"     Costo ruta crítica: {costo}")
    print(f"     Top-1 betweenness: {betw[0]['node']} ({betw[0]['fw_betweenness']})")
    print(f"     Tiempo total: {elapsed} ms")

    return {
        "campaign": campaign_name,
        "n_nodes": s["n_nodes"],
        "n_edges": s["n_edges"],
        "density": s["density"],
        "is_dag": s["is_dag"],
        "n_techniques": s["n_techniques"],
        "avg_weight": avg_weight,
        "by_tactic_counts": by_tac_counts,
        "dijkstra": {
            "costo_minimo": costo,
            "n_pasos": len(ruta),
            "ruta": ruta,
            "ruta_detalle": ruta_tactics,
        },
        "fw_betweenness_top5": betw[:5],
        "tiempo_ms": elapsed,
    }


def cross_compare(results: list[dict]) -> dict:
    """Compara resultados entre campañas."""
    print("\n  [Analisis cruzado]")

    # ¿Coincide el top-1 betweenness entre campañas?
    top1_nodes = [r["fw_betweenness_top5"][0]["node"] for r in results]
    top1_names = [r["fw_betweenness_top5"][0]["name"] for r in results]

    # ¿Comparten nodos en la ruta crítica?
    rutas = [set(r["dijkstra"]["ruta"]) - {ENTRY_NODE, TARGET_NODE} for r in results]
    n = len(rutas)
    jaccard_matrix = {}
    for i in range(n):
        for j in range(i+1, n):
            inter = rutas[i] & rutas[j]
            union = rutas[i] | rutas[j]
            jac = round(len(inter)/len(union), 4) if union else 1.0
            key = f"{results[i]['campaign'][:20]} vs {results[j]['campaign'][:20]}"
            jaccard_matrix[key] = {"jaccard": jac, "nodos_comunes": sorted(inter)}
            print(f"     Jaccard [{results[i]['campaign'][:15]} vs {results[j]['campaign'][:15]}]: {jac:.3f} — comunes: {sorted(inter)}")

    # Táctica más representada en rutas críticas (¿hay patrón?)
    tactic_freq: dict[str, int] = {}
    for r in results:
        for step in r["dijkstra"]["ruta_detalle"]:
            for tac in step["tactics"]:
                tactic_freq[tac] = tactic_freq.get(tac, 0) + 1

    tactic_sorted = sorted(tactic_freq.items(), key=lambda x: -x[1])

    # Costo promedio
    costos = [r["dijkstra"]["costo_minimo"] for r in results]
    avg_costo = round(sum(costos)/len(costos), 4)

    return {
        "top1_betweenness_por_campana": [
            {"campaign": r["campaign"], "node": top1_nodes[i], "name": top1_names[i],
             "fw_betweenness": r["fw_betweenness_top5"][0]["fw_betweenness"]}
            for i, r in enumerate(results)
        ],
        "jaccard_rutas_criticas": jaccard_matrix,
        "tacticas_en_rutas_criticas": [{"tactica": t, "apariciones": c} for t, c in tactic_sorted],
        "costo_promedio": avg_costo,
        "costo_min": min(costos),
        "costo_max": max(costos),
        "conclusion": (
            "Jaccard bajo entre campañas indica que el método discrimina correctamente "
            "entre actores y campañas distintas. Tácticas con alta frecuencia en rutas "
            "críticas son candidatos a controles de seguridad universales."
        )
    }


def run():
    print("\n" + "="*70)
    print("  COMPARACIÓN MULTI-CAMPAÑA — Generalización del método")
    print("  SolarWinds (APT29) · Operation Wocao (APT20) · Dream Job (Lazarus)")
    print("="*70)

    print("\n[0] Cargando bundle MITRE ATT&CK...")
    bundle = download_mitre()

    results = []
    for campaign_name, actor, context in CAMPAIGNS:
        print(f"\n[Campaña] {campaign_name} — {actor} — {context}")
        try:
            r = run_campaign(bundle, campaign_name)
            r["actor"] = actor
            r["context"] = context
            results.append(r)
        except Exception as e:
            print(f"  [ERROR] {campaign_name}: {e}")

    print("\n[Cross-compare]")
    cross = cross_compare(results)

    output = {
        "campanas": results,
        "comparacion_cruzada": cross,
        "metodologia": (
            "Mismo pipeline en todas las campañas: bundle STIX 2.1 → extracción de "
            "técnicas por campaña → DiGraph con pesos (mitigaciones + CVE) → Dijkstra "
            "→ Floyd-Warshall betweenness. Los parámetros son idénticos; solo cambia "
            "la campaña de entrada."
        )
    }

    out_path = RESULTS_DIR / "comparacion_campanas.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("  Resumen ejecutivo:")
    for r in results:
        print(f"    {r['campaign']:<30} nodos={r['n_nodes']}  costo={r['dijkstra']['costo_minimo']}  top1={r['fw_betweenness_top5'][0]['node']}")
    print(f"\n  Jaccard entre campañas:")
    for k, v in cross["jaccard_rutas_criticas"].items():
        print(f"    {k}: {v['jaccard']:.3f}")
    print(f"\n  Táctica más frecuente en rutas críticas: {cross['tacticas_en_rutas_criticas'][0]['tactica']} ({cross['tacticas_en_rutas_criticas'][0]['apariciones']} campañas)")
    print(f"\n  Guardado: {out_path}")
    print("="*70)


if __name__ == "__main__":
    run()
