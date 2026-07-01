"""
dataset_edges_comparacion.py — Comparacion honesta: aristas cartesianas vs
co-ocurrencia real, sobre la(s) misma(s) campana(s).

Pregunta: ¿cuanto infla el supuesto cartesiano (cross-product entre tacticas
consecutivas) el numero de aristas frente a lo que un actor real documentado
efectivamente conecto? ¿Sobrevive la ruta critica al cambiar de modo?

Salida: results/real/comparacion_modos_aristas.json
"""

import json
from pathlib import Path

from dataset_real import (
    download_mitre,
    extract_campaign,
    build_attack_graph,
    graph_summary,
    TARGET_CAMPAIGN_NAME,
    ENTRY_NODE,
    TARGET_NODE,
)
from analisis_real import dijkstra, reconstruct_path

RESULTS_DIR = Path("results/real")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CAMPAIGNS = [
    "SolarWinds Compromise",
    "Operation Wocao",
    "Operation Dream Job",
]


def compare_edge_modes(bundle: dict, campaign_name: str) -> dict:
    """
    Construye el grafo de una campana en ambos modos de aristas y compara
    Dijkstra sobre cada uno. Reporta reduccion de aristas, alcanzabilidad,
    y si es alcanzable en ambos, costo/ruta lado a lado.
    """
    campaign_obj, techniques = extract_campaign(bundle, campaign_name)

    G_cart, _, _ = build_attack_graph(bundle, techniques, edge_mode="cartesian")
    s_cart = graph_summary(G_cart, campaign_name)

    G_cooc, _, _ = build_attack_graph(
        bundle, techniques, campaign=campaign_obj, edge_mode="cooccurrence"
    )
    s_cooc = graph_summary(G_cooc, campaign_name)

    dist_cart, prev_cart = dijkstra(G_cart, ENTRY_NODE)
    ruta_cart = reconstruct_path(prev_cart, ENTRY_NODE, TARGET_NODE)
    costo_cart = round(dist_cart.get(TARGET_NODE, float("inf")), 4)

    dist_cooc, prev_cooc = dijkstra(G_cooc, ENTRY_NODE)
    ruta_cooc = reconstruct_path(prev_cooc, ENTRY_NODE, TARGET_NODE)
    costo_cooc = round(dist_cooc.get(TARGET_NODE, float("inf")), 4)

    reachable_cooc = bool(ruta_cooc)
    reduction_pct = round(
        100 * (1 - s_cooc["n_edges"] / s_cart["n_edges"]), 2
    ) if s_cart["n_edges"] else 0.0

    result = {
        "campaign": campaign_name,
        "n_edges_cartesian": s_cart["n_edges"],
        "n_edges_cooccurrence": s_cooc["n_edges"],
        "edge_reduction_pct": reduction_pct,
        "cooccurrence_stats": s_cooc.get("edge_construction_stats", {}),
        "reachable_in_cooccurrence": reachable_cooc,
    }

    if reachable_cooc:
        orig_set = set(ruta_cart) - {ENTRY_NODE, TARGET_NODE}
        new_set = set(ruta_cooc) - {ENTRY_NODE, TARGET_NODE}
        inter = orig_set & new_set
        union = orig_set | new_set
        jaccard = round(len(inter) / len(union), 4) if union else 1.0
        result.update({
            "costo_cartesian": costo_cart,
            "costo_cooccurrence": costo_cooc,
            "ruta_cartesian": ruta_cart,
            "ruta_cooccurrence": ruta_cooc,
            "jaccard_rutas": jaccard,
        })
    else:
        stats = s_cooc.get("edge_construction_stats", {})
        isolated = stats.get("isolated_techniques", [])
        # Diagnostico: a que tactica pertenecen las tecnicas aisladas
        isolated_detail = [
            {"node": n, "tactics": G_cooc.nodes[n].get("tactics", [])}
            for n in isolated if n in G_cooc.nodes
        ]
        result.update({
            "costo_cartesian": costo_cart,
            "ruta_cartesian": ruta_cart,
            "diagnostico_desconexion": {
                "n_techniques_isolated": stats.get("n_techniques_isolated", 0),
                "isolated_techniques_detail": isolated_detail[:20],
            },
        })

    return result


def run(campaigns: list[str] | None = None):
    campaigns = campaigns or DEFAULT_CAMPAIGNS

    print("\n" + "=" * 70)
    print("  COMPARACION DE MODOS DE ARISTAS — cartesiano vs co-ocurrencia real")
    print("=" * 70)

    bundle = download_mitre()

    results = []
    for name in campaigns:
        print(f"\n[Campana] {name}")
        try:
            r = compare_edge_modes(bundle, name)
            results.append(r)
            print(f"     Aristas: cartesiano={r['n_edges_cartesian']} "
                  f"co-ocurrencia={r['n_edges_cooccurrence']} "
                  f"({r['edge_reduction_pct']:+.2f}% vs cartesiano)")
            if r["reachable_in_cooccurrence"]:
                print(f"     Alcanzable en ambos modos. "
                      f"Costo cart={r['costo_cartesian']} cooc={r['costo_cooccurrence']} "
                      f"Jaccard rutas={r['jaccard_rutas']}")
            else:
                print(f"     [DESCONEXION] co-ocurrencia no llega a IMPACT. "
                      f"Tecnicas aisladas: {r['diagnostico_desconexion']['n_techniques_isolated']}")
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")

    n_reachable = sum(1 for r in results if r["reachable_in_cooccurrence"])
    reachability_rate = round(n_reachable / len(results), 4) if results else 0.0

    output = {
        "campanas_evaluadas": results,
        "resumen": {
            "n_campanas": len(results),
            "n_alcanzables_en_cooccurrence": n_reachable,
            "tasa_alcanzabilidad": reachability_rate,
            "conclusion": (
                "El modo co-ocurrencia usa solo aristas respaldadas por un actor real "
                "documentado (malware/tool/intrusion-set) que uso ambas tecnicas, en vez "
                "del cross-product completo entre tacticas consecutivas. Esto reduce "
                "sustancialmente el numero de aristas pero puede dejar la campana "
                "desconectada si ningun actor documentado conecta ciertas tecnicas -- "
                "un hallazgo honesto sobre los limites de granularidad del dataset STIX, "
                "no un defecto del metodo."
            ),
        },
    }

    out_path = RESULTS_DIR / "comparacion_modos_aristas.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"  Tasa de alcanzabilidad en modo co-ocurrencia: "
          f"{n_reachable}/{len(results)} ({reachability_rate*100:.1f}%)")
    print(f"  Guardado: {out_path}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaigns", nargs="*", default=None,
                         help="Lista de nombres de campana (default: 3 legacy)")
    args = parser.parse_args()
    run(campaigns=args.campaigns)
