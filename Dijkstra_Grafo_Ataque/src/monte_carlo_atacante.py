"""
monte_carlo_atacante.py — Simulacion de atacante NO racional (Monte-Carlo).

Cuantifica la Limitacion L2 (documentada en guia-dataset.html): Dijkstra asume
un atacante que SIEMPRE elige la ruta de menor resistencia. En la practica,
un atacante real puede no conocer el grafo completo, cometer errores, o
priorizar otros factores. Esta simulacion pregunta: si el atacante elige
cada paso con una preferencia SESGADA (no perfecta) hacia menor peso, ¿que
tan cerca del optimo Dijkstra termina, y con que probabilidad?

Metodologia: random walk ponderado. En cada nodo, la probabilidad de elegir
un sucesor v es proporcional a (1/peso(u,v))**bias_power:
  bias_power=0    -> atacante completamente aleatorio (ignora resistencia)
  bias_power=1    -> preferencia leve hacia menor resistencia (proporcional inverso)
  bias_power alto -> converge al comportamiento Dijkstra (siempre el minimo)

No introduce ningun dato nuevo: usa los mismos pesos STIX-derivados ya
presentes en el grafo (ver dataset_real.py). Es una adicion metodologica,
no de datos.

Salida: results/real/monte_carlo_atacante_solarwinds.json
"""

import json
import math
import random
from pathlib import Path

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

DEFAULT_BIAS_POWERS = (0, 0.5, 1, 2, 5, 10)


def weighted_random_walk(G, source: str, target: str, rng: random.Random,
                          bias_power: float = 1.0, max_steps: int | None = None):
    """
    Camino aleatorio ponderado desde source hasta target.

    En cada nodo u, elige el siguiente salto v entre los sucesores con
    probabilidad proporcional a (1/peso(u,v))**bias_power, normalizado.
    Un peso mas bajo (menor resistencia) es mas probable, pero no garantizado
    -- a diferencia de Dijkstra, que SIEMPRE toma el minimo.

    max_steps evita loops infinitos (salvaguarda; por construccion TACTIC_ORDER
    el grafo es aciclico o casi-aciclico, pero no se asume).

    Retorna (path, costo_total) o (None, None) si el walk llega a un nodo
    sin sucesores antes de alcanzar target (dead-end, trial descartado).
    """
    if max_steps is None:
        max_steps = G.number_of_nodes() * 2

    path = [source]
    cost = 0.0
    current = source

    for _ in range(max_steps):
        if current == target:
            return path, cost

        successors = list(G.successors(current))
        if not successors:
            return None, None

        weights = [G[current][v]["weight"] for v in successors]
        # Preferencia inversa: menor peso = mayor probabilidad
        scores = [(1.0 / max(w, 1e-6)) ** bias_power for w in weights]
        total = sum(scores)
        probs = [s / total for s in scores]

        chosen = rng.choices(successors, weights=probs, k=1)[0]
        cost += G[current][chosen]["weight"]
        path.append(chosen)
        current = chosen

    return None, None  # excedio max_steps sin llegar a target


def monte_carlo_run(G, source: str, target: str, n_trials: int = 10000,
                     bias_power: float = 1.0, seed: int = 42) -> dict:
    """
    Corre weighted_random_walk() n_trials veces (seed fijo, reproducible).
    Compara la distribucion de costos contra el costo Dijkstra-optimo.
    """
    rng = random.Random(seed)
    dist, prev = dijkstra(G, source)
    optimal_path = reconstruct_path(prev, source, target)
    optimal_cost = dist.get(target, float("inf"))

    costs = []
    dead_ends = 0
    exact_match = 0

    for _ in range(n_trials):
        path, cost = weighted_random_walk(G, source, target, rng, bias_power=bias_power)
        if path is None:
            dead_ends += 1
            continue
        costs.append(cost)
        if path == optimal_path:
            exact_match += 1

    n_success = len(costs)
    if n_success == 0:
        return {
            "bias_power": bias_power,
            "n_trials": n_trials,
            "n_success": 0,
            "dead_end_rate": 1.0,
            "conclusion": "Todos los trials terminaron en dead-end (bias_power demasiado bajo "
                          "para este grafo, o grafo con nodos sin salida hacia target)."
        }

    costs.sort()
    n = len(costs)
    percentiles = {
        p: round(costs[min(int(n * p / 100), n - 1)], 4)
        for p in (5, 25, 50, 75, 95)
    }
    mean_cost = sum(costs) / n
    variance = sum((c - mean_cost) ** 2 for c in costs) / n if n > 1 else 0.0
    std_cost = math.sqrt(variance)
    ci95 = (
        round(mean_cost - 1.96 * std_cost / math.sqrt(n), 4),
        round(mean_cost + 1.96 * std_cost / math.sqrt(n), 4),
    )

    within_pct = {}
    for x in (5, 10, 20, 50):
        threshold = optimal_cost * (1 + x / 100)
        frac = sum(1 for c in costs if c <= threshold) / n
        within_pct[f"within_{x}pct"] = round(frac, 4)

    return {
        "bias_power": bias_power,
        "n_trials": n_trials,
        "n_success": n_success,
        "dead_end_rate": round(dead_ends / n_trials, 4),
        "optimal_cost": round(optimal_cost, 4),
        "mean_cost": round(mean_cost, 4),
        "median_cost": percentiles[50],
        "std_cost": round(std_cost, 4),
        "ci95_mean_cost": list(ci95),
        "percentiles": percentiles,
        "ratio_mean_vs_optimal": round(mean_cost / optimal_cost, 4) if optimal_cost > 0 else None,
        "exact_path_match_rate": round(exact_match / n_success, 4),
        "within_optimal_pct": within_pct,
    }


def sweep_bias_power(G, source: str, target: str, n_trials: int = 10000,
                      powers: tuple = DEFAULT_BIAS_POWERS, seed: int = 42) -> list[dict]:
    """
    Corre monte_carlo_run() para cada bias_power. Permite observar como la
    "racionalidad" del atacante (bias_power) se correlaciona con cercania
    al optimo Dijkstra -- el insight de robustez central de este modulo.
    """
    results = []
    for bp in powers:
        print(f"  [MC] bias_power={bp} ({n_trials} trials)...")
        r = monte_carlo_run(G, source, target, n_trials=n_trials, bias_power=bp, seed=seed)
        results.append(r)
        if r["n_success"] > 0:
            print(f"        media={r['mean_cost']} (optimo={r['optimal_cost']}, "
                  f"ratio={r['ratio_mean_vs_optimal']}), "
                  f"exact_match={r['exact_path_match_rate']*100:.1f}%, "
                  f"dead_end={r['dead_end_rate']*100:.1f}%")
        else:
            print(f"        [WARN] 0 trials exitosos (100% dead-end)")
    return results


def run(campaign_name: str = TARGET_CAMPAIGN_NAME, n_trials: int = 10000,
        edge_mode: str = "cartesian", weight_mode: str = "mitigations") -> dict:
    print("\n" + "=" * 70)
    print("  MONTE-CARLO — Atacante NO racional (SolarWinds Compromise)")
    print(f"  n_trials={n_trials} por bias_power, edge_mode={edge_mode}, weight_mode={weight_mode}")
    print("=" * 70)

    bundle = download_mitre()
    campaign_obj, techniques = extract_campaign(bundle, campaign_name)
    G, tech_by_id, by_tactic = build_attack_graph(
        bundle, techniques, campaign=campaign_obj,
        edge_mode=edge_mode, weight_mode=weight_mode,
    )

    dist, prev = dijkstra(G, ENTRY_NODE)
    optimal_cost = dist.get(TARGET_NODE, float("inf"))
    if optimal_cost == float("inf"):
        raise ValueError(
            f"ATTACKER->IMPACT no alcanzable con edge_mode={edge_mode}. "
            "Monte-Carlo requiere un grafo conectado; usa edge_mode=cartesian "
            "o una campana con cobertura de co-ocurrencia completa."
        )

    print(f"\n  Costo Dijkstra-optimo: {round(optimal_cost, 4)}")
    print(f"\n[Sweep de bias_power]")
    sweep = sweep_bias_power(G, ENTRY_NODE, TARGET_NODE, n_trials=n_trials)

    # Insight de robustez: a partir de que bias_power el 95% de los trials
    # cae dentro del 10% del costo optimo
    robust_threshold = None
    for r in sweep:
        if r["n_success"] > 0 and r["within_optimal_pct"]["within_10pct"] >= 0.95:
            robust_threshold = r["bias_power"]
            break

    output = {
        "campaign": campaign_name,
        "edge_mode": edge_mode,
        "weight_mode": weight_mode,
        "optimal_cost": round(optimal_cost, 4),
        "n_trials_per_bias_power": n_trials,
        "sweep_bias_power": sweep,
        "bias_power_para_robustez_95_10pct": robust_threshold,
        "conclusion": (
            "Un atacante con bias_power bajo (0-1, decisiones casi aleatorias o "
            "levemente sesgadas hacia baja resistencia) rara vez replica la ruta "
            "Dijkstra-optima exacta, pero el costo medio resultante puede seguir "
            "siendo cercano al optimo si el grafo tiene pocas alternativas de alto "
            "costo. bias_power_para_robustez_95_10pct indica el nivel minimo de "
            "'racionalidad' necesario para que 95% de los ataques simulados caigan "
            "dentro del 10% del costo optimo -- una medida cuantitativa de cuan "
            "fragil es la ventaja de un atacante perfectamente racional sobre uno "
            "imperfecto, en este grafo especifico."
            if robust_threshold is not None else
            "Ningun nivel de bias_power evaluado alcanzo el umbral de robustez "
            "(95% de trials dentro del 10% del costo optimo) -- el grafo tiene "
            "suficiente varianza de costos entre rutas alternativas para que la "
            "irracionalidad del atacante importe incluso con fuerte sesgo hacia "
            "el optimo."
        ),
    }

    out_path = RESULTS_DIR / f"monte_carlo_atacante_{campaign_name.lower().replace(' ', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"  Umbral de robustez (95% dentro de +10% del optimo): "
          f"bias_power={robust_threshold}")
    print(f"  Guardado: {out_path}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", default=TARGET_CAMPAIGN_NAME)
    parser.add_argument("--n-trials", type=int, default=10000)
    parser.add_argument("--edge-mode", choices=["cartesian", "cooccurrence"], default="cartesian")
    parser.add_argument("--weight-mode", choices=["mitigations", "combined"], default="mitigations")
    args = parser.parse_args()
    run(campaign_name=args.campaign, n_trials=args.n_trials,
        edge_mode=args.edge_mode, weight_mode=args.weight_mode)
