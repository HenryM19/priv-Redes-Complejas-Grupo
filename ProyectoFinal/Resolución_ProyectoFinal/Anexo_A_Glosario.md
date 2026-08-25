## Notación matemática

A lo largo del informe se usa la siguiente notación estándar de teoría de grafos:

| Símbolo | Significado |
|---------|-------------|
| $G = (V, E)$ | Grafo: conjunto de nodos $V$ y conjunto de aristas $E$ |
| $V$ | Conjunto de todos los nodos (equipos de red). $\|V\| = n$ |
| $E$ | Conjunto de todas las aristas (cables). $\|E\| = m$ |
| $n = \|V\|$ | Número total de nodos. En UCuenca: $n = 177$ |
| $m = \|E\|$ | Número total de aristas. En UCuenca: $m = 209$ |
| $u, v, w$ | Nodos individuales del grafo |
| $(u, v) \in E$ | Arista que conecta los nodos $u$ y $v$ |
| $\mathcal{N}(v)$ | Vecindad de $v$: conjunto de nodos directamente conectados a $v$ |
| $k_v$ | Grado del nodo $v$: número de aristas que inciden en $v$ |
| $d(u, v)$ | Distancia más corta (en saltos) entre los nodos $u$ y $v$ |
| $S \subseteq V$ | Subconjunto de nodos (por ejemplo, una comunidad o campus) |
| $G - v$ | Subgrafo resultante de eliminar el nodo $v$ y todas sus aristas |
| $G - e$ | Subgrafo resultante de eliminar la arista $e$ |
| $\kappa(G)$ | Número de componentes conexas del grafo $G$ |
| $A$ | Matriz de adyacencia: $A_{uv} = 1$ si $(u,v) \in E$, 0 en caso contrario |
| $D$ | Matriz diagonal de grados: $D_{vv} = k_v$ |
| $\sigma_{st}$ | Número total de caminos más cortos entre los nodos $s$ y $t$ |
| $\sigma_{st}(v)$ | Número de caminos más cortos entre $s$ y $t$ que pasan por $v$ |
| $\langle \cdot \rangle$ | Promedio sobre todos los nodos: $\langle k \rangle = \frac{1}{n}\sum_v k_v$ |
| $f, q$ | Fracción de nodos/aristas eliminados en experimentos de percolación |
| $\beta, \gamma$ | Tasa de infección y recuperación en el modelo SIR |
| $c(u,v)$ | Capacidad del enlace $(u,v)$ en Mbps |
| $w(u,v)$ | Peso del enlace $(u,v)$ según el modelo de costo elegido |

---

## Glosario de Conceptos Clave

Esta sección recoge una explicación en lenguaje llano de todos los conceptos matemáticos usados en el informe. Están ordenados temáticamente. Las definiciones formales se encuentran en cada sección de fase.

---

### Conceptos básicos de grafos

**Grafo:** un conjunto de *nodos* (equipos de red) conectados por *aristas* (cables). Se escribe $G = (V, E)$ donde $V$ es el conjunto de nodos y $E$ el de aristas. *En palabras simples:* un mapa donde los puntos son equipos y las líneas son cables.

**Grafo no dirigido:** los cables no tienen dirección: si A está conectado a B, también B está conectado a A. *En redes físicas Ethernet*, los datos pueden fluir en ambas direcciones por el mismo cable.

**Grafo conexo:** existe al menos un camino entre cualquier par de nodos. *En palabras simples:* no hay "islas" aisladas — siempre hay una ruta, aunque sea larga, para llegar de cualquier equipo a cualquier otro.

**Componente gigante (GCC):** el subconjunto más grande de nodos donde todos están conectados entre sí. En redes de infraestructura, idealmente la GCC es toda la red.

**Densidad $\rho$:** fracción de los posibles cables que realmente existen. Una densidad de 0.013 significa que solo el 1.3% de los cables posibles están instalados. *En palabras simples:* qué tan "poblado de cables" está el grafo respecto al máximo teórico.

**Árbol:** grafo conexo sin ciclos. Tiene exactamente $n-1$ aristas. *En palabras simples:* como el árbol genealógico — hay un único camino entre cualquier par de nodos, sin "volver por donde se vino".

---

### Grado y distribución

**Grado de un nodo $k_v$:** número de cables que salen del equipo $v$. Un switch con 5 puertos usados tiene grado 5. *En infraestructura:* el grado indica cuántos equipos están directamente conectados a este switch.

**Grado medio $\langle k \rangle$:** promedio de grados de todos los nodos. Siempre igual a $2m/n$ porque cada cable añade 1 al grado de ambos extremos. En UCuenca: 2.36 cables por equipo en promedio.

**Distribución de grado $P(k)$:** histograma normalizado de grados. $P(3) = 0.034$ significa que el 3.4% de los nodos tienen exactamente 3 conexiones.

**Red libre de escala (*scale-free*):** red donde $P(k) \sim k^{-\gamma}$ — la distribución sigue una ley de potencia. Tiene muy pocos nodos con grado altísimo (hubs) y muchos con grado bajo. *En palabras simples:* como una red de aeropuertos: pocos aeropuertos como Heathrow tienen miles de vuelos, pero la mayoría de aeropuertos tienen pocos destinos.

**Ley de potencia $P(k) \sim k^{-\gamma}$:** en escala log-log aparece como una línea recta con pendiente $-\gamma$. El parámetro $\gamma$ controla la "pesadez de la cola" — qué tan probable es encontrar hubs extremos.

**Hub:** nodo con grado muy superior al promedio. En UCuenca, `DATCC-2A-C3` (grado 17) frente al grado medio de 2.36.

---

### Centralidades

**Centralidad de grado $C_G$:** qué fracción de la red está directamente conectada a este nodo. Un nodo central por grado es un "vecino de muchos". *En redes:* importante para switches de distribución/core.

**Centralidad de intermediación (betweenness) $C_B$:** fracción de rutas más cortas de la red que pasan por este nodo. *En palabras simples:* cuántas "autopistas" pasan por esta ciudad. Un nodo con alta betweenness es un cuello de botella — si falla, muchos pares de nodos pierden su ruta más corta.

**Centralidad de cercanía (closeness) $C_C$:** inverso de la distancia media a todos los demás nodos. Un nodo con alta closeness puede alcanzar a cualquier otro nodo rápidamente. *Ideal para:* servidores DNS, NTP o de monitoreo que deben responder a toda la red.

**Centralidad de vector propio $C_E$:** un nodo es importante si sus vecinos son importantes. Es un ranking recursivo — como el PageRank de Google. *En palabras simples:* no es lo mismo tener 5 vecinos mediocres que 5 vecinos influyentes.

---

### Estructura local y global

**Coeficiente de clustering $C(v)$:** fracción de los pares de vecinos de $v$ que están conectados entre sí. $C(v) = 1$ si todos los vecinos de $v$ también son vecinos entre sí (triangulación completa); $C(v) = 0$ si ningún par de vecinos comparte enlace. *En redes jerárquicas:* es casi cero porque se prohíben los bucles en la capa de acceso.

**Triángulo:** conjunto de 3 nodos todos conectados entre sí. La presencia de triángulos eleva el clustering. *En redes sociales:* "amigos de amigos son amigos". En redes de infraestructura: un ciclo de 3 entre core, agregación y acceso sería inusual.

**Diámetro $D$:** la distancia más larga entre cualquier par de nodos. El "peor caso" de la red. En UCuenca $D = 11$: hay equipos que necesitan 11 saltos para comunicarse.

**Distancia media $\langle d \rangle$:** promedio de todas las distancias entre pares. En UCuenca $\langle d \rangle = 5.83$ saltos. *En palabras simples:* si eliges dos equipos al azar, necesitarán en promedio casi 6 saltos para comunicarse.

**Mundo pequeño (*small world*):** propiedad donde $\langle d \rangle$ crece muy lentamente con $n$ (escala como $\log n$) pero el clustering es alto. *Ejemplo:* en una red social de millones de personas, dos desconocidos están separados por ~6 "saltos" de amistad. UCuenca no es *small world* porque su clustering es demasiado bajo.

**Asortatividad $r$:** correlación entre los grados de los extremos de las aristas. $r > 0$ (asortativa): los hubs se conectan con hubs. $r < 0$ (disasortativa): los hubs se conectan con hojas. En UCuenca $r = -0.147$: los switches de core se conectan con switches de acceso de grado 1, nunca directamente entre sí.

---

### Puntos de fallo

**Punto de articulación (vértice de corte):** nodo cuya eliminación divide el grafo en dos o más partes. *En redes:* si falla, uno o más segmentos quedan aislados. En UCuenca hay 47 puntos de articulación, casi todos en la capa de agregación.

**Puente (arista de corte):** arista cuya eliminación divide el grafo. *En palabras simples:* cable sin alternativa — si se corta, algún segmento queda incomunicado. En UCuenca el 67% de los cables son puentes.

**Algoritmo de Tarjan:** algoritmo DFS que encuentra todos los puntos de articulación y puentes en una sola pasada por el grafo, con complejidad $O(n+m)$. Usa el concepto de "número de descubrimiento" y "valor low" para detectar qué nodos no tienen camino alternativo hacia sus ancestros.

---

### Algoritmos de recorrido

**BFS (Búsqueda en Anchura):** recorre el grafo por "capas" — primero todos los vecinos directos, luego los vecinos de vecinos, etc. Garantiza encontrar el camino más corto (en saltos). *Como ondas en un estanque:* se expande desde el origen hacia afuera uniformemente.

**DFS (Búsqueda en Profundidad):** sigue un camino hasta el fondo antes de retroceder y explorar otra rama. *Como resolver un laberinto siguiendo siempre la pared izquierda:* llega muy lejos antes de volver.

**Número ciclomático $\mu = m - n + 1$:** cuenta los ciclos independientes de un grafo conexo. Cada arista "extra" sobre el árbol mínimo ($n-1$ aristas) crea exactamente un ciclo. En UCuenca: $\mu = 209 - 177 + 1 = 33$ ciclos = 33 enlaces redundantes.

**Arista de retroceso (back edge):** en DFS, arista que lleva a un ancestro ya visitado. Cada back edge indica la existencia de un ciclo. El número de back edges coincide con el número ciclomático.

---

### Algoritmos de caminos mínimos

**Dijkstra:** algoritmo que encuentra el camino más corto desde un nodo origen a todos los demás. Usa una cola de prioridad (montículo) para procesar siempre el nodo más cercano conocido. Funciona con pesos no negativos. *Como el algoritmo que usa tu GPS:* siempre expande el punto más cercano primero.

**Floyd-Warshall:** calcula todos los caminos mínimos entre todos los pares de nodos en $O(n^3)$. Pregunta para cada posible nodo intermedio $k$: "¿ir de $i$ a $j$ pasando por $k$ es más corto que la ruta directa conocida?". *Ventaja:* una sola ejecución da toda la información. *Desventaja:* muy lento para redes grandes.

**Camino más corto:** secuencia de nodos de menor peso total entre origen y destino. El peso puede ser saltos, latencia, carga, o cualquier métrica.

---

### Comunidades

**Comunidad:** subconjunto de nodos más densamente conectados entre sí que con el resto del grafo. *En redes sociales:* grupos de amigos. *En UCuenca:* los campus físicos tienden a ser comunidades porque los equipos de un campus se conectan más entre sí que con otros campus.

**Modularidad $Q$:** medida de calidad de una partición en comunidades. $Q > 0.3$ indica estructura comunitaria significativa. $Q$ compara las aristas internas reales con las esperadas en un grafo aleatorio con los mismos grados. En UCuenca $Q = 0.763$, muy alto.

**Algoritmo Louvain:** método greedy de dos fases para maximizar $Q$. Fase 1: cada nodo trata de moverse a la comunidad de su vecino que más aumenta $Q$. Fase 2: se contrae el grafo y se repite. Converge rápido incluso en redes grandes.

**Límite de resolución:** problema de la modularidad donde comunidades pequeñas no son detectables si el grafo es grande. Umbral aproximado: comunidades con menos de $\sqrt{2m}$ aristas internas pueden ser "tragadas" por comunidades más grandes.

**NMI (Información Mutua Normalizada):** mide el acuerdo entre dos particiones de la misma red. $\text{NMI} = 0$: sin relación. $\text{NMI} = 1$: particiones idénticas. En UCuenca, Louvain vs campus físico: NMI = 0.618.

**ARI (Índice de Rand Ajustado):** también compara dos particiones, corrigiendo por coincidencias aleatorias. $\text{ARI} = 1$: idénticas; $\text{ARI} = 0$: azar puro; puede ser negativo si acuerdan menos que el azar.

**k-means espectral:** técnica que primero calcula los vectores propios del Laplaciano normalizado del grafo (representación "espectral") y luego aplica k-means clustering estándar sobre esas coordenadas espectrales. Los vectores propios capturan la estructura de conectividad de forma que nodos bien conectados quedan cerca en el espacio espectral.

**Laplaciano normalizado $L_{\text{sym}}$:** versión normalizada de la matriz $L = D - A$ que escala por el grado de cada nodo. Tiene la propiedad de que sus vectores propios más pequeños identifican grupos de nodos bien conectados internamente.

---

### Flujo en redes

**Flujo máximo:** la cantidad máxima de "datos" que pueden circular simultáneamente de una fuente a un sumidero, respetando las capacidades de los cables. *En palabras simples:* cuánta agua por segundo puede pasar de la fuente al grifo a través de una red de cañerías.

**Ford-Fulkerson:** algoritmo que encuentra el flujo máximo buscando repetidamente "caminos aumentantes" (rutas con capacidad residual) y saturándolos. Termina cuando no queda ningún camino disponible.

**Edmonds-Karp:** variante de Ford-Fulkerson que siempre elige el camino aumentante más corto (BFS). Garantiza convergencia en $O(V \cdot E^2)$ incluso con capacidades irracionales.

**Capacidad residual:** cuánta capacidad le queda a un arco para aumentar el flujo. Si un cable de 10 Gbps ya lleva 7 Gbps de flujo, su capacidad residual es 3 Gbps.

**Corte (S, T):** partición de los nodos en dos conjuntos donde $S$ contiene la fuente y $T$ el sumidero. La capacidad del corte es la suma de capacidades de los arcos que van de $S$ a $T$.

**Teorema Max-Flow Min-Cut:** el flujo máximo entre dos nodos siempre iguala la capacidad mínima de corte entre ellos. *En palabras simples:* el caudal máximo que puede fluir está limitado por el "cuello de botella" más estrecho de toda la red.

**Flujo de costo mínimo:** extensión del flujo máximo donde cada arco tiene un costo por unidad de flujo. El objetivo es enviar una demanda dada con el menor costo total. *Ejemplo:* enviar datos eligiendo rutas de menor latencia o menor precio de ancho de banda.

---

### Localización de instalaciones

**p-Mediana:** problema de colocar $p$ instalaciones en los nodos del grafo para minimizar la suma de distancias de cada nodo a la instalación más cercana. Mide eficiencia promedio. *Ejemplo:* dónde poner $p$ servidores DNS para que la latencia promedio sea mínima.

**p-Centro:** problema de colocar $p$ instalaciones para minimizar la distancia máxima de cualquier nodo a la instalación más cercana (criterio minimax). Mide equidad / cobertura. *Ejemplo:* dónde poner $p$ servidores de respaldo para que ningún equipo esté a más de $R$ saltos de uno de ellos.

**Heurística greedy de localización:** en cada iteración, añade la instalación que más reduce la función objetivo (mediana o centro). No garantiza el óptimo global pero es eficiente computacionalmente y da soluciones de buena calidad.

---

### Robustez y percolación

**Percolación:** proceso de eliminación secuencial de nodos o aristas. Se estudia cómo la conectividad y la eficiencia del grafo decaen conforme se eliminan componentes.

**Eficiencia global $E(G)$:** medida de cuán bien conectados están todos los pares de nodos, considerando la inversa de su distancia. $E = 0.208$ en UCuenca intacto; cae a medida que se eliminan nodos.

**Umbral de percolación $f_c$:** fracción de nodos eliminados donde la red "colapsa" (la componente gigante deja de ser gigante o la eficiencia cae drásticamente). En UCuenca bajo ataque por grado: $f_c \approx 0.05$.

**Ataque dirigido vs fallo aleatorio:** un ataque dirigido elimina primero los nodos más importantes (mayor grado o betweenness); un fallo aleatorio elimina nodos sin criterio. Las redes heterogéneas (con hubs) son robustas frente a fallos aleatorios pero frágiles frente a ataques dirigidos.

**Robustez:** capacidad de la red de mantener funcionalidad tras la eliminación de componentes. Una red robusta mantiene $E(G)$ alto incluso con una fracción $f$ grande de nodos eliminados.

---

### Dinámica: cascadas y epidemias

**Modelo de carga-capacidad (Motter-Lai):** modelo donde cada nodo tiene una carga (proporcional a su betweenness) y una capacidad $(1+\alpha)$ veces su carga inicial. Al fallar un nodo, su carga se redistribuye; si la carga de otro nodo supera su capacidad, también falla. *En palabras simples:* es el modelo de apagones en cascada de la red eléctrica aplicado a redes de datos.

**Cascada de fallos:** propagación en dominó de fallos. Un fallo inicial sobrecarga a otros nodos que fallan, sobrecargando a otros más, etc. La tolerancia $\alpha$ controla qué tan resistente es la red.

**Tolerancia $\alpha$:** exceso de capacidad sobre la carga nominal. $\alpha = 0$: sin margen (cualquier sobrecarga provoca fallo). $\alpha = 1$: capacidad doble (aguanta hasta duplicar la carga nominal). En UCuenca, con $\alpha \geq 1.5$ la cascada desde `DATCC-2A-C3` se limita a 5 nodos.

**Modelo SIR:** modelo epidemiológico con tres estados: Susceptible (sano), Infectado (comprometido), Recuperado (parcheado). Cada infectado contagia a sus vecinos con tasa $\beta$ y se recupera con tasa $\gamma$. *En redes de datos:* modela la propagación de malware, misconfiguraciones o vulnerabilidades.

**Tasa de infección $\beta$:** probabilidad de que un nodo infectado contagie a un vecino susceptible en un paso de tiempo.

**Tasa de recuperación $\gamma$:** probabilidad de que un nodo infectado se recupere (parchee) en un paso de tiempo.

**Umbral crítico $\tau_c = \langle k \rangle / \langle k^2 \rangle$:** si $\beta > \tau_c$, la infección se propaga a una fracción finita de la red (epidemia). Si $\beta < \tau_c$, la infección se extingue localmente. En UCuenca: $\tau_c = 0.186$.

**Inmunización por vecino (*acquaintance immunization*):** estrategia práctica donde se elige un nodo al azar y se vacuna a uno de sus vecinos al azar. Tiende a encontrar hubs (porque los hubs tienen más probabilidad de ser vecino de alguien) sin necesitar conocer la topología completa. *Como vacunar a los amigos de personas seleccionadas al azar* en lugar de buscar directamente a las personas más influyentes.

---

### Modelos nulos

**Erdős-Rényi G(n,m):** grafo aleatorio con $n$ nodos y $m$ aristas elegidas uniformemente al azar. Es el modelo de "azar puro" — cualquier subgrafo de $m$ aristas es igualmente probable. La distribución de grado es binomial / Poisson.

**Modelo de Configuración (CM):** grafo aleatorio que preserva exactamente la secuencia de grados de la red real, pero conecta las "medias aristas" de forma aleatoria. Permite separar qué propiedades son consecuencia de los grados y cuáles de la topología específica.

**Modelo Barabási-Albert (BA):** genera redes mediante crecimiento + enlace preferencial. En cada paso añade un nodo con $m$ aristas que se conectan a nodos existentes con probabilidad proporcional a su grado. Produce distribución de ley de potencia $P(k) \sim k^{-3}$. *En palabras simples:* modela redes que crecen orgánicamente donde "el que tiene más conexiones, recibe más conexiones nuevas".

---
