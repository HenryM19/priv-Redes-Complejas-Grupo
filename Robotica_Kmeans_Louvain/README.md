# Robotica_Kmeans_Louvain

Proyecto **unificado** de clustering de actuadores robóticos. Fusiona en una sola
carpeta y un solo enfoque los tres proyectos previos:

| Proyecto original | Aporte integrado |
|---|---|
| `Kmeans_Robot_Jean/Robotica_kmeans_sintetico` | Pipeline modular base (síntesis, features, K-Means++, PCA, animaciones) |
| `Kmeans_Robot_Henry` | Idea de **grafo** sobre los datos (aquí: grafo k-NN de actuadores) |
| `Kmeans_Comparacion` | Espíritu comparativo → ahora **K-Means vs Louvain cuantitativo** |

## Enfoque

Sobre **el mismo dataset** de actuadores se ejecutan dos paradigmas de agrupamiento
y se comparan:

- **K-Means** — particional, geométrico, requiere K (auto-seleccionado por silhouette + codo).
- **Louvain** — detección de comunidades en un **grafo k-NN**, K **emergente** maximizando
  la modularidad Q. Implementado desde cero (`src/louvain.jl`).

## Estructura

```
Robotica_Kmeans_Louvain/
├── Project.toml
├── run_pipeline.jl          ← orquesta las 8 etapas
├── src/
│   ├── synthesis.jl         — dataset sintético (3 estados de mantenimiento)
│   ├── features.jl          — 10 features + z-score ponderado
│   ├── clustering.jl        — K-Means++, auto_select_k, silhouette
│   ├── louvain.jl           — grafo k-NN + modularidad + Louvain multinivel
│   ├── comparison.jl        — ARI, NMI, purity, contingencia
│   ├── animation.jl         — GIFs K-Means + GIF/PNG Louvain + panel comparativo
│   └── reporting.jl         — tablas, CSVs, reporte.md
└── results/                 — generado por el pipeline
    ├── reporte.md
    ├── animations/          — *.gif
    └── report/              — *.csv, *.png
```

## Ejecutar

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'   # primera vez
julia --project=. run_pipeline.jl
```

Opciones útiles: `--n-piezas 200`, `--knn-k 25`, `--no-anim`, `--seed 7`.

## Resultado clave

Ambos métodos, partiendo de principios distintos, recuperan **los mismos 3 estados
de mantenimiento** con **ARI = NMI = 1.000** y **purity = 1.000**. Ver
[RESULTADOS.md](RESULTADOS.md).
