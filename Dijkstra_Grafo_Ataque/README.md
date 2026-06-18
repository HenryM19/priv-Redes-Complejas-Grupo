# Dijkstra en Grafos de Ataque — Caminos Mínimos con CVEs reales

**P1 · Redes Complejas — Universidad de Cuenca · DEET**

Modela una infraestructura como **grafo dirigido**: los nodos son hosts/servicios
y las aristas son **vulnerabilidades explotables (CVEs)**. El peso de cada arista
proviene del **CVSS inverso**:

```
w = 10 − CVSS
```

Así, las vulnerabilidades **críticas** (CVSS alto) tienen **menor costo** y
representan el **camino de menor resistencia** para el atacante.

## Rol de Dijkstra

> Camino de mínimo costo desde un nodo externo (`INTERNET`) hasta el activo
> crítico (`DB-CRITICAL`) = **secuencia de ataque más probable**.

Salida: **ruta crítica** + **nodos cuello de botella**.

## Datos

CVEs **reales** desde la **National Vulnerability Database (NVD)**:
- `src/nvd_fetch.py` consulta la API live del NVD (`services.nvd.nist.gov`).
- Fallback offline: dataset embebido de ~20 CVEs reales conocidos con su CVSS v3
  real (Log4Shell, EternalBlue, BlueKeep, Zerologon, ProxyLogon…).

## Estructura

```
Dijkstra_Grafo_Ataque/
├── requirements.txt
├── src/
│   ├── nvd_fetch.py      — CVEs reales (NVD live + fallback embebido)
│   ├── attack_graph.py   — grafo dirigido por capas, w = 10 − CVSS
│   ├── dijkstra.py       — Dijkstra desde cero + ruta crítica + cuellos de botella
│   └── animate.py        — GIFs de la expansión paso a paso  (en progreso)
└── results/              — generado por el pipeline
```

## Estado

🟢 Módulos core funcionando (NVD + grafo + Dijkstra).
🟡 Animaciones GIF y diapositivas HTML — en progreso.

## Ejecutar

```bash
pip install -r requirements.txt
python src/run_pipeline.py            # (próximamente)
python src/dijkstra.py                # demo rápida offline
```
