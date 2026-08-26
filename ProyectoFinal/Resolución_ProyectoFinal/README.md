# Resolución — Proyecto integrador de Redes Complejas (Red UCuenca)

Solución de los 11 problemas (P1–P11) del enunciado `../proyecto_red_ucuenca.pdf`
sobre la red de datos de la Universidad de Cuenca (177 nodos, 209 aristas).

**Repositorio de entrega del proyecto final:**
[jeanaucapina/ProeyctoFinal_RedesComplejas_Aucapina_Maldonado](https://github.com/jeanaucapina/ProeyctoFinal_RedesComplejas_Aucapina_Maldonado)

## Reproducir todos los resultados

```bash
cd Resolución_ProyectoFinal
python3 -m pip install -r requirements.txt
python3 -m pip install -r ../codigo_base/requirements.txt   # networkx/numpy/scipy/pandas/matplotlib

cd src
python3 problema1.py    # Fase 1 — Medidas fundamentales
python3 problema2.py    # Fase 1 — Modelos nulos y visualización
python3 problema3.py    # Fase 2 — BFS/DFS
python3 problema4.py    # Fase 2 — Comunidades y modularidad
python3 problema5.py    # Fase 3 — Caminos mínimos
python3 problema6.py    # Fase 3 — Flujo máximo y corte mínimo
python3 problema7.py    # Fase 3 — p-Mediana / p-Centro (heurística + solver exacto)
python3 problema8.py    # Fase 4 — Percolación
python3 problema9.py    # Fase 4 — Cascadas y SIR
python3 problema10.py   # Fase 4 — Ranking de puntos críticos
python3 problema11.py   # Fase 5 — Propuesta de rediseño
```

Cada script se ejecuta de forma independiente (no hay dependencias de orden
entre ellos, salvo que todos parten del mismo `codigo_base/cargar_red.py`) y
al final imprime "Todas las comprobaciones pasaron" al cargar la red — si no,
revisar la instalación antes de continuar. Los scripts `comparar_layouts.py`
y `comparar_betweenness_layouts.py` son auxiliares de visualización para P1/P2,
no resuelven un ítem numerado por separado.

**Tiempo de ejecución:** la mayoría de scripts corre en segundos. `problema7.py`
tarda más porque, además de la heurística voraz, resuelve el óptimo exacto de
p-mediana y p-centro con un solver de programación entera (PuLP/CBC) para
cada $p \in \{1,2,3,5\}$ — del orden de 1–2 minutos en total. `problema9.py`
promedia el modelo SIR y las estrategias de inmunización sobre 30 realizaciones
cada una, del orden de 1 minuto.

## Salidas

- `results/tablas/` — CSV y TXT con las tablas numéricas de cada problema.
- `results/imagenes/` — todas las figuras (PNG, 150–180 dpi) referenciadas en `Informe.md`.
- `Informe.md` — informe completo (definiciones, resultados, análisis) por fase y problema; es la fuente de la que se genera `informe_latex/informe.pdf`.

## Dependencias

`requirements.txt` (esta carpeta) cubre lo específico de esta resolución:
`scikit-learn` y `python-louvain` (P4 — clustering espectral y Louvain) y
`pulp` (P7 — solver exacto de programación entera). `../codigo_base/requirements.txt`
cubre lo común a todo el módulo (`networkx`, `numpy`, `scipy`, `pandas`, `matplotlib`).

## Autoría

Ver portada de `informe_latex/informe.pdf` para nombres y correos institucionales
de los integrantes del grupo.
