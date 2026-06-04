# Kmeans_Applitation

**Tipo:** `python`  
**Fecha de creación:** 2026-06-03

## Descripción

Pipeline de analisis para actuadores de exoesqueleto con:
- Metodo del codo (inercia, silhouette, Davies-Bouldin)
- K-means final configurable
- PCA 3D para visualizacion
- Estadisticas por variable y cluster
- Matriz de correlacion
- Varianza explicada por PCA

## Estructura

```
Kmeans_Applitation/
    main.py
    README.md
    src/
        __init__.py
        data/
            exoesqueleto_actuadores.csv
        functions/
            __init__.py
            pipeline_kmeans_exoesqueleto.py
            decision_matrix.py
    docs/
        reporte_exoesqueleto_kmeans.md
    results/
        images/
            01_metodo_codo.png
            01a_evolucion_codo.gif
            01b_evolucion_silhouette.gif
            01c_evolucion_davies.gif
            02_pca_3d_scatter.png
            03_estadisticas_clusters.png
            04_distribucion_actuadores.png
            05_matriz_correlacion.png
            06_varianza_pca.png
            07_centroides_3d_evolucion.gif
            07_centroides_3d_trayectoria.png
        reports/
            analisis_kmeans.json
            exoesqueleto_con_clusters.csv
            estadisticas_clusters_detalle.csv
```

## Usage

```bash
python main.py

# Opcional: customizar parametros
python main.py --input src/data/exoesqueleto_actuadores.csv --output-dir results --k-min 2 --k-max 9 --k-final 4

# Opcional: abrir automaticamente el GIF de evolucion de centroides
python main.py --open-centroid-evolution

# Regenerar base sintetica balanceada
python src/functions/generar_base_sintetica_balanceada.py
```
