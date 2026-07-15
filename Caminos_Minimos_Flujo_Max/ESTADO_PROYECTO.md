# Estado del proyecto — Flujo máximo (Ford-Fulkerson vs Edmonds-Karp)

**Última actualización:** 14 de julio de 2026
**Entrega:** una semana después de la sesión de laboratorio
**Rúbrica:** 10 puntos

---

## ⚠️ Hay DOS soluciones completas en esta carpeta — hay que decidir qué se entrega

Henry y Jean resolvimos la actividad **en paralelo, sin coordinarnos**. El merge fue
limpio (los archivos no colisionan), así que ahora conviven las dos:

| | Henry | Jean |
|---|---|---|
| **Código** | `src/01_ford_fulkerson.jl`, `02_edmonds_karp.jl`, `03..06_parte*.jl` | `src/{motor,redes,busqueda_red}.jl`, `src/parte{1,2,3,4}_*.jl` |
| **Resultados** | `results/{files,images,animations}/parte*` | `results/{data,animations}/` |
| **Informe** | `results/report/report.md` | `INFORME.md` |
| **Diapositivas** | — | `presentacion/` (13 láminas + libreto) |
| **Red propia** | 8 nodos, 14 arcos | 9 nodos, 16 arcos |
| **Ejecutado con** | motor Python equivalente (no tuvo acceso a instalar Julia) | **Julia 1.12.5 real** |

### Las dos soluciones se validan mutuamente

Esto es lo valioso del merge: **dos implementaciones independientes, en dos lenguajes
distintos, dan los mismos números**.

- **Red CLRS** — los dos obtenemos 3 iteraciones con los mismos caminos y los mismos Δ,
  tanto en BFS como en DFS. Y los dos medimos `usa_arco_retroceso = False` en **todas**
  las iteraciones: la guía da por supuesto que hay un retroceso en CLRS y **no lo hay**.
- **Zigzag** — los dos medimos que la DFS de orden invertido **no empeora nada** (2
  iteraciones para todo M), y que hace falta un adversario explícito para llegar a 2M.
  Henry lo llama «oráculo adversarial», Jean «adversario alternante»; los dos dan
  20 / 200 / 2 000 / 20 000 exactos.
- **La conclusión de fondo también coincide**, escrita por separado: el peor caso no lo
  produce DFS, sino la libertad de elegir mal que Ford-Fulkerson deja abierta; BFS es
  inmune porque mientras exista el camino de 2 arcos nunca tomará el de 3.

### Qué hay que decidir entre los dos

1. **Cuál red propia se entrega.** Son distintas (8/14 vs 9/16) y las dos cumplen los
   cuatro requisitos. La de Jean tiene además corte no trivial y documentación del
   proceso de búsqueda; la de Henry es más pequeña y quizá más fácil de explicar en clase.
2. **Cuál informe.** `report.md` o `INFORME.md`, o uno fusionado.
3. **Ejecutar los scripts de Henry con Julia real** antes de entregar — él mismo lo
   recomienda en su nota metodológica, porque sus números salieron de un motor Python
   equivalente. Los de Jean ya están corridos en Julia 1.12.5.
4. Si se entrega una sola solución, **borrar la otra de la carpeta** para no confundir al
   profesor. Ninguno de los dos debería borrar el trabajo del otro sin hablarlo.

---

## Avance global

| Parte | Puntos | Estado | Evidencia |
|---|---:|---|---|
| 1 — Exploración guiada | 2 | ✅ completa | `src/parte1_exploracion.jl` · `results/data/parte1_clrs.json` |
| 2 — Experimento zigzag | 3 | ✅ completa | `src/parte2_zigzag.jl` · `results/data/parte2_zigzag.json` |
| 3 — Red propia | 3 | ✅ completa | `src/parte3_red_propia.jl` · `src/busqueda_red.jl` |
| 4 — Análisis comparativo | 2 | ✅ completa | `src/parte4_comparacion.jl` |
| Informe | — | ✅ completo | `INFORME.md` |
| Diapositivas | — | 🔄 en curso | `presentacion/` |

---

## Checklist de la rúbrica

### Parte 1 — Exploración guiada (2 pts)
- [x] Tabla por iteración BFS: camino, longitud, Δ, flujo acumulado
- [x] Tabla por iteración DFS
- [x] Arco de retroceso identificado y explicado
- [x] Onda BFS: qué es `d` y por qué el camino tiene `d(t)` arcos
- [x] Comparación final: corte, flujo, flujos arco por arco

### Parte 2 — Experimento zigzag (3 pts)
- [x] Mediciones para los cuatro valores de M (10, 100, 1000, 10000)
- [x] Análisis del orden de exploración de `buscar_camino_dfs`
- [x] Modificación de la DFS implementada y explicada
- [x] Por qué Edmonds-Karp es inmune

### Parte 3 — Red propia (3 pts)
- [x] ≥ 8 nodos (tenemos 9) y ≥ 12 arcos (tenemos 16)
- [x] Par de arcos antiparalelos (c ⇄ d)
- [x] Al menos una ejecución usa arco de retroceso (**ambas** lo usan)
- [x] Iteraciones BFS ≠ DFS (5 vs 8)
- [x] GIFs con `animar_ford_fulkerson` y `animar_edmonds_karp`
- [x] Corte mínimo verificado a mano
- [x] Proceso de diseño documentado, con intentos fallidos

### Parte 4 — Análisis comparativo (2 pts)
- [x] Cuadro 3 completo
- [x] Pregunta 1 — similitudes y teorema
- [x] Pregunta 2 — monotonía de longitudes y su papel en O(V·E²)
- [x] Pregunta 3 — cuándo preferir DFS
- [x] Pregunta 4 — dos aplicaciones en redes complejas, una modelada

### Entregables
- [x] Informe con tablas, respuestas y análisis (`INFORME.md`)
- [x] Código Julia ejecutable con `julia --project=.`
- [x] Animaciones GIF de la red propia con ambos algoritmos
- [ ] **Nombre y correo del segundo integrante** ← pendiente
- [ ] Exportar `INFORME.md` a PDF (máx. 12 páginas sin anexos)

---

## Resultados principales

**Red CLRS** — flujo máximo 23. BFS y DFS dan trazas **idénticas** (3 iteraciones, mismos caminos, mismo reparto). La red es demasiado benigna para separar los métodos.

**Red zigzag** — flujo máximo 2M.

| Método | M=10 | M=100 | M=1000 | M=10000 |
|---|---:|---:|---:|---:|
| BFS / DFS repo / DFS invertida | 2 | 2 | 2 | 2 |
| DFS profunda | 4 | 4 | 4 | 4 |
| Adversario alternante | 20 | 200 | 2 000 | 20 000 |
| *peor caso teórico (2M)* | *20* | *200* | *2 000* | *20 000* |

**Red propia** — 9 nodos, 16 arcos, flujo máximo 24.

| | BFS | DFS |
|---|---:|---:|
| Iteraciones | 5 | 8 |
| Longitudes | 3,3,3,5,7 (no decrecen) | 3,4,3,4,3,4,5,6 (oscilan) |
| Arco de retroceso | iter 5: f→b | iter 8: d→b |
| Corte mínimo | {s,a,c,e} = 24 | {s,a,c,e} = 24 |

Corte verificado a mano: s→b (8) + c→d (5) + c→f (8) + e→t (3) = **24** = flujo máximo ✓

---

## Decisiones y hallazgos que conviene recordar

**1. En CLRS no hay arcos de retroceso con las variantes estándar.** La guía (punto 1.2) pide identificar una iteración que use uno, pero verificamos que ni BFS, ni la DFS del repositorio, ni la DFS de orden invertido lo hacen: las tres llegan a 23 sin cancelar nada. Para responder, forzamos el fenómeno con una DFS profunda (que prefiere caminos largos): su iteración 3 usa el retroceso v₂→v₃. Está documentado como tal en el informe, sin fingir que salía de la ejecución normal.

**2. El peor caso 2M no lo alcanza ninguna DFS razonable.** Este fue el hallazgo que más trabajo costó. La razón es geométrica: el camino trampa tiene 3 arcos y el atajo solo 2, así que cualquier búsqueda que corte al descubrir `t` toma el atajo. Ni siquiera la DFS profunda basta (4 iteraciones): cruza la trampa una vez y luego el atajo se lleva M−1 unidades de golpe. Hizo falta `buscar_camino_alternante`, que alterna s→u→v→t y s→v→u→t; el segundo usa el retroceso v→u que **reabre** el arco trampa. Ese sí clava 2M exacto.

La lectura: el peor caso es del *método*, no de DFS.

**3. La sugerencia de la guía de invertir el orden de vecinos no empeora nada.** La implementamos (`buscar_camino_dfs_adversaria`) y sigue en 2 iteraciones; solo cambia qué ruta toma primero. Se reporta como resultado negativo, no se esconde.

**4. Se retiró el experimento de capacidades irracionales.** La primera versión daba un "estancamiento en el 50 %" que era un artefacto: los arcos de capacidad 100 dominaban el flujo máximo y las capacidades irracionales (1, φ, φ²) quedaban irrelevantes. Reproducir Zwick de verdad exige aritmética exacta en ℚ(√5): en Float64 el invariante de la razón áurea se rompe por redondeo y Ford-Fulkerson termina *por el error numérico*, lo que "confirmaría" la terminación por el motivo equivocado. Se cita la teoría y se apoya el argumento en el peor caso 2M, que sí es evidencia propia.

**5. La red propia salió de una búsqueda dirigida, no de la intuición.** El primer intento a mano falló 2 de 4 requisitos. La búsqueda sobre 400 000 combinaciones reveló que solo ~0.02 % cumple las seis condiciones, y que el 77.5 % falla porque **DFS no resulta peor que BFS**. Ese número es un resultado por sí mismo: explica por qué CLRS no separa los métodos.

**6. Detalle técnico.** `ford_fulkerson.jl` y `edmonds_karp.jl` definen ambos `RedFlujo`, así que no se pueden `include` en el mismo ámbito. En `parte3_red_propia.jl` el segundo se carga dentro de `module EK` para aislar sus definiciones.

---

## Pendientes

1. **Completar el nombre y correo del segundo integrante** en `INFORME.md`.
2. **Exportar el informe a PDF** (máx. 12 páginas sin anexos). Con pandoc:
   `pandoc INFORME.md -o INFORME.pdf --pdf-engine=xelatex -V geometry:margin=2.5cm`
3. **Terminar las diapositivas** en `presentacion/`.
4. Revisar que los GIF de la red propia se vean bien proyectados (los de 7 arcos de la iteración 5 de BFS son densos).
