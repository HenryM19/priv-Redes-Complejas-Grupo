"""
analisis_pesos_finos.py — Comparacion pesos "solo mitigaciones" vs "combinado"
(mitigaciones + deteccion).

Pregunta: ¿cuanto reduce el modelo combinado (compute_weight_v2) el problema
de empates documentado en ESTADO_PROYECTO.md (Limitacion L4)? ¿Sobrevive la
ruta critica y el ranking de betweenness al cambiar de modelo?

Salida: results/real/comparacion_pesos_finos.json
"""

import json
from collections import Counter
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
from analisis_real import dijkstra, reconstruct_path, floyd_warshall, fw_betweenness

RESULTS_DIR = Path("results/real")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def count_ties(weights: list[float]) -> dict:
    """
    Cuenta valores de peso duplicados en una lista de pesos de nodo.
    Metrica directa de granularidad: mas valores unicos = menos empates =
    Dijkstra/Floyd-Warshall tienen menos ambiguedad al elegir entre rutas
    de "igual" costo.
    """
    freq = Counter(weights)
    n_values = len(weights)
    n_unique = len(freq)
    n_tied = sum(c for c in freq.values() if c > 1)  # valores que SI se repiten
    return {
        "n_valores": n_values,
        "n_valores_unicos": n_unique,
        "n_valores_en_empate": n_tied,
        "distribucion_frecuencia": sorted(
            [{"peso": round(w, 3), "n_tecnicas": c} for w, c in freq.items()],
            key=lambda x: -x["n_tecnicas"],
        ),
    }


def _spearman(rank_a: list[int], rank_b: list[int]) -> float:
    n = len(rank_a)
    if n <= 1:
        return 1.0
    d2 = sum((a - b) ** 2 for a, b in zip(rank_a, rank_b))
    return 1 - (6 * d2) / (n * (n ** 2 - 1))


def run(campaign_name: str = TARGET_CAMPAIGN_NAME) -> dict:
    print("\n" + "=" * 70)
    print("  COMPARACION DE PESOS — solo mitigaciones vs combinado (mit+deteccion)")
    print("=" * 70)

    bundle = download_mitre()
    campaign_obj, techniques = extract_campaign(bundle, campaign_name)

    G_mit, _, _ = build_attack_graph(
        bundle, techniques, campaign=campaign_obj, weight_mode="mitigations"
    )
    G_comb, _, _ = build_attack_graph(
        bundle, techniques, campaign=campaign_obj, weight_mode="combined"
    )

    weights_mit = [
        G_mit.nodes[n]["weight"] for n in G_mit.nodes()
        if n not in (ENTRY_NODE, TARGET_NODE)
    ]
    weights_comb = [
        G_comb.nodes[n]["weight"] for n in G_comb.nodes()
        if n not in (ENTRY_NODE, TARGET_NODE)
    ]

    ties_mit = count_ties(weights_mit)
    ties_comb = count_ties(weights_comb)
    reduccion_pct = round(
        100 * (1 - ties_comb["n_valores_en_empate"] / ties_mit["n_valores_en_empate"]), 2
    ) if ties_mit["n_valores_en_empate"] else 0.0

    print(f"\n  Empates (solo mitigaciones): {ties_mit['n_valores_en_empate']}/{ties_mit['n_valores']} "
          f"tecnicas comparten peso con otra ({ties_mit['n_valores_unicos']} valores unicos)")
    print(f"  Empates (combinado):         {ties_comb['n_valores_en_empate']}/{ties_comb['n_valores']} "
          f"tecnicas comparten peso con otra ({ties_comb['n_valores_unicos']} valores unicos)")
    print(f"  Reduccion de empates: {reduccion_pct:+.2f}%")

    # Dijkstra en ambos modelos
    dist_mit, prev_mit = dijkstra(G_mit, ENTRY_NODE)
    ruta_mit = reconstruct_path(prev_mit, ENTRY_NODE, TARGET_NODE)
    costo_mit = round(dist_mit.get(TARGET_NODE, float("inf")), 4)

    dist_comb, prev_comb = dijkstra(G_comb, ENTRY_NODE)
    ruta_comb = reconstruct_path(prev_comb, ENTRY_NODE, TARGET_NODE)
    costo_comb = round(dist_comb.get(TARGET_NODE, float("inf")), 4)

    orig_set = set(ruta_mit) - {ENTRY_NODE, TARGET_NODE}
    new_set = set(ruta_comb) - {ENTRY_NODE, TARGET_NODE}
    inter = orig_set & new_set
    union = orig_set | new_set
    jaccard_ruta = round(len(inter) / len(union), 4) if union else 1.0
    ruta_identica = ruta_mit == ruta_comb

    print(f"\n  Costo ruta critica: mitigaciones={costo_mit}  combinado={costo_comb}")
    print(f"  Ruta identica: {ruta_identica}  (Jaccard nodos: {jaccard_ruta})")

    # Betweenness en ambos modelos, comparar ranking
    fw_dist_mit, nodes_mit, idx_mit = floyd_warshall(G_mit)
    betw_mit = fw_betweenness(fw_dist_mit, nodes_mit, idx_mit, G_mit)

    fw_dist_comb, nodes_comb, idx_comb = floyd_warshall(G_comb)
    betw_comb = fw_betweenness(fw_dist_comb, nodes_comb, idx_comb, G_comb)

    rank_mit = {b["node"]: i for i, b in enumerate(betw_mit)}
    rank_comb = {b["node"]: i for i, b in enumerate(betw_comb)}
    common_nodes = sorted(set(rank_mit) & set(rank_comb))
    spearman = _spearman(
        [rank_mit[n] for n in common_nodes],
        [rank_comb[n] for n in common_nodes],
    )

    top1_mit = betw_mit[0]["node"] if betw_mit else None
    top1_comb = betw_comb[0]["node"] if betw_comb else None

    print(f"\n  Top-1 betweenness: mitigaciones={top1_mit}  combinado={top1_comb}")
    print(f"  Spearman betweenness (mit vs combinado): rho={spearman:.4f}")

    output = {
        "campaign": campaign_name,
        "n_empates_mitigaciones_solo": ties_mit["n_valores_en_empate"],
        "n_empates_combinado": ties_comb["n_valores_en_empate"],
        "reduccion_empates_pct": reduccion_pct,
        "distribucion_pesos_mitigaciones": ties_mit["distribucion_frecuencia"],
        "distribucion_pesos_combinado": ties_comb["distribucion_frecuencia"],
        "costo_ruta_critica_mitigaciones": costo_mit,
        "costo_ruta_critica_combinado": costo_comb,
        "ruta_critica_mitigaciones": ruta_mit,
        "ruta_critica_combinado": ruta_comb,
        "ruta_critica_identica": ruta_identica,
        "jaccard_ruta_critica": jaccard_ruta,
        "top1_betweenness_mitigaciones": top1_mit,
        "top1_betweenness_combinado": top1_comb,
        "spearman_betweenness_mit_vs_combinado": round(spearman, 6),
        "conclusion": (
            "El modelo combinado (mitigaciones + deteccion) anade una segunda fuente "
            "STIX independiente (relaciones 'detects' + profundidad de analiticas), "
            "aumentando la resolucion del espacio de pesos posibles y reduciendo el "
            "numero de tecnicas que comparten exactamente el mismo peso, sin introducir "
            "ningun dato externo a ATT&CK."
        ),
    }

    out_path = RESULTS_DIR / "comparacion_pesos_finos.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"  Guardado: {out_path}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", default=TARGET_CAMPAIGN_NAME)
    args = parser.parse_args()
    run(campaign_name=args.campaign)
