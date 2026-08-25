## Anexo C — Metodología Detallada

Esta sección recoge, organizados por problema e ítem, los bloques de **implementación paso a paso** (pseudocódigo, estructuras de datos, justificación de librerías, derivaciones extendidas) que se movieron fuera del cuerpo principal del informe para cumplir el límite de 30 páginas. El cuerpo conserva en cada caso la fórmula central, la tabla de resultados y el análisis; aquí se documenta el **cómo** se implementó cada método.

---

### P2 — Modelos Nulos y Visualización

#### Ítem 3 · Algoritmos de layout usados en las visualizaciones propias

**BFS por profundidad desde `INTERNET-MPLS` (visualización por campus):** se calcula la profundidad BFS de cada nodo desde el gateway; la posición Y es proporcional a esa profundidad (gateway abajo, acceso arriba) y dentro de cada fila los nodos se ordenan por campus para agrupar colores. El tamaño del nodo refleja su capa (core/WAN más grandes). Se prefirió sobre Fruchterman-Reingold porque la profundidad BFS desde el gateway es la métrica operacional relevante (saltos a internet) y un layout de fuerzas no la expone directamente.

**Kamada-Kawai escalado ×3.5 (visualización por betweenness):** asigna a cada par de nodos una longitud ideal de arco proporcional a su distancia en el grafo y minimiza la diferencia con las distancias euclídeas dibujadas; las posiciones normalizadas en $[-1,1]$ se multiplican por 3.5 para separar los nodos sin alterar su estructura relativa, reduciendo solapamiento entre los círculos grandes del centro (figura 18×14", tamaño máximo de nodo 1200 unidades). Kamada-Kawai coloca los nodos más centrales —los de mayor betweenness— en el centro geométrico del dibujo.

---

### P3 — BFS y DFS sobre la Red

#### Ítem 1 · Estructura de datos empleada e implementación (BFS y DFS desde cero)

Ambos algoritmos se implementaron **desde cero** sin usar `nx.bfs_tree`, `nx.dfs_tree` ni funciones equivalentes de NetworkX. Solo se usa `G.neighbors(u)` para acceder a los vecinos de cada nodo.

**BFS — Cola FIFO (`collections.deque`)**

La cola FIFO (First In, First Out) es la estructura clave de BFS. El primer nodo en entrar es el primero en procesarse, lo que garantiza que se exploren primero los nodos más cercanos al origen:

```
cola = deque([origen])
mientras cola no esté vacía:
    u = cola.popleft()          # sacar del frente — O(1)
    para cada vecino v de u:
        si v no visitado:
            cola.append(v)      # agregar al final — O(1)
```

Si se reemplazara la cola por una pila el algoritmo dejaría de ser BFS — procesaría primero el último nodo agregado y se convertiría en DFS.

**DFS — Pila LIFO implícita (recursión)**

DFS usa una pila LIFO (Last In, First Out). En la implementación recursiva, la pila de llamadas del sistema operativo actúa como pila implícita: cada llamada recursiva apila un nuevo frame; cuando no hay más vecinos sin visitar, la función retorna y desapila:

```
función dfs_recursivo(u, padre):
    marcar u como visitado
    tiempo_descubrimiento[u] = ++t
    para cada vecino v de u:
        si v no visitado:
            arista_árbol(u, v)
            dfs_recursivo(v, u)       # ← apilar
        sino si v ≠ padre:
            arista_retroceso(u, v)    # ← ciclo detectado
    tiempo_finalización[u] = ++t      # ← desapilar
```

**Comparación de estructuras y complejidades:**

| Algoritmo | Estructura de datos | Por qué esa estructura | Complejidad temporal | Complejidad espacial |
|-----------|--------------------|-----------------------|---------------------|---------------------|
| BFS | Cola FIFO (`deque`) | Procesa nodos por orden de llegada → explora nivel a nivel → garantiza camino más corto | $O(n + m)$ | $O(n)$ |
| DFS | Pila LIFO (recursión) | Procesa el último nodo apilado → va tan profundo como puede antes de retroceder → detecta ciclos | $O(n + m)$ | $O(n)$ |

Ambos visitan cada nodo una vez ($n$ operaciones) y cada arista dos veces — una desde cada extremo ($2m$ operaciones) — de ahí $O(n+m)$. El espacio adicional $O(n)$ corresponde al conjunto de nodos visitados y la cola/pila en el peor caso.

#### Ítem 4 · Cómo DFS detecta ciclos (implementación desde cero)

Durante el DFS, cada arista se clasifica automáticamente:

- **Arista de árbol** $(u \to v)$: $v$ no había sido visitado → construye el árbol DFS.
- **Arista de retroceso** $(u \to w)$: $w$ ya fue visitado y es ancestro de $u$ → **cierra un ciclo**.

Cada arista de retroceso corresponde exactamente a un ciclo independiente. El número ciclomático predice cuántas deben encontrarse: $\mu = m - n + 1 = 209 - 177 + 1 = 33$.

La función `detectar_ciclos()` de `problema3.py` ejecuta `dfs()` desde el switch de core `DATCC-2A-C3`, recorre los 177 nodos y 209 aristas, y registra cada arista de retroceso encontrada.

**Esquema de por qué aparece un ciclo (doble uplink) vs. no aparece (uplink único):**

```
 Caso CON ciclo (redundancia):        Caso SIN ciclo (árbol):

     C2 ————— C3                           C10
      \       /                             |
       \     /    ← triángulo              AGG-Y   ← un solo uplink
        AGG-X     = 1 ciclo                |
           |                             acceso
         acceso
```

En el caso con ciclo, si el cable `AGG-X → C2` falla, el tráfico toma `AGG-X → C3`. En el caso sin ciclo, si el cable `AGG-Y → C10` falla, todos los equipos de acceso quedan sin conexión.

---

### P4 — Comunidades y Modularidad

#### Ítem 1 · Cómo funciona Louvain (implementación en dos fases)

Louvain no fija las comunidades de antemano y luego mide Q — las construye **maximizando Q en cada paso**:

**Fase 1 — Reasignación local:** se asigna a cada nodo su propia comunidad (al inicio hay tantas comunidades como nodos). Luego, para cada nodo, se calcula cuánto cambiaría Q si ese nodo se uniera a la comunidad de cada uno de sus vecinos. Si algún movimiento incrementa Q, el nodo se mueve a la comunidad que más lo incrementa. Se repite para todos los nodos hasta que ningún movimiento mejore Q.

```
Inicio: 177 nodos → 177 comunidades individuales

Para cada nodo u:
  Para cada vecino v de u:
    ¿Q sube si u se une a la comunidad de v?
    Si sí → mover u a esa comunidad
Repetir hasta que ningún movimiento mejore Q
```

**Fase 2 — Contracción:** cada comunidad detectada se colapsa en un único super-nodo. Los enlaces entre comunidades se convierten en enlaces entre super-nodos (con pesos proporcionales al número de aristas originales). Sobre este grafo reducido se repite la Fase 1.

```
Iteración 1: 177 nodos → agrupa en ~40 comunidades
Iteración 2: 40 super-nodos → agrupa en ~14 comunidades
Iteración 3: 14 super-nodos → ningún movimiento mejora Q → fin
```

El algoritmo para cuando ningún movimiento en ningún nodo incrementa Q — en ese punto la partición es un **máximo local de Q** y se reportan el número de comunidades y el valor final de Q.

#### Ítem 4 · k-means espectral — fuente del código y adaptación

**Fuente del código:** adaptado de `codigo_referencia/kmeans/ejemplo1.jl` (Dr. Fabián Astudillo-Salinas, Módulo 1217 — Redes Complejas). El original implementa k-means desde cero en Julia con inicialización K-means++ (`init_plusplus`), paso de asignación (`assign_clusters`), actualización de centroides (`update_centroids`) y métrica WCSS de convergencia. La adaptación a Python usa `sklearn.cluster.KMeans` con `init="k-means++"`, que implementa los mismos pasos internamente. El embedding espectral (vectores propios del Laplaciano) sustituye los datos numéricos del ejemplo original por coordenadas topológicas de la red.

**Por qué hace falta un embedding antes de aplicar k-means:** un grafo no tiene coordenadas euclídeas naturales — los nodos no existen en un espacio geométrico, solo existen conexiones entre ellos. Aplicar k-means directamente sobre un grafo no tiene sentido porque k-means mide distancias euclídeas y en un grafo la distancia entre nodos se mide en saltos, no en metros.

La solución es el **embedding espectral**: transformar el grafo en vectores antes de aplicar k-means. Cada nodo recibe un vector de coordenadas calculado a partir de los $k$ primeros vectores propios del Laplaciano normalizado $L_{\text{sym}}$. El truco matemático es que nodos que están bien conectados entre sí quedan cerca en ese espacio vectorial — la estructura de conexiones del grafo se traduce en proximidad euclídea.

```
Grafo (conexiones)  →  Laplaciano  →  vectores propios  →  coordenadas por nodo
                                                              ↓
                                                         k-means (distancia euclídea)
```

---

### P5 — Caminos Mínimos con Múltiples Métricas de Peso

#### Ítem 4 · Rutas salto a salto completas (par de equipos de acceso más distante por modelo)

**Modelo Saltos (11 hops, `ENF-2B-A122` → `POST-2A-A66`):**

```
ENF-2B-A122           (acceso, Enfermería)
  → ENF-2B-A22        (acceso, Enfermería)
  → CP-ENFERMERIA-D1  (agregación, Campus Central)
  → CPAR-C10          (core, Campus Huayna-Capac)
  → ROUTER-CAMPUS-HUAYNA-CAPAC  (WAN salida)
  → INTERNET-MPLS     (nube MPLS)
  → PE2-CENTRAL       (PE Campus Central)
  → DATCC-2A-C3       (core, Campus Central)
  → CC-FILOSOFIA-A-D108 (agregación)
  → POST-1A-A64       (acceso, Posgrados)
  → POST-1A-A65       (acceso, Posgrados)
  → POST-2A-A66       (acceso, Posgrados)   ← 11 saltos
```

**Modelo Latencia (34.70 ms, `POST-2A-A66` → `QUIN-1A-A128`):**

```
POST-2A-A66           (acceso, 100 Mbps → +10.10 ms)
  → POST-1A-A65       (acceso, 100 Mbps → +10.10 ms)
  → POST-1A-A64       (acceso, 100 Mbps → +10.10 ms)
  → CC-FILOSOFIA-A-D108 (agregación, 1 Gbps → +1.10 ms)
  → DATCC-2A-C3       (core, 10 Gbps → +0.20 ms)
  → PE2-CENTRAL       (PE WAN, 10 Gbps → +0.15 ms)
  → INTERNET-MPLS     (nube MPLS → +0.20 ms)
  → PE2-BALZAY        (PE Balzay, 10 Gbps → +0.20 ms)
  → DT-0A-C13         (core Balzay, 10 Gbps → +0.15 ms)
  → CB-EADMI-D6       (agregación, 1 Gbps → +0.20 ms)
  → BAL-EADM-D3       (agregación, 1 Gbps → +1.10 ms)
  → QUIN-1A-A117      (acceso, 100 Mbps → +1.10 ms)
  → QUIN-1A-A128      (acceso, 100 Mbps)   ← 34.70 ms acumulados
```

**Modelo Carga (utilización acumulada = 1.7057, `ARQ-1E-A92` → `INV-1B-A162`):**

```
ARQ-1E-A92            (acceso, Arquitectura — carga=0.9664)
  → ARQ-1E-A91        (acceso, Arquitectura — carga=0.0963)
  → CC-ARQUITECTURA-D107 (agregación — carga≈0.0000)
  → DATCC-2A-C3       (core Central — carga≈0.0000)
  → PE2-CENTRAL       (PE WAN — carga≈0.0000)
  → INTERNET-MPLS     (nube MPLS — carga≈0.0000)
  → ROUTER-CAMPUS-HUAYNA-CAPAC (WAN salida — carga≈0.0000)
  → CPAR-C10          (core Huayna-Capac — carga=0.0318)
  → CP-INVESTIGACION-D5 (agregación — carga=0.0085)
  → INV-1B-A62        (acceso — carga=0.0619)
  → INV-1B-A162       (acceso, Investigación — carga=0.5409)   ← 1.7057 total
```

---

#### Ítem 1 · Justificación de no negatividad de los pesos (requisito de Dijkstra)

Dijkstra exige $w(u,v) \geq 0$ para todo enlace; si algún peso fuera negativo el algoritmo podría devolver distancias incorrectas y habría que reemplazarlo por Bellman-Ford ($O(nm)$). Se justifica a continuación que los tres modelos cumplen esta condición:

| Modelo | Expresión | Por qué $w \geq 0$ |
|--------|-----------|-------------------|
| Saltos | $w = 1$ | Constante positiva por definición. |
| Latencia | $w = \alpha + \beta / c(u,v)$ | $\alpha = 0.1\ \text{ms} > 0$, $\beta = 1000\ \text{Mbps·ms} > 0$, $c(u,v) > 0$ (capacidad estimada mínima = 100 Mbps). La suma de dos términos positivos es positiva. |
| Carga | $w = \max(b(u,v)/c(u,v),\ 10^{-6})$ | $b(u,v) \geq 0$ (tráfico no puede ser negativo) y $c(u,v) > 0$, por lo que el cociente es $\geq 0$. El `max` con $10^{-6}$ evita además el caso $w = 0$ en aristas sin tráfico medido. |

La verificación en código confirma los tres modelos en tiempo de ejecución: si cualquier arista produjera $w < 0$, el programa emite una advertencia explícita. En esta red los tres modelos pasan sin advertencias.

**Dijkstra** — implementación propia con cola de prioridad (`heapq`), complejidad $O((n+m)\log n)$.

**Floyd-Warshall** — implementación triple bucle anidado, complejidad $O(n^3)$.

---

### P6 — Flujo Máximo y Corte Mínimo

#### Ítem 3 · Longitudes de caminos aumentantes por campus (FF-DFS vs EK-BFS)

| Campus | FF-DFS (longitudes) | EK-BFS (longitudes) |
|--------|---|---|
| Central | [9,10,5,5,5,5,6,6,5,6,6,6,8,8,8,8,8,7,7,7,7,7,6,6,6,6,6,6,6,3,6,6,6,8,8,8,8,8,8,8,8,8,8] | [3,5,5,5,5,5,5,5,5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,7,8,8,8,8,8,8,8,8,8,9,10] |
| Balzay | [10,6,5,5,5,5,5,5,5,5,5,6,6,6,6,6,6,6,6,6,6,7,6] | [5,5,5,5,5,5,5,5,5,5,6,6,6,6,6,6,6,6,6,6,6,6,7] |
| Paraíso | [5,5,5,5,5,5,5,5,5,5] | [5,5,5,5,5,5,5,5,5,5] |
| Yanuncay | [4] | [4] |
| Hospitalidad | [3] | [3] |
| Sede C. Histórico | [9,4,6] | [4,6] |
| Sede Museo | [8,5,7] | [5,6] |

En Central, EK-BFS empieza por el camino más corto (3 saltos) y las longitudes solo crecen (lema de Edmonds-Karp); FF-DFS empieza por caminos largos (9, 10 saltos) sin garantía de orden. En las Sedes, DFS comienza con un camino largo innecesario que BFS evita, de ahí la diferencia de 3 vs 2 iteraciones.

**Cortes mínimos completos:**
- Central: `DATCC-2A-C3→PE2-CENTRAL` (20 000), `DATCC-2A-C3→FORTIGATE-1800F-CENTRAL` (10 000), `DATCC-2A-C2→FORTIGATE-1800F-CENTRAL` (10 000), `ROUTER-CAMPUS-CENTRO-HISTORICO→ROUTER-L2TP-BALZAY` (1 000), `ROUTER-CAMPUS-MUSEO→ROUTER-L2TP-BALZAY` (1 000), `CCJ-CJURIDICO-D4→INTERNET-MPLS` (1 000).
- Sede C. Histórico: `SW-ARUBA-CENTRO-HISTORICO→DATCC-2A-C3` (10 000) + `ROUTER-CAMPUS-CENTRO-HISTORICO→ROUTER-L2TP-BALZAY` (1 000).
- Sede Museo: `SW-ARUBA-MUSEO→DATCC-2A-C2` (10 000) + `ROUTER-CAMPUS-MUSEO→ROUTER-L2TP-BALZAY` (1 000).

---

#### Ítem 1 · Función de capacidad c(u,v) — supuestos adicionales documentados

- Los 4 enlaces WAN estimados corresponden a conexiones MPLS inferidas del informe (rol `inferido`) que el diagrama no dibuja pero el texto describe como conexiones de 10 Gbps al *provider edge*.
- Ninguna arista de respaldo (`rol=respaldo`, 12 en total) cae en la categoría acceso–acceso; todas tienen al menos un extremo de agregación o core y heredan 1 000 Mbps o 10 000 Mbps respectivamente. Los enlaces de respaldo no reciben reducción de capacidad porque en la red UCuenca el respaldo es activo-pasivo conmutado, no degradado.

#### Ítem 2 · Implementaciones reutilizadas — Ford-Fulkerson (DFS) y Edmonds-Karp (BFS)

- **Ford-Fulkerson con DFS** — adaptado de `codigo_referencia/ford-fulkerson/ford_fulkerson.jl` (Dr. Fabián Astudillo-Salinas). La función `buscar_camino_dfs()` del original en Julia usa una pila explícita; aquí se porta a Python manteniendo la misma lógica. Busca *cualquier* camino aumentante, no necesariamente el más corto. Complejidad: $O(E \cdot f^*)$.

- **Edmonds-Karp con BFS** — adaptado de `codigo_referencia/edmonds-karp/edmonds_karp.jl` (Dr. Fabián Astudillo-Salinas). Siempre encuentra el camino aumentante con **menos arcos** usando BFS. Esto garantiza que las longitudes de los caminos nunca decrezcan entre iteraciones, lo que acota el número de aumentos a $O(V \cdot E)$ y la complejidad total a $O(V \cdot E^2)$.

**Modelado del super-nodo fuente:** para cada campus se crea un **super-nodo fuente** $s$ conectado con capacidad infinita a todos los switches de acceso del campus. El sumidero es `INTERNET-MPLS`.

---

### P7 — p-Mediana y p-Centro

#### Ítem 2 · Formulación completa reutilizada para el solver exacto (PuLP/CBC)

$$\text{p-Mediana:}\quad \min \sum_i \sum_j d_{ij}\,x_{ij} \quad \text{s.a.} \quad \sum_j y_j = p,\ \sum_j x_{ij}=1\ \forall i,\ x_{ij}\le y_j,\ x_{ij},y_j\in\{0,1\}$$

$$\text{p-Centro:}\quad \min R \quad \text{s.a.} \quad \sum_j y_j = p,\ \sum_j x_{ij}=1\ \forall i,\ \sum_j d_{ij}x_{ij}\le R\ \forall i,\ x_{ij}\le y_j$$

Con 177 nodos, CBC resuelve ambos modelos para los cuatro valores de $p$ en segundos, certificando `Optimal` en todos los casos. Como explorar todas las combinaciones posibles ($\binom{177}{5} \approx 34$ millones para $p=5$) sería inviable con fuerza bruta, se implementó una **heurística voraz** (añade un colector a la vez, el que más mejora el objetivo) y, siguiendo lo que pide el enunciado ("si les es posible, con un solver de programación entera"), también el **óptimo exacto**.

---

### P9 — Fallas en Cascada y Epidemias SIR

#### Ítem 1 · Algoritmo implementado — modelo de carga-capacidad (Motter-Lai)

El modelo se ejecuta de la siguiente forma para cada nodo disparador:

1. **Inicialización:** calcular el betweenness $B_i$ de todos los nodos en la red intacta. Asignar $C_i = (1+\alpha) \cdot B_i$ como capacidad máxima de cada nodo.
2. **Fallo inicial:** eliminar el nodo disparador del grafo.
3. **Redistribución:** recalcular el betweenness de todos los nodos restantes — los caminos que antes pasaban por el nodo caído ahora pasan por rutas alternativas, aumentando la carga de esos nodos.
4. **Detección de nuevos fallos:** identificar todos los nodos cuyo nuevo betweenness supera su capacidad $C_i$.
5. **Propagación:** eliminar esos nodos del grafo y volver al paso 3.
6. **Criterio de parada:** la cascada termina cuando ningún nodo activo supera su capacidad, o cuando no quedan nodos.

El resultado de cada ejecución es el conjunto total de nodos fallidos (disparador + caídos en cascada) y el número de pasos que tomó la propagación. Se repite para todo $\alpha \in \{0, 0.05, 0.10, 0.20, 0.50, 1.00, 1.50, 2.00\}$ y para cada nodo posible como disparador, para identificar los más peligrosos.

#### Ítem 3 · Diseño del experimento SIR

La predicción teórica de campo medio establece $\tau_c = \langle k \rangle / \langle k^2 \rangle = 0.1861$. Para verificarla, el código fija $\gamma = 0.1$ (probabilidad de recuperación por paso) y elige dos valores de $\beta$ a ambos lados del umbral: $\beta_{\text{sub}} = \tau_c / 2$ y $\beta_{\text{sup}} = 2\tau_c$. Estos son **parámetros de diseño del experimento**, no propiedades de la red — su propósito es mostrar los dos regímenes contrastantes.

El SIR es un proceso **estocástico** (cada contagio y cada recuperación es un sorteo aleatorio): una sola corrida puede sub- o sobre-estimar el alcance real del brote. Por eso ambos casos se promedian sobre **30 realizaciones independientes** (semillas distintas) y se reporta $R_{\text{final}}$ como media ± desviación estándar.

#### Ítem 4 · Diseño del experimento de inmunización

Se comparan cuatro estrategias con el mismo número de nodos inmunizados (misma fracción $f$ del total): aleatoria, por grado (parchear primero los switches más conectados), por betweenness (parchear los más intermediarios) y por vecino aleatorio (proxy práctico que no requiere conocer la topología completa). El escenario usa $\beta = 2\tau_c = 0.3722$ (régimen sobre-crítico) para que la diferencia entre estrategias sea visible. Igual que el SIR base, cada punto se promedia sobre 30 realizaciones — incluida la selección aleatoria de inmunes en las estrategias "aleatoria" y "por vecino", que también son estocásticas.
