"""
run_pipeline.py — Pipeline completo del proyecto Dijkstra · Grafo de Ataque.

Etapas:
  1. Obtener CVEs reales (NVD live + fallback embebido).
  2. Construir el grafo de ataque dirigido (w = 10 − CVSS).
  3. Ejecutar Dijkstra desde cero (INTERNET → DB-CRITICAL).
  4. Analizar ruta crítica + nodos cuello de botella.
  5. Generar visualizaciones (PNG del grafo + 2 GIFs).
  6. Escribir reporte.md, RESULTADOS.md y CSVs.

Uso:
  python src/run_pipeline.py [--offline] [--seed N]
"""

import sys, os, csv, json, argparse
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from nvd_fetch import load_cves
from attack_graph import build_attack_graph, graph_summary, layered_layout, LAYER_ORDER
from dijkstra import dijkstra_steps, bottleneck_nodes, critical_path_report, path_edges
from animate import render_graph_png, render_dijkstra_gif, render_critical_path_gif

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS  = os.path.join(ROOT, "results")
ANIM     = os.path.join(RESULTS, "animations")
REPORT   = os.path.join(RESULTS, "report")
SOURCE   = "INTERNET"
TARGET   = "DB-CRITICAL"


def _w(path, rows, header):
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=header)
        wr.writeheader()
        wr.writerows(rows)


def write_reporte_md(G, result, bottlenecks, cves, source_kind, out):
    rows = critical_path_report(G, result)
    with open(out, "w", encoding="utf-8") as f:
        w = f.write
        w("# Reporte — Caminos Mínimos en Grafos de Ataque (Dijkstra)\n\n")
        w(f"> **Generado:** {date.today()}  |  **Fuente CVE:** {source_kind}  ")
        w(f"|  **Nodos:** {G.number_of_nodes()}  |  **Aristas:** {G.number_of_edges()}\n\n")
        w("---\n\n## 1. Modelo\n\n")
        w("Infraestructura modelada como **grafo dirigido**: nodos = hosts/servicios, ")
        w("aristas = **CVEs explotables**. Peso `w = 10 − CVSS` (CVSS inverso): ")
        w("vulnerabilidades críticas → menor costo → **camino de menor resistencia**.\n\n")
        w(f"- **Entrada:** `{SOURCE}` (atacante externo)\n")
        w(f"- **Objetivo:** `{TARGET}` (activo crítico)\n\n")
        w("![Grafo de ataque](animations/attack_graph.png)\n\n")
        w("---\n\n## 2. Ruta Crítica (secuencia de ataque más probable)\n\n")
        w("Camino de mínimo costo hallado por Dijkstra:\n\n")
        w("**" + "  →  ".join(result["path"]) + "**\n\n")
        w(f"Resistencia total (Σ w): **{result['cost']:.2f}**  ·  ")
        w(f"Iteraciones de Dijkstra: **{len(result['steps'])}**\n\n")
        w("| # | Salto | CVE | CVSS | w | Severidad | Producto |\n")
        w("|---|-------|-----|------|---|-----------|----------|\n")
        for i, r in enumerate(rows, 1):
            w(f"| {i} | {r['from']} → {r['to']} | {r['cve']} | {r['cvss']} | {r['weight']} | {r['severity']} | {r['product']} |\n")
        w("\n![Ruta crítica](animations/critical_path.gif)\n\n")
        w("---\n\n## 3. Expansión de Dijkstra\n\n")
        w("El frente de exploración avanza nodo a nodo eligiendo siempre la menor ")
        w("distancia acumulada. Los números amarillos son la resistencia mínima ")
        w("conocida hasta cada nodo.\n\n")
        w("![Expansión Dijkstra](animations/dijkstra_expansion.gif)\n\n")
        w("---\n\n## 4. Nodos Cuello de Botella\n\n")
        w("Nodos por los que pasan más de las rutas de menor costo — puntos de ")
        w("control prioritarios para la defensa:\n\n")
        w("| Nodo | Rutas que lo atraviesan |\n|------|:---:|\n")
        for n, c in bottlenecks:
            w(f"| `{n}` | {c} |\n")
        w("\n---\n\n## 5. Interpretación defensiva\n\n")
        w("- **Parchar primero los CVEs de la ruta crítica** sube su resistencia y ")
        w("obliga al atacante a un camino más costoso.\n")
        w("- **Segmentar/monitorear los cuellos de botella** corta múltiples rutas a la vez.\n")
        w(f"- La arista más barata (CVE más crítico) de la ruta es el eslabón a priorizar.\n\n")
        w("---\n*Datos CVE/CVSS reales de la National Vulnerability Database (NVD).*\n")
    print(f"  reporte.md: {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="No consultar NVD live; usar dataset embebido")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(ANIM, exist_ok=True)
    os.makedirs(REPORT, exist_ok=True)

    print("\n" + "=" * 64)
    print("  PIPELINE — DIJKSTRA EN GRAFOS DE ATAQUE (CVEs reales)")
    print("=" * 64)

    print("\n[1/6] Obteniendo CVEs reales…")
    cves, kind = load_cves(use_live=not args.offline,
                           cache_path=os.path.join(ROOT, "data", "cves_cache.json"))

    print("\n[2/6] Construyendo grafo de ataque…")
    G = build_attack_graph(cves, seed=args.seed)
    summ = graph_summary(G)
    print(f"  {summ['n_nodes']} nodos · {summ['n_edges']} aristas · capas: {' → '.join(LAYER_ORDER)}")

    print("\n[3/6] Ejecutando Dijkstra (desde cero)…")
    result = dijkstra_steps(G, SOURCE, TARGET)
    if not result["path"]:
        print("  ¡No hay ruta hasta el activo crítico! Revisa el grafo."); return
    print(f"  Ruta crítica: {' -> '.join(result['path'])}")
    print(f"  Resistencia total: {result['cost']:.2f}  ·  iteraciones: {len(result['steps'])}")

    print("\n[4/6] Analizando cuellos de botella…")
    bn = bottleneck_nodes(G, SOURCE, TARGET, top_k=3)
    print(f"  {bn}")

    print("\n[5/6] Generando visualizaciones…")
    render_graph_png(G, SOURCE, TARGET, os.path.join(ANIM, "attack_graph.png"))
    render_dijkstra_gif(G, result, SOURCE, TARGET, os.path.join(ANIM, "dijkstra_expansion.gif"))
    render_critical_path_gif(G, result, SOURCE, TARGET, os.path.join(ANIM, "critical_path.gif"))

    print("\n[6/6] Escribiendo reportes y CSVs…")
    # CSVs
    _w(os.path.join(REPORT, "ruta_critica.csv"), critical_path_report(G, result),
       ["from", "to", "cve", "cvss", "weight", "product", "severity"])
    _w(os.path.join(REPORT, "aristas_grafo.csv"),
       [{"from": u, "to": v, **{k: d[k] for k in ("cve","cvss","weight","severity","product")}}
        for u, v, d in G.edges(data=True)],
       ["from", "to", "cve", "cvss", "weight", "severity", "product"])
    _w(os.path.join(REPORT, "cuellos_botella.csv"),
       [{"nodo": n, "rutas": c} for n, c in bn], ["nodo", "rutas"])
    with open(os.path.join(REPORT, "cves_usados.json"), "w", encoding="utf-8") as f:
        json.dump({"source": kind, "cves": cves}, f, indent=2, ensure_ascii=False)

    write_reporte_md(G, result, bn, cves, kind, os.path.join(RESULTS, "reporte.md"))

    print("\n" + "=" * 64)
    print("  ✓ Pipeline completado")
    print(f"  Ruta: {' -> '.join(result['path'])}  (resistencia {result['cost']:.2f})")
    print(f"  Resultados en: {RESULTS}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
