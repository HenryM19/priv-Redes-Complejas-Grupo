## Anexo B — Notas Extendidas

Esta sección recoge las explicaciones pedagógicas extendidas (lectura detallada de notación y analogías) que se referencian desde el cuerpo principal del informe, organizadas por sección de origen.

---

### Notas extendidas — Ítem 2 · Distribución de grado

**Nota 1:**

*Lectura:* el grado $k_v$ es la cantidad de nodos $u$ que pertenecen al grafo ($u \in V$) y que tienen un enlace directo con $v$ ($(u,v) \in E$). Las llaves $\{\cdots\}$ forman el conjunto de esos vecinos y las barras $|\cdots|$ cuentan cuántos hay. En otras palabras: **cuántos cables salen del equipo $v$**.

*Ejemplo UCuenca:* `DATCC-2A-C3` tiene 17 switches conectados directamente → $k_v = 17$. Un switch de acceso como `ARQ-0A-A84` solo se conecta a su switch de agregación → $k_v = 1$.

**Nota 2:**

*Lectura:* del total de $n$ nodos, ¿qué fracción tiene exactamente $k$ conexiones? El numerador cuenta cuántos nodos cumplen esa condición y el denominador normaliza entre 0 y 1. Por ejemplo, en UCuenca $P(1) = 113/177 = 0.638$: el 63.8% de los equipos tiene un solo cable.

**Nota 3:**

*Lectura:* se suman los grados de todos los nodos y se divide entre $n$. La igualdad $2m/n$ viene de que cada arista contribuye +1 al grado de ambos extremos, por eso la suma total de grados es siempre $2m$. En UCuenca: $\langle k \rangle = 2 \times 209 / 177 = 2.362$ conexiones por equipo en promedio.

**Nota 4:**

*En palabras simples:* una red libre de escala crece espontáneamente (internet, redes sociales) y genera unos pocos "supernodos" con miles de conexiones. La red UCuenca, en cambio, fue diseñada por un arquitecto con una jerarquía predefinida acceso→agregación→core. Con solo 20 nodos en la cola, ningún test puede *confirmar* si esa cola sigue o no una ley de potencia con rigor — lo que sí sostiene la evidencia estructural (P1 ítem 4: asortatividad negativa, clustering bajo) es que el mecanismo generador es diseño jerárquico, no crecimiento preferencial emergente, independientemente de cómo ajuste su cola de grado.

---

### Notas extendidas — Ítem 3 · Centralidades

**Nota 1:**

*Lectura:* divide el grado real de $v$ entre el grado máximo posible ($n-1$, si estuviera conectado con todos). Es la fracción de nodos a los que $v$ llega en un solo salto. En UCuenca, `DATCC-2A-C3` tiene $C_G = 17/176 = 0.097$: se conecta directamente al 9.7% de la red.

**Nota 2:**

*Lectura:* para cada par de nodos $(s, t)$ distintos de $v$, se pregunta: ¿qué fracción de los caminos más cortos entre $s$ y $t$ pasan por $v$? ($\sigma_{st}(v)/\sigma_{st}$). Se suma esa fracción sobre todos los pares posibles y se normaliza. Un valor alto significa que $v$ es un "puente de tráfico": si falla, muchos pares de nodos pierden su ruta más corta. En UCuenca, `DATCC-2A-C3` tiene $C_B = 0.447$: casi la mitad de todos los caminos más cortos de la red pasan por él.

**Nota 3:**

*Lectura:* el denominador suma las distancias (en saltos) desde $v$ hasta todos los demás nodos. Cuanto más pequeña es esa suma, más "cerca" está $v$ de todos. Se invierte y se multiplica por $n-1$ para que el resultado quede entre 0 y 1. Un nodo con $C_C$ alto puede alcanzar cualquier equipo de la red en pocos saltos: ideal para ubicar servidores DNS, NTP o monitoreo. En UCuenca, `INTERNET-MPLS` lidera con $C_C = 0.276$.

**Nota 4:**

*Lectura:* la centralidad de $v$ es proporcional a la **suma de las centralidades de sus vecinos** $\mathcal{N}(v)$. $\lambda$ es una constante de normalización (el autovalor dominante de la matriz de adyacencia). La idea es que no es lo mismo tener muchos vecinos mediocres que pocos vecinos influyentes. Un switch de acceso conectado a `DATCC-2A-C3` (el hub más importante) hereda parte de su importancia. En UCuenca, el top de vector propio lo lideran los switches directamente conectados a los dos cores del Campus Central.

---

### Notas extendidas — Ítem 4 · Clustering, diámetro, distancia media y asortatividad

**Nota 1:**

*Lectura:* entre todos los vecinos de $v$, ¿cuántos pares de vecinos están también conectados entre sí? El numerador cuenta esos enlaces existentes ($t_v$ triángulos × 2); el denominador es el total de pares posibles $\binom{k_v}{2} = k_v(k_v-1)/2$. Si todos los vecinos de $v$ se conocen entre sí, $C(v) = 1$. Si ningún par de vecinos está conectado, $C(v) = 0$. Para nodos de grado 0 ó 1 no tiene sentido calcularlo → $C(v) = 0$.

*Ejemplo UCuenca:* `DATCC-2A-C3` tiene 17 vecinos. Para que $C > 0$ debería haber enlaces entre esos 17 switches (ej. que dos switches de agregación estuvieran conectados entre sí). En la red jerárquica eso no ocurre → $C \approx 0$.

**Nota 2:**

*Lectura:* promedio del clustering local de todos los nodos. En UCuenca $\langle C \rangle = 0.034$: en promedio solo el 3.4% de los pares de vecinos de un equipo están conectados entre sí.

**Nota 3:**

*Lectura:* se suman las distancias más cortas (en saltos) entre todos los pares ordenados de nodos distintos, y se divide entre el número de pares $n(n-1)$. Es el "número de saltos típico" para ir de un equipo cualquiera a otro. En UCuenca $\langle d \rangle = 5.83$: en promedio se necesitan casi 6 saltos para cruzar la red.

**Nota 4:**

*Lectura:* la distancia más larga entre cualquier par de nodos. Es el "peor caso": los dos equipos más alejados de la red. En UCuenca $D = 11$: hay al menos un par de equipos que necesita 11 saltos para comunicarse.

**Nota 5:**

*Lectura:* para cada arista $(u,v)$, se observan los grados de sus dos extremos $k_u$ y $k_v$. La fórmula es el coeficiente de Pearson entre esos dos conjuntos de valores (uno por extremo). Si los nodos de alto grado tienden a conectarse con nodos de alto grado → $r > 0$ (red **asortativa**, como redes sociales). Si los nodos de alto grado tienden a conectarse con nodos de bajo grado → $r < 0$ (red **disasortativa**, como UCuenca con $r = -0.147$).

---

### Notas extendidas — Ítem 5 · Puntos de articulación y puentes

**Nota 1:**

*Lectura:* si "borras" el nodo $v$ y todos sus enlaces, ¿el grafo se parte en más trozos que antes? Si sí, $v$ es imprescindible para mantener la red unida. En UCuenca, un switch de agregación como `BAL-AG-C4` conecta todos los switches de acceso de un edificio con el core; eliminarlo deja ese edificio sin ruta.

**Nota 2:**

*Lectura:* si ese único cable entre $u$ y $v$ se corta, alguna parte de la red queda aislada — no existe ninguna ruta alternativa. El 67% de los enlaces de UCuenca son puentes, lo que significa que cortar cualquiera de esos cables aísla al menos un equipo.

---

### Notas extendidas — Ítem 1 · Erdős–Rényi y Modelo de Configuración (100 realizaciones)

**Nota 1:**

*Lectura:* el modelo ER es el "azar puro": se ponen los mismos $n$ nodos y $m$ aristas de la red real, pero las conexiones se sortean al azar sin ninguna preferencia. Si la red real difiere de ER, esa diferencia no se debe al azar sino a algún principio de organización (jerarquía, diseño, evolución).

**Nota 2:**

*Lectura:* en ER, la probabilidad de que dos vecinos de $v$ estén conectados entre sí es simplemente la densidad $p$ — no hay estructura local. La distancia media crece muy lentamente con $n$ (efecto "mundo pequeño" aleatorio). La asortatividad tiende a cero porque no hay preferencia por conectar nodos similares.

**Nota 3:**

*Lectura:* el CM le "da" a cada nodo los mismos $k_v$ enlaces que tiene en la red real, pero los conecta al azar. Si una propiedad (por ejemplo la asortatividad) coincide entre CM y la red real, significa que esa propiedad es consecuencia matemática de *quién tiene cuántos enlaces*, no de *a quién están conectados*. Si difiere, hay una organización adicional más allá de los grados.

---

### Notas extendidas — Ítem 2 · Modelo Barabási–Albert

**Nota 1:**

*Lectura:* cuando llega un nuevo nodo a la red, no elige sus vecinos al azar — prefiere conectarse a los que ya tienen más enlaces. La probabilidad de elegir el nodo $i$ es proporcional a su grado actual $k_i$. Un nodo con el doble de enlaces tiene el doble de probabilidad de recibir una nueva conexión. Este mecanismo de "los ricos se hacen más ricos" (*rich-get-richer*) produce hubs dominantes y en el límite $n \to \infty$ genera $P(k) \sim k^{-3}$.

---

### Notas extendidas — Ítem 1 · BFS y DFS desde cero

**Nota 1:**

*Lectura:* la distancia $d(s,v)$ que BFS encuentra es el número mínimo de aristas para ir de $s$ a $v$. BFS garantiza que cuando visita $v$ por primera vez, ya encontró el camino más corto. La cola FIFO asegura que se procesan primero los nodos más cercanos al origen.

**Nota 2:**

*Lectura:* se parte de $v_1$, se recorre la secuencia de aristas, y se regresa a $v_1$ sin repetir ningún nodo. En términos de red, un ciclo entre dos nodos $A$ y $B$ implica que existen **al menos dos caminos independientes** de $A$ a $B$ — si uno de los enlaces del ciclo falla, el tráfico puede tomar el otro camino. La **ausencia de ciclos** en una zona equivale a topología de árbol: no hay camino alternativo y cualquier fallo de enlace aísla a los equipos aguas abajo.

**Nota 3:**

*Lectura:* tanto BFS como DFS visitan cada nodo una vez y cada arista a lo sumo dos veces (una por cada extremo), de ahí el $O(n+m)$. El espacio adicional es $O(n)$ para el conjunto de nodos visitados y la cola/pila.

**Nota 4:**

*Lectura:* un árbol de $n$ nodos tiene exactamente $n-1$ aristas y cero ciclos. Cada arista adicional sobre ese árbol crea exactamente un ciclo nuevo. En UCuenca: $\mu = 209 - 177 + 1 = 33$. Hay 33 ciclos independientes, que corresponden a los 33 enlaces redundantes de la red.

---

### Notas extendidas — Ítem 1 · Louvain con 5 semillas

**Nota 1:**

*Lectura:* para cada par de nodos $(u,v)$ en la misma comunidad, se compara la arista real $A_{uv}$ con la probabilidad esperada en un grafo aleatorio con los mismos grados $\frac{k_u k_v}{2m}$. Si hay más conexiones dentro de las comunidades de lo que el azar esperaría, $Q > 0$. $Q \in [-1, 1]$; valores > 0.3 indican estructura comunitaria significativa.

---

### Notas extendidas — Ítem 2 · Comparación con partición por campus (NMI y ARI)

**Nota 1:**

*Lectura:* mide cuánta información comparten dos particiones. $\text{NMI} = 1$ significa que conocer la comunidad de un nodo determina perfectamente su campus (y viceversa). $\text{NMI} = 0$ significa que son independientes. Aquí NMI = 0.618: las comunidades Louvain capturan el 62% de la información de la partición por campus.

**Nota 2:**

*Lectura:* compara par a par todos los nodos: ¿los nodos que Louvain pone en la misma comunidad también están en el mismo campus? ARI = 0.33 indica coincidencia moderada, corrigiendo por el azar.

---

### Notas extendidas — Ítem 4 · k-means espectral (Laplaciano)

**Nota 1:**

*Lectura:* $D$ es la matriz diagonal de grados y $A$ la matriz de adyacencia. Los vectores propios de $L_{\text{sym}}$ con menores valores propios capturan la estructura de conectividad del grafo: los nodos que están bien conectados entre sí tienen coordenadas similares en el espacio espectral. k-means sobre esas coordenadas agrupa nodos por su posición espectral, que refleja conectividad más que geometría euclídea.

---

### Notas extendidas — Modelos de peso

**Nota 1:**

*Lectura:* todos los enlaces valen lo mismo. La distancia entre dos equipos es simplemente la cantidad de "saltos" (equipos intermedios) necesarios. Es el modelo más simple: ideal para contar hops en traceroute.

*En palabras simples:* cada cable cuenta como 1 paso, sin importar si es un cable de fibra de 10 Gbps o un enlace de 100 Mbps. Se usa para saber cuántos equipos hay entre el origen y el destino.

**Nota 2:**

*Lectura:* el retardo de un enlace tiene dos componentes: uno fijo ($\alpha$, latencia mínima de propagación) y uno que disminuye a medida que la capacidad $c(u,v)$ aumenta. Un enlace de 10 000 Mbps tiene retardo adicional $1000/10000 = 0.1$ ms; uno de 100 Mbps tiene $1000/100 = 10$ ms. Caminos de alto ancho de banda son "más baratos" para este modelo.

*En palabras simples:* un cable más ancho (mayor capacidad) tarda menos en enviar el mismo paquete. Este modelo elige rutas por cables rápidos aunque tengan más saltos.

**Nota 3:**

*Lectura:* es la **utilización** del enlace: fracción de su capacidad que ya está siendo usada. Un enlace al 90% de su capacidad tiene $w = 0.9$ (saturado); uno al 5% tiene $w = 0.05$ (holgado). El camino de carga mínima evita los cuellos de botella actuales.

*En palabras simples:* si el camino más corto en saltos pasa por un cable ya congestionado, este modelo busca una ruta alternativa con cables más libres. Es como usar Waze para evitar el tráfico.

---

### Notas extendidas — Ítem 1 · Implementación de Dijkstra y Floyd-Warshall — verificación sobre 20 pares

**Nota 1:**

*Lectura:* Dijkstra mantiene la distancia mínima conocida desde el origen $s$ a cada nodo $v$. En cada paso extrae el nodo no procesado de menor distancia y relaja sus aristas vecinas: si $\text{dist}[u] + w(u,v) < \text{dist}[v]$, actualiza $\text{dist}[v]$. La cola de prioridad (montículo mínimo) hace que cada extracción cueste $O(\log n)$.

**Nota 2:**

*Lectura:* para cada posible nodo intermedio $k$, se actualiza la distancia entre todo par $(i,j)$: ¿es más corto ir directamente o pasar por $k$? Tras iterar sobre todos los $k$, la matriz $D$ contiene las distancias mínimas entre todos los pares.

---

### Notas extendidas — Ítem 1 · Función de capacidad $c(u,v)$

**Nota 1:**

*En palabras simples:* la "capacidad" de un cable es cuánta información puede pasar por él al mismo tiempo (como el número de carriles de una autopista). El core tiene autopistas de 10 Gbps; la agregación tiene avenidas de 1 Gbps; el acceso tiene calles de 100 Mbps.

---

### Notas extendidas — Ítem 2 · Modelo fuente–sumidero — Ford-Fulkerson (DFS) y Edmonds-Karp (BFS)

**Nota 1:**

*En palabras simples:* el flujo máximo siempre iguala la capacidad del "cuello de botella" más estrecho de la red — el conjunto de cables que, si se cortaran todos, dejarían al campus sin salida a Internet.

---

### Notas extendidas — Ítem 5 · Formulación de flujo de costo mínimo

**Nota 1:**

*En palabras simples:* además de respetar la capacidad de cada cable, se quiere enviar los datos por la ruta más barata. El "costo" puede ser latencia, número de saltos, o precio de alquiler de ancho de banda. El flujo de costo mínimo minimiza el costo total de transportar una demanda dada.

---

### Notas extendidas — Ítem 1 · Formulación matemática de ambos modelos

**Nota 1:**

*En palabras simples:* busca los $p$ nodos donde instalar colectores de modo que la **suma total de saltos** de todos los equipos a su colector más cercano sea mínima. Optimiza el promedio — acepta que algún equipo quede lejos si la mayoría queda cerca.

**Nota 2:**

*En palabras simples:* busca los $p$ nodos donde instalar colectores de modo que el equipo **más lejano** de todos esté lo más cerca posible. Optimiza el peor caso — garantiza que nadie quede a más de $R^*$ saltos de un colector.

---

### Notas extendidas — Ítem 4 · Eficiencia global E(f) y su degradación anticipada

**Nota 1:**

*En palabras simples:* mide qué tan bien se comunican todos los pares de nodos. Si dos nodos están a 1 salto contribuyen 1; si están a 5 saltos contribuyen 1/5; si están desconectados contribuyen 0. Cuando la red se fragmenta o los caminos se alargan, $E$ cae.

---

### Notas extendidas — Ítem 1 · Modelo de carga-capacidad (Motter-Lai)

**Nota 1:**

*Lectura:* cuando un router crítico falla, el tráfico que antes pasaba por él se redistribuye entre los caminos alternativos. Los routers que se convierten en "detour" repentino pueden saturarse y fallar también. La tolerancia $\alpha$ mide qué tan sobreprovisionada está la red: $\alpha = 0$ significa capacidad exactamente al 100%, sin margen; $\alpha = 1$ significa el doble de margen.

*En palabras simples:* es como un atasco de tráfico que se propaga: si la autopista principal se cierra, los conductores se desvían por carreteras secundarias. Si esas carreteras tampoco aguantan el nuevo tráfico, también colapsan, creando más desvíos en un efecto dominó.

---

### Notas extendidas — Ítem 3 · Modelo SIR y umbral crítico

**Nota 1:**

*Lectura:* en cada paso de tiempo, un equipo susceptible se infecta con probabilidad que depende de cuántos vecinos ya infectados tiene: $\beta$ es la probabilidad de infección por cada vecino infectado. Un equipo infectado se recupera con probabilidad $\gamma$ en cada paso.

*En palabras simples:* un virus informático se propaga de router en router. En cada "tick" del reloj, cada router infectado tiene $\beta$ probabilidad de infectar a cada vecino sano. Los routers infectados se parchean con probabilidad $\gamma$ por tick. Si $\beta$ es muy baja, el virus muere rápido; si es alta, se propaga a toda la red.

**Nota 2:**

*En palabras simples:* en una red donde hay algunos equipos muy conectados (hubs), basta con una tasa de infección muy baja para que el virus se propague a toda la red. Los hubs actúan como "superpropagadores": cualquier virus que los alcance se distribuye de golpe a todos sus vecinos.

---

