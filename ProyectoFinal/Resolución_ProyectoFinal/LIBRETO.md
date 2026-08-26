# Libreto de presentación — Diagnóstico y Rediseño de la Red UCuenca

**Proyecto:** Módulo 1217 · Redes Complejas · Universidad de Cuenca
**Autores:** Jean Carlo Aucapiña · Henry Maldonado
**Deck a usar:** `presentacion_v2/main.html` (35 diapositivas, formato fijo 1280×720, navegación con flechas/espacio/ESC)
**Duración estimada:** 18–22 min de exposición + preguntas

Este documento cubre tres cosas: **qué se hizo**, **a qué se llegó** (los hallazgos que sostienen todo), y **cómo presentarlo** diapositiva por diapositiva con tiempos sugeridos.

---

## 1. Qué se hizo (resumen para quien no vio el proceso)

Se analizó la infraestructura de datos real de la Universidad de Cuenca — reconstruida a partir de 34 diagramas técnicos institucionales — como un grafo de **177 nodos y 209 aristas**, aplicando los 11 problemas del sílabo del módulo en 4 fases:

| Fase | Contenido | Problemas |
|---|---|---|
| 1 · Modelado y caracterización | Densidad, grado, MLE de ley de potencia, centralidades, puentes/articulación, modelos nulos | P1, P2 |
| 2 · Recorrido y partición | BFS/DFS, ciclos, Louvain, k-means espectral | P3, P4 |
| 3 · Optimización | Caminos mínimos (3 pesos), flujo máximo/corte mínimo, p-mediana/p-centro | P5, P6, P7 |
| 4 · Percolación y robustez | Percolación de nodos/aristas, cascadas Motter-Lai, SIR, inmunización | P8, P9 |
| 5 · Síntesis y rediseño | Índice de criticidad compuesto (ICC), propuesta de 5 enlaces nuevos | P10, P11 |

Más allá de lo pedido por el enunciado, se agregó verificación metodológica donde la heurística estándar podía estar equivocada:
- **P1:** test bootstrap (Clauset et al. 2009) para no forzar una conclusión "libre de escala" sin evidencia suficiente.
- **P7:** solver exacto de programación entera (PuLP/CBC) junto a la heurística voraz — reveló que el greedy falla en el peor caso posible (100% de gap).
- **P9:** margen crítico probado en 5 nodos (no solo 1) y SIR/inmunización promediados sobre 30 realizaciones con desviación estándar reportada.

**Entregables:**
- `Informe.md` → PDF completo (34 páginas, resumen ejecutivo + 11 problemas + conclusiones + referencias)
- `presentacion.html` — deck single-file, grafo canvas con zoom/pan libre, gráficas animadas
- `presentacion_v2/` — deck de 35 diapositivas fijas estilo "informe visual", con explorador de red interactivo (slide 09) — **este es el que usa este libreto**

---

## 2. A qué se llegó — los 3 hallazgos que sostienen la charla

Todo lo demás en la presentación es evidencia de apoyo a estos tres puntos. Si algo se corta por tiempo, estos tres NO se cortan:

### Hallazgo 1 — Es una red diseñada, no una red que creció sola
Densidad ρ=0.0134, clustering ⟨C⟩=0.034 (casi cero — la jerarquía prohíbe triángulos por diseño), asortatividad negativa r=−0.147 (los hubs solo se conectan a nodos de bajo grado). El ajuste de ley de potencia da γ̂=3.65, fuera del rango libre-de-escala (2<γ<3), con solo 20 de 177 nodos en la cola — **evidencia insuficiente para llamarla scale-free**. Comparada con Barabási-Albert: se parece superficialmente, pero el mecanismo es opuesto — fue construida top-down (core→agregación→acceso), no por crecimiento orgánico.

### Hallazgo 2 — La heurística falla exactamente donde más importa
Para p-mediana (minimizar distancia promedio) el algoritmo voraz es casi óptimo (gap ≤5.15%). Para p-centro (minimizar la distancia máxima — "que nadie quede muy lejos") **el greedy se estanca en radio 6 desde p=1 y nunca mejora**, mientras el solver exacto baja a radio 3. Gap del 100% en el peor caso. Causa: el greedy solo *añade* centros, nunca *reubica* los que ya eligió. Lección: verificar siempre con un solver exacto cuando el objetivo es min-máx.

### Hallazgo 3 — La paradoja clásica de robustez, confirmada con datos propios
La red tolera el **75%** de fallos aleatorios antes de colapsar, pero un atacante que recalcula intermediación tras cada baja la colapsa con solo el **10%** de los nodos (≈18 equipos) — ratio 7.5:1. Es estructuralmente resistente a cascadas de sobrecarga (máximo observado: 6.8% de la red, muy por debajo del umbral de riesgo de 20%) pero **vulnerable a epidemias dirigidas**: con β = 2× el umbral crítico, un brote SIR infecta en promedio el 79% de la red — reducible a ~3% inmunizando por grado con solo 20% de cobertura.

**La propuesta de rediseño (5 enlaces) mejora la operación normal (+11.9% eficiencia, −14.7% distancia, flujo a Paraíso ×19) pero NO cambia el umbral de percolación bajo ataque dirigido (f_c=0.011 antes y después)** — mejorar el día a día y blindarse contra un ataque deliberado son problemas distintos.

---

## 3. Guion diapositiva por diapositiva

Convención: **[tiempo]** es acumulado desde el inicio. Ajustar según tiempo real disponible — las diapositivas marcadas ⭐ son las que NO se deben cortar; las marcadas 💬 tienen contenido interactivo para mostrar en vivo.

### Apertura (slides 01–05) · 0:00–3:00

**01 · Portada** [0:00]
> "Vamos a mostrar qué encontramos al aplicar teoría de redes complejas a la infraestructura de datos real de la Universidad de Cuenca: 177 equipos, 209 enlaces, reconstruidos de los diagramas técnicos institucionales."
Señalar los 3 números de la portada (177·209, P1–P11, 100% gap) — son el mapa de lo que viene.

**02 · Caso de estudio** [0:30]
Explicar la topología de 3 capas (core → agregación → acceso) y que 6 campus + 2 sedes se conectan vía nube MPLS externa. "INTERNET-MPLS es el único punto de salida — eso va a importar mucho más adelante."

**03 · Vista estructural** [1:15]
Mostrar el diagrama simplificado. Señalar el dato incómodo: "Central y Balzay sí tienen núcleo doble real. Paraíso no — solo tiene un switch de core, aunque el informe técnico institucional decía que sí había redundancia."

**04 · Agenda** [2:00]
Repaso rápido de las 5 fases y su peso — 20 segundos, sin detenerse.

**05 · Resumen ejecutivo** ⭐ [2:20]
Leer los 3 hallazgos en voz alta, uno por uno, con pausa entre cada uno. Esta diapositiva es el "spoiler" deliberado — el resto de la charla es la evidencia de estos 3 puntos.

---

### Fase 1 — Caracterización (slides 06–10) · 3:00–7:30

**06 · P1 Métricas básicas** [3:00]
ρ=0.0134, ⟨k⟩=2.362, 64% de nodos con grado 1. "La red es dispersa por diseño: cada equipo solo se conecta a su vecino inmediato en la jerarquía."

**07 · Distribución de grado / MLE** [3:50]
Explicar brevemente qué es una red libre de escala y por qué se probó. "γ̂=3.65 queda fuera del rango 2–3, y solo 20 de 177 nodos entran en la cola de la distribución — no hay evidencia suficiente para decir que esta red sea scale-free, aunque a primera vista lo pareciera."

**08 · Centralidades** [4:45]
DATCC-2A-C3 lidera grado y betweenness; INTERNET-MPLS lidera closeness pese a tener pocas conexiones directas. "Grado e intermediación no son lo mismo: CPAR-C10 tiene mucha intermediación con grado modesto, porque todo el tráfico de Paraíso pasa forzosamente por él."

**09 · Explora la red real** 💬⭐ [5:30] — **momento interactivo, tomarse 90 segundos**
> "Aquí está la red completa, los 177 nodos reales, no una ilustración." Pasar el cursor sobre 2–3 nodos (mostrar la ficha lateral). Cambiar a modo "intermediación" para que los hubs crezcan visualmente. **Apretar "Simular ataque dirigido"** y dejar correr la animación completa (~6 segundos) mientras se narra: "Esto va a eliminar nodos en orden de intermediación descendente — miren cómo cae la componente gigante." Señalar el contador P∞ cayendo. Esto anticipa el Hallazgo 3 sin decirlo todavía.

**10 · Puentes y articulación** ⭐ [7:00]
47 puntos de articulación, 141 puentes (67% de los enlaces). "Y aquí está la contradicción con el informe técnico: dice que Paraíso tiene redundancia de núcleo completa. En los datos, Paraíso tiene un solo switch de core — el 'doble enlace' que menciona el informe es en realidad agregación de puertos hacia el mismo equipo, no una segunda ruta."

---

### Fase 1 cont. — Modelos nulos (slides 11–12) · 7:30–8:30

**11 · Modelos nulos ER/CM** [7:30]
"¿Qué de lo que vemos se explica solo por cuántas conexiones tiene cada nodo? El modelo de configuración reproduce la asortatividad negativa, pero no el clustering ni la distancia media — la jerarquía impone algo que va más allá de la secuencia de grados."

**12 · Barabási-Albert** [8:00]
30 segundos: "Se parece superficialmente a una red de crecimiento preferencial, pero el mecanismo es opuesto: esta red fue diseñada de arriba hacia abajo, no creció nodo por nodo."

---

### Fase 2 — Recorrido y comunidades (slides 13–15) · 8:30–10:00

**13 · BFS/DFS y ciclos** [8:30]
Número ciclomático μ=33, confirmado exactamente por DFS. "Los ciclos están en Central (21) y Balzay (9) — donde el informe dice que hay redundancia real. Paraíso, Yanuncay y Hospitalidad tienen cero ciclos: son árbol puro, cualquier fallo aísla permanentemente esos edificios."

**14 · Louvain** [9:10]
Q=0.7632, muy alto. "Louvain no ve campus, ve edificios — detecta 14 comunidades, más finas que los 8 campus reales, porque las subestructuras densas por edificio pesan más que la etiqueta administrativa."

**15 · k-means espectral** [9:40]
20 segundos: coincide 86% con Louvain, ligeramente mejor contra la partición real por campus — mencionar y avanzar.

---

### Fase 3 — Optimización (slides 16–20) · 10:00–14:00

**16 · Caminos mínimos** [10:00]
Tres modelos de peso (saltos, latencia, carga) dan rankings distintos. "Dijkstra repetido es 7 a 10 veces más rápido que Floyd-Warshall en esta red porque es dispersa — Floyd-Warshall solo compensa en grafos densos."

**17 · Flujo máximo** [10:45]
Central puede sacar 43 Gbps hacia Internet; Yanuncay y Hospitalidad solo 1 Gbps. "El corte mínimo no siempre coincide con los puentes de P1 — mide algo distinto: capacidad, no solo conectividad."

**18 · p-Mediana** [11:30]
"Para minimizar la distancia promedio, la heurística es casi tan buena como el óptimo — gap máximo 5%."

**19 · p-Centro** ⭐ [12:00]
"Pero para minimizar la distancia MÁXIMA — que ningún equipo quede muy lejos — la heurística se estanca en radio 6 desde el primer colector y nunca mejora, aunque agreguemos más. El solver exacto sí baja a radio 3."

**20 · El gap del 100%** ⭐ [12:45] — **diapositiva de pausa dramática, dejar el número solo en pantalla 3–4 segundos antes de hablar**
> "Cien por ciento de gap. La heurística estándar, la que cualquiera implementaría primero, se equivoca en el doble en el peor caso posible — y el enunciado ni siquiera lo pedía verificar. Lo verificamos nosotros con un solver de programación entera, y por eso lo encontramos."

---

### Fase 4 — Percolación y robustez (slides 21–26) · 14:00–18:00

**21 · Percolación de nodos** [14:00]
"Esto usa el mismo marco teórico que nuestro trabajo de Teoría de Percolación —ahí lo probamos en una red ISP de 9 nodos—, aquí lo aplicamos empíricamente a los 177 nodos reales." f_c=0.75 aleatorio vs 0.10 dirigido.

**22 · Percolación de aristas** [14:45]
"La eficiencia cae antes de que la red se rompa: con solo el 5% de los nodos de mayor grado eliminados, la eficiencia ya cayó a la mitad, aunque la red 'siga conectada' en el sentido de componente gigante."

**23 · La paradoja de la robustez** ⭐ [15:30] — segunda pausa dramática
> "75% versus 10%. Ratio de 7.5 a 1. Esta red tolera perder tres cuartas partes de sus equipos al azar — pero un atacante que sabe qué está haciendo la colapsa con dieciocho equipos."

**24 · Cascadas Motter-Lai** [16:15]
"Buena noticia: ni con cero margen de tolerancia una falla en cascada supera el 6.8% de la red — muy por debajo del umbral de riesgo del 20%. Los 132 switches de acceso de grado 1 no redistribuyen carga al fallar, así que la cascada se frena en agregación."

**25 · Modelo SIR** [17:00]
"Pero sí es vulnerable a epidemias: el umbral crítico es bajo (0.186) porque los hubs concentran mucha conexión. Con una tasa de contagio del doble de ese umbral, el brote promedio infecta el 79% de la red."

**26 · Inmunización** [17:45]
"La defensa es simple y barata: vacunar por grado, no al azar. Con solo 20% de cobertura bajamos de 79% a 2.8% de afectación."

---

### Síntesis y cierre (slides 27–35) · 18:00–21:00

**27 · Índice ICC** [18:00]
"Combinamos las cuatro fases en un solo ranking: intermediación, articulación, participación en el corte mínimo, y daño en cascada. INTERNET-MPLS sale como el nodo más crítico de toda la red."

**28 · Cinco enlaces propuestos** [18:40]
Repasar rápido la tabla E1–E5, señalando que cada uno resuelve un problema específico del ranking ICC — no son arbitrarios.

**29 · Antes/después** ⭐ [19:15]
"Con solo 5 enlaces nuevos: 14.7% menos distancia media, 11.9% más eficiencia, y el flujo hacia Paraíso se multiplica por 19." Pausa. **"Pero el umbral de percolación bajo ataque dirigido no cambia — 0.011 antes y después. Mejorar la operación normal y blindarse contra un atacante deliberado son problemas distintos, y esta intervención solo resuelve el primero."**

**30 · Comparación con alternativas** [20:00]
20 segundos: "Probamos conectar simplemente los nodos de mayor grado — mejora más la eficiencia agregada, pero no resuelve el problema real de Paraíso. Nuestra propuesta es la única que ataca directamente los 4 nodos más críticos del ranking."

**31 · Limitaciones** [20:20]
Mencionar brevemente: capacidades nominales no tráfico medido, no hay verificación física de puertos disponibles, Motter-Lai asume redistribución instantánea que en la práctica limitan STP/HSRP.

**32, 34 · Preguntas de la guía** — usar solo si sobra tiempo o si preguntan algo que ya está ahí; si no, saltar directo a conclusiones.

**33 · Conclusiones** ⭐ [20:40]
Cerrar repitiendo los 3 hallazgos del resumen ejecutivo, y la recomendación final: "E4 y E5 se pueden ejecutar ya, mismo campus, costo mínimo. E1 y E3 requieren negociar con el proveedor. E2 es la inversión de mayor impacto. Y, más allá de cualquier enlace nuevo: vacunar por grado es la política de mayor retorno con el menor presupuesto."

**35 · Referencias y cierre** [21:00]
Cierre.

---

## 4. Preguntas probables y respuesta corta

**¿Por qué no puede ser scale-free si tiene hubs tan grandes?**
Tener algunos nodos de grado alto no basta — se necesita que la *distribución completa* siga una ley de potencia con exponente entre 2 y 3, y aquí solo 20 de 177 nodos (11%) caen en el rango donde el ajuste es mejor, con γ̂=3.65 fuera de ese rango. Es insuficiente para afirmarlo con rigor.

**¿Por qué confiar en el solver exacto y no en la heurística si son casi iguales en p-mediana?**
Justamente eso es la lección: para p-mediana (min-suma) son casi iguales, pero para p-centro (min-máx) divergen hasta el 100%. No hay forma de saber de antemano cuál objetivo se comporta mal sin verificar.

**¿Por qué la red tolera cascadas pero no epidemias, si ambas involucran los mismos hubs?**
Las cascadas de carga solo se propagan a través de nodos que *redistribuyen* tráfico — y el 64% de los nodos (grado 1) no lo hacen, así que la cascada se frena rápido. Una epidemia SIR se propaga por *contacto*, sin importar si el nodo redistribuye o no — cualquier vecino infectado puede contagiar a cualquier otro, así que los hubs sí importan como amplificadores.

**¿Los 5 enlaces son la solución óptima?**
No — encontrar el conjunto óptimo de k enlaces es NP-difícil. Es una heurística guiada por el ranking ICC, verificada contra dos alternativas (por grado, por intermediación) y superior en la métrica operativa más relevante (flujo hacia Paraíso), pero no hay garantía de optimalidad combinatoria — se dice explícitamente en las limitaciones.

**¿Esto sirve para ciberseguridad?**
Los hallazgos son de *disponibilidad* (qué tan conectada sigue la red), no de *seguridad* (si un atacante puede entrar). Son complementarios pero no intercambiables — se aclara en el ítem de limitaciones de P11.

---

## 5. Notas técnicas para quien presente

- El deck `presentacion_v2/main.html` se abre localmente con doble clic — no necesita servidor ni internet, salvo la carga de Google Fonts (si no hay internet, cae a fuente del sistema, sigue siendo legible).
- Navegación: flechas ← → o espacio para avanzar, Home/End para ir al inicio/final, ESC abre el índice en cuadrícula (clic en cualquier miniatura salta ahí).
- La diapositiva 09 (explorador) es la única con lógica interactiva real — practicar el flujo de "hover → cambiar modo de color → simular ataque → restaurar" antes de presentar en vivo, para no perder tiempo en el momento.
- Si el proyector recorta el frame de 1280×720, verificar con `F11` (pantalla completa del navegador) antes de empezar — el deck se autoescala al tamaño de ventana.
