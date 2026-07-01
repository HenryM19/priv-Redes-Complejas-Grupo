"""
comparacion_campanas.py — Generalización del método: múltiples campañas ATT&CK.

Ejecuta el mismo pipeline Dijkstra + Floyd-Warshall sobre N campañas,
auto-seleccionadas del bundle STIX (ver select_campaigns / list_eligible_campaigns
en dataset_real.py) por un único criterio objetivo: número mínimo de técnicas
documentadas. Nada de lista curada a mano.

Modo legacy (--legacy3): reproduce las 3 campañas originales hardcodeadas
(SolarWinds, Operation Wocao, Operation Dream Job) para no invalidar los
números ya citados en el paper/slides.

Pregunta de investigación extendida:
  ¿La metodología produce resultados consistentes y diferenciados entre campañas
  de actores distintos con objetivos distintos?

Salida: results/real/comparacion_campanas.json (modo --legacy3)
        results/real/comparacion_campanas_N{n}.json (modo default, N campañas)
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
    list_eligible_campaigns,
    ENTRY_NODE,
    TARGET_NODE,
    TACTIC_ORDER,
)
from analisis_real import dijkstra, reconstruct_path, floyd_warshall, fw_betweenness

RESULTS_DIR = Path("results/real")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LEGACY_CAMPAIGNS = [
    ("SolarWinds Compromise",  "APT29",   "Espionaje EEUU — cadena suministro"),
    ("Operation Wocao",        "APT20",   "Espionaje Europa/Asia — sectores estratégicos"),
    ("Operation Dream Job",    "Lazarus", "Espionaje/cibercrimen — sector aeroespacial/defensa"),
]


def _resolve_actor_context(bundle: dict, campaign_id: str, campaign_obj: dict) -> tuple[str, str]:
    """
    Actor y contexto derivados 100% de campos STIX, sin curacion manual:
      - actor: nombre del intrusion-set atribuido via relacion 'attributed-to',
        si existe; si no, "no atribuido" (dato real: no hay atribucion documentada).
      - context: descripcion STIX de la campana (campo 'description'), truncada
        a 120 caracteres -- mismo patron usado para descripciones de tecnicas
        en build_attack_graph().
    """
    objects = bundle["objects"]
    id_map = {o["id"]: o for o in objects}

    actor = "no atribuido"
    for o in objects:
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "attributed-to"
                and o.get("source_ref") == campaign_id
                and o.get("target_ref", "").startswith("intrusion-set--")):
            intrusion_set = id_map.get(o["target_ref"])
            if intrusion_set:
                actor = intrusion_set.get("name", actor)
            break

    context = (campaign_obj.get("description", "") or "").strip().replace("\n", " ")[:120]
    if not context:
        context = "(sin descripcion STIX)"

    return actor, context


def select_campaigns(bundle: dict, n: int = 10, min_techniques: int = 10) -> list[tuple[str, str, str]]:
    """
    Selecciona las top-n campañas por número de técnicas (criterio objetivo,
    reproducible via list_eligible_campaigns). Resuelve actor/context desde
    campos STIX reales -- ver _resolve_actor_context.

    Retorna lista de (campaign_name, actor, context), mismo shape que
    LEGACY_CAMPAIGNS para reusar run_campaign() sin cambios.
    """
    eligible = list_eligible_campaigns(bundle, min_techniques=min_techniques)[:n]
    result = []
    for c in eligible:
        campaign_obj = next(o for o in bundle["objects"] if o["id"] == c["id"])
        actor, context = _resolve_actor_context(bundle, c["id"], campaign_obj)
        result.append((c["name"], actor, context))
    return result


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

    reachable = bool(ruta)
    empty_tactics = [tac for tac in TACTIC_ORDER if not by_tactic.get(tac)]

    elapsed = round((time.perf_counter() - t0)*1000, 2)

    print(f"     Costo ruta crítica: {costo}")
    if not reachable:
        print(f"     [DESCONEXION] ATTACKER->IMPACT no alcanzable. "
              f"Tacticas vacias: {empty_tactics}")
    if betw:
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
        "reachable": reachable,
        "empty_tactics": empty_tactics,
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

    reachable_results = [r for r in results if r.get("reachable", True)]
    n_unreachable = len(results) - len(reachable_results)
    if n_unreachable:
        print(f"     [AVISO] {n_unreachable}/{len(results)} campañas sin ruta ATTACKER->IMPACT "
              f"(tacticas intermedias vacias) — excluidas de metricas de costo/betweenness cruzadas.")

    # ¿Coincide el top-1 betweenness entre campañas? (solo alcanzables, con betweenness no vacio)
    top1_source = [r for r in reachable_results if r["fw_betweenness_top5"]]
    top1_nodes = [r["fw_betweenness_top5"][0]["node"] for r in top1_source]
    top1_names = [r["fw_betweenness_top5"][0]["name"] for r in top1_source]

    # ¿Comparten nodos en la ruta crítica? (solo alcanzables)
    rutas = [set(r["dijkstra"]["ruta"]) - {ENTRY_NODE, TARGET_NODE} for r in reachable_results]
    n = len(rutas)
    jaccard_matrix = {}
    for i in range(n):
        for j in range(i+1, n):
            inter = rutas[i] & rutas[j]
            union = rutas[i] | rutas[j]
            jac = round(len(inter)/len(union), 4) if union else 1.0
            key = f"{reachable_results[i]['campaign'][:20]} vs {reachable_results[j]['campaign'][:20]}"
            jaccard_matrix[key] = {"jaccard": jac, "nodos_comunes": sorted(inter)}
            print(f"     Jaccard [{reachable_results[i]['campaign'][:15]} vs {reachable_results[j]['campaign'][:15]}]: {jac:.3f} — comunes: {sorted(inter)}")

    # Táctica más representada en rutas críticas (¿hay patrón?) (solo alcanzables)
    tactic_freq: dict[str, int] = {}
    for r in reachable_results:
        for step in r["dijkstra"]["ruta_detalle"]:
            for tac in step["tactics"]:
                tactic_freq[tac] = tactic_freq.get(tac, 0) + 1

    tactic_sorted = sorted(tactic_freq.items(), key=lambda x: -x[1])

    # Costo promedio (solo alcanzables -- inf rompe el promedio)
    costos = [r["dijkstra"]["costo_minimo"] for r in reachable_results]
    avg_costo = round(sum(costos)/len(costos), 4) if costos else None

    # Resumen agregado de Jaccard (headline number para N grande, la matriz
    # completa se vuelve ilegible mas alla de ~5 campañas)
    jaccard_values = [v["jaccard"] for v in jaccard_matrix.values()]
    jaccard_summary = {
        "n_pares": len(jaccard_values),
        "media": round(sum(jaccard_values)/len(jaccard_values), 4) if jaccard_values else 0.0,
        "mediana": round(sorted(jaccard_values)[len(jaccard_values)//2], 4) if jaccard_values else 0.0,
        "min": round(min(jaccard_values), 4) if jaccard_values else 0.0,
        "max": round(max(jaccard_values), 4) if jaccard_values else 0.0,
    }
    print(f"\n  Jaccard resumen: media={jaccard_summary['media']} "
          f"min={jaccard_summary['min']} max={jaccard_summary['max']} "
          f"(sobre {jaccard_summary['n_pares']} pares)")

    return {
        "n_campanas_evaluadas": len(results),
        "n_campanas_alcanzables": len(reachable_results),
        "n_campanas_desconectadas": n_unreachable,
        "top1_betweenness_por_campana": [
            {"campaign": r["campaign"], "node": top1_nodes[i], "name": top1_names[i],
             "fw_betweenness": r["fw_betweenness_top5"][0]["fw_betweenness"]}
            for i, r in enumerate(top1_source)
        ],
        "jaccard_rutas_criticas": jaccard_matrix,
        "jaccard_summary": jaccard_summary,
        "tacticas_en_rutas_criticas": [{"tactica": t, "apariciones": c} for t, c in tactic_sorted],
        "costo_promedio": avg_costo,
        "costo_min": min(costos) if costos else None,
        "costo_max": max(costos) if costos else None,
        "conclusion": (
            "Jaccard bajo entre campañas indica que el método discrimina correctamente "
            "entre actores y campañas distintas. Tácticas con alta frecuencia en rutas "
            "críticas son candidatos a controles de seguridad universales. Campañas "
            "desconectadas (sin ruta ATTACKER->IMPACT) reflejan huecos reales en la "
            "cobertura tactica documentada de esa campana en el bundle STIX, no un "
            "defecto del metodo."
        )
    }


def run(campaigns: list[tuple[str, str, str]], out_name: str, header: str, bundle: dict | None = None):
    print("\n" + "="*70)
    print("  COMPARACIÓN MULTI-CAMPAÑA — Generalización del método")
    print(f"  {header}")
    print("="*70)

    if bundle is None:
        print("\n[0] Cargando bundle MITRE ATT&CK...")
        bundle = download_mitre()

    results = []
    for campaign_name, actor, context in campaigns:
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
            "técnicas por campaña → DiGraph con pesos (mitigaciones documentadas) → Dijkstra "
            "→ Floyd-Warshall betweenness. Los parámetros son idénticos; solo cambia "
            "la campaña de entrada."
        )
    }

    out_path = RESULTS_DIR / out_name
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("  Resumen ejecutivo:")
    for r in results:
        top1 = r["fw_betweenness_top5"][0]["node"] if r["fw_betweenness_top5"] else "(sin ruta)"
        print(f"    {r['campaign']:<30} nodos={r['n_nodes']}  costo={r['dijkstra']['costo_minimo']}  top1={top1}")
    if cross["tacticas_en_rutas_criticas"]:
        t0 = cross["tacticas_en_rutas_criticas"][0]
        print(f"\n  Táctica más frecuente en rutas críticas: {t0['tactica']} ({t0['apariciones']} campañas)")
    print(f"\n  Guardado: {out_path}")
    print("="*70)

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy3", action="store_true",
                         help="Reproduce las 3 campañas originales hardcodeadas")
    parser.add_argument("--n", type=int, default=10, help="Numero de campañas a auto-seleccionar")
    parser.add_argument("--min-techniques", type=int, default=10,
                         help="Umbral minimo de tecnicas para elegibilidad")
    args = parser.parse_args()

    if args.legacy3:
        run(LEGACY_CAMPAIGNS, "comparacion_campanas.json",
            "SolarWinds (APT29) · Operation Wocao (APT20) · Dream Job (Lazarus) [legacy]")
    else:
        bundle = download_mitre()
        campaigns = select_campaigns(bundle, n=args.n, min_techniques=args.min_techniques)
        run(campaigns, f"comparacion_campanas_N{args.n}.json",
            f"{args.n} campañas auto-seleccionadas (min_techniques={args.min_techniques})",
            bundle=bundle)
