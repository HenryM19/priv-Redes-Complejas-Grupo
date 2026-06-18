---
title: "Resultados — Caminos Mínimos en Grafos de Ataque con Dijkstra"
author:
  - "Ing. Jean Carlo Aucapina"
  - "Ing. Henry Maldonado"
date: "2026-06-17"
---

# Resultados — Dijkstra en Grafos de Ataque

Proyecto **P1** de Redes Complejas. Modela una infraestructura como grafo
dirigido de CVEs reales y usa **Dijkstra** para hallar el camino de menor
resistencia desde Internet hasta un activo crítico.

---

## 1. Modelo

| Elemento | Significado |
|----------|-------------|
| Nodo | Host / servicio de la red |
| Arista `u → v` | CVE explotable que lleva de `u` a `v` |
| Peso `w` | `10 − CVSS` (CVSS inverso) |
| Entrada | `INTERNET` (atacante externo) |
| Objetivo | `DB-CRITICAL` (activo crítico) |

Vulnerabilidad crítica (CVSS alto) → peso bajo → **camino de menor
resistencia**. Dijkstra minimiza la resistencia total `Σ w`.

## 2. Datos

CVEs **reales** de la **National Vulnerability Database (NVD)** con su CVSS v3
oficial. La API live se consulta primero; si no está disponible se usa un
dataset embebido de ~20 CVEs reales conocidos (Log4Shell, EternalBlue,
BlueKeep, Zerologon, ProxyLogon, PwnKit…).

> Nota: en la última corrida el NVD devolvió `HTTP 503`, por lo que se usó el
> fallback embebido (los puntajes CVSS siguen siendo los oficiales).

Grafo resultante: **11 nodos · 16 aristas · 6 capas**
(internet → perímetro → web → servicio → host → datos).

## 3. Ruta Crítica

Camino de mínimo costo hallado por Dijkstra:

**INTERNET → FW-VPN → APP-02 → MAIL-EX → WS-ADMIN → DB-CRITICAL**

| # | Salto | CVE | CVSS | w | Producto |
|---|-------|-----|------|---|----------|
| 1 | INTERNET → FW-VPN | CVE-2023-27997 | 9.8 | 0.2 | Fortinet FortiOS |
| 2 | FW-VPN → APP-02 | CVE-2021-44228 | 10.0 | 0.1 | Apache Log4j (Log4Shell) |
| 3 | APP-02 → MAIL-EX | CVE-2019-0708 | 9.8 | 0.2 | Microsoft RDP (BlueKeep) |
| 4 | MAIL-EX → WS-ADMIN | CVE-2019-0708 | 9.8 | 0.2 | Microsoft RDP (BlueKeep) |
| 5 | WS-ADMIN → DB-CRITICAL | CVE-2019-10149 | 9.8 | 0.2 | Exim MTA |

**Resistencia total (Σ w): 0.90**  ·  **Iteraciones de Dijkstra: 9**

Todos los saltos usan CVEs **CRITICAL** (CVSS ≥ 9.8): el atacante prefiere
las vulnerabilidades más graves porque son el camino más barato.

## 4. Nodos Cuello de Botella

| Nodo | Rutas de bajo costo que lo atraviesan |
|------|:---:|
| `FW-VPN` | 4 |
| `APP-02` | 4 |
| `MAIL-EX` | 3 |

## 5. Interpretación Defensiva

1. **Parchar primero la ruta crítica** — subir el CVSS efectivo (mitigar el CVE)
   aumenta el peso de esas aristas y fuerza un camino más costoso.
2. **Segmentar / monitorear los cuellos de botella** — aislar `FW-VPN` y
   `APP-02` corta la mayoría de las rutas de menor resistencia a la vez.
3. **Priorizar el eslabón más barato** — la arista de menor peso
   (Log4Shell, `w = 0.1`) es el primer parche.

## 6. Visualizaciones

- `results/animations/attack_graph.png` — grafo por capas, aristas por severidad.
- `results/animations/dijkstra_expansion.gif` — expansión paso a paso (9 iter).
- `results/animations/critical_path.gif` — ruta crítica trazada salto a salto.
- `diapositivas/` — deck HTML de 8 slides + PDF.

## 7. Archivos

```
Dijkstra_Grafo_Ataque/
├── src/
│   ├── nvd_fetch.py      — CVEs reales (NVD live + fallback embebido)
│   ├── attack_graph.py   — grafo dirigido por capas, w = 10 − CVSS
│   ├── dijkstra.py       — Dijkstra desde cero + ruta crítica + cuellos
│   ├── animate.py        — PNG + 2 GIFs (estética command-center)
│   └── run_pipeline.py   — orquesta todo
├── results/
│   ├── reporte.md
│   ├── animations/*.png|gif
│   └── report/*.csv|json
└── diapositivas/         — deck HTML (8 slides) + PDF
```

## 8. Ejecutar

```bash
pip install -r requirements.txt
python src/run_pipeline.py            # NVD live + fallback
python src/run_pipeline.py --offline  # solo dataset embebido
```

---

*Datos CVE/CVSS reales de la National Vulnerability Database (NVD).
Universidad de Cuenca — DEET, 2026.*
