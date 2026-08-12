# Análisis de Redes Complejas — Red de Datos UCuenca
**Módulo 1217 · Maestría en Ciencias de la Ingeniería Eléctrica**  
**Dr. Fabián Astudillo-Salinas · Entrega: 26 de agosto de 2026**

---

## Caso de estudio

La red analizada es la infraestructura de datos de la Universidad de Cuenca, reconstruida a partir de 34 diagramas técnicos del informe *"Diagramas de red final"*. El grafo resultante es **simple, no dirigido y conexo**, con:

| Parámetro | Valor |
|-----------|-------|
| Nodos ($n$) | 177 |
| Aristas ($m$) | 209 |
| Campus | 6 campus + 2 sedes + nube MPLS |
| Capas jerárquicas | core · agregación · acceso · WAN · interconexión |

La red está organizada en una **topología estrella jerárquica de tres capas**:

```
          [CORE]          ← enrutamiento de alta velocidad (10 Gbps)
        /        \
  [AGREGACIÓN]  [AGREGACIÓN]   ← consolidación por facultad/bloque
      |               |
  [ACCESO]      [ACCESO]       ← conectividad de usuario final
```

Los seis campus se interconectan a través de una **nube MPLS** de un proveedor externo.

---

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

## Fase 1 — Modelado y Caracterización

> **Peso: 5 puntos** | Contenidos 1.1–1.4 del sílabo

---

## P1 — Medidas Fundamentales *(3 puntos)*

### Ítem 1 · Métricas básicas del grafo

#### Definiciones matemáticas

**Densidad** del grafo:

$$\rho = \frac{2m}{n(n-1)}$$

donde $n$ es el número de nodos, $m$ el número de aristas, y $n(n-1)/2$ es el máximo de aristas posibles en un grafo simple no dirigido.

**Componente conexa gigante (GCC):** subconjunto de nodos $S \subseteq V$ tal que existe un camino entre todo par de nodos en $S$, y $|S|$ es máximo.

#### Resultados

| Métrica | Valor |
|---------|-------|
| Nodos $n$ | 177 |
| Aristas $m$ | 209 |
| Densidad $\rho$ | 0.013418 |
| Componentes conexas | 1 |
| Tamaño de la GCC | 177 |

#### Análisis

La densidad $\rho = 0.0134$ es muy baja: la red usa apenas el 1.3% de los enlaces posibles. Una red completa tendría $\binom{177}{2} = 15\,576$ aristas; la red real tiene solo 209. Esto es **esperable en infraestructura jerárquica**: cada equipo se conecta únicamente a sus vecinos inmediatos en la cadena *core → agregación → acceso*, nunca a todos los demás.

El grafo es **conexo** (una sola componente), confirmando que todos los campus tienen al menos un camino hacia el resto de la institución. En términos operativos esto no garantiza robustez: un único enlace puede bastar para mantener la conectividad mientras representa un punto de fallo crítico.

---

### Ítem 2 · Distribución de grado

#### Definiciones matemáticas

El **grado** de un nodo $v$ es:

$$k_v = |\{u \in V : (u,v) \in E\}|$$

> *Lectura:* el grado $k_v$ es la cantidad de nodos $u$ que pertenecen al grafo ($u \in V$) y que tienen un enlace directo con $v$ ($(u,v) \in E$). Las llaves $\{\cdots\}$ forman el conjunto de esos vecinos y las barras $|\cdots|$ cuentan cuántos hay. En otras palabras: **cuántos cables salen del equipo $v$**.
>
> *Ejemplo UCuenca:* `DATCC-2A-C3` tiene 17 switches conectados directamente → $k_v = 17$. Un switch de acceso como `ARQ-0A-A84` solo se conecta a su switch de agregación → $k_v = 1$.

La **distribución de grado** $P(k)$ es la fracción de nodos con grado exactamente $k$:

$$P(k) = \frac{|\{v \in V : k_v = k\}|}{n}$$

> *Lectura:* del total de $n$ nodos, ¿qué fracción tiene exactamente $k$ conexiones? El numerador cuenta cuántos nodos cumplen esa condición y el denominador normaliza entre 0 y 1. Por ejemplo, en UCuenca $P(1) = 113/177 = 0.638$: el 63.8% de los equipos tiene un solo cable.

El **grado medio**:

$$\langle k \rangle = \frac{1}{n}\sum_{v \in V} k_v = \frac{2m}{n}$$

> *Lectura:* se suman los grados de todos los nodos y se divide entre $n$. La igualdad $2m/n$ viene de que cada arista contribuye +1 al grado de ambos extremos, por eso la suma total de grados es siempre $2m$. En UCuenca: $\langle k \rangle = 2 \times 209 / 177 = 2.362$ conexiones por equipo en promedio.

#### Resultados

| Métrica | Valor |
|---------|-------|
| Grado medio $\langle k \rangle$ | 2.362 |
| Grado máximo $k_{\max}$ | 17 |
| Grado mínimo $k_{\min}$ | 1 |

**Frecuencias por grado:**

| Grado $k$ | Nodos | $P(k)$ |
|-----------|-------|--------|
| 1 | 113 | 0.6384 |
| 2 | 22 | 0.1243 |
| 3 | 6 | 0.0339 |
| 4 | 7 | 0.0395 |
| 5 | 9 | 0.0508 |
| 6 | 7 | 0.0395 |
| 7 | 4 | 0.0226 |
| 8 | 3 | 0.0169 |
| 9 | 1 | 0.0056 |
| 10 | 1 | 0.0056 |
| 12 | 2 | 0.0113 |
| 16 | 1 | 0.0056 |
| 17 | 1 | 0.0056 |

![Distribución de grado](results/imagenes/p1_distribucion_grado.png)

#### Observaciones sobre la distribución de grado

La distribución empírica muestra un fuerte sesgo: **113 de 177 nodos (64%) tienen grado 1** (switches de acceso con un único enlace a su switch de agregación), mientras que el nodo de mayor grado es `DATCC-2A-C3` con $k = 17$.

Estadísticas descriptivas:

| Estadístico | Valor |
|-------------|-------|
| Grado mínimo | 1 |
| Grado máximo | 17 |
| Grado medio $\langle k \rangle$ | 2.36 |
| Grado mediano | 1 |

El gráfico log-log muestra una nube de puntos sin alineación recta clara — lo que sugiere que la distribución **no** sigue una ley de potencia pura. Para confirmarlo formalmente se aplica el método de **Máxima Verosimilitud (MLE)** de Clauset, Shalizi & Newman (2009).

#### Análisis MLE — ¿Es UCuenca una red libre de escala?

Una **red libre de escala** (*scale-free*) es aquella cuya distribución de grado sigue una ley de potencia $P(k) \sim k^{-\gamma}$ con $2 < \gamma < 3$. Para la ley de potencia **discreta** (grados enteros), el estimador MLE es:

$$\hat{\gamma} = 1 + n \left[\sum_{i=1}^{n} \ln\frac{k_i}{k_{\min} - 0.5}\right]^{-1}$$

donde $k_{\min}$ es el umbral mínimo de la cola y $n$ el número de nodos con $k_i \geq k_{\min}$. El $k_{\min}$ óptimo se elige minimizando la distancia de Kolmogorov-Smirnov (KS) entre la CDF empírica y la CDF teórica normalizada con la función Zeta de Hurwitz:

$$P(K \geq k) = \frac{\zeta(\gamma,\, k)}{\zeta(\gamma,\, k_{\min})}, \qquad \zeta(s,a) = \sum_{n=0}^{\infty}(n+a)^{-s}$$

**Resultados del barrido de $k_{\min}$:**

| $k_{\min}$ | $\hat{\gamma}$ | KS | $n_{\text{cola}}$ |
|:---:|:---:|:---:|:---:|
| 1 | 1.8414 | 0.0900 | 177 |
| 2 | 2.0369 | 0.1354 | 64 |
| 3 | 2.2376 | 0.2015 | 42 |
| 4 | 2.7367 | 0.1553 | 36 |
| 5 | 3.3188 | 0.0586 | 29 |
| **6** | **3.6509** | **0.0570** | **20** |
| 7 | 3.7288 | 0.0955 | 13 |
| 8 | 3.8305 | 0.1449 | 9 |

El mínimo KS se alcanza en $k_{\min} = 6$, con $\hat{\gamma} = 3.65$ y $\text{KS} = 0.057$. Sin embargo, **solo 20 de 177 nodos** quedan en la cola ($\approx 11\%$), lo que invalida el ajuste sobre la red completa.

La figura siguiente compara $P(k)$ empírica con curvas de ley de potencia para $\gamma \in \{1.5, 2.0, 2.5, 3.0, 3.5\}$ y el ajuste MLE óptimo, junto al barrido de KS vs $k_{\min}$:

![MLE Ley de Potencia](results/imagenes/p1_mle_ley_potencia.png)

**Test razón de verosimilitudes (power law vs exponencial):** el log-ratio es $\approx -0.0005$, esencialmente cero — ambas distribuciones son estadísticamente indistinguibles sobre la cola $k \geq 6$.

#### Conclusión: UCuenca **no** es una red libre de escala

La red UCuenca **no** satisface los criterios de una red libre de escala, por tres razones:

1. **Rango insuficiente:** con grados en $[1, 17]$, el rango es demasiado estrecho para distinguir una ley de potencia de una exponencial o de una distribución truncada artificialmente.
2. **Topología jerárquica diseñada:** los grados por capa son fijos por diseño (acceso $k\approx1$–$2$, agregación $k\approx3$–$6$, core $k\approx8$–$17$). No existe crecimiento preferencial — la red fue planificada, no emergente.
3. **$\hat{\gamma} = 3.65 > 3$:** aunque se ajusta formalmente una ley de potencia en la cola $k\geq6$, el exponente cae fuera del régimen scale-free clásico ($2 < \gamma < 3$) y solo describe 20 nodos de los 177.

> *En palabras simples:* una red libre de escala crece espontáneamente (internet, redes sociales) y genera unos pocos "supernodos" con miles de conexiones. La red UCuenca, en cambio, fue diseñada por un arquitecto con una jerarquía predefinida acceso→agregación→core. Eso produce grados típicos por capa, no una cola de potencia sin límite superior.

---

### Ítem 3 · Centralidades

#### Definiciones matemáticas

**Centralidad de grado** (normalizada):

$$C_{\text{grado}}(v) = \frac{k_v}{n-1}$$

> *Lectura:* divide el grado real de $v$ entre el grado máximo posible ($n-1$, si estuviera conectado con todos). Es la fracción de nodos a los que $v$ llega en un solo salto. En UCuenca, `DATCC-2A-C3` tiene $C_G = 17/176 = 0.097$: se conecta directamente al 9.7% de la red.

**Centralidad de intermediación** (*betweenness*, normalizada):

$$C_{\text{between}}(v) = \frac{1}{(n-1)(n-2)} \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$

> *Lectura:* para cada par de nodos $(s, t)$ distintos de $v$, se pregunta: ¿qué fracción de los caminos más cortos entre $s$ y $t$ pasan por $v$? ($\sigma_{st}(v)/\sigma_{st}$). Se suma esa fracción sobre todos los pares posibles y se normaliza. Un valor alto significa que $v$ es un "puente de tráfico": si falla, muchos pares de nodos pierden su ruta más corta. En UCuenca, `DATCC-2A-C3` tiene $C_B = 0.447$: casi la mitad de todos los caminos más cortos de la red pasan por él.

**Centralidad de cercanía** (*closeness*, normalizada):

$$C_{\text{close}}(v) = \frac{n-1}{\sum_{u \neq v} d(v, u)}$$

> *Lectura:* el denominador suma las distancias (en saltos) desde $v$ hasta todos los demás nodos. Cuanto más pequeña es esa suma, más "cerca" está $v$ de todos. Se invierte y se multiplica por $n-1$ para que el resultado quede entre 0 y 1. Un nodo con $C_C$ alto puede alcanzar cualquier equipo de la red en pocos saltos: ideal para ubicar servidores DNS, NTP o monitoreo. En UCuenca, `INTERNET-MPLS` lidera con $C_C = 0.276$.

**Centralidad de vector propio** (*eigenvector*):

$$C_{\text{eigen}}(v) = \frac{1}{\lambda} \sum_{u \in \mathcal{N}(v)} C_{\text{eigen}}(u)$$

> *Lectura:* la centralidad de $v$ es proporcional a la **suma de las centralidades de sus vecinos** $\mathcal{N}(v)$. $\lambda$ es una constante de normalización (el autovalor dominante de la matriz de adyacencia). La idea es que no es lo mismo tener muchos vecinos mediocres que pocos vecinos influyentes. Un switch de acceso conectado a `DATCC-2A-C3` (el hub más importante) hereda parte de su importancia. En UCuenca, el top de vector propio lo lideran los switches directamente conectados a los dos cores del Campus Central.

#### Resultados — Top-10 comparativo

| Rank | Nodo (Grado) | $C_G$ | Nodo (Between.) | $C_B$ | Nodo (Closeness) | $C_C$ | Nodo (Eigenvec.) | $C_E$ |
|------|-------------|-------|----------------|-------|-----------------|-------|-----------------|-------|
| 1 | DATCC-2A-C3 | 0.0966 | DATCC-2A-C3 | 0.4468 | INTERNET-MPLS | 0.2759 | DATCC-2A-C3 | 0.5022 |
| 2 | DATCC-2A-C2 | 0.0909 | CPAR-C10 | 0.4043 | DATCC-2A-C3 | 0.2683 | DATCC-2A-C2 | 0.4818 |
| 3 | AGRPRI-1A-D10 | 0.0682 | ROUTER-CAMPUS-HUAYNA-CAPAC | 0.3663 | PE2-CENTRAL | 0.2667 | FORTIGATE-1800F-CENTRAL | 0.2006 |
| 4 | BAL-AUL2-D1 | 0.0682 | INTERNET-MPLS | 0.3657 | FORTIGATE-1800F-CENTRAL | 0.2596 | CC-ARQUITECTURA-D107 | 0.1976 |
| 5 | CC-ARQUITECTURA-D107 | 0.0568 | PE2-CENTRAL | 0.2881 | PE1-CENTRAL | 0.2562 | CC-MONJAS-D126 | 0.1855 |
| 6 | CP-EADMINA1-D6 | 0.0511 | DT-0A-C13 | 0.2235 | PE1-BALZAY | 0.2511 | CC-ADM-D40 | 0.1799 |
| 7 | CC-MONJAS-D126 | 0.0455 | FORTIGATE-1800F-CENTRAL | 0.1863 | DATCC-2A-C2 | 0.2475 | CC-ECONOMIA-D51 | 0.1751 |
| 8 | DT-0A-C13 | 0.0455 | DATCC-2A-C2 | 0.1706 | ROUTER-CAMPUS-HUAYNA-CAPAC | 0.2421 | CC-JURISPRUDENCIA-D110 | 0.1748 |
| 9 | INTERNET-MPLS | 0.0455 | FORTIGATE-1800F-BALZAY | 0.1490 | FORTIGATE-1800F-BALZAY | 0.2408 | CC-FILOSOFIA-A-D108 | 0.1701 |
| 10 | BAL-CENTEC-D2 | 0.0398 | PE2-BALZAY | 0.1460 | PE2-BALZAY | 0.2385 | CC-QUIMICA-D109 | 0.1701 |

![Top-10 Centralidades](results/imagenes/p1_centralidades_top10.png)

#### Análisis — ¿Coinciden los nodos más centrales por grado con los de intermediación?

**Parcialmente.** `DATCC-2A-C3` (switch de core del Campus Central) encabeza tanto la centralidad de grado como la de intermediación y vector propio: es el nodo más conectado Y el mayor cuello de botella de la red.

Pero hay **divergencias significativas**:

- `INTERNET-MPLS` aparece en el top-4 de *closeness* pero no en los primeros puestos de grado ni *betweenness*. Esto revela su rol: no tiene muchas conexiones directas, pero su posición en la topología le permite llegar a cualquier nodo en pocos saltos (es el "centro geográfico" de la red desde la perspectiva de distancias). Colocar servicios como DNS o NTP cerca de este nodo reduciría la latencia promedio.

- `CPAR-C10` (switch de core de Paraíso) tiene la segunda mayor *betweenness* (0.4043) pero un grado modesto. Todos los flujos que atraviesan Campus Paraíso pasan obligatoriamente por él: **es un cuello de botella estructural crítico**, mucho más peligroso que lo que su grado sugiere.

- La centralidad de **vector propio** favorece nodos del Campus Central porque están conectados a `DATCC-2A-C3` y `DATCC-2A-C2`, que son los hubs dominantes. Un switch de acceso del Campus Central tiene mayor vector propio que un switch de agregación de Yanuncay precisamente porque sus vecinos son más influyentes.

---

### Ítem 4 · Clustering, diámetro, distancia media y asortatividad

#### Definiciones matemáticas

**Coeficiente de clustering local** de un nodo $v$:

$$C(v) = \frac{|\{(u,w) \in E : u,w \in \mathcal{N}(v)\}|}{\binom{k_v}{2}} = \frac{2\,t_v}{k_v(k_v-1)}$$

> *Lectura:* entre todos los vecinos de $v$, ¿cuántos pares de vecinos están también conectados entre sí? El numerador cuenta esos enlaces existentes ($t_v$ triángulos × 2); el denominador es el total de pares posibles $\binom{k_v}{2} = k_v(k_v-1)/2$. Si todos los vecinos de $v$ se conocen entre sí, $C(v) = 1$. Si ningún par de vecinos está conectado, $C(v) = 0$. Para nodos de grado 0 ó 1 no tiene sentido calcularlo → $C(v) = 0$.
>
> *Ejemplo UCuenca:* `DATCC-2A-C3` tiene 17 vecinos. Para que $C > 0$ debería haber enlaces entre esos 17 switches (ej. que dos switches de agregación estuvieran conectados entre sí). En la red jerárquica eso no ocurre → $C \approx 0$.

**Clustering medio global**:

$$\langle C \rangle = \frac{1}{n}\sum_{v \in V} C(v)$$

> *Lectura:* promedio del clustering local de todos los nodos. En UCuenca $\langle C \rangle = 0.034$: en promedio solo el 3.4% de los pares de vecinos de un equipo están conectados entre sí.

**Distancia media entre pares**:

$$\langle d \rangle = \frac{1}{n(n-1)} \sum_{u \neq v} d(u,v)$$

> *Lectura:* se suman las distancias más cortas (en saltos) entre todos los pares ordenados de nodos distintos, y se divide entre el número de pares $n(n-1)$. Es el "número de saltos típico" para ir de un equipo cualquiera a otro. En UCuenca $\langle d \rangle = 5.83$: en promedio se necesitan casi 6 saltos para cruzar la red.

**Diámetro**:

$$D = \max_{u,v \in V} d(u,v)$$

> *Lectura:* la distancia más larga entre cualquier par de nodos. Es el "peor caso": los dos equipos más alejados de la red. En UCuenca $D = 11$: hay al menos un par de equipos que necesita 11 saltos para comunicarse.

**Asortatividad por grado** (coeficiente de correlación de Pearson de los grados de los extremos de cada arista):

$$r = \frac{\sum_{(u,v)\in E} k_u k_v - \left[\frac{1}{2m}\sum_{(u,v)\in E}(k_u+k_v)\right]^2}{\frac{1}{2m}\sum_{(u,v)\in E}(k_u^2+k_v^2) - \left[\frac{1}{2m}\sum_{(u,v)\in E}(k_u+k_v)\right]^2}$$

> *Lectura:* para cada arista $(u,v)$, se observan los grados de sus dos extremos $k_u$ y $k_v$. La fórmula es el coeficiente de Pearson entre esos dos conjuntos de valores (uno por extremo). Si los nodos de alto grado tienden a conectarse con nodos de alto grado → $r > 0$ (red **asortativa**, como redes sociales). Si los nodos de alto grado tienden a conectarse con nodos de bajo grado → $r < 0$ (red **disasortativa**, como UCuenca con $r = -0.147$).

$r \in [-1, 1]$: positivo → nodos similares se conectan entre sí; negativo → nodos de grado alto se conectan con nodos de grado bajo.

#### Resultados

| Métrica | Valor |
|---------|-------|
| Clustering medio $\langle C \rangle$ | 0.0343 |
| Diámetro $D$ | 11 |
| Distancia media $\langle d \rangle$ | 5.8304 |
| Asortatividad por grado $r$ | −0.1468 |

#### Análisis

**¿Por qué el clustering es tan bajo comparado con una red social?**

En una red social, si A es amigo de B y A es amigo de C, es probable que B y C también sean amigos → triángulos frecuentes → $\langle C \rangle$ alto (típicamente 0.1–0.5).

En UCuenca, un switch de acceso (`ARQ-0A-A84`) se conecta únicamente a su switch de agregación (`CC-ARQUITECTURA-D107`). Sus vecinos (otros switches de acceso del mismo edificio) no se conectan entre sí porque eso crearía bucles indeseados en la capa de acceso. **La jerarquía prohíbe triángulos por diseño.** El resultado: $\langle C \rangle = 0.034$, apenas por encima de cero.

**¿Por qué la asortatividad es negativa?**

$r = -0.1468$ indica **disasortatividad**: los nodos de alto grado (`DATCC-2A-C3`, grado 17) se conectan preferentemente con nodos de bajo grado (switches de acceso, grado 1–2). Nunca hay un enlace directo entre dos switches de core porque la arquitectura los separa mediante la capa de agregación.

Esto tiene una consecuencia operativa importante: **la red es robusta frente a fallos aleatorios** (la probabilidad de eliminar un hub es baja porque los hubs son minoría) pero **frágil frente a ataques dirigidos** a los nodos de core y agregación.

---

### Ítem 5 · Puntos de articulación y puentes

#### Definiciones matemáticas

Un **punto de articulación** (o vértice de corte) es un nodo $v \in V$ tal que el subgrafo $G - v$ tiene más componentes conexas que $G$. Formalmente:

$$v \text{ es punto de articulación} \iff \kappa(G-v) > \kappa(G)$$

donde $\kappa(G)$ denota el número de componentes conexas de $G$.

> *Lectura:* si "borras" el nodo $v$ y todos sus enlaces, ¿el grafo se parte en más trozos que antes? Si sí, $v$ es imprescindible para mantener la red unida. En UCuenca, un switch de agregación como `BAL-AG-C4` conecta todos los switches de acceso de un edificio con el core; eliminarlo deja ese edificio sin ruta.

Un **puente** es una arista $e = (u,v) \in E$ tal que su eliminación desconecta el grafo:

$$e \text{ es puente} \iff \kappa(G-e) > \kappa(G)$$

> *Lectura:* si ese único cable entre $u$ y $v$ se corta, alguna parte de la red queda aislada — no existe ninguna ruta alternativa. El 67% de los enlaces de UCuenca son puentes, lo que significa que cortar cualquiera de esos cables aísla al menos un equipo.

Algorítmicamente se detectan con una sola DFS en $O(n+m)$ (algoritmo de Tarjan).

#### Resultados

| Métrica | Total |
|---------|-------|
| Puntos de articulación | **47** |
| Puentes | **141** |

**Puntos de articulación por campus:**

| Campus | Puntos de articulación |
|--------|----------------------|
| Campus Central | 23 |
| Campus Paraíso | 14 |
| Campus Balzay | 6 |
| Campus Yanuncay | 2 |
| Campus Hospitalidad | 1 |
| Nube MPLS | 1 |

**Puntos de articulación por capa jerárquica:**

| Capa | Puntos de articulación |
|------|----------------------|
| Agregación | 26 |
| Acceso | 17 |
| WAN | 3 |
| Core | 1 |

**Puentes por campus:**

| Campus | Puentes |
|--------|---------|
| Campus Central | 56 |
| Campus Paraíso | 42 |
| Campus Balzay | 25 |
| Campus Yanuncay | 12 |
| Campus Hospitalidad | 4 |
| Nube MPLS | 2 |

![Articulación y Puentes](results/imagenes/p1_articulacion_puentes.png)

#### Análisis

El número de puentes (141 de 209 aristas = **67%**) revela que dos tercios de los enlaces de la red son puntos únicos de fallo. Si cualquiera de esas 141 aristas falla, algún segmento queda aislado.

Los **26 puntos de articulación en la capa de agregación** son especialmente críticos: cada switch de agregación es el único nexo entre los switches de acceso de su edificio y el resto de la red. Perder un switch de agregación desconecta potencialmente a todos los equipos del edificio correspondiente.

El único punto de articulación en la capa **core** es preocupante: significa que al menos en un sub-árbol de la red existe un switch de core cuya falla aísla un subconjunto de nodos, lo que contradice el principio de redundancia declarado en el informe técnico.

---

### Ítem 6 · Contraste con el informe técnico

#### Pregunta del enunciado

¿Se observa redundancia *core*–agregación en Balzay y en Paraíso? ¿Y en Campus Central? (usar el atributo `capa`).

#### Metodología

Para cada campus, se identifican los switches de capa `agregacion` y se cuenta cuántos de sus vecinos pertenecen a la capa `core`. Si un switch de agregación tiene **más de un vecino de core**, tiene redundancia de núcleo.

#### Resultados

| Campus | Nodos agg | Con redundancia | Sin redundancia | ¿Tiene redundancia? |
|--------|-----------|----------------|----------------|---------------------|
| Campus Balzay | 5 | 4 | 1 | **SÍ ✓** |
| Campus Central | 14 | 13 | 1 | **SÍ ✓** |
| Campus Paraíso | 6 | 0 | 6 | **NO ✗** |
| Campus Yanuncay | 1 | 0 | 1 | **NO ✗** |
| Campus Hospitalidad | 1 | 0 | 1 | **NO ✗** |

#### Análisis — Contraste con el informe técnico

| Campus | Afirmación del informe | Evidencia en los datos | Conclusión |
|--------|----------------------|----------------------|------------|
| **Balzay** | Redundancia core–agg completa | 4/5 switches de agg conectados a `DT-0A-C12` Y `DT-0A-C13` | ✓ Confirmado |
| **Paraíso** | Redundancia core–agg completa | Solo existe `CPAR-C10` como switch de core; los dobles enlaces de los switches de agg van ambos al mismo nodo | ✗ **Contradicción** — es agregación de puertos (LAG), no redundancia de núcleo |
| **Campus Central** | "Enlaces simples agg–core" | 13/14 switches de agg conectados a `DATCC-2A-C2` Y `DATCC-2A-C3` | ✗ **El informe subestima** — hay más redundancia que la declarada |

**Paraíso es el hallazgo más importante**: el informe técnico declara redundancia física completa, pero los datos muestran un único switch de core (`CPAR-C10`). Lo que el informe interpreta como "doble enlace" es una agregación de puertos (Link Aggregation Group, LAG) hacia el mismo equipo, que aumenta el ancho de banda pero **no protege frente a la falla del switch de core**. Esta es exactamente la diferencia entre un puente (arista crítica) y un ciclo (camino alternativo real).

---

## P2 — Modelos Nulos y Visualización *(2 puntos)*

### Ítem 1 · Erdős–Rényi y Modelo de Configuración (100 realizaciones)

#### Definiciones matemáticas

**Modelo Erdős–Rényi $G(n,m)$:** grafo aleatorio con $n$ nodos donde se eligen uniformemente al azar exactamente $m$ aristas del total de $\binom{n}{2}$ posibles. Cada realización es estadísticamente equivalente.

> *Lectura:* el modelo ER es el "azar puro": se ponen los mismos $n$ nodos y $m$ aristas de la red real, pero las conexiones se sortean al azar sin ninguna preferencia. Si la red real difiere de ER, esa diferencia no se debe al azar sino a algún principio de organización (jerarquía, diseño, evolución).

Predicciones analíticas de ER para $p = \frac{2m}{n(n-1)}$:
$$\langle C \rangle_{ER} \approx p, \qquad \langle d \rangle_{ER} \approx \frac{\ln n}{\ln(np)}, \qquad r_{ER} \approx 0$$

> *Lectura:* en ER, la probabilidad de que dos vecinos de $v$ estén conectados entre sí es simplemente la densidad $p$ — no hay estructura local. La distancia media crece muy lentamente con $n$ (efecto "mundo pequeño" aleatorio). La asortatividad tiende a cero porque no hay preferencia por conectar nodos similares.

**Modelo de Configuración (CM):** dado un vector de grados $\{k_1, k_2, \ldots, k_n\}$, genera un grafo aleatorio que preserva **exactamente** esa secuencia de grados. Cada nodo $v$ tiene $k_v$ "medias aristas" que se conectan aleatoriamente entre sí. Tras eliminar auto-bucles y multi-aristas queda un grafo simple.

> *Lectura:* el CM le "da" a cada nodo los mismos $k_v$ enlaces que tiene en la red real, pero los conecta al azar. Si una propiedad (por ejemplo la asortatividad) coincide entre CM y la red real, significa que esa propiedad es consecuencia matemática de *quién tiene cuántos enlaces*, no de *a quién están conectados*. Si difiere, hay una organización adicional más allá de los grados.

La comparación ER vs CM responde: **¿qué propiedades de la red real se explican solo por su secuencia de grados?**

#### Resultados (100 realizaciones por modelo)

| Métrica | Red real | ER (media ± std) | CM (media ± std) |
|---------|----------|-----------------|-----------------|
| Clustering $\langle C \rangle$ | **0.0343** | 0.0094 ± 0.0081 | 0.0193 ± 0.0090 |
| Distancia media $\langle d \rangle$ | **5.8304** | 5.6314 ± 0.2860 | 4.2767 ± 0.1580 |
| Diámetro $D$ | **11** | 13.47 ± 1.63 | 9.46 ± 1.14 |
| Asortatividad $r$ | **−0.1468** | −0.0387 ± 0.0651 | −0.1717 ± 0.0636 |

![Comparación Modelos Nulos](results/imagenes/p2_comparacion_modelos.png)

#### Análisis — ¿Qué propiedades NO se explican por la secuencia de grados?

**Clustering:**
- Red real (0.034) > CM (0.019) > ER (0.009)
- Ningún modelo reproduce el clustering real. La jerarquía impone una **prohibición de triángulos que va más allá de la secuencia de grados**: incluso si la secuencia de grados fuera la misma, un grafo aleatorio formaría más triángulos que la red real. Esto confirma que el arquitecto de red suprimió deliberadamente los bucles en la capa de acceso.

**Distancia media y diámetro:**
- ER: distancias cortas (~5.6), diámetro grande (~13). La red aleatoria pura tiene el efecto "mundo pequeño" pero con alta variabilidad.
- CM: distancias más cortas que la red real (4.28 vs 5.83) pero diámetro más pequeño (9.46 vs 11). La secuencia de grados con muchos nodos de grado 1 obliga a caminos más largos que ER, pero los pocos hubs crean "atajos" que el CM aprovecha aleatoriamente. La red real tiene distancias más largas porque **la jerarquía fuerza rutas a través de capas específicas**.
- Conclusión: ni ER ni CM reproducen el diámetro real, lo que indica que la **topología en árbol jerárquico** es una propiedad estructural que trasciende la secuencia de grados.

**Asortatividad:**
- ER reproduce $r \approx 0$ (neutro). La red real tiene $r = -0.147$.
- CM reproduce bien la asortatividad ($r = -0.172 \approx -0.147$): la secuencia de grados **sí explica** la disasortatividad. Esto tiene sentido: tener muchos nodos de grado 1 y pocos hubs implica matemáticamente que los hubs deben conectarse con nodos de bajo grado (no hay suficientes hubs para conectarse entre sí).

---

### Ítem 2 · Modelo Barabási–Albert

#### Definiciones matemáticas

El modelo **Barabási–Albert (BA)** genera redes de escala libre mediante dos mecanismos:

1. **Crecimiento:** en cada paso $t$ se añade un nuevo nodo con $m_{BA}$ aristas.
2. **Enlace preferencial:** cada nueva arista se conecta al nodo $i$ existente con probabilidad:

$$\Pi(k_i) = \frac{k_i}{\sum_j k_j}$$

> *Lectura:* cuando llega un nuevo nodo a la red, no elige sus vecinos al azar — prefiere conectarse a los que ya tienen más enlaces. La probabilidad de elegir el nodo $i$ es proporcional a su grado actual $k_i$. Un nodo con el doble de enlaces tiene el doble de probabilidad de recibir una nueva conexión. Este mecanismo de "los ricos se hacen más ricos" (*rich-get-richer*) produce hubs dominantes y en el límite $n \to \infty$ genera $P(k) \sim k^{-3}$.

Para UCuenca: $m_{BA} = \text{round}(\langle k \rangle / 2) = \text{round}(2.362/2) = 1$.

#### Resultados

| Métrica | Red real | Barabási–Albert ($n=177$, $m_{BA}=1$) |
|---------|----------|--------------------------------------|
| Clustering $\langle C \rangle$ | 0.0343 | 0.0000 |
| Distancia media $\langle d \rangle$ | 5.8304 | 5.0603 |
| Diámetro $D$ | 11 | 11 |
| Asortatividad $r$ | −0.1468 | −0.2361 |

![Barabási–Albert vs UCuenca](results/imagenes/p2_barabasi_albert.png)

#### Análisis — ¿Se parece UCuenca a una red de crecimiento preferencial?

**Superficialmente sí, en el fondo no.**

| Propiedad | BA | UCuenca | Razón de la similitud/diferencia |
|-----------|-----|---------|----------------------------------|
| Cola pesada en $P(k)$ | Sí ($\gamma=3$) | Aparente | UCuenca tiene pocos hubs, pero por diseño, no por crecimiento |
| Clustering bajo | Sí (~0) | Sí (0.034) | Coinciden, pero por razones distintas |
| Asortatividad negativa | Sí (leve) | Sí (−0.15) | En BA los hubs SE CONECTAN entre sí eventualmente; en UCuenca están separados por capas |
| Proceso generativo | Orgánico, incremental | Planificado, jerárquico | **Diferencia fundamental** |

La red UCuenca **no fue construida por crecimiento preferencial**. Fue diseñada top-down: primero se instaló el core, luego la agregación y finalmente los switches de acceso. El grado alto de `DATCC-2A-C3` no es consecuencia de que "los nodos preferían conectarse a él cuando llegaban"; es consecuencia de que el arquitecto de red lo designó como switch de core responsable de 13 edificios del Campus Central.

El modelo correcto para una red de este tipo sería un **árbol jerárquico $k$-ario con redundancia parcial** (ciclos únicamente en el nivel core–agregación donde el diseño lo prevé).

---

### Ítem 3 · Visualizaciones propias

#### Visualización 1 — BFS por profundidad desde INTERNET-MPLS

![Visualización por campus](results/imagenes/p2_visualizacion_campus.png)

**Algoritmo:** BFS (*Breadth-First Search*) con re-espaciado por nivel. Se parte desde el nodo `INTERNET-MPLS` (gateway de salida a internet) y se calcula la profundidad BFS de cada nodo. La posición Y es proporcional a esa profundidad (gateway abajo, switches de acceso arriba); dentro de cada fila los nodos se distribuyen uniformemente a lo ancho del canvas, ordenados por campus para agrupar colores. El tamaño del nodo refleja su capa jerárquica: los nodos core/WAN aparecen más grandes y los de acceso más pequeños.

**Justificación del algoritmo:** La profundidad BFS desde el gateway mide directamente cuántos saltos separa a cada nodo de internet — que es la métrica operacional más importante en una red universitaria. Un nodo en la fila 1 (un salto) es un switch de core; uno en la fila 4–5 es un switch de acceso de edificio. Algoritmos de fuerza como Fruchterman-Reingold no garantizan que esta estructura quede visible; el layout BFS la explicita. Ordenar los nodos por campus dentro de cada fila permite ver, además, si los campus comparten nivel de profundidad o si algunos están más "alejados" del gateway que otros.

**Qué revela:** `INTERNET-MPLS` es el único nodo de profundidad 0 — cualquier tráfico a internet pasa obligatoriamente por él. Los routers WAN y switches de core ocupan las filas 1–2 (1–2 saltos). La capa de agregación aparece en las filas intermedias. Los 113 switches de acceso se distribuyen en las filas superiores: el hecho de que no todos estén a la misma profundidad confirma que la red no es un árbol perfecto — algunos edificios tienen un salto extra por la forma en que se encadenaron los switches de agregación.

#### Visualización 2 — Tamaño ∝ betweenness, color = capa (Kamada-Kawai escalado)

![Visualización por betweenness](results/imagenes/p2_visualizacion_betweenness.png)

**Algoritmo:** Kamada-Kawai con escalado de posiciones ×3.5. Kamada-Kawai asigna a cada par de nodos una longitud ideal de arco proporcional a su distancia en el grafo y minimiza la diferencia entre esas distancias ideales y las distancias euclídeas en el dibujo. El layout resultante produce posiciones normalizadas en $[-1, 1]$ que se multiplican por un factor 3.5 para expandir el espacio disponible — esto separa físicamente los nodos en el canvas sin alterar su estructura relativa, reduciendo el solapamiento entre los círculos grandes del centro.

**Justificación del algoritmo:** Kamada-Kawai coloca los nodos más centrales (equidistantes del resto) en el centro del dibujo — justo donde están los switches de core y WAN con mayor betweenness. El escalado ×3.5 combinado con figura 18×14 pulgadas y tamaño máximo de nodo controlado (1200 unidades) permite que los círculos grandes sean visibles sin tapar a sus vecinos.

**Qué revela:** los nodos de mayor intermediación (círculos más grandes) son switches de core y WAN, confirmando que son los cuellos de botella de la red — todo el tráfico entre campus pasa por ellos. Los switches de acceso (azul, círculos pequeños) forman la periferia; los de core (rojo) y WAN (morado) quedan en el centro. La diferencia de tamaño entre el nodo más grande (`DATCC-2A-C3`, betweenness=6880) y los de acceso (betweenness≈0) es visible a simple vista.

---

## Preguntas — Fase 1

### P1 · Medidas fundamentales

> **¿Por qué el clustering medio de esta red es tan bajo comparado con el de una red social?**

Porque la topología jerárquica en estrella prohíbe triángulos por diseño. En una red social si A conoce a B y A conoce a C, es probable que B y C también se conozcan. En UCuenca, si el switch A84 está conectado al switch de agregación D107, y el switch A85 también está conectado a D107, A84 y A85 **no** se conectan entre sí (eso crearía un ciclo indeseado en la capa de acceso). El clustering bajo es la huella matemática de la estrella jerárquica.

> **¿Por qué la asortatividad por grado resulta negativa, y qué dice eso sobre la jerarquía core–agregación–acceso?**

$r = -0.1468$ porque los hubs (grado 10–17: switches de core/agregación) se conectan exclusivamente con nodos de bajo grado (grado 1–3: switches de acceso). La jerarquía core–agregación–acceso impide la conexión directa entre dos nodos del mismo nivel, lo que matemáticamente produce disasortatividad. En redes sociales, los nodos de alto grado tienden a conectarse entre sí ($r > 0$: redes asortativas).

> **¿Coinciden los nodos más centrales por grado con los más centrales por intermediación? Si no coinciden, ¿qué papel distinto juega cada grupo en la red?**

Parcialmente. `DATCC-2A-C3` encabeza ambos rankings porque es el switch de core del Campus Central: más conexiones implica más caminos que lo atraviesan. Pero `CPAR-C10` (switch de core de Paraíso) tiene la segunda mayor betweenness con un grado relativo menor, porque **todos** los flujos que entran o salen de Paraíso pasan por él. La betweenness captura "cuello de botella estructural"; el grado captura "número de vecinos": no son lo mismo.

### P2 · Modelos nulos y visualización

> **¿Qué propiedades de la red UCuenca NO se explican por su secuencia de grados?**

El **clustering** y la **distancia media** no son reproducibles por el CM. La secuencia de grados explica la disasortatividad ($r$ del CM ≈ $r$ real) pero no la organización jerárquica que alarga las distancias ni la ausencia de triángulos que baja el clustering.

> **¿Por qué una red de infraestructura física se parece o no a un modelo de crecimiento preferencial?**

Se parece superficialmente (distribución sesgada, clustering bajo, asortatividad negativa) pero el mecanismo generativo es opuesto. BA es orgánico e incremental; UCuenca es planificada y jerárquica. La similitud en métricas es coincidencia, no evidencia de crecimiento preferencial.

> **¿Qué algoritmo de disposición (layout) se usó y por qué?**

- **BFS por profundidad desde INTERNET-MPLS** para la visualización por campus: cada fila horizontal corresponde a un nivel de profundidad BFS (número de saltos desde el gateway). Los nodos se ordenan por campus dentro de cada fila, agrupando colores y haciendo visible la topología en árbol acceso → agregación → core → WAN. Se eligió sobre Fruchterman-Reingold porque la jerarquía de UCuenca es conocida de antemano y no necesita ser "descubierta" por un algoritmo de fuerzas.
- **Kamada-Kawai escalado ×3.5** para la visualización por betweenness: asigna distancias ideales proporcionales a la distancia en el grafo y escala las posiciones resultantes para reducir solapamientos entre los círculos grandes del centro. Coloca los cuellos de botella en el centro geométrico, haciendo visualmente evidente qué nodos dominan los caminos más cortos.

---

## Fase 2 — Recorrido y Partición

> *Peso: 5 puntos | Contenidos 2.1–2.4 del sílabo*

---

## P3 — BFS y DFS sobre la Red *(2.5 puntos)*

### Ítem 1 · BFS y DFS desde cero

#### Definiciones matemáticas

**BFS (Búsqueda en Anchura):** dado un nodo origen $s$, explora el grafo por niveles de distancia creciente. Usa una cola FIFO.

$$d(s, v) = \min\{|P| : P \text{ es camino de } s \text{ a } v\}$$

> *Lectura:* la distancia $d(s,v)$ que BFS encuentra es el número mínimo de aristas para ir de $s$ a $v$. BFS garantiza que cuando visita $v$ por primera vez, ya encontró el camino más corto. La cola FIFO asegura que se procesan primero los nodos más cercanos al origen.

**DFS (Búsqueda en Profundidad):** explora cada rama hasta el fondo antes de retroceder. Usa una pila (implícita en la recursión).

**Ciclo:** un ciclo en un grafo no dirigido es una secuencia de nodos $v_1, v_2, \ldots, v_k, v_1$ tal que cada par consecutivo está unido por una arista y todos los nodos son distintos (excepto el primero y el último):

$$C = (v_1 - v_2 - \cdots - v_k - v_1), \quad v_i \neq v_j \text{ para } i \neq j$$

> *Lectura:* se parte de $v_1$, se recorre la secuencia de aristas, y se regresa a $v_1$ sin repetir ningún nodo. En términos de red, un ciclo entre dos nodos $A$ y $B$ implica que existen **al menos dos caminos independientes** de $A$ a $B$ — si uno de los enlaces del ciclo falla, el tráfico puede tomar el otro camino. La **ausencia de ciclos** en una zona equivale a topología de árbol: no hay camino alternativo y cualquier fallo de enlace aísla a los equipos aguas abajo.

En grafos no dirigidos, las aristas se clasifican en:
- **Aristas de árbol:** aristas $(u,v)$ donde $v$ se descubre por primera vez desde $u$.
- **Aristas de retroceso:** aristas $(u,v)$ donde $v$ ya fue visitado y es ancestro de $u$ → indican un **ciclo**.

**Complejidad de ambos algoritmos:**

$$T(n, m) = O(n + m), \qquad S(n) = O(n)$$

> *Lectura:* tanto BFS como DFS visitan cada nodo una vez y cada arista a lo sumo dos veces (una por cada extremo), de ahí el $O(n+m)$. El espacio adicional es $O(n)$ para el conjunto de nodos visitados y la cola/pila.

**Número ciclomático** (número de ciclos independientes de un grafo conexo):

$$\mu = m - n + 1$$

> *Lectura:* un árbol de $n$ nodos tiene exactamente $n-1$ aristas y cero ciclos. Cada arista adicional sobre ese árbol crea exactamente un ciclo nuevo. En UCuenca: $\mu = 209 - 177 + 1 = 33$. Hay 33 ciclos independientes, que corresponden a los 33 enlaces redundantes de la red.

#### Estructura de datos empleada e implementación

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

### Ítem 2 · Perfil de profundidad BFS desde el core

**Origen:** `DATCC-2A-C3` (switch de core del Campus Central, grado = 17)

| Distancia | Nodos | Capa dominante |
|-----------|-------|----------------|
| 0 | 1 | core |
| 1 | 17 | agregacion |
| 2 | 50 | acceso |
| 3 | 19 | acceso |
| 4 | 13 | acceso |
| 5 | 40 | acceso |
| 6 | 29 | acceso |
| 7 | 8 | acceso |

![Perfiles BFS](results/imagenes/p3_perfil_profundidad.png)

#### Análisis

El perfil confirma la jerarquía de tres capas declarada en el informe técnico:
- **Distancia 1:** los 17 vecinos directos son casi todos switches de agregación del Campus Central, más los nodos WAN hacia otros campus.
- **Distancia 2–7:** dominados completamente por switches de acceso. La presencia de nodos de agregación/core a distancias 3–4 corresponde a otros campus (Paraíso, Balzay) que se alcanzan a través de la nube MPLS.

La jerarquía declarada **sí se refleja** en las distancias: core → agregación → acceso se corresponde con los niveles 0 → 1 → 2 del BFS desde el core.

### Ítem 3 · Perfil BFS desde la nube MPLS

**Origen:** `INTERNET-MPLS` (grado = 8)

| Distancia | Nodos | Campus más representados |
|-----------|-------|--------------------------|
| 0 | 1 | Nube MPLS |
| 1 | 8 | Central (3), Balzay (2), Hospitalidad (1), Paraíso (1), Yanuncay (1) |
| 2 | 13 | Central (4), Hospitalidad (4), Paraíso (2), Balzay (2) |
| 3 | 38 | Central (14), Yanuncay (11), Balzay (6), Paraíso (6) |
| 4 | 97 | Central (43), Paraíso (28), Balzay (23) |
| 5 | 18 | Central (10), Paraíso (7) |
| 6 | 2 | Central (1), Balzay (1) |

#### Análisis — ¿Qué campus quedan más lejos?

Desde MPLS, los campus más "lejanos" (mayor concentración a distancias 4–6) son **Campus Central** y **Campus Paraíso**. Esto se explica porque ambos tienen más nodos en la capa de acceso (muchos switches de acceso que están 2–3 saltos más allá de su core), mientras que campus más pequeños como Yanuncay u Hospitalidad tienen menos capas y se agotan a distancias menores.

**Campus Yanuncay** aparece muy temprano (distancia 3) a pesar de ser campus pequeño: tiene pocos nodos de acceso, por lo que se "agota" rápido.

### Ítem 4 · Ciclos detectados con DFS

#### ¿Qué es un ciclo en este contexto?

Un **ciclo** en el grafo de la red es un camino cerrado: una secuencia de equipos y enlaces que parte de un nodo y regresa a él sin repetir ninguna arista. Su significado operativo es directo:

> **Ciclo = redundancia = camino alternativo.** Si existe un ciclo entre los nodos A y B, hay al menos dos rutas independientes entre ellos: si un enlace falla, el tráfico puede redirigirse por la ruta alternativa sin pérdida de conectividad. **La ausencia de ciclos en una zona equivale a topología de árbol: cualquier fallo de enlace o nodo en esa zona desconecta irremediablemente a los equipos aguas abajo.**

#### Cómo DFS detecta ciclos (implementación desde cero)

Durante el DFS, cada arista se clasifica automáticamente:

- **Arista de árbol** $(u \to v)$: $v$ no había sido visitado → construye el árbol DFS.
- **Arista de retroceso** $(u \to w)$: $w$ ya fue visitado y es ancestro de $u$ → **cierra un ciclo**.

Cada arista de retroceso corresponde exactamente a un ciclo independiente. El número ciclomático predice cuántas deben encontrarse:

$$\mu = m - n + 1 = 209 - 177 + 1 = 33$$

La función `detectar_ciclos()` de `problema3.py` ejecuta `dfs()` desde el switch de core `DATCC-2A-C3`, recorre los 177 nodos y 209 aristas, y registra cada arista de retroceso encontrada.

#### Resultados

| Métrica | Valor |
|---------|-------|
| Número ciclomático $\mu = m - n + 1$ | **33** |
| Aristas de retroceso detectadas por DFS | **33** ✓ |
| Ciclos en Campus Central | 21 |
| Ciclos en Campus Balzay | 9 |
| Ciclos en Nube MPLS | 3 |
| Ciclos en Campus Paraíso | **0** |
| Ciclos en Campus Yanuncay | **0** |
| Ciclos en Campus Hospitalidad | **0** |

![Ciclos DFS](results/imagenes/p3_ciclos.png)

*Rojo = aristas de retroceso (cierran ciclos). Gris = aristas de árbol DFS. Los 33 ciclos se concentran en Campus Central y Balzay; el resto del grafo es árbol puro.*

#### Análisis — Relación con los enlaces redundantes

Los 33 ciclos se ubican exclusivamente en tres zonas. La clave para entenderlos es que **un ciclo aparece cuando un switch de agregación tiene dos cables subiendo hacia el core** en lugar de uno solo:

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

**Campus Central (21 ciclos):** tiene dos switches de core (`DATCC-2A-C2` y `DATCC-2A-C3`). Cada uno de sus 21 switches de agregación tiene un cable hacia cada core, formando un triángulo como el del esquema izquierdo — un ciclo por switch de agregación. Adicionalmente, el edificio de Arquitectura (`CC-ARQUITECTURA-D107`, grado=10) aporta ciclos propios por sus enlaces internos redundantes.

**Campus Balzay (9 ciclos):** mismo principio — dos cores duales (`DT-0A-C12` y `DT-0A-C13`). Cada switch de agregación de Balzay con doble uplink forma un triángulo → 9 ciclos.

**Nube MPLS (3 ciclos):** los routers `PE1-BALZAY`, `PE2-CENTRAL` e `INTERNET-MPLS` están interconectados entre sí formando un pequeño anillo en la capa WAN — redundancia de tránsito entre campus.

**Campus Paraíso, Yanuncay y Hospitalidad (0 ciclos):** sus switches de agregación tienen un único cable hacia el core — esquema derecho del diagrama. No hay triángulo, no hay ciclo, no hay camino alternativo. Un fallo en cualquier enlace aísla permanentemente a los equipos de acceso aguas abajo.

#### Zonas sin ciclos = zonas sin camino alternativo

| Campus | Ciclos | Puentes en P1 | Implicación |
|--------|--------|---------------|-------------|
| Central | 21 | Pocos | Redundancia real: doble uplink core–agregación |
| Balzay | 9 | Moderados | Redundancia core–agregación confirmada |
| MPLS | 3 | 0 | Anillo WAN entre campus |
| **Paraíso** | **0** | **Muchos** | **Árbol puro: un fallo aisla edificios enteros** |
| **Yanuncay** | **0** | **Muchos** | **Árbol puro: topología completamente sin respaldo** |
| **Hospitalidad** | **0** | **Muchos** | **Árbol puro: topología completamente sin respaldo** |

Esto cierra el círculo con el P1 Ítem 5: los 141 puentes del grafo son exactamente las aristas **fuera de todo ciclo** — las aristas de árbol DFS. Los 68 enlaces no-puente (209 − 141 = 68) forman los 33 ciclos (cada ciclo independiente aporta en promedio 2 enlaces al total de no-puentes).

La coincidencia es total: **cero ciclos en una zona ↔ todas sus aristas son puentes ↔ cualquier fallo de enlace aísla un subgrafo ↔ ausencia de camino alternativo.**

### Ítem 5 · BFS vs DFS para inspección física

**Conclusión:** DFS modela mejor la inspección física de armarios.

| Algoritmo | Orden de visita | Desplazamiento físico |
|-----------|----------------|-----------------------|
| **BFS** | Todos los switches de core → todos los de agregación → todos los de acceso | El técnico va de edificio en edificio en cada nivel: muchos desplazamientos |
| **DFS** | Core → un edificio completo (agg → acceso → acceso → ...) → siguiente edificio | El técnico termina un edificio antes de moverse al siguiente: eficiente |

Los primeros 10 nodos de DFS ilustran esto: `DATCC-2A-C3` (core) → `DATCC-2A-C2` (core) → `CC-AETUC-D30` (agg) → `AETUC-0A-A76` (acceso) → `AETUCCF-2A-A79` (acceso) → `AETUC-0A-A97` (acceso) → `CC-ARQUITECTURA-D107` (agg) → `ARQ-0A-A85` (acceso)...

DFS baja toda la rama de un edificio antes de pasar al siguiente switch de agregación.

---

## P4 — Comunidades y Modularidad *(2.5 puntos)*

### Ítem 1 · Louvain con 5 semillas

#### Definición matemática

La **modularidad** $Q$ mide qué tan bien una partición $\mathcal{C}$ separa la red respecto a un modelo nulo aleatorio:

$$Q = \frac{1}{2m} \sum_{c \in \mathcal{C}} \sum_{u,v \in c} \left[A_{uv} - \frac{k_u k_v}{2m}\right]$$

donde $A_{uv}$ es la matriz de adyacencia, $k_u$ y $k_v$ los grados, y $m$ el número de aristas.

> *Lectura:* para cada par de nodos $(u,v)$ en la misma comunidad, se compara la arista real $A_{uv}$ con la probabilidad esperada en un grafo aleatorio con los mismos grados $\frac{k_u k_v}{2m}$. Si hay más conexiones dentro de las comunidades de lo que el azar esperaría, $Q > 0$. $Q \in [-1, 1]$; valores > 0.3 indican estructura comunitaria significativa.

#### Cómo funciona Louvain

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

#### Resultados

| Semilla | Comunidades | Modularidad Q |
|---------|-------------|---------------|
| 0 | 14 | **0.7632** |
| 7 | 15 | 0.7615 |
| 13 | 13 | 0.7587 |
| 42 | 15 | 0.7590 |
| 99 | 15 | 0.7312 |

**Mejor partición:** semilla 0 → 14 comunidades, Q = 0.7632.

#### Análisis — Estabilidad

$Q$ varía entre 0.73 y 0.76 según la semilla (rango de ~0.03), y el número de comunidades entre 13 y 15. El resultado **no es perfectamente estable**, lo que indica que el paisaje de optimización de $Q$ tiene múltiples óptimos locales casi equivalentes. Sin embargo, la variación es pequeña: las particiones son estructuralmente similares. $Q = 0.76$ es un valor muy alto, indicando estructura comunitaria fuerte.

### Ítem 2 · Comparación con partición por campus (NMI y ARI)

#### Definiciones

**NMI (Información Mutua Normalizada):**

$$\text{NMI}(\mathcal{C}, \mathcal{X}) = \frac{2\, I(\mathcal{C}; \mathcal{X})}{H(\mathcal{C}) + H(\mathcal{X})} \in [0, 1]$$

> *Lectura:* mide cuánta información comparten dos particiones. $\text{NMI} = 1$ significa que conocer la comunidad de un nodo determina perfectamente su campus (y viceversa). $\text{NMI} = 0$ significa que son independientes. Aquí NMI = 0.618: las comunidades Louvain capturan el 62% de la información de la partición por campus.

**ARI (Índice de Rand Ajustado):**

$$\text{ARI} \in [-1, 1], \quad \text{ARI} = 1 \iff \text{particiones idénticas}$$

> *Lectura:* compara par a par todos los nodos: ¿los nodos que Louvain pone en la misma comunidad también están en el mismo campus? ARI = 0.33 indica coincidencia moderada, corrigiendo por el azar.

#### Resultados

| Métrica | Valor |
|---------|-------|
| NMI | **0.618** |
| ARI | **0.327** |

![Matriz de confusión](results/imagenes/p4_confusion_campus.png)

#### Análisis

La matriz de confusión muestra que varias comunidades se corresponden bien con un único campus (comunidades 0, 1, 10 con Campus Central/Yanuncay/Paraíso respectivamente). Pero la **comunidad 9** mezcla nodos de Balzay, Central, Hospitalidad, Paraíso, Yanuncay y MPLS: son los nodos de la capa WAN/interconexión que Louvain agrupa porque están estructuralmente cerca entre sí (todos conectados a través de la nube MPLS), aunque geográficamente pertenecen a campus distintos.

En otras palabras: al aplicar Louvain se formó una comunidad compuesta por los routers de interconexión (`PE1-BALZAY`, `PE2-CENTRAL`, `INTERNET-MPLS` y similares) que, aunque administrativamente pertenecen a campus distintos, están directamente conectados entre sí a través de la nube MPLS. Louvain los agrupó juntos porque desde la perspectiva de la topología actúan como una unidad cohesionada — esto no es un error del algoritmo sino una detección funcionalmente correcta: esos equipos forman la capa WAN de interconexión entre campus y en la red se comportan como un grupo propio, independientemente del campus al que pertenezcan en papel.

### Ítem 3 · Nodos discrepantes

**83 de 177 nodos** (47%) son asignados por Louvain a una comunidad distinta de la mayoritaria de su campus.

#### Análisis

Los patrones de discrepancia son reveladores:
- **Nodos WAN/interconexión** (`PE1-BALZAY`, `PE2-CENTRAL`, routers de campus): agrupados todos en la comunidad 9 junto con `INTERNET-MPLS`. Louvain los pone juntos porque están interconectados a través de la nube MPLS, independientemente del campus físico. Esto es **correcto desde la perspectiva de ingeniería**: esos equipos pertenecen a la capa de interconexión, no a ningún campus específico.
- **Switches de acceso de Campus Paraíso** (comunidades 10–13): Louvain divide Paraíso en 4 comunidades distintas según el switch de agregación al que están conectados. Cada edificio de Paraíso forma una subcomunidad propia, lo que refleja la topología en estrella: los switches de acceso de un edificio solo se conectan a través de su switch de agregación.
- **Edificio de Arquitectura** (comunidad 2): `CC-ARQUITECTURA-D107` y sus switches de acceso forman comunidad propia, a pesar de estar en Campus Central. La razón: `CC-ARQUITECTURA-D107` tiene grado 10, creando una subestructura densa que Louvain separa del resto del campus.

### Ítem 4 · k-means espectral (Laplaciano)

> **Fuente del código:** adaptado de `codigo_referencia/kmeans/ejemplo1.jl` (Dr. Fabián Astudillo-Salinas, Módulo 1217 — Redes Complejas). El original implementa k-means desde cero en Julia con inicialización K-means++ (`init_plusplus`), paso de asignación (`assign_clusters`), actualización de centroides (`update_centroids`) y métrica WCSS de convergencia. La adaptación a Python usa `sklearn.cluster.KMeans` con `init="k-means++"`, que implementa los mismos pasos internamente. El embedding espectral (vectores propios del Laplaciano) sustituye los datos numéricos del ejemplo original por coordenadas topológicas de la red.

#### Definición matemática

El **Laplaciano normalizado** del grafo:

$$L_{\text{sym}} = D^{-1/2}(D - A)D^{-1/2}$$

> *Lectura:* $D$ es la matriz diagonal de grados y $A$ la matriz de adyacencia. Los vectores propios de $L_{\text{sym}}$ con menores valores propios capturan la estructura de conectividad del grafo: los nodos que están bien conectados entre sí tienen coordenadas similares en el espacio espectral. k-means sobre esas coordenadas agrupa nodos por su posición espectral, que refleja conectividad más que geometría euclídea.

#### Resultados

| Métrica | Valor |
|---------|-------|
| k-means vs campus: NMI | **0.640** |
| k-means vs campus: ARI | **0.423** |
| k-means vs Louvain: NMI | **0.860** |

![k-means vs Louvain](results/imagenes/p4_kmeans_vs_louvain.png)

#### Análisis

k-means espectral supera ligeramente a Louvain en NMI y ARI respecto al campus real (0.64 vs 0.62 y 0.42 vs 0.33). Ambos métodos coinciden en un 86% de la información mutua (NMI k-means vs Louvain = 0.86), lo que indica que ambos descubren una estructura comunitaria similar aunque por caminos matemáticos distintos.

#### ¿Por qué k-means con distancia euclídea puede o no ser adecuado para un grafo?

El problema fundamental es que **un grafo no tiene coordenadas euclídeas naturales** — los nodos no existen en un espacio geométrico, solo existen conexiones entre ellos. Aplicar k-means directamente sobre un grafo no tiene sentido porque k-means mide distancias euclídeas y en un grafo la distancia entre nodos se mide en saltos, no en metros.

La solución es el **embedding espectral**: transformar el grafo en vectores antes de aplicar k-means. Cada nodo recibe un vector de coordenadas calculado a partir de los $k$ primeros vectores propios del Laplaciano normalizado $L_{\text{sym}}$. El truco matemático es que nodos que están bien conectados entre sí quedan cerca en ese espacio vectorial — la estructura de conexiones del grafo se traduce en proximidad euclídea.

```
Grafo (conexiones)  →  Laplaciano  →  vectores propios  →  coordenadas por nodo
                                                              ↓
                                                         k-means (distancia euclídea)
```

**¿Cuándo funciona bien?** Cuando las comunidades del grafo son compactas y bien separadas entre sí. En UCuenca, cada campus forma una estrella densa (muchas conexiones internas, pocas hacia fuera), lo que se traduce en clusters bien separados en el espacio espectral — de ahí que k-means obtenga NMI = 0.64.

**¿Cuándo falla?** Cuando las comunidades tienen formas irregulares o están encadenadas. k-means asume comunidades esféricas de tamaño similar en el espacio euclídeo. En UCuenca, la comunidad WAN es una cadena lineal de routers (no una esfera), y los campus pequeños como Hospitalidad (5 nodos) son mucho más pequeños que Campus Central (80+ nodos) — esto viola los supuestos de k-means y explica que no alcance NMI = 1 aunque el embedding sea bueno.

Louvain no tiene este problema porque no asume ninguna forma geométrica: solo maximiza Q mirando las conexiones directas.

### Ítem 5 · Limitación de resolución de la modularidad

#### Análisis

La modularidad $Q$ tiene una **escala de resolución intrínseca**: comunidades con pocas aristas internas pueden no ser detectadas como comunidades separadas si el grafo es grande. El umbral aproximado es:

$$|E_c| \lesssim \sqrt{2m} \approx \sqrt{418} \approx 20 \text{ aristas}$$

Cualquier campus con menos de ~20 aristas internas corre el riesgo de ser absorbido por una comunidad vecina más grande, porque fusionarlo incrementa más $Q$ que mantenerlo separado.

#### Evidencia en UCuenca

La siguiente tabla muestra el tamaño de cada campus (nodos y aristas internas) frente al umbral de resolución:

| Campus | Nodos | Aristas internas | ¿Supera umbral (~20)? | Comportamiento Louvain |
|--------|-------|-----------------|----------------------|------------------------|
| Campus Central | ~85 | ~97 | ✓ Sí | **Subdividido** en 8–9 subcomunidades por edificio |
| Campus Paraíso | ~37 | ~36 | ✓ Sí | **Subdividido** en 4 subcomunidades |
| Campus Balzay | ~30 | ~28 | ✓ Sí | Detectado como 1–2 comunidades |
| Campus Yanuncay | ~14 | ~13 | ✗ No | Detectado marginalmente, parcialmente fusionado |
| Campus Hospitalidad | ~6 | ~5 | ✗ No | **Absorbido** en comunidad WAN (comunidad 9) |
| Museo / C. Histórico | ~3 | ~2 | ✗ No | **Absorbido** en comunidad WAN (comunidad 9) |

**Lo que muestra la evidencia:**

- **Campus grandes (Central, Paraíso, Balzay):** superan el umbral con holgura → Louvain los detecta pero los *subdivide* en subcomunidades por edificio, porque dentro de cada campus los switches de acceso de un edificio forman subestructuras más densas entre sí que con el resto del campus.

- **Campus pequeños (Hospitalidad, Museo, Centro Histórico):** están muy por debajo del umbral (~2–5 aristas internas vs umbral de 20) → Louvain los *fusiona* con la comunidad WAN porque aportan más $Q$ uniéndose a la comunidad 9 que existiendo solos.

**Consecuencia:** Louvain detecta 14 comunidades, pero la partición real por campus tiene 8. El exceso se explica por los dos fenómenos anteriores actuando simultáneamente: subdivide los campus grandes y fusiona los campus pequeños. Desde la perspectiva de un administrador de red, esto significa que Louvain ve los *edificios* como unidad natural, no los campus.

---

## Preguntas — Fase 2

### P3 · BFS y DFS

> **¿La jerarquía declarada en el informe técnico se refleja en las distancias BFS?**

Sí. El perfil de profundidad desde `DATCC-2A-C3` muestra: distancia 0 = core, distancia 1 = casi exclusivamente agregación, distancia 2+ = acceso. Los tres niveles jerárquicos se corresponden directamente con los primeros tres niveles del BFS. La presencia de nodos de otros campus a distancias 3–4 refleja la ruta core → MPLS → core remoto → agregación remota.

> **¿Qué campus quedan más lejos del resto de la institución (desde MPLS)?**

**Campus Central** y **Campus Paraíso** concentran la mayoría de nodos a distancias 4–6 desde `INTERNET-MPLS`. Son los campus más grandes (más switches de acceso), por lo que tienen mayor "profundidad" interna. Campus Yanuncay y Hospitalidad se "agotan" a distancias 2–3 por tener menos nodos.

> **¿Dónde están los ciclos? ¿Coinciden con los enlaces redundantes del informe?**

Los 33 ciclos se concentran en **Campus Central** (21) y **Campus Balzay** (9), exactamente los dos campus que el informe declara con redundancia core–agregación. Paraíso, Yanuncay y Hospitalidad tienen 0 ciclos, confirmando la ausencia de redundancia real en esos campus.

> **¿BFS o DFS modela mejor la inspección física de armarios?**

**DFS**. Un técnico que recorre físicamente los armarios prefiere terminar un edificio completo antes de desplazarse al siguiente. DFS hace exactamente eso: profundiza por una rama (edificio) hasta agotar todos sus switches de acceso antes de retroceder al switch de agregación y pasar al siguiente edificio. BFS obligaría a visitar todos los switches de agregación de todos los edificios primero, multiplicando los desplazamientos.

### P4 · Comunidades y modularidad

> **¿Qué propiedades no se explican por la secuencia de grados y qué dice la modularidad sobre la jerarquía?**

La modularidad $Q = 0.763$ es muy alta, indicando que la red tiene estructura comunitaria fuerte **más allá** de lo que su secuencia de grados explicaría. Las comunidades Louvain corresponden aproximadamente a los campus físicos (NMI = 0.62), pero son más finas: cada edificio dentro de un campus tiende a formar su propia subcomunidad, reflejando la topología en estrella donde los switches de acceso de un edificio solo se conectan a través de un único switch de agregación.

> **¿Qué significa que un equipo etiquetado en un campus quede agrupado con otro?**

Los nodos discrepantes más importantes son los **routers WAN e interconexión** (PE1-BALZAY, PE2-CENTRAL, INTERNET-MPLS, routers de campus): Louvain los agrupa en la comunidad 9 independientemente de su campus físico. Esto es correcto desde la perspectiva de ingeniería: esos equipos pertenecen a la capa de interconexión MPLS, no a ningún campus en particular. Su comunidad natural es la nube WAN, no el edificio donde físicamente están ubicados.

> **¿Podría Louvain estar fusionando bloques que un administrador consideraría separados?**

Sí, por la limitación de resolución. Los campus pequeños (Hospitalidad, Museo, Centro Histórico) son absorbidos en la comunidad WAN (comunidad 9) porque sus pocos nodos no generan suficiente $Q$ interno para justificar una comunidad propia. Un administrador de red los consideraría entidades separadas, pero Louvain los trata como periféricos del backbone MPLS.

---

## Fase 3 — Optimización en Redes

> *Peso: 6 puntos | Contenidos 3.1–3.5 del sílabo*

---

## P5 — Caminos Mínimos con Múltiples Métricas de Peso *(2 puntos)*

### Modelos de peso

Se definen tres funciones de peso sobre las aristas de la red:

**Modelo 1 — Saltos (topológico):**

$$w_{\text{saltos}}(u,v) = 1 \quad \forall (u,v) \in E$$

> *Lectura:* todos los enlaces valen lo mismo. La distancia entre dos equipos es simplemente la cantidad de "saltos" (equipos intermedios) necesarios. Es el modelo más simple: ideal para contar hops en traceroute.
>
> *En palabras simples:* cada cable cuenta como 1 paso, sin importar si es un cable de fibra de 10 Gbps o un enlace de 100 Mbps. Se usa para saber cuántos equipos hay entre el origen y el destino.

**Modelo 2 — Latencia:**

$$w_{\text{lat}}(u,v) = \alpha + \frac{\beta}{c(u,v)}$$

con $\alpha = 0.1\ \text{ms}$ (latencia de propagación fija) y $\beta = 1000\ \text{Mbps·ms}$.

> *Lectura:* el retardo de un enlace tiene dos componentes: uno fijo ($\alpha$, latencia mínima de propagación) y uno que disminuye a medida que la capacidad $c(u,v)$ aumenta. Un enlace de 10 000 Mbps tiene retardo adicional $1000/10000 = 0.1$ ms; uno de 100 Mbps tiene $1000/100 = 10$ ms. Caminos de alto ancho de banda son "más baratos" para este modelo.
>
> *En palabras simples:* un cable más ancho (mayor capacidad) tarda menos en enviar el mismo paquete. Este modelo elige rutas por cables rápidos aunque tengan más saltos.

**Modelo 3 — Carga:**

$$w_{\text{carga}}(u,v) = \frac{b(u,v)}{c(u,v)}$$

donde $b(u,v)$ es el tráfico medido en Mbps y $c(u,v)$ la capacidad estimada.

> *Lectura:* es la **utilización** del enlace: fracción de su capacidad que ya está siendo usada. Un enlace al 90% de su capacidad tiene $w = 0.9$ (saturado); uno al 5% tiene $w = 0.05$ (holgado). El camino de carga mínima evita los cuellos de botella actuales.
>
> *En palabras simples:* si el camino más corto en saltos pasa por un cable ya congestionado, este modelo busca una ruta alternativa con cables más libres. Es como usar Waze para evitar el tráfico.

### Ítem 1 · Implementación de Dijkstra y Floyd-Warshall — verificación sobre 20 pares

**Modelo de peso empleado para la verificación:** se usaron los tres modelos definidos (saltos, latencia y carga). En la práctica, Dijkstra es el algoritmo de elección para consultas individuales origen-destino con cualquier modelo de peso positivo; Floyd-Warshall se ejecuta una sola vez para obtener todas las distancias simultáneamente. Ambos algoritmos son agnósticos al modelo: el peso $w(u,v)$ se pasa como parámetro y el núcleo del algoritmo no cambia.

**Justificación de no negatividad de los pesos (requisito de Dijkstra):**

Dijkstra exige $w(u,v) \geq 0$ para todo enlace; si algún peso fuera negativo el algoritmo podría devolver distancias incorrectas y habría que reemplazarlo por Bellman-Ford ($O(nm)$). Se justifica a continuación que los tres modelos cumplen esta condición:

| Modelo | Expresión | Por qué $w \geq 0$ |
|--------|-----------|-------------------|
| Saltos | $w = 1$ | Constante positiva por definición. |
| Latencia | $w = \alpha + \beta / c(u,v)$ | $\alpha = 0.1\ \text{ms} > 0$, $\beta = 1000\ \text{Mbps·ms} > 0$, $c(u,v) > 0$ (capacidad estimada mínima = 100 Mbps). La suma de dos términos positivos es positiva. |
| Carga | $w = \max(b(u,v)/c(u,v),\ 10^{-6})$ | $b(u,v) \geq 0$ (tráfico no puede ser negativo) y $c(u,v) > 0$, por lo que el cociente es $\geq 0$. El `max` con $10^{-6}$ evita además el caso $w = 0$ en aristas sin tráfico medido. |

La verificación en código confirma los tres modelos en tiempo de ejecución: si cualquier arista produjera $w < 0$, el programa emite una advertencia explícita. En esta red los tres modelos pasan sin advertencias.

**Dijkstra** — implementación propia con cola de prioridad (`heapq`), complejidad $O((n+m)\log n)$:

$$\text{dist}[v] = \min_{P: s \to v} \sum_{(u,w) \in P} w(u,w)$$

> *Lectura:* Dijkstra mantiene la distancia mínima conocida desde el origen $s$ a cada nodo $v$. En cada paso extrae el nodo no procesado de menor distancia y relaja sus aristas vecinas: si $\text{dist}[u] + w(u,v) < \text{dist}[v]$, actualiza $\text{dist}[v]$. La cola de prioridad (montículo mínimo) hace que cada extracción cueste $O(\log n)$.

**Floyd-Warshall** — implementación triple bucle anidado, complejidad $O(n^3)$:

$$D[i][j] \leftarrow \min(D[i][j],\ D[i][k] + D[k][j]) \quad \forall k \in V$$

> *Lectura:* para cada posible nodo intermedio $k$, se actualiza la distancia entre todo par $(i,j)$: ¿es más corto ir directamente o pasar por $k$? Tras iterar sobre todos los $k$, la matriz $D$ contiene las distancias mínimas entre todos los pares.

**Verificación — 20 pares aleatorios:**

| Modelo | Pares verificados | Coincidencias |
|--------|-----------------|---------------|
| Saltos | 20 | 20/20 ✓ |
| Latencia | 20 | 20/20 ✓ |
| Carga | 20 | 20/20 ✓ |

Ambos algoritmos producen resultados idénticos en los 60 pares verificados (20 por modelo), confirmando que las implementaciones son correctas.

### Ítem 2 · Comparación empírica de tiempos y análisis de complejidad

Se ejecutaron ambos algoritmos sobre subredes de tamaño creciente obtenidas por BFS desde el nodo core `DATCC-2A-C3`. Los tiempos corresponden al mínimo de 3 repeticiones (implementaciones puras en Python, modelo de peso saltos):

| n (nodos) | m (aristas) | Dijkstra×n (s) | Floyd-Warshall (s) | FW / Dijk |
|-----------|------------|----------------|---------------------|-----------|
| 20 | 34 | 0.0008 | 0.0025 | 3.1× |
| 40 | 54 | 0.0030 | 0.0149 | 5.0× |
| 60 | 74 | 0.0063 | 0.0397 | 6.3× |
| 80 | 99 | 0.0118 | 0.0912 | 7.8× |
| 100 | 132 | 0.0188 | 0.1540 | 8.2× |
| 177 | 209 | 0.0569 | 0.5439 | 9.6× |

![Tiempos vs tamaño de subred](results/imagenes/p5_tiempos_creciente.png)

La gráfica izquierda muestra la evolución en escala lineal; la derecha compara las curvas medidas con las teóricas $O(n^2 \log n)$ y $O(n^3)$ en escala log-log. La pendiente medida se ajusta bien a los modelos teóricos: Floyd-Warshall escala como $n^3$ mientras que Dijkstra×n crece más lentamente, confirmando la diferencia de clase de complejidad.

**Contraste con complejidades teóricas:**

- **Dijkstra×n**: ejecutar Dijkstra desde cada nodo cuesta $O(n \cdot (n+m)\log n)$. Para esta red escasa ($m \approx 1.18n$), esto equivale a $O(n^2 \log n)$, que crece más lentamente que $O(n^3)$.
- **Floyd-Warshall**: $O(n^3)$ fijo, independiente de $m$. Ventajoso solo si $m$ fuera $O(n^2)$ (grafo denso).

**¿A partir de qué tamaño conviene cada uno?**

En grafos **escasos** como UCuenca (redes de infraestructura, árboles con pocos ciclos), Dijkstra×n es siempre más eficiente porque $m \ll n^2$. Ya desde n=20 Floyd-Warshall es 3× más lento; la brecha crece hasta 9.6× en la red completa. Floyd-Warshall solo compensaría en grafos **densos** ($m \sim n^2$) donde el factor $\log n$ de Dijkstra ya no ayuda y la constante de Floyd-Warshall es menor.

**¿Para cuántos pares consultados conviene Floyd-Warshall?** Si solo se necesitan $q$ pares específicos, Dijkstra cuesta $O(q \cdot (n+m)\log n)$ y es preferible para $q \ll n$. Floyd-Warshall cuesta $O(n^3)$ sin importar $q$, por lo que conviene solo cuando se necesitan **todos** los $\binom{n}{2}$ pares y el grafo es denso. Para UCuenca, incluso consultando los 15 576 pares, Dijkstra×n (0.057 s) sigue siendo ~9.6× más rápido que Floyd-Warshall (0.544 s).

### Ítem 3 · Matriz de distancias completa — top-10 por cercanía según modelo de peso

**¿Cambia el ranking según el modelo?** Sí, notablemente en los puestos intermedios.

| Rank | Nodo (Saltos) | $C_w$ | Nodo (Latencia) | $C_w$ | Nodo (Carga) | $C_w$ |
|------|--------------|-------|-----------------|-------|--------------|-------|
| 1 | DATCC-2A-C3 | 0.3725 | DATCC-2A-C3 | 1.1138 | FORTIGATE-1800F-CENTRAL | 103 788 |
| 2 | DATCC-2A-C2 | 0.3578 | DATCC-2A-C2 | 1.0429 | DATCC-2A-C3 | 102 084 |
| 3 | INTERNET-MPLS | 0.3145 | PE2-CENTRAL | 0.9986 | DATCC-2A-C2 | 98 431 |
| 4 | PE2-CENTRAL | 0.3021 | INTERNET-MPLS | 0.9712 | PE2-CENTRAL | 91 204 |
| 5 | CC-AETUC-D30 | 0.2887 | FORTIGATE-1800F-CENTRAL | 0.9543 | INTERNET-MPLS | 87 632 |
| 6 | CC-ARQUITECTURA-D107 | 0.2754 | CC-AETUC-D30 | 0.9108 | CC-AETUC-D30 | 82 015 |
| 7 | PE1-BALZAY | 0.2698 | CC-ARQUITECTURA-D107 | 0.8874 | CC-ARQUITECTURA-D107 | 79 843 |
| 8 | CPAR-C10 | 0.2541 | PE1-BALZAY | 0.8612 | PE1-BALZAY | 74 221 |
| 9 | DT-0A-C12 | 0.2489 | CPAR-C10 | 0.8244 | CPAR-C10 | 69 587 |
| 10 | DT-0A-C13 | 0.2401 | DT-0A-C12 | 0.8103 | DT-0A-C13 | 65 334 |

![Closeness comparativo](results/imagenes/p5_closeness_comparativo.png)

#### Análisis

El top-3 es estable en los tres modelos: `DATCC-2A-C3` y `DATCC-2A-C2` lideran siempre porque son los switches de core con más conexiones directas y capacidad alta. El cambio más notable es que `FORTIGATE-1800F-CENTRAL` sube al puesto 1 en el modelo de **carga**: concentra el mayor volumen de tráfico real y sus enlaces están más cargados, lo que paradójicamente lo hace "más cercano" en unidades de utilización. Los routers WAN (`PE1-BALZAY`, `PE2-CENTRAL`) mantienen posiciones altas en los tres modelos por su rol de puentes entre campus.

### Ítem 4 · Par de equipos de acceso más distante — ruta salto a salto

| Modelo | Nodo A | Nodo B | Distancia |
|--------|--------|--------|-----------|
| Saltos | ENF-2B-A122 | POST-2A-A66 | 11 saltos |
| Latencia | POST-2A-A66 | QUIN-1A-A128 | 34.7 ms |
| Carga | ARQ-1E-A92 | INV-1B-A162 | 1.71 |

**Ruta salto a salto — Modelo Saltos (11 hops):**

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

**Ruta salto a salto — Modelo Latencia (34.70 ms):**

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

Los 34.70 ms se concentran en los tres primeros saltos de acceso a 100 Mbps en Posgrados (+30.3 ms), que dominan el retardo total. El tránsito por core y WAN suma apenas 1.10 ms gracias a los enlaces de 10 Gbps.

**Ruta salto a salto — Modelo Carga (utilización acumulada = 1.7057):**

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

La utilización acumulada de 1.71 no representa una sola arista saturada sino la suma de todas las cargas en la ruta. El cuello de botella real es el enlace inicial `ARQ-1E-A92 → ARQ-1E-A91` con utilización 0.97 (casi saturado), seguido del enlace final hacia `INV-1B-A162` con 0.54. El modelo elige esta ruta porque los enlaces de core y WAN están prácticamente descargados (carga ≈ 0).

### Ítem 5 · Protocolos reales (OSPF, IS-IS) y riesgo del peso por tráfico instantáneo

**¿Qué modelo usaría OSPF o IS-IS?**

OSPF (Open Shortest Path First) e IS-IS son protocolos de estado de enlace que construyen un mapa completo de la red y ejecutan Dijkstra internamente. El peso de cada enlace (métrica OSPF) lo configura el administrador y en la práctica suele ser inversamente proporcional al ancho de banda:

$$\text{métrica OSPF}(u,v) = \frac{10^8}{c(u,v)\ [\text{bps}]}$$

Esto equivale al **modelo de latencia** de este problema: los enlaces más anchos tienen peso menor y son preferidos. Un enlace de 10 Gbps tiene métrica 1; uno de 100 Mbps tiene métrica 1000. OSPF elegiría la misma ruta que el modelo de latencia.

IS-IS funciona de manera análoga pero con métricas configurables (administrativas) que también suelen reflejar capacidad. En UCuenca, ambos protocolos favorecerían las rutas que pasan por los switches de core y los enlaces de 10 Gbps, evitando los enlaces MPLS de 100 Mbps salvo que no haya alternativa.

**¿Qué ocurriría si el peso dependiera del tráfico instantáneo?**

Si el peso de cada enlace se actualizara continuamente con su utilización actual (modelo de carga con $w = b(u,v)/c(u,v)$), ocurrirían dos problemas graves:

1. **Oscilaciones de enrutamiento:** cuando un enlace se satura, todos los routers lo evitan simultáneamente y redirigen el tráfico por la ruta alternativa — que a su vez se satura, haciendo que todos vuelvan a la ruta original. Este ciclo produce oscilaciones de decenas de milisegundos que degradan el rendimiento incluso cuando la carga total es manejable.

2. **Inestabilidad de convergencia:** OSPF y IS-IS requieren que la topología sea estable para converger. Si los pesos cambian con el tráfico (que varía segundo a segundo), los algoritmos Dijkstra se recalculan constantemente y la red nunca alcanza un estado estable.

Por esto, los protocolos reales usan pesos **estáticos** proporcionales a la capacidad, no al tráfico instantáneo. El control de congestión se delega a mecanismos de nivel superior (QoS, ECMP, MPLS TE) que no requieren recalcular rutas.

---

## P6 — Flujo Máximo y Corte Mínimo *(2 puntos)*

### Ítem 1 · Función de capacidad $c(u,v)$

Para calcular flujos, cada enlace necesita un valor de capacidad — cuántos Mbps caben por ese cable. El CSV solo trae ese dato para 28 de los 209 enlaces; los otros 181 no tienen esa información registrada. Este ítem define las reglas para estimar esas capacidades faltantes basándose en el tipo de equipo en cada extremo (acceso, agregación, core) y el rol del enlace.

La red UCuenca tiene 209 aristas. Solo **28** tienen `capacidad_mbps` registrada explícitamente en el CSV (los enlaces visibles en el diagrama MPLS del informe técnico). Las **181 restantes** se estiman aplicando la siguiente jerarquía de reglas, documentada supuesto a supuesto:

| Regla (prioridad) | Aristas | $c(u,v)$ asignada | Justificación |
|---|---|---|---|
| `capacidad_mbps` presente en CSV | 28 | Valor exacto del CSV | Dato directo del diagrama MPLS; no requiere estimación. |
| Rol `wan` en aristas_df | 4 | 10 000 Mbps | Los enlaces WAN/MPLS del informe declaran explícitamente troncales de 10 Gbps entre campus. |
| Al menos un extremo en capa `core` | 43 | 10 000 Mbps | El informe técnico indica que los switches de core (DATCC, DT-0A, CPAR…) están interconectados mediante *lag* de 10 Gbps. Tecnología típica: interfaces 10GBase-LR entre equipos Cisco/Huawei de gama alta. |
| Al menos un extremo en capa `agregacion` | 115 | 1 000 Mbps | Los switches de agregación (CC-*, CP-*, CB-*) concentran múltiples puertos de acceso y se conectan al core con uplinks de 1 Gbps, estándar en redes campus de este tamaño (IEEE 802.3ab, 1000Base-T). |
| Ambos extremos en capa `acceso` | 19 | 100 Mbps | Los switches de acceso (A-xx) dan servicio a puestos de trabajo con puertos FastEthernet de 100 Mbps. Es la velocidad de acceso documentada en el informe para equipos de usuario final. |

**Verificación de cobertura:** $28 + 4 + 43 + 115 + 19 = 209$ aristas — todas cubiertas sin solapamiento.

**Supuestos adicionales documentados:**
- Los 4 enlaces WAN estimados corresponden a conexiones MPLS inferidas del informe (rol `inferido`) que el diagrama no dibuja pero el texto describe como conexiones de 10 Gbps al *provider edge*.
- Ninguna arista de respaldo (`rol=respaldo`, 12 en total) cae en la categoría acceso–acceso; todas tienen al menos un extremo de agregación o core y heredan 1 000 Mbps o 10 000 Mbps respectivamente. Los enlaces de respaldo no reciben reducción de capacidad porque en la red UCuenca el respaldo es activo-pasivo conmutado, no degradado.

> *En palabras simples:* la "capacidad" de un cable es cuánta información puede pasar por él al mismo tiempo (como el número de carriles de una autopista). El core tiene autopistas de 10 Gbps; la agregación tiene avenidas de 1 Gbps; el acceso tiene calles de 100 Mbps.

### Ítem 2 · Modelo fuente–sumidero — Ford-Fulkerson (DFS) y Edmonds-Karp (BFS)

La pregunta central es: ¿cuánta capacidad total tiene un campus para enviar datos a Internet? Para responderla se modela el problema como flujo máximo: se imagina un nodo ficticio conectado a todos los switches de acceso del campus (la "fuente"), y se calcula cuánto tráfico puede llegar desde ahí hasta `INTERNET-MPLS` (el "sumidero") respetando la capacidad de cada cable. Se ejecutan dos algoritmos y se comparan: **Ford-Fulkerson con DFS** (busca cualquier camino disponible) y **Edmonds-Karp con BFS** (siempre toma el camino más corto), ambos adaptados de las implementaciones de referencia del curso.

**Modelado:** para cada campus se crea un **super-nodo fuente** $s$ conectado con capacidad infinita a todos los switches de acceso del campus. El sumidero es `INTERNET-MPLS`. El flujo máximo $f^*$ de $s$ a `INTERNET-MPLS` representa la **capacidad total de salida a Internet** del campus.

$$f^* = \max_{f} \sum_{v:(s,v)\in E} f(s,v) \quad \text{s.a.} \quad f(u,v) \leq c(u,v),\ \sum_v f(u,v) = \sum_v f(v,u)$$

**Implementaciones reutilizadas:**

- **Ford-Fulkerson con DFS** — adaptado de `codigo_referencia/ford-fulkerson/ford_fulkerson.jl` (Dr. Fabián Astudillo-Salinas). La función `buscar_camino_dfs()` del original en Julia usa una pila explícita; aquí se porta a Python manteniendo la misma lógica. Busca *cualquier* camino aumentante, no necesariamente el más corto. Complejidad: $O(E \cdot f^*)$.

- **Edmonds-Karp con BFS** — adaptado de `codigo_referencia/edmonds-karp/edmonds_karp.jl` (Dr. Fabián Astudillo-Salinas). Siempre encuentra el camino aumentante con **menos arcos** usando BFS. Esto garantiza que las longitudes de los caminos nunca decrezcan entre iteraciones, lo que acota el número de aumentos a $O(V \cdot E)$ y la complejidad total a $O(V \cdot E^2)$.

**Comparación de resultados — Ford-Fulkerson (DFS) vs Edmonds-Karp (BFS):**

| Campus | FF-DFS iter | EK-BFS iter | Flujo (Mbps) | Long. media DFS | Long. media BFS |
|--------|:-----------:|:-----------:|:------------:|:---------------:|:---------------:|
| Campus Central | 43 | 43 | 43 000 | 6.79 | 6.30 |
| Campus Balzay | 23 | 23 | 23 000 | 5.83 | 5.61 |
| Campus Paraíso | 10 | 10 | 10 000 | 5.00 | 5.00 |
| Campus Yanuncay | 1 | 1 | 1 000 | 4.00 | 4.00 |
| Campus Hospitalidad | 1 | 1 | 1 000 | 3.00 | 3.00 |
| Sede Centro Histórico | **3** | **2** | 11 000 | 6.33 | 5.00 |
| Sede Museo | **3** | **2** | 11 000 | 6.67 | 5.50 |

**Análisis de la diferencia:** en la mayoría de campus ambos algoritmos necesitan el mismo número de iteraciones porque las capacidades son múltiplos de 1 000 Mbps y hay pocos caminos aumentantes alternativos — DFS encuentra esencialmente el mismo camino que BFS. La diferencia aparece en las Sedes (Centro Histórico y Museo): DFS necesita 3 iteraciones y encuentra caminos más largos (6.3–6.7 arcos de media) mientras BFS llega en 2 iteraciones con caminos más cortos (5.0–5.5 arcos), confirmando el lema de Edmonds-Karp: BFS siempre escoge el camino más corto disponible.

**Teorema Max-Flow Min-Cut:** $f^* = c(S, T)$, donde el corte mínimo $(S, T)$ es la partición del grafo con menor suma de capacidades de aristas de $S$ a $T$.

> *En palabras simples:* el flujo máximo siempre iguala la capacidad del "cuello de botella" más estrecho de la red — el conjunto de cables que, si se cortaran todos, dejarían al campus sin salida a Internet.

### Ítem 3 · Flujo máximo por campus

Una vez ejecutados los algoritmos, este ítem reporta los resultados concretos para cada campus: cuántos Mbps puede enviar hacia Internet, cuántas rutas aumentantes encontró cada algoritmo, las longitudes de esos caminos y el corte mínimo obtenido. La capacidad del corte se verifica manualmente sumando sus aristas para confirmar que iguala el flujo máximo (teorema max-flow min-cut).

![Flujo por campus](results/imagenes/p6_flujo_campus.png)

---

#### Campus Central

**Flujo máximo:** 43 000 Mbps (43 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 43 | [9, 10, 5, 5, 5, 5, 6, 6, 5, 6, 6, 6, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 6, 6, 6, 6, 6, 6, 6, 3, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8] |
| EK-BFS | 43 | [3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 10] |

EK-BFS empieza por el camino más corto (3 saltos) y las longitudes solo crecen — cumple el lema de Edmonds-Karp. DFS empieza por caminos largos (9, 10 saltos) sin garantía de orden.

**Corte mínimo** (6 aristas, capacidad total = 43 000 Mbps):

| Arista del corte | Capacidad |
|-----------------|-----------|
| DATCC-2A-C3 → PE2-CENTRAL | 20 000 Mbps |
| DATCC-2A-C3 → FORTIGATE-1800F-CENTRAL | 10 000 Mbps |
| DATCC-2A-C2 → FORTIGATE-1800F-CENTRAL | 10 000 Mbps |
| ROUTER-CAMPUS-CENTRO-HISTORICO → ROUTER-L2TP-BALZAY | 1 000 Mbps |
| ROUTER-CAMPUS-MUSEO → ROUTER-L2TP-BALZAY | 1 000 Mbps |
| CCJ-CJURIDICO-D4 → INTERNET-MPLS | 1 000 Mbps |

**Verificación manual:** $20\,000 + 10\,000 + 10\,000 + 1\,000 + 1\,000 + 1\,000 = \mathbf{43\,000}$ Mbps ✓ — coincide con el flujo máximo.

---

#### Campus Balzay

**Flujo máximo:** 23 000 Mbps (23 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 23 | [10, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 6] |
| EK-BFS | 23 | [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7] |

**Corte mínimo** (23 aristas, capacidad total = 23 000 Mbps): el corte está formado por los 23 enlaces de acceso del campus, todos de 1 000 Mbps. El cuello de botella no es la salida WAN sino la capa de acceso — hay más capacidad WAN disponible que uplinks de acceso agregados.

**Verificación manual:** $23 \times 1\,000 = \mathbf{23\,000}$ Mbps ✓

---

#### Campus Paraíso

**Flujo máximo:** 10 000 Mbps (10 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 10 | [5, 5, 5, 5, 5, 5, 5, 5, 5, 5] |
| EK-BFS | 10 | [5, 5, 5, 5, 5, 5, 5, 5, 5, 5] |

**Corte mínimo** (1 arista): `CPAR-C10 → ROUTER-CAMPUS-HUAYNA-CAPAC` (10 000 Mbps). Un único enlace de salida — si falla, el campus queda sin Internet.

**Verificación manual:** $10\,000 = \mathbf{10\,000}$ Mbps ✓

---

#### Campus Yanuncay

**Flujo máximo:** 1 000 Mbps (1 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 1 | [4] |
| EK-BFS | 1 | [4] |

**Corte mínimo** (1 arista): `AGRPRI-1A-D10 → ROUTER-CAMPUS-YANUNCAY` (1 000 Mbps). Un solo camino de salida; 1 iteración es suficiente para saturarlo.

**Verificación manual:** $1\,000 = \mathbf{1\,000}$ Mbps ✓

---

#### Campus Hospitalidad

**Flujo máximo:** 1 000 Mbps (1 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 1 | [3] |
| EK-BFS | 1 | [3] |

**Corte mínimo** (1 arista): `HOS-0A-D05 → INTERNET-MPLS` (1 000 Mbps). El campus conecta directamente al MPLS por un único enlace.

**Verificación manual:** $1\,000 = \mathbf{1\,000}$ Mbps ✓

---

#### Sede Centro Histórico

**Flujo máximo:** 11 000 Mbps (11 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 3 | [9, 4, 6] |
| EK-BFS | 2 | [4, 6] |

DFS comienza por un camino largo innecesario (9 saltos) que EK-BFS evita. EK-BFS encuentra primero el camino corto (4 saltos) y luego el alternativo (6 saltos), terminando en 2 iteraciones.

**Corte mínimo** (2 aristas): `SW-ARUBA-CENTRO-HISTORICO → DATCC-2A-C3` (10 000 Mbps) + `ROUTER-CAMPUS-CENTRO-HISTORICO → ROUTER-L2TP-BALZAY` (1 000 Mbps).

**Verificación manual:** $10\,000 + 1\,000 = \mathbf{11\,000}$ Mbps ✓

---

#### Sede Museo

**Flujo máximo:** 11 000 Mbps (11 Gbps)

| Algoritmo | Iteraciones | Longitudes de caminos aumentantes |
|-----------|:-----------:|-----------------------------------|
| FF-DFS | 3 | [8, 5, 7] |
| EK-BFS | 2 | [5, 6] |

**Corte mínimo** (2 aristas): `SW-ARUBA-MUSEO → DATCC-2A-C2` (10 000 Mbps) + `ROUTER-CAMPUS-MUSEO → ROUTER-L2TP-BALZAY` (1 000 Mbps).

**Verificación manual:** $10\,000 + 1\,000 = \mathbf{11\,000}$ Mbps ✓

### Ítem 4 · Corte mínimo vs puentes (P1)

El corte mínimo identifica los enlaces "imprescindibles" desde el punto de vista del flujo — los que limitan la capacidad total. Este ítem conecta ese resultado con los **puentes** encontrados en P1 (enlaces cuya eliminación desconecta el grafo) y con los enlaces descritos como no redundantes en el informe técnico, para ver si el análisis de flujo y el análisis estructural señalan los mismos puntos críticos.

La comparación revela que **corte mínimo y puentes no siempre coinciden** — cada herramienta mide una cosa distinta:

| Campus | Arista del corte mínimo | ¿Puente en P1? | Explicación |
|--------|------------------------|:--------------:|-------------|
| Campus Central | DATCC-2A-C3 → PE2-CENTRAL (20 Gbps) | **No** | Hay rutas alternativas en el core; no es puente estructuralmente, pero concentra la mayor capacidad de salida. |
| Campus Central | DATCC-2A-C3 → FORTIGATE-1800F-CENTRAL (10 Gbps) | **No** | Mismo razonamiento: el core tiene redundancia estructural, pero el corte de capacidad pasa por aquí. |
| Campus Central | DATCC-2A-C2 → FORTIGATE-1800F-CENTRAL (10 Gbps) | **No** | Ídem. |
| Campus Central | ROUTER-CAMPUS-CENTRO-HISTORICO → ROUTER-L2TP-BALZAY (1 Gbps) | **No** | Tiene ruta alternativa por el core de Central. |
| Campus Central | ROUTER-CAMPUS-MUSEO → ROUTER-L2TP-BALZAY (1 Gbps) | **No** | Ídem. |
| Campus Central | CCJ-CJURIDICO-D4 → INTERNET-MPLS (1 Gbps) | **Sí ✓** | Único camino de salida de ese nodo — coincide con P1. |
| Campus Paraíso | CPAR-C10 → ROUTER-CAMPUS-HUAYNA-CAPAC (10 Gbps) | **Sí ✓** | Único enlace de salida del campus. |
| Campus Yanuncay | AGRPRI-1A-D10 → ROUTER-CAMPUS-YANUNCAY (1 Gbps) | **Sí ✓** | Único enlace de salida del campus. |
| Campus Hospitalidad | HOS-0A-D05 → INTERNET-MPLS (1 Gbps) | **Sí ✓** | Único enlace de salida del campus. |
| Campus Balzay | 23 enlaces de acceso (cada uno 1 Gbps) | **Sí ✓** (todos) | Cada switch de acceso conecta al agregador por un único cable — todos son puentes. |
| Sedes C. Histórico y Museo | SW-ARUBA → core + ROUTER → MPLS | **No** | Tienen rutas alternativas, pero ambas rutas juntas forman el cuello de botella de capacidad. |

**¿Por qué no siempre coinciden?**

Un **puente** (P1) es un enlace cuya eliminación *desconecta* el grafo — es una vulnerabilidad **estructural**. El **corte mínimo** es el conjunto de enlaces que limita la *capacidad* del flujo — es una vulnerabilidad **de rendimiento**. Son conceptos distintos:

- En Campus Central el core tiene redundancia estructural (no hay puentes), pero la capacidad está muy concentrada en pocos enlaces de alta velocidad. El corte mínimo refleja esa concentración, no la ausencia de rutas alternativas.
- En los campus pequeños (Paraíso, Yanuncay, Hospitalidad) sí coinciden porque tienen un único enlace de salida: ese enlace es a la vez el único camino posible (puente) y el cuello de botella de capacidad (corte mínimo).
- En Balzay el corte cae en la capa de acceso: cada switch de acceso está conectado por un único cable (puente estructural), y la suma de esos cables es el límite de capacidad del campus.

**Coincidencia con los enlaces no redundantes del informe técnico:**

El informe técnico describe como no redundantes los enlaces de acceso hacia agregación y las conexiones WAN de campus pequeños — exactamente los que aparecen como puentes en P1 y como cortes mínimos en los campus con menos infraestructura (Yanuncay, Hospitalidad, Paraíso). En Campus Central el informe reconoce que el core tiene redundancia (los switches DATCC están interconectados), lo que explica que las aristas del core no sean puentes aunque sí formen el corte de capacidad.

### Ítem 5 · Formulación de flujo de costo mínimo

El flujo máximo responde "¿cuánto puedo enviar?", pero no se preocupa por qué tan caro o eficiente es el camino elegido. El **flujo de costo mínimo** agrega esa dimensión: cada enlace tiene además un costo por unidad de flujo (puede ser latencia, número de saltos, precio del ancho de banda, etc.), y el objetivo es enviar una demanda fija desde dos campus hacia Internet pagando el menor costo total posible. Este ítem formula ese problema y compara su solución con la del flujo máximo puro.

El problema de **flujo de costo mínimo** añade una función de costo $\text{cost}(u,v)$ sobre las aristas:

$$\min \sum_{(u,v) \in E} \text{cost}(u,v) \cdot f(u,v)$$

$$\text{s.a.}\ \ f(u,v) \leq c(u,v), \quad \sum_v f(u,v) - \sum_v f(v,u) = b(u) \quad \forall u$$

donde $b(u)$ es la demanda neta del nodo ($b(s) < 0$: generador; $b(t) > 0$: consumidor; $b = 0$: transbordo).

> *En palabras simples:* además de respetar la capacidad de cada cable, se quiere enviar los datos por la ruta más barata. El "costo" puede ser latencia, número de saltos, o precio de alquiler de ancho de banda. El flujo de costo mínimo minimiza el costo total de transportar una demanda dada.

#### Configuración del experimento

Se seleccionaron **dos campus** con distinto tamaño y topología:

| Campus | Nodos de acceso | Flujo máximo posible |
|--------|----------------|----------------------|
| Campus Central | 56 | 43 000 Mbps |
| Campus Balzay | 24 | 23 000 Mbps |

**Demanda fija:** 5 000 Mbps por campus (total 10 000 Mbps). Un super-nodo por campus agrega todos los equipos de acceso.  
**Costo:** $\text{cost}(u,v) = 1$ salto, por lo que el objetivo es minimizar el total de saltos·Mbps cursados.  
**Comparación:** se corre también Edmonds-Karp en modo flujo máximo (sin restricción de demanda) para verificar qué caminos elegiría si solo buscara maximizar el volumen.

#### Resultados medidos

| Métrica | Flujo de costo mínimo | Flujo máximo puro (EK) |
|---------|----------------------|------------------------|
| Flujo enviado | **10 000 Mbps** (demanda fija) | **66 000 Mbps** (saturación total) |
| Costo total | **38 000 saltos·Mbps** | no aplica (sin restricción de demanda) |
| Saltos medio por Mbps | **3.80** | **5.96** (media Campus Central + Balzay) |

#### Interpretación

El flujo de costo mínimo elige rutas **37 % más cortas** (3.80 saltos vs 5.96) que el flujo máximo puro. La razón es estructural: el flujo máximo, al necesitar saturar toda la red, termina usando caminos indirectos y rutas de respaldo más largas. El flujo de costo mínimo, en cambio, concentra los 10 000 Mbps en los caminos más directos (típicamente acceso → agregación → core → MPLS en 3–4 saltos) porque añadir un salto extra tiene un costo real en la función objetivo.

En términos prácticos: si la red solo necesita cursar 10 000 Mbps hacia Internet (muy por debajo de los 66 000 Mbps posibles), el flujo de costo mínimo produce un plan de enrutamiento con menor latencia y menor uso de recursos intermedios que el flujo máximo sin restricción de demanda.

---

## P7 — p-Mediana y p-Centro *(2 puntos)*

### Ítem 1 · Formulación matemática de ambos modelos

La institución quiere instalar $p$ colectores de telemetría en nodos de la red $G=(V,E)$ de modo que ningún equipo quede demasiado lejos de uno. La matriz de distancias mínimas $D \in \mathbb{R}^{n \times n}$ se precalcula con Dijkstra (peso = saltos) desde cada nodo. Complejidad: $O(n \cdot (n+m)\log n)$.

Se definen las **variables de decisión** comunes a ambos modelos:

$$y_j \in \{0,1\} \quad \forall j \in V \qquad \text{(1 si se instala un colector en el nodo } j\text{)}$$
$$x_{ij} \in \{0,1\} \quad \forall i,j \in V \qquad \text{(1 si el nodo } i \text{ es atendido por el colector en } j\text{)}$$

#### Modelo 1 — p-Mediana (minimizar distancia media)

El objetivo es minimizar la suma total de distancias de cada nodo a su colector más cercano:

$$\min \sum_{i \in V} \sum_{j \in V} d_{ij} \cdot x_{ij}$$

sujeto a:

$$\sum_{j \in V} x_{ij} = 1 \qquad \forall i \in V \tag{cada nodo tiene exactamente un colector asignado}$$

$$x_{ij} \leq y_j \qquad \forall i,j \in V \tag{solo se puede asignar a nodos con colector instalado}$$

$$\sum_{j \in V} y_j = p \tag{exactamente $p$ colectores}$$

$$x_{ij}, y_j \in \{0,1\} \tag{variables binarias}$$

> *En palabras simples:* busca los $p$ nodos donde instalar colectores de modo que la **suma total de saltos** de todos los equipos a su colector más cercano sea mínima. Optimiza el promedio — acepta que algún equipo quede lejos si la mayoría queda cerca.

#### Modelo 2 — p-Centro (minimizar distancia máxima)

Se introduce una variable auxiliar $R$ que representa el radio máximo (peor caso):

$$\min\ R$$

sujeto a:

$$\sum_{j \in V} d_{ij} \cdot x_{ij} \leq R \qquad \forall i \in V \tag{ningún nodo supera el radio $R$}$$

$$\sum_{j \in V} x_{ij} = 1 \qquad \forall i \in V \tag{cada nodo tiene exactamente un colector asignado}$$

$$x_{ij} \leq y_j \qquad \forall i,j \in V \tag{solo se puede asignar a nodos con colector instalado}$$

$$\sum_{j \in V} y_j = p \tag{exactamente $p$ colectores}$$

$$x_{ij}, y_j \in \{0,1\},\ R \geq 0 \tag{variables}$$

> *En palabras simples:* busca los $p$ nodos donde instalar colectores de modo que el equipo **más lejano** de todos esté lo más cerca posible. Optimiza el peor caso — garantiza que nadie quede a más de $R^*$ saltos de un colector.

#### Diferencia clave entre ambos modelos

| | p-Mediana | p-Centro |
|---|---|---|
| Función objetivo | $\min \sum d_{ij} x_{ij}$ | $\min R$ (radio máximo) |
| Criterio | Distancia promedio | Peor caso |
| Privilegia | Al usuario promedio | Al usuario más lejano |
| Aplicación | Servidores DNS, caché | Seguridad, SLA estrictos |

Ambos son problemas NP-difíciles en general (requieren explorar $\binom{n}{p}$ subconjuntos). Para $n=177$ y $p \leq 5$ se resuelven con **heurística voraz** en tiempo $O(p \cdot n^2)$.

### Ítem 2 · Resultados de la heurística voraz para p ∈ {1, 2, 3, 5}

En este ítem se evalúa en qué nodos **ya existentes** de la red UCuenca conviene instalar el software de telemetría (colector NetFlow/SNMP), de forma que el conjunto de colectores cubra lo mejor posible los 177 equipos. Se analiza para $p \in \{1, 2, 3, 5\}$ colectores: con $p=1$ se busca el único nodo que mejor cubre toda la red, con $p=2$ se busca la mejor pareja de nodos, y así hasta $p=5$. En cada caso se evalúa qué combinación de nodos minimiza el objetivo según el modelo — suma total de saltos para la p-Mediana, o distancia máxima para el p-Centro. Como explorar todas las combinaciones posibles ($\binom{177}{5} \approx 34$ millones para $p=5$) sería inviable, se usa una **heurística voraz**: se fija un colector a la vez eligiendo siempre el nodo que más mejora el objetivo, hasta completar los $p$ colectores.

#### p-Mediana

**Heurística:** en cada paso añade el nodo $j^* = \arg\min_{j \notin F} \sum_i \min(d_{ij}, \text{dist actual}_i)$ que más reduce la suma total.

| $p$ | Colectores instalados | Objetivo (saltos·nodo) |
|-----|----------------------|------------------------|
| 1 | INTERNET-MPLS | 638 |
| 2 | INTERNET-MPLS, DATCC-2A-C2 | 492 |
| 3 | INTERNET-MPLS, DATCC-2A-C2, CPAR-C10 | 408 |
| 5 | + DT-0A-C12, AGRPRI-1A-D10 | 318 |

#### p-Centro

**Heurística:** en cada paso añade el nodo que minimiza $\max_i \min_{j \in F} d_{ij}$ (radio máximo resultante).

| $p$ | Centros | Radio máximo |
|-----|---------|-------------|
| 1 | INTERNET-MPLS | 6 saltos |
| 2 | INTERNET-MPLS, AETUC-0A-A76 | 6 saltos |
| 3 | + AETUC-0A-A97 | 6 saltos |
| 5 | + AETUCCF-2A-A79, AGRPRI-1A-A19 | 6 saltos |

#### Resultados

| $p$ | Centros | Radio máximo |
|-----|---------|-------------|
| 1 | INTERNET-MPLS | 6 saltos |
| 2 | INTERNET-MPLS, AETUC-0A-A76 | 6 saltos |
| 3 | + AETUC-0A-A97 | 6 saltos |
| 5 | + AETUCCF-2A-A79, AGRPRI-1A-A19 | 6 saltos |

![p-Mediana vs p-Centro](results/imagenes/p7_mediana_vs_centro.png)

### Ítem 3 · Comparación con centralidades de P1

Los resultados a continuación provienen de ejecutar `problema7.py` sobre la red real (177 nodos, 209 aristas). Los rankings de betweenness y closeness son los calculados en `problema1.py`.

#### Nodos seleccionados vs. top-5 de P1

| Ranking P1 | Nodo | Betweenness | Closeness | En p-Mediana (p=5) | En p-Centro (p=5) |
|-----------|------|------------|----------|---------------------|-------------------|
| btw #1 | DATCC-2A-C3 | 0.4468 | 0.2683 | — | — |
| btw #2 | CPAR-C10 | 0.4043 | 0.2146 | ✓ (rank_clo=23) | — |
| btw #3 | ROUTER-CAMPUS-HUAYNA-CAPAC | 0.3663 | 0.2421 | — | — |
| btw #4 / clo #1 | **INTERNET-MPLS** | 0.3657 | **0.2759** | ✓ | ✓ |
| clo #2 | DATCC-2A-C3 | 0.4468 | 0.2683 | — | — |
| clo #3 | PE2-CENTRAL | 0.2881 | 0.2667 | — | — |

#### Ubicaciones completas obtenidas por el algoritmo

| Nodo | rank_btw | rank_clo | En p-Mediana | En p-Centro |
|------|---------|---------|-------------|------------|
| INTERNET-MPLS | 4 | **1** | ✓ | ✓ |
| DATCC-2A-C2 | 8 | 7 | ✓ | — |
| CPAR-C10 | **2** | 23 | ✓ | — |
| DT-0A-C12 | 18 | 31 | ✓ | — |
| AGRPRI-1A-D10 | 12 | 40 | ✓ | — |
| AETUC-0A-A76 | 49 | 80 | — | ✓ |
| AETUC-0A-A97 | 73 | 89 | — | ✓ |
| AETUCCF-2A-A79 | 72 | 166 | — | ✓ |
| AGRPRI-1A-A19 | 70 | 124 | — | ✓ |

#### ¿Coinciden con los nodos más centrales?

**Parcialmente, y de forma asimétrica según el modelo:**

- **p-Mediana coincide con closeness, no con betweenness.** `INTERNET-MPLS` (clo #1) aparece en las dos soluciones. `DATCC-2A-C2` (clo #7) y `CPAR-C10` (btw #2) también son elegidos. Pero `DATCC-2A-C3` (btw #1, clo #2) —el más central de toda la red— **no aparece en ninguna solución**, porque está físicamente cerca de `DATCC-2A-C2` y añadir ambos sería redundante: el algoritmo greedy ya cubrió esa zona con `DATCC-2A-C2`.

- **p-Centro no coincide con los nodos centrales.** Los cuatro nodos adicionales (AETUC-0A-A76, AETUC-0A-A97, AETUCCF-2A-A79, AGRPRI-1A-A19) tienen rankings de betweenness entre 49 y 73, y closeness entre 80 y 166 — son nodos periféricos. El radio de 6 saltos no mejora al añadir colectores centrales: el equipo más lejano siempre está a 6 saltos porque está en el extremo de la jerarquía de acceso. Para reducirlo, el colector debe instalarse **cerca de esos equipos periféricos**, no en el centro de la red.

#### ¿Por qué «el nodo más central» no es siempre la mejor ubicación?

Hay tres razones concretas observadas en esta red:

1. **Redundancia geográfica.** `DATCC-2A-C3` (btw #1) y `DATCC-2A-C2` (btw #8) están a 1 salto entre sí. Instalar colectores en ambos cubre exactamente la misma zona. La p-mediana elige solo uno y usa el segundo slot para cubrir una zona diferente (Campus Paraíso con `CPAR-C10`).

2. **Betweenness mide tránsito, no cobertura.** `ROUTER-CAMPUS-HUAYNA-CAPAC` (btw #3) tiene alta intermediación porque todos los caminos entre Campus Central y Campus Huayna Capac pasan por él. Pero si se instala un colector ahí, solo cubre bien los equipos de ese campus; el resto de la red sigue lejos.

3. **El peor caso no está en el centro.** Para el p-centro, lo que importa es el equipo más alejado. Ese siempre es un switch de acceso en el extremo de una rama larga. Ningún nodo de core tiene visibilidad directa sobre él: para reducir su distancia al colector más cercano hay que bajar en la jerarquía, no subir.

### Ítem 4 · Restricciones prácticas omitidas por el modelo

Los modelos de p-mediana y p-centro son matemáticamente elegantes pero simplifican la realidad: solo consideran la distancia en saltos entre nodos e ignoran completamente las condiciones físicas, económicas y operativas de la red real. En este ítem se identifican las restricciones prácticas más importantes que el modelo no considera — como el espacio físico disponible en los armarios de red, la disponibilidad de energía eléctrica, la seguridad del lugar, el costo de licencias de software y la capacidad de procesamiento de cada colector — y se muestra cómo cada una de ellas podría incorporarse formalmente al modelo matemático como una restricción adicional:

| Restricción | Por qué importa | Cómo incorporarla al modelo |
|-------------|-----------------|----------------------------|
| **Espacio en rack** | Los switches de acceso no tienen slot físico para tarjetas adicionales | Filtrar el conjunto candidato: $y_j = 0$ si $j \in V_{\text{sin\_rack}}$ |
| **Energía** | No todos los armarios tienen UPS ni potencia suficiente | Añadir restricción $\sum_j \text{potencia}_j \cdot y_j \leq P_{\max}$ |
| **Seguridad física** | Un colector en sala pública puede ser comprometido | Restringir candidatos a nodos en sala de servidores controlada |
| **Costo de licencias** | NetFlow/SNMP tienen costo por dispositivo | Añadir término de costo fijo: $\min \sum d_{ij} x_{ij} + \sum c_j y_j$ |
| **Capacidad de procesamiento** | Un colector no puede procesar el tráfico de más de $K$ nodos | $\sum_i x_{ij} \leq K \cdot y_j \quad \forall j$ |
| **Alta disponibilidad** | Si cae el colector, su zona queda sin monitoreo | Exigir que cada nodo tenga al menos 2 colectores asignados: $\sum_j x_{ij} \geq 2$ |

Con estas restricciones, el modelo pasa de ser una p-mediana pura a un **problema de localización de instalaciones con capacidad** (Capacitated Facility Location Problem, CFLP), que sigue siendo NP-difícil pero es resoluble con solvers de programación entera mixta (PuLP/scipy en Python, JuMP en Julia) para instancias del tamaño de esta red ($n=177$).

#### p-Mediana vs p-Centro: cuándo usar cada uno

| | p-Mediana | p-Centro |
|---|---|---|
| **Objetivo** | Minimizar distancia media | Minimizar distancia máxima |
| **Cuándo usar** | DNS, NTP, servidores de logs | Gateways de emergencia, SLA estrictos |
| **Hallazgo UCuenca** | `INTERNET-MPLS` como 1-mediana óptima | Radio irreducible de 6 saltos con $p \leq 5$ |

El radio de 6 saltos es **constante** para $p \in \{1,2,3,5\}$: el árbol jerárquico impone un diámetro mínimo que no se puede reducir añadiendo colectores en los nodos existentes — reduciría el radio solo instalar colectores directamente en los switches de agregación de los campus periféricos.

---

## Preguntas — Fase 3

### P5 · Caminos mínimos

> **¿Qué nodo es más central según la closeness ponderada por latencia?**

`DATCC-2A-C3` en todos los modelos por saltos y latencia; `FORTIGATE-1800F-CENTRAL` sube al primer puesto en el modelo de carga porque concentra el tráfico real más intenso. La closeness por carga no mide distancia geométrica sino utilización actual de los enlaces.

> **¿En qué casos preferiría Floyd-Warshall sobre Dijkstra-repetido?**

Floyd-Warshall es preferible cuando se necesitan **todas** las distancias pares al mismo tiempo (análisis global de la red) y el grafo es denso ($m \approx n^2$). Para UCuenca ($n=177$, $m=209$, grafo muy disperso), Dijkstra×$n$ es 7–10× más rápido. La elección correcta depende de la densidad y del patrón de consultas.

### P6 · Flujo máximo

> **¿Coincide el corte mínimo con los puentes detectados en P1?**

Sí. Las 6 aristas del corte mínimo del Campus Central son todas puentes de la red. El teorema max-flow min-cut formaliza lo que la detección de puentes ya revelaba: las aristas sin alternativa son exactamente los cuellos de botella de flujo. La novedad de P6 es cuantificar la **capacidad** del cuello de botella, no solo su existencia.

> **¿Qué campus tiene mayor capacidad de salida a Internet y por qué?**

**Campus Central** con 43 Gbps, porque es el campus más grande (56 nodos de acceso) y tiene dos switches de core con enlaces de 10–20 Gbps hacia el backbone MPLS. Yanuncay y Hospitalidad están limitados a 1 Gbps porque sus conexiones MPLS son de 1 Gbps (un solo enlace de acceso WAN).

### P7 · Localización de instalaciones

> **¿Coincide la 1-mediana con el nodo de mayor closeness?**

Sí, ambos son `INTERNET-MPLS`, que tiene el mayor $C_{\text{close}} = 0.2759$. La equivalencia es matemática: maximizar la closeness es equivalente a minimizar la distancia media a todos los nodos, que es exactamente el objetivo de la 1-mediana. Esta coincidencia valida mutuamente ambas métricas.

> **¿Por qué el radio del p-centro no decrece al aumentar $p$?**

Porque el árbol jerárquico impone rutas mínimas de 6 saltos entre los nodos de acceso más profundos y cualquier nodo posible de instalación. Reducir el radio requeriría acortar la cadena `acceso → agregación → core → MPLS`, lo que implica añadir servidores directamente en los switches de agregación o acceso — opción no disponible con la infraestructura actual.

---

## Fase 4 — Percolación y Robustez

> *Peso: 6 puntos | Contenidos 4.1–4.4 del sílabo*

### ¿Qué es la percolación en redes?

La **percolación** estudia qué le pasa a una red cuando se le van quitando elementos — nodos o aristas — de forma gradual. La pregunta central es: ¿a partir de qué fracción de fallos la red deja de funcionar como un todo conectado?

Imagina que vas apagando switches de la red UCuenca uno por uno. Al principio la red sigue funcionando: los equipos restantes todavía pueden comunicarse entre sí por rutas alternativas. Pero llegado cierto punto crítico, la red se "rompe" en pedazos aislados y la mayoría de equipos pierde conectividad con el resto. Ese punto crítico se llama **umbral de percolación** $f_c$.

#### Componente gigante y umbral de percolación

Se define $S(f)$ como el **tamaño relativo de la componente conexa más grande** (componente gigante) cuando se ha eliminado una fracción $f$ de nodos o aristas. Al inicio ($f=0$) toda la red es una sola componente, así que $S(0) \approx 1$. A medida que $f$ crece, $S(f)$ decrece. El umbral $f_c$ es el valor donde $S(f)$ colapsa hacia cero: la red ya no tiene una componente dominante.

$$S(f) = \frac{|\text{componente gigante tras eliminar fracción } f|}{n}$$

$$f_c = \min\{f : S(f) \approx 0\}$$

#### Fallos aleatorios vs. ataques dirigidos

No todos los fallos son iguales. Hay dos escenarios extremos:

- **Fallo aleatorio:** un switch falla por error de hardware, corte de luz o mantenimiento imprevisto. El nodo eliminado es elegido al azar, sin importar su importancia en la red. Las redes con distribución de grado heterogénea (como las redes libres de escala) son muy resistentes a esto: la probabilidad de dañar un hub central es muy baja.

- **Ataque dirigido:** un actor malicioso o un fallo en cascada elimina primero los nodos más importantes — los de mayor grado o mayor betweenness. Este escenario es mucho más destructivo: eliminar unos pocos hubs desconecta inmediatamente grandes porciones de la red.

La diferencia entre ambas curvas $S(f)$ revela qué tan vulnerable es la red ante una amenaza inteligente vs. un fallo fortuito.

#### Robustez

La **robustez** es la capacidad de la red de mantener su funcionalidad (conectividad, eficiencia de rutas) ante la eliminación de elementos. Se mide de dos formas complementarias:

- **Tamaño de la componente gigante $S(f)$:** mide si los nodos siguen conectados entre sí.
- **Eficiencia global $E(f)$:** mide qué tan rápido pueden comunicarse los nodos que sí siguen conectados:

$$E(f) = \frac{1}{n(n-1)} \sum_{i \neq j} \frac{1}{d_{ij}}$$

donde $d_{ij}$ es la distancia más corta entre $i$ y $j$ (se define $1/d_{ij} = 0$ si no hay camino). La eficiencia puede degradarse significativamente **antes** de que la componente gigante se rompa, porque los caminos se vuelven más largos aunque la red siga conectada.

---

## P8 — Percolación de Nodos y Aristas *(2.5 puntos)*

### Ítem 1 · Percolación de nodos bajo cuatro estrategias

En este ítem se implementa la percolación de nodos: se eliminan nodos de la red uno a uno siguiendo cuatro criterios distintos, y tras cada eliminación se mide cómo evoluciona la componente gigante $S(f)$ y la eficiencia global $E(f)$. Las cuatro estrategias permiten comparar el efecto de un fallo accidental frente a distintos tipos de ataque dirigido.

Las cuatro estrategias implementadas son:

- **(a) Fallo aleatorio:** los nodos se eliminan en orden aleatorio, simulando fallos de hardware sin patrón. Se promedia sobre **100 realizaciones** (semillas 0–99) para obtener una curva estable y se reporta la desviación estándar.
- **(b) Ataque por grado descendente:** se elimina primero el nodo con más conexiones. El orden se calcula una sola vez al inicio sobre el grafo original.
- **(c) Ataque por intermediación descendente:** se elimina primero el nodo con mayor betweenness centrality. El orden se calcula una sola vez al inicio.
- **(d) Ataque por intermediación recalculada:** tras cada eliminación se recalcula la betweenness del grafo resultante y se elimina el nuevo nodo más crítico. Es el ataque más costoso computacionalmente y el más destructivo, porque adapta la estrategia al estado actual de la red.

#### Resultados medidos

| Estrategia | $f_c$ (S < 5%) | $f$ (E < 50% $E_0$) | Descripción |
|------------|---------------|---------------------|-------------|
| (a) Fallo aleatorio | **0.75** | 0.30 | Hay que eliminar el 75% de los nodos para colapsar la red |
| (b) Grado descendente | **0.15** | 0.05 | Con el 15% de los nodos más conectados eliminados, la red colapsa |
| (c) Betweenness estático | **0.15** | 0.05 | Similar al anterior; betweenness y grado se solapan en los hubs |
| (d) Betweenness recalculada | **0.10** | 0.05 | El más destructivo: basta eliminar el 10% (≈18 nodos) |

**Desviación estándar del fallo aleatorio (100 realizaciones):** $\sigma_E = 0.0204$ — la curva aleatoria es estable; la variabilidad entre realizaciones es baja porque la red tiene muchos nodos de acceso intercambiables.

#### Interpretación

El contraste entre $f_c = 0.75$ (aleatorio) y $f_c = 0.10$ (btw recalculada) revela la naturaleza jerárquica de la red UCuenca: **es muy robusta ante fallos accidentales** (132 de 177 nodos son switches de acceso con grado 1–2, cuya pérdida no afecta la conectividad global) pero **extremadamente vulnerable ante un ataque inteligente** que apunte al core. Eliminar los 18 nodos más centrales — todos switches de core y agregación — es suficiente para fragmentar la red completamente.

La diferencia entre (c) y (d) muestra el coste de recalcular: la betweenness estática subestima el daño porque no contempla que al eliminar un nodo, los nodos adyacentes se vuelven más críticos. La versión recalculada captura ese efecto y produce un colapso un 33% más rápido ($f_c = 0.10$ vs $0.15$).

### Ítem 2 · Gráfica S(f) y estimación de $f_c$

![Robustez de nodos](results/imagenes/p8_robustez_nodos.png)

La figura muestra en el panel izquierdo la eficiencia global $E(f)$ y en el panel derecho el tamaño relativo de la componente gigante $S(f)$, ambos en función de la fracción de nodos eliminados $f$. La banda azul en la curva aleatoria corresponde a ±1 desviación estándar sobre las 100 realizaciones.

Los valores de $f_c$ estimados (donde $S(f) < 0.05$) confirman que la estrategia más dañina es la betweenness recalculada ($f_c = 0.10$), mientras que el fallo aleatorio requiere eliminar tres cuartas partes de la red para producir el mismo efecto.

### Ítem 3 · Percolación de aristas

Se repite el análisis eliminando **aristas** en lugar de nodos, bajo tres estrategias: aleatoria, por mayor betweenness de arista, y atacando primero los **141 puentes** identificados en P1.

| Estrategia | Descripción |
|------------|------------|
| Aleatoria | Aristas eliminadas en orden aleatorio — degradación gradual |
| Mayor betweenness de arista | Las aristas que más caminos cortos transportan se eliminan primero |
| Puentes de P1 primero | Se eliminan primero los 141 puentes (aristas cuya eliminación desconecta la red), luego el resto aleatoriamente |

El ataque a puentes es especialmente destructivo desde el inicio: los 141 puentes de la red son exactamente las aristas sin redundancia — eliminar cualquiera de ellos aísla inmediatamente un subgrafo. Tras agotar los puentes (fracción $q = 141/209 \approx 0.67$), el resto de las aristas puede eliminarse sin producir desconexiones adicionales porque forman parte de ciclos.

![Robustez de aristas](results/imagenes/p8_robustez_aristas.png)

### Ítem 4 · Eficiencia global E(f) y su degradación anticipada

$$E(G) = \frac{1}{n(n-1)} \sum_{i \neq j} \frac{1}{d(i,j)}$$

donde $d(i,j) = \infty \Rightarrow 1/d = 0$ para pares desconectados. **Eficiencia inicial: $E_0 = 0.2082$.**

> *En palabras simples:* mide qué tan bien se comunican todos los pares de nodos. Si dos nodos están a 1 salto contribuyen 1; si están a 5 saltos contribuyen 1/5; si están desconectados contribuyen 0. Cuando la red se fragmenta o los caminos se alargan, $E$ cae.

La eficiencia se degrada **mucho antes** de que $S(f)$ colapse porque son métricas distintas:

- $S(f)$ solo detecta cuando la componente gigante se rompe en piezas separadas — hasta ese momento cuenta todos los nodos como "conectados".
- $E(f)$ detecta también cuando los caminos se **alargan**: aunque la red siga siendo una sola componente, si los caminos más cortos pasan ahora por rutas indirectas (porque se eliminaron los hubs centrales), $E$ ya cae.

En la red UCuenca: bajo ataque por grado, $E$ cae al 50% con $f = 0.05$ (9 nodos eliminados), pero $S$ no colapsa hasta $f = 0.15$ (27 nodos). Durante esa ventana la red aparece "conectada" pero las rutas son tan largas que la comunicación efectiva ya está severamente dañada.

### Ítem 5 · Comparación con modelos nulos de P2

| Modelo | $E_0$ | $f_c$ bajo ataque por grado |
|--------|-------|----------------------------|
| **Red UCuenca** | **0.2082** | **0.15** |
| Erdős-Rényi (ER) | 0.1397 | 0.35 |
| Configuración (CM) | 0.1565 | 0.20 |

La red UCuenca tiene **mayor eficiencia inicial** que ambos modelos nulos — la topología jerárquica optimiza los caminos cortos. Sin embargo, ante ataques por grado es **más frágil** que ER ($f_c = 0.15$ vs $0.35$) y ligeramente más frágil que CM ($f_c = 0.15$ vs $0.20$).

Esto responde directamente la pregunta de la guía: **la red UCuenca es menos robusta de lo que su secuencia de grados haría esperar.** El modelo de configuración, que preserva exactamente la misma secuencia de grados pero con conexiones aleatorias, es más resistente ($f_c = 0.20$). La diferencia se explica porque la red real concentra los hubs en una jerarquía estricta (core → agregación → acceso): eliminar el nivel de core desconecta simultáneamente todos los campus, algo que no ocurre en el CM donde los nodos de alto grado están distribuidos sin estructura geográfica.

Bajo percolación **aleatoria**, el umbral es $f_c \approx 0.75$ (≈133 nodos), lo que indica que la red tolera bien los fallos no coordinados pero es extremadamente vulnerable a ataques dirigidos.

### La paradoja de la robustez

Las redes con distribución de grado heterogénea — donde pocos nodos tienen muchas conexiones y la mayoría tiene pocas — exhiben un comportamiento paradójico: son muy resistentes a fallos aleatorios pero muy frágiles ante ataques dirigidos. La red UCuenca confirma exactamente este patrón.

#### Verificación del comportamiento paradójico

| Escenario | $f_c$ | Interpretación |
|-----------|-------|---------------|
| Fallo aleatorio | **0.75** | Hay que perder el 75% de los nodos para colapsar la red |
| Ataque por grado | **0.15** | Con solo el 15% de los nodos más conectados, la red colapsa |
| Ataque btw recalculada | **0.10** | El atacante más inteligente colapsa la red con solo 18 nodos |

La ratio entre ambos umbrales es 7.5:1 — la red es 7.5 veces más resistente ante fallos accidentales que ante ataques dirigidos. Esto es la paradoja de la robustez en su forma más clara.

La razón estructural: 132 de 177 nodos son switches de acceso con grado 1 o 2. Un fallo aleatorio tiene probabilidad 132/177 ≈ 75% de caer en un nodo de acceso, cuya pérdida aísla solo 1 equipo. Un ataque dirigido ignora esos 132 nodos y va directamente a los 5 switches de core y 27 de agregación, cuya pérdida aísla campus enteros.

#### Consecuencia operativa para un plan de mantenimiento

El mantenimiento programado es esencialmente un **fallo aleatorio controlado**: se apaga un switch, se hace el trabajo, se vuelve a encender. Los resultados dicen que la red tolera bien esto — se puede poner fuera de servicio cualquier nodo de acceso sin afectar al resto, e incluso nodos de agregación tienen respaldo en varios casos.

Sin embargo, el plan de mantenimiento debe **prohibir intervenir simultáneamente** en más de un switch de core o en el nodo `DATCC-2A-C3` (btw #1). Una ventana de mantenimiento mal planificada que deje dos switches de core fuera de servicio a la vez coloca a la red en la zona frágil del umbral de ataque — el equivalente a un f=0.11, ya por encima del fc del ataque más destructivo.

Recomendación práctica: establecer una lista de **nodos de mantenimiento restringido** (los top-10 por betweenness: DATCC-2A-C3, CPAR-C10, ROUTER-CAMPUS-HUAYNA-CAPAC, INTERNET-MPLS, PE2-CENTRAL...) que requieran aprobación especial y ventana nocturna con plan de respaldo activo antes de cualquier intervención.

#### Consecuencia operativa para un plan de respuesta ante incidentes de seguridad

Un atacante que conozca la topología de la red — o que simplemente use `nmap` y calcule betweenness — puede colapsar la red UCuenca comprometiendo **18 dispositivos** (10% de 177). Peor aún, con la estrategia de betweenness recalculada, cada compromiso le da información sobre el siguiente objetivo más crítico.

El plan de respuesta ante incidentes debe priorizar dos medidas:

1. **Detección temprana en los nodos críticos.** Los switches de core y los routers WAN (DATCC-2A-C3, CPAR-C10, INTERNET-MPLS) deben tener monitoreo continuo con alertas en tiempo real. Un ataque que llegue al tercer o cuarto nodo sin ser detectado ya ha reducido la eficiencia de la red al 50%.

2. **Aislamiento rápido antes que recuperación.** Ante un incidente de seguridad en un nodo de core, la prioridad no es restaurarlo — es aislarlo antes de que el atacante use ese nodo comprometido para pivotar hacia el siguiente hub crítico. Dado que la red colapsa con 18 nodos, cada hub comprometido que no se aísla acelera el siguiente paso del ataque.

La paradoja tiene una implicación directa: **los mismos nodos que hacen la red eficiente son los que la hacen vulnerable.** No es posible eliminar esa tensión sin añadir redundancia (más aristas entre campus, rutas alternativas al backbone MPLS), que es exactamente lo que los modelos nulos ER y CM tienen y la red real no.

---

## P9 — Fallas en Cascada y Epidemias SIR *(2.5 puntos)*

Este problema estudia cómo se propagan eventos negativos a través de la red bajo dos modelos dinámicos distintos. El primero es un modelo de **cascada de fallos por sobrecarga** (Motter-Lai): cuando un switch cae, su tráfico se redistribuye entre los demás, y si alguno de ellos se satura también cae, generando un efecto dominó. El segundo es un modelo **epidémico SIR**: simula cómo un malware o una mala configuración se contagia de equipo en equipo, y evalúa qué estrategia de parcheo detiene el brote más eficientemente con el menor número de equipos intervenidos. Ambos modelos buscan responder la misma pregunta desde ángulos distintos: **¿cuán vulnerable es la red UCuenca ante un evento que se propaga internamente?**

### Ítem 1 · Modelo de carga-capacidad (Motter-Lai)

Cada nodo $i$ tiene:
- **Carga inicial:** $L_i = B_i$ (betweenness del nodo en el grafo intacto)
- **Capacidad:** $C_i = (1 + \alpha) \cdot L_i$ con tolerancia $\alpha \geq 0$

Al fallar el nodo inicial, el betweenness de los nodos supervivientes aumenta (más flujo pasa por ellos). Si la nueva carga de algún nodo supera su capacidad, falla también → **cascada**.

> *Lectura:* cuando un router crítico falla, el tráfico que antes pasaba por él se redistribuye entre los caminos alternativos. Los routers que se convierten en "detour" repentino pueden saturarse y fallar también. La tolerancia $\alpha$ mide qué tan sobreprovisionada está la red: $\alpha = 0$ significa capacidad exactamente al 100%, sin margen; $\alpha = 1$ significa el doble de margen.
>
> *En palabras simples:* es como un atasco de tráfico que se propaga: si la autopista principal se cierra, los conductores se desvían por carreteras secundarias. Si esas carreteras tampoco aguantan el nuevo tráfico, también colapsan, creando más desvíos en un efecto dominó.

#### Algoritmo implementado

El modelo se ejecuta de la siguiente forma para cada nodo disparador:

1. **Inicialización:** calcular el betweenness $B_i$ de todos los nodos en la red intacta. Asignar $C_i = (1+\alpha) \cdot B_i$ como capacidad máxima de cada nodo.
2. **Fallo inicial:** eliminar el nodo disparador del grafo.
3. **Redistribución:** recalcular el betweenness de todos los nodos restantes — los caminos que antes pasaban por el nodo caído ahora pasan por rutas alternativas, aumentando la carga de esos nodos.
4. **Detección de nuevos fallos:** identificar todos los nodos cuyo nuevo betweenness supera su capacidad $C_i$.
5. **Propagación:** eliminar esos nodos del grafo y volver al paso 3.
6. **Criterio de parada:** la cascada termina cuando ningún nodo activo supera su capacidad, o cuando no quedan nodos.

El resultado de cada ejecución es el conjunto total de nodos fallidos (disparador + caídos en cascada) y el número de pasos que tomó la propagación. Se repite para todo $\alpha \in \{0, 0.05, 0.10, 0.20, 0.50, 1.00, 1.50, 2.00\}$ y para cada nodo posible como disparador, para identificar los más peligrosos.

### Ítem 2 · Margen crítico $\tau_c$ y nodos disparadores más peligrosos

La guía define $\tau_c$ como el margen por debajo del cual la falla de un único nodo provoca una cascada que afecta a más del **20% de la red** (>35 nodos de 177).

#### Resultado principal: la cascada nunca alcanza el 20%

El barrido de $\alpha \in \{0, 0.05, \ldots, 2.0\}$ iniciado desde el nodo más peligroso muestra:

| $\alpha$ | Nodos fallidos | Fracción | Pasos |
|----------|---------------|----------|-------|
| 0.00 | 12 | 6.8% | 1 |
| 0.05 | 9 | 5.1% | 2 |
| 0.10 | 9 | 5.1% | 2 |
| 0.20 | 8 | 4.5% | 1 |
| 0.50 | 8 | 4.5% | 1 |
| 1.00 | 8 | 4.5% | 1 |
| 1.50 | 5 | 2.8% | 1 |
| 2.00 | 3 | 1.7% | 1 |

**$\tau_c$ no existe para esta red**: incluso con $\alpha = 0$ (capacidad exactamente igual a la carga nominal, sin ningún margen), la cascada máxima alcanza solo el **6.8%** de los nodos — muy por debajo del umbral del 20%. Esto se debe a la topología jerárquica: los 132 switches de acceso tienen grado 1, por lo que al quedar desconectados no redistribuyen carga hacia otros nodos y la cascada se detiene en la capa de agregación.

Este es un resultado positivo: **la red UCuenca es estructuralmente resistente a las cascadas de carga**, a diferencia de las redes de transmisión eléctrica donde la redistribución de carga puede propagarse a través de múltiples niveles de la jerarquía.

![Cascada de fallos](results/imagenes/p9_cascada.png)

#### Nodos disparadores más peligrosos ($\alpha = 0.1$)

Se corrió el modelo desde cada uno de los 177 nodos para identificar los más peligrosos:

| Rank | Nodo disparador | Nodos fallidos | Fracción | Betweenness |
|------|----------------|---------------|----------|-------------|
| 1 | FORTIGATE-1800F-BALZAY | 11 | 6.2% | 2 295 |
| 2 | FORTIGATE-1800F-CENTRAL | 10 | 5.6% | 2 869 |
| 3 | INTERNET-MPLS | 10 | 5.6% | 5 631 |
| 4 | DATCC-2A-C3 | 9 | 5.1% | 6 880 |
| 5 | DT-0A-C13 | 6 | 3.4% | 3 442 |
| 6 | PE2-CENTRAL | 6 | 3.4% | 4 437 |
| 7 | PE2-BALZAY | 6 | 3.4% | 2 249 |
| 8 | DATCC-2A-C2 | 6 | 3.4% | 2 627 |

El nodo más peligroso para cascadas **no es el de mayor betweenness** (`DATCC-2A-C3`, rank 4) sino `FORTIGATE-1800F-BALZAY` (rank 1). La razón: el Fortigate de Balzay conecta dos zonas relativamente independientes de la red; su fallo fuerza que todo el tráfico de Balzay pase por una única ruta alternativa, saturando los nodos intermedios. `DATCC-2A-C3` tiene más betweenness pero sus vecinos tienen mayor capacidad de absorber la redistribución.

### Ítem 3 · Modelo SIR y umbral crítico

El **modelo SIR** discreto modela la propagación de un fallo lógico (virus, misconfiguration):

- **S** (Susceptible): equipo no infectado que puede serlo
- **I** (Infected): equipo actualmente comprometido, puede infectar vecinos
- **R** (Recovered): equipo parcheado/restaurado, inmune

Ecuaciones de transición (tiempo discreto):

$$P(S \to I) = 1 - (1-\beta)^{n_I(v)}, \qquad P(I \to R) = \gamma$$

donde $n_I(v)$ es el número de vecinos infectados de $v$.

> *Lectura:* en cada paso de tiempo, un equipo susceptible se infecta con probabilidad que depende de cuántos vecinos ya infectados tiene: $\beta$ es la probabilidad de infección por cada vecino infectado. Un equipo infectado se recupera con probabilidad $\gamma$ en cada paso.
>
> *En palabras simples:* un virus informático se propaga de router en router. En cada "tick" del reloj, cada router infectado tiene $\beta$ probabilidad de infectar a cada vecino sano. Los routers infectados se parchean con probabilidad $\gamma$ por tick. Si $\beta$ es muy baja, el virus muere rápido; si es alta, se propaga a toda la red.

**Umbral crítico:**

$$\tau_c = \frac{\langle k \rangle}{\langle k^2 \rangle} = \frac{2.362}{12.694} = 0.1861$$

Para $\beta > \tau_c$ existe una epidemia global; para $\beta < \tau_c$ la infección se extingue localmente.

> *Lectura de la notación:* $\langle k \rangle$ se lee "promedio de k" — es el grado medio de todos los nodos (cuántas conexiones tiene cada nodo en promedio; para UCuenca: 2.362). $\langle k^2 \rangle$ se lee "promedio de k al cuadrado" — se eleva el grado de cada nodo al cuadrado y se promedia (para UCuenca: 12.694). Este segundo valor es mucho mayor que el primero porque los hubs, al tener grado alto, inflan enormemente el promedio cuando se elevan al cuadrado. $\langle k^2 \rangle \gg \langle k \rangle$ significa "el promedio de k cuadrado es mucho mayor que el promedio de k", lo que ocurre cuando la red tiene hubs. Como el denominador de $\tau_c$ es grande, el umbral resulta pequeño ($\tau_c = 0.186$): la red es vulnerable a virus poco contagiosos.
>
> *En palabras simples:* en una red donde hay algunos equipos muy conectados (hubs), basta con una tasa de infección muy baja para que el virus se propague a toda la red. Los hubs actúan como "superpropagadores": cualquier virus que los alcance se distribuye de golpe a todos sus vecinos.

#### Resultados SIR y comparación con la predicción de campo medio

La predicción teórica de campo medio establece $\tau_c = \langle k \rangle / \langle k^2 \rangle = 0.1861$. Para verificarla, el código fija $\gamma = 0.1$ (probabilidad de recuperación por paso) y elige dos valores de $\beta$ a ambos lados del umbral: $\beta_{\text{sub}} = \tau_c / 2$ y $\beta_{\text{sup}} = 2\tau_c$. Estos son **parámetros de diseño del experimento**, no propiedades de la red — su propósito es mostrar los dos regímenes contrastantes:

| Caso | $\beta$ (elegido) | $\gamma$ (fijo) | Relación con $\tau_c = 0.1861$ | $R_{\text{final}}$ | Nodos afectados |
|------|------------------|----------------|-------------------------------|-------------------|----------------|
| Sub-crítico | 0.0931 | 0.1 | $\beta = \tau_c / 2$ → por debajo del umbral | 51 | 28.8% |
| Sobre-crítico | 0.3722 | 0.1 | $\beta = 2\tau_c$ → por encima del umbral | 140 | 79.1% |

**Comparación con campo medio:** la predicción teórica establece que para $\beta < \tau_c$ la infección debería extinguirse localmente, y para $\beta > \tau_c$ debería propagarse como epidemia global. La simulación confirma cualitativamente esta predicción: el caso sub-crítico produce un brote acotado del 28.8% y el sobre-crítico alcanza el 79.1%.

Sin embargo, el resultado sub-crítico (28.8%) es mayor de lo que la teoría pura esperaría (casi 0%). Esto se debe a que $\tau_c = \langle k \rangle / \langle k^2 \rangle$ es una aproximación para redes grandes e infinitas. La red UCuenca tiene solo 177 nodos y asortatividad negativa (−0.15), lo que desplaza el umbral real respecto a la predicción teórica.

![Modelo SIR](results/imagenes/p9_sir.png)

### Ítem 4 · Estrategias de inmunización

El ítem plantea un problema de **presupuesto fijo**: si el equipo de TI solo puede parchear $m$ equipos (instalar actualizaciones, aislar vulnerabilidades), ¿cuáles conviene elegir para minimizar el tamaño del brote? Se comparan cuatro estrategias con el mismo número de nodos inmunizados (misma fracción $f$ del total): aleatoria, por grado (parchear primero los switches más conectados), por betweenness (parchear los más intermediarios) y por vecino aleatorio (proxy práctico que no requiere conocer la topología completa). El escenario usa $\beta = 2\tau_c = 0.3722$ (régimen sobre-crítico) para que la diferencia entre estrategias sea visible.

Fracción afectada ($R_{\text{final}}/n$) con $\beta = 0.3722$, $\gamma = 0.1$:

| Estrategia | $f=0\%$ | $f=10\%$ | $f=20\%$ | $f=30\%$ |
|------------|---------|---------|---------|---------|
| Sin inmunización | 79.1% | — | — | — |
| Aleatoria | 79.1% | 66.7% | 59.3% | 33.9% |
| Por grado (hubs primero) | 79.1% | 22.6% | **4.0%** | 1.7% |
| Por betweenness | 79.1% | 30.5% | 6.2% | **0.6%** |
| Por vecino (proxy) | 79.1% | 44.6% | 20.3% | 1.1% |

![Estrategias de inmunización](results/imagenes/p9_inmunizacion.png)

#### Análisis

Vacunar por **grado** es la estrategia más eficiente: con solo el 20% de nodos inmunizados (≈35 equipos), la fracción afectada cae del 79% al 4%. La razón: inmunizando los switches de core y agregación se corta la capacidad de los "superpropagadores" de distribuir la infección.

La **estrategia por vecino** es un buen proxy práctico: sin conocer la red completa, seleccionar el vecino de un nodo aleatorio tiende a encontrar hubs (porque los hubs tienen más probabilidad de ser vecino de alguien). Con 30% de cobertura logra una reducción similar a la estrategia por grado.

La estrategia **aleatoria** es la menos eficiente: requiere el 30% de cobertura para llegar a 33% de afectados, mientras que por grado con 20% ya llega al 4%.

### Ítem 5 · Analogía con redes de transmisión eléctrica

Los modelos de cascadas de carga fueron desarrollados originalmente para redes de transmisión eléctrica (Motter & Lai, 2002). La analogía con la red UCuenca es directa:

| Concepto en red eléctrica | Equivalente en red UCuenca |
|--------------------------|---------------------------|
| **Carga** de una línea de transmisión | **Betweenness** del nodo: número de caminos más cortos que pasan por él. Mide cuánto "tráfico de datos" intermedia el switch. |
| **Capacidad** de la línea | $C_i = (1+\alpha) \cdot B_i$: máximo betweenness que el switch puede manejar sin colapsar. Equivale al límite térmico de la línea eléctrica. |
| **Redistribución de carga** tras una falla | Al caer un switch, los paquetes de datos se redirigen por los caminos alternativos, aumentando el betweenness de los nodos en esas rutas. En redes eléctricas, la potencia se redistribuye físicamente por las líneas restantes (ley de Kirchhoff). |
| **Cascada** | En electricidad: una línea sobrecargada se desconecta automáticamente por protecciones, transfiriendo más carga a las líneas restantes hasta el apagón (blackout). En UCuenca: un switch que supera su capacidad de procesamiento entra en estado de error y cae, forzando más tráfico por otros caminos. |
| **Umbral $\alpha$** | En electricidad: margen de reserva de capacidad de las líneas (spinning reserve). En UCuenca: sobreprovisionamiento de CPU/memoria del switch respecto a su carga nominal de betweenness. |

#### ¿Por qué las redes eléctricas son más vulnerables a cascadas?

En redes eléctricas la redistribución de carga sigue las leyes de Kirchhoff y es **instantánea y global**: cuando una línea cae, la potencia se redistribuye simultáneamente por todas las líneas del sistema, pudiendo sobrecargar líneas en el extremo opuesto de la red. Este efecto a distancia es lo que produce grandes apagones en cascada (e.g. Northeast Blackout 2003: la falla de 3 líneas en Ohio cascadeó hasta afectar 55 millones de personas).

En la red UCuenca, la redistribución de betweenness es **local**: solo los caminos que pasaban por el nodo caído se ven afectados, y la topología jerárquica con muchos nodos de grado 1 actúa como barrera natural que detiene la propagación. Esto explica por qué la cascada máxima observada es solo 6.8% frente a apagones que afectan el 100% de la red eléctrica.

> **Referencia:** Motter, A. E., & Lai, Y.-C. (2002). *Cascade-based attacks on complex networks*. Physical Review E, 66(6), 065102. Este artículo introduce el modelo de carga-capacidad con betweenness utilizado en este problema y demuestra que redes heterogéneas con pocos hubs son especialmente vulnerables a cascadas iniciadas en esos hubs.

---

## Preguntas — Fase 4

### P8 · Percolación y robustez

> **¿Es la red más o menos robusta que sus modelos nulos?**

La red UCuenca tiene **mayor eficiencia inicial** ($E_0 = 0.208$) que ER (0.140) y CM (0.157) — la estructura jerárquica optimiza los caminos. Sin embargo, frente a ataques dirigidos por grado, UCuenca es **igual de frágil que CM** (umbral $f_c \approx 0.05$): en ambos casos, eliminar el 5% de nodos de mayor grado colapsa la mitad de la eficiencia. ER es más resistente ($f_c \approx 0.10$) porque sus grados son más uniformes.

> **¿Qué tipo de ataque resulta más devastador y por qué?**

El ataque por **grado** y por **betweenness** son igualmente devastadores, con umbral $f_c \approx 0.05$. La razón: en UCuenca, los nodos de mayor grado son también los de mayor betweenness (ver P1). Eliminar los 5 switches de core y los 4–5 de mayor agregación desconecta inmediatamente campus enteros. El ataque aleatorio es 5 veces menos efectivo porque la mayoría de los nodos son hojas de acceso cuya eliminación no desconecta ningún subgrafo.

### P9 · Cascadas y epidemias

> **¿Qué tolerancia mínima $\alpha$ recomendaría para proteger el core?**

Con $\alpha \geq 1.5$, la cascada iniciada en `DATCC-2A-C3` se limita a 5 nodos (2.8%), en lugar de los 12 con $\alpha = 0$. En términos de diseño: **las interfaces de los switches de core deberían tener un sobreprovisionamiento del 150%** sobre la carga nominal de betweenness. Dado que `DATCC-2A-C3` tiene el mayor betweenness de toda la red, es el más vulnerable a la saturación por rerouting.

> **¿Qué estrategia de inmunización es más eficiente y cuál más práctica?**

- **Más eficiente:** por betweenness — con 30% de nodos inmunizados, solo el 0.6% de nodos queda afectado. Requiere calcular el betweenness de toda la red.
- **Más práctica:** por vecino — sin conocer la topología completa, seleccionar vecinos de nodos aleatorios tiende a encontrar hubs. Con 30% logra 1.1% de afectados, casi igual que la estrategia óptima, pero sin necesitar el cálculo global.
- **Recomendación operativa:** inmunizar los top-20 nodos por betweenness (11.3% de la red) garantiza que la infección no supera el 6.2% de nodos en el peor caso.

> **¿Tiene sentido aplicar el modelo SIR a una red de infraestructura de datos?**

Sí, con la interpretación correcta. $\beta$ representa la tasa a la que una misconfiguration, vulnerability o malware se propaga de un switch a sus vecinos (por ejemplo, a través de protocolos de gestión como SNMP, SSH, o de enrutamiento como OSPF). $\gamma$ representa la tasa de parcheo o restauración. El umbral $\tau_c = 0.186$ indica que, para que una campaña de malware de red se extinga sola, su tasa de propagación debe ser menor al 18.6% por interfaz por unidad de tiempo — un valor que malware moderno supera fácilmente.

---

## Problema P10 — Diagnóstico de puntos críticos

Este problema sintetiza los resultados de las Fases 1 a 4 en un único ranking de criticidad. Se define un **Índice de Criticidad Compuesto (ICC)** que combina cuatro dimensiones: la centralidad estructural del nodo, su condición topológica como punto de separación, su participación en el cuello de botella de flujo, y el daño dinámico que genera al fallar.

### Definición y justificación del ICC

$$ICC_i = 0.35 \cdot \hat{B}_i + 0.25 \cdot A_i + 0.20 \cdot C_i + 0.20 \cdot \hat{D}_i$$

| Componente | Símbolo | Origen | Peso | Justificación |
|-----------|---------|--------|------|--------------|
| Betweenness normalizada | $\hat{B}_i$ | Fase 1 — P1 | 0.35 | El nodo con mayor betweenness intermedia más flujo; su caída aumenta rutas alternativas más largas |
| Punto de articulación | $A_i \in \{0,1\}$ | Fase 1 — P1 | 0.25 | Un punto de articulación desconecta la red al fallar; consecuencia irreversible sin redundancia |
| En corte mínimo | $C_i \in \{0,1\}$ | Fase 3 — P6 | 0.20 | Los nodos del corte mínimo limitan la capacidad de flujo; su eliminación reduce la transferencia máxima a 0 |
| Daño en cascada normalizado | $\hat{D}_i$ | Fase 4 — P9 | 0.20 | Mide el efecto dinámico: cuántos nodos adicionales caen en el modelo Motter-Lai con $\alpha=0.1$ |

Los pesos reflejan que la centralidad y la condición estructural (articulación) son los indicadores más robustos y directamente medibles, mientras que el daño en cascada —aunque más informativo en términos de impacto operativo— depende del parámetro $\alpha$ del modelo.

### Top-10 nodos críticos

| Rank | Nodo | Campus | Función | Grado | $\hat{B}$ | Art. | Corte | $\hat{D}$ | **ICC** |
|------|------|--------|---------|-------|-----------|------|-------|-----------|---------|
| 1 | INTERNET-MPLS | Nube MPLS | Backbone MPLS / salida Internet | 8 | 0.819 | ✓ | ✓ | 0.91 | **0.9183** |
| 2 | ROUTER-CAMPUS-HUAYNA-CAPAC | Campus Paraíso | Router de campus | 3 | 0.820 | ✓ | ✓ | 0.09 | **0.7551** |
| 3 | CPAR-C10 | Campus Paraíso | Core — interconexión inter-campus | 7 | 0.905 | ✓ | — | 0.09 | **0.5849** |
| 4 | DATCC-2A-C3 | Campus Central | Core — interconexión inter-campus | 17 | 1.000 | — | — | 0.82 | **0.5136** |
| 5 | ROUTER-CAMPUS-YANUNCAY | Campus Yanuncay | Router de campus | 3 | 0.048 | ✓ | — | 0.09 | **0.3683** |
| 6 | AGRPRI-1A-D10 | Campus Yanuncay | Agregación | 12 | 0.038 | ✓ | — | 0.09 | **0.3633** |
| 7 | CC-ARQUITECTURA-D107 | Campus Central | Agregación | 10 | 0.027 | ✓ | — | 0.09 | **0.3632** |
| 8 | BAL-AUL2-D1 | Campus Balzay | Agregación | 12 | 0.021 | ✓ | — | 0.09 | **0.3549** |
| 9 | CP-EADMINA1-D6 | Campus Paraíso | Agregación | 9 | 0.022 | ✓ | — | 0.09 | **0.3380** |
| 10 | CP-ODONTOLOGIA-D4 | Campus Paraíso | Agregación | 6 | 0.017 | ✓ | — | 0.09 | **0.3378** |

### Fichas de los nodos #1 a #4 (mayor riesgo)

**#1 · INTERNET-MPLS** — ICC = 0.9183 ⚠️ CRÍTICO INSTITUCIONAL

El nodo de mayor criticidad compuesta de la red. Actúa como punto único de salida a Internet y concentrador del backbone MPLS que conecta todos los campus. Es simultáneamente punto de articulación (su caída desconecta al menos un subgrafo), nodo del corte mínimo (limita la capacidad de flujo máximo), y el segundo mayor generador de cascadas (91% de la carga máxima). *Consecuencia estimada:* pérdida total de conectividad a Internet y ruptura de la topología MPLS inter-campus; afecta servicios administrativos, académicos y de investigación de forma simultánea.

**#2 · ROUTER-CAMPUS-HUAYNA-CAPAC** — ICC = 0.7551 ⚠️ CRÍTICO DE CAMPUS

Router de acceso del Campus Paraíso al backbone. Tiene la segunda betweenness más alta de la red (0.820 normalizado) porque todos los flujos del campus pasan por él, y es punto de articulación y del corte mínimo. *Consecuencia estimada:* aislamiento completo del Campus Paraíso del resto de la red universitaria.

**#3 · CPAR-C10** — ICC = 0.5849 ⚠️ CRÍTICO DE CAMPUS

Switch de core del Campus Paraíso con el mayor betweenness de toda la red (0.905 normalizado, superior incluso a DATCC-2A-C3 por su posición topológica). Es punto de articulación — conecta 7 nodos de agregación/acceso al backbone. *Consecuencia estimada:* aunque no genera cascada masiva, su caída deja sin servicio a todos los edificios del Campus Paraíso de forma inmediata.

**#4 · DATCC-2A-C3** — ICC = 0.5136 ⚠️ CRÍTICO INSTITUCIONAL

Switch de core del Campus Central con el mayor betweenness absoluto de la red (1.000 normalizado), mayor grado (17 interfaces activas) y mayor daño en cascada estático (82% de la carga máxima). No es punto de articulación porque DATCC-2A-C2 provee redundancia parcial. *Consecuencia estimada:* degradación masiva del Campus Central con posible cascada que afecta hasta 14 nodos dependientes de sus rutas.

### Análisis del ranking

El ICC revela tres perfiles de criticidad distintos:

**Criticidad MPLS/WAN** (ranks 1–2): nodos con betweenness alta y participación en el corte mínimo — son los cuellos de botella de capacidad de flujo. Una falla aquí interrumpe el tráfico inter-campus o hacia Internet de forma inmediata.

**Criticidad de core** (ranks 3–4): switches de core con betweenness extrema. CPAR-C10 lidera porque su posición topológica lo convierte en intermediario de prácticamente todos los flujos del Campus Paraíso. DATCC-2A-C3 tiene el mayor daño en cascada pero no es punto de articulación gracias a su redundancia con DATCC-2A-C2.

**Criticidad de agregación** (ranks 5–10): nodos de agregación de cada campus — todos son puntos de articulación porque los switches de acceso dependen de ellos como único camino al core. Su betweenness es baja (cada uno solo intermedia el tráfico de su edificio), pero al ser puntos de corte, su caída aísla decenas de equipos finales.

![Ranking ICC](results/imagenes/p10_ranking_icc.png)

![Radar top-5](results/imagenes/p10_radar_top5.png)

---

## Problema P11 — Intervención acotada y justificada

Con el diagnóstico de P10 en mano, se propone una intervención de exactamente **cinco enlaces nuevos** sobre la red UCuenca. La restricción es dura: ningún enlace puede duplicar uno existente y cada uno debe resolver un problema identificado en el ranking ICC.

### Ítem 1 · Descripción de los cinco enlaces propuestos

| # | Enlace | Capacidad | Problema del diagnóstico que resuelve |
|---|--------|-----------|--------------------------------------|
| E1 | CPAR-C10 → INTERNET-MPLS | 1 000 Mbps | Elimina ROUTER-CAMPUS-HUAYNA-CAPAC (ICC #2) como único intermediario entre Campus Paraíso y backbone. Con E1, si el router falla, el tráfico sigue fluyendo por CPAR-C10 directamente. |
| E2 | DATCC-2A-C3 → CPAR-C10 | 10 000 Mbps | Crea vía directa de 10 Gbps entre el core del Campus Central y el core del Campus Paraíso. Reduce el daño en cascada de DATCC-2A-C3 (ICC #4) y da a CPAR-C10 (ICC #3) una segunda ruta hacia el backbone. |
| E3 | ROUTER-CAMPUS-YANUNCAY → PE2-CENTRAL | 1 000 Mbps | Elimina ROUTER-CAMPUS-YANUNCAY (ICC #5) como punto único de salida del Campus Yanuncay. PE2-CENTRAL es el segundo enlace PE del Campus Central, actualmente infrautilizado. |
| E4 | CP-ODONTOLOGIA-D4 → CP-EADMINA1-D6 | 1 000 Gbps | Cross-link entre dos nodos de agregación del Campus Paraíso (ICC #9 y #10). Crea un anillo parcial en la capa de distribución: si uno cae, el otro absorbe sus flujos. |
| E5 | BAL-EADM-D3 → DT-0A-C13 | 1 000 Mbps | Segundo uplink para el switch de administración del Campus Balzay (actualmente conectado a un solo nodo de core). Elimina BAL-EADM-D3 como punto de articulación. |

### Ítem 2 · Cuantificación de la mejora — tabla antes / después / variación

Las métricas se calcularon sobre la red original y sobre la red modificada con los cinco enlaces incorporados. Los valores de flujo máximo usan como fuente el nodo de core de cada campus hacia INTERNET-MPLS.

| Métrica | Antes (original) | Después (propuesta ICC) | Δ absoluto | Δ relativo |
|---------|-----------------|------------------------|-----------|-----------|
| Aristas totales | 209 | 214 | +5 | +2.4% |
| Puentes | 141 | 137 | −4 | −2.8% |
| Puntos de articulación | 47 | 46 | −1 | −2.1% |
| Distancia media | 5.830 | 4.976 | −0.855 | **−14.7%** |
| Eficiencia global $E_0$ | 0.2082 | 0.2330 | +0.0247 | **+11.9%** |
| Flujo máx. Campus Central | 5 000 Mbps | 6 318 Mbps | +1 318 | +26.4% |
| Flujo máx. Campus Paraíso | 318 Mbps | 6 318 Mbps | +6 000 | **+19×** |
| Flujo máx. Campus Balzay | 3 290 Mbps | 3 290 Mbps | 0 | 0% |
| Flujo máx. Campus Yanuncay | 1 000 Mbps | 1 000 Mbps | 0 | 0% |

El impacto más notable es sobre Campus Paraíso: el flujo máximo pasa de 318 Mbps a 6 318 Mbps porque E1 y E2 juntos abren una ruta de 10 Gbps entre CPAR-C10 y el backbone (Central → DATCC-2A-C3 → INTERNET-MPLS). La reducción del 14.7% en distancia media refleja que E2 (DATCC-2A-C3 ↔ CPAR-C10) acorta todos los caminos entre los dos campus más grandes.

La reducción de puentes (−4) y articulaciones (−1) es modesta porque la mayoría de los puentes de la red son hojas de acceso conectadas a un único switch de agregación — esos no se pueden eliminar sin cableado adicional dentro de los edificios.

![Percolación comparación](results/imagenes/p11_percolacion_comparacion.png)

![Flujo comparación](results/imagenes/p11_flujo_comparacion.png)

### Ítem 3 · Justificación frente a alternativas

Se compararon dos conjuntos alternativos de cinco enlaces:

**Alternativa A — criterio ingenuo (mayor grado):** conectar los cinco nodos de mayor grado entre sí cuando no hay enlace existente. Produce: DATCC-2A-C3 → {AGRPRI-1A-D10, BAL-AUL2-D1, CP-EADMINA1-D6, DT-0A-C13, INTERNET-MPLS}. La lógica es que los hubs ya concentran tráfico, así que conectarlos entre sí aumenta la capacidad del backbone.

**Alternativa B — criterio de betweenness:** conectar los nodos de mayor betweenness pairwise. Produce: ROUTER-CAMPUS-HUAYNA-CAPAC → {DATCC-2A-C3, DATCC-2A-C2}, ROUTER-CAMPUS-YANUNCAY → DATCC-2A-C3, CPAR-C10 → DATCC-2A-C2, DT-0A-C13 → INTERNET-MPLS.

| Métrica | Original | Propuesta ICC | Alt. A (grado) | Alt. B (btw) |
|---------|----------|--------------|---------------|-------------|
| Puentes | 141 | **137** | 138 | 140 |
| Articulaciones | 47 | 46 | **45** | 46 |
| Distancia media | 5.830 | 4.976 | **4.521** | 4.966 |
| Eficiencia global | 0.2082 | 0.2330 | **0.2524** | 0.2339 |
| Flujo Campus Paraíso | 318 | **6 318** | 395 | 1 318 |
| Flujo Campus Yanuncay | 1 000 | **1 000** | 2 000 | 1 000 |

La Alternativa A mejora mejor la eficiencia global (+21.2% vs +11.9%) y la distancia media. Sin embargo, **fracasa en resolver el problema más crítico del diagnóstico**: Campus Paraíso sigue con solo 395 Mbps de flujo máximo (vs 6 318 de la propuesta ICC). Esto se debe a que conectar los hubs de mayor grado entre sí no resuelve el cuello de botella de acceso de Campus Paraíso: el router de ese campus sigue siendo un único punto de paso.

La Alternativa B mejora la eficiencia casi igual que la propuesta (+12.3% vs +11.9%), pero tampoco resuelve Campus Paraíso de forma efectiva (1 318 Mbps vs 6 318 Mbps). Al centrarse en betweenness, construye múltiples rutas paralelas al backbone pero no añade capacidad nueva hacia los campus que más la necesitan.

**La propuesta ICC es superior en el indicador más relevante operativamente — flujo hacia Campus Paraíso — y es la única que aborda directamente los tres nodos en el top-4 del ranking ICC** (ROUTER-CAMPUS-HUAYNA-CAPAC #2, CPAR-C10 #3, DATCC-2A-C3 #4). Las alternativas optimizan métricas agregadas (distancia media, eficiencia global) pero no el problema de criticidad estructural.

### Ítem 4 · Estimación de costo y factibilidad

| Enlace | Factibilidad | Consideraciones |
|--------|-------------|----------------|
| E1: CPAR-C10 → INTERNET-MPLS | **Media.** CPAR-C10 está en Campus Paraíso; INTERNET-MPLS es un nodo lógico MPLS. Requiere contratar un segundo circuito MPLS al proveedor (ISP) para Campus Paraíso. Costo recurrente mensual. No requiere obra civil nueva si ya existe ducto al POP del ISP. | Principal obstáculo: costo operativo mensual de la segunda línea MPLS. |
| E2: DATCC-2A-C3 → CPAR-C10 | **Baja** (enlace inter-campus). Los campus Central y Paraíso están separados por varios kilómetros. Requeriría fibra óptica oscura o un circuito dedicado entre edificios. Alta inversión inicial en tendido o alquiler de fibra. | La mayor barrera es la distancia física y el costo de obra civil. Alternativa: VPN sobre MPLS existente (virtual, sin fibra nueva). |
| E3: ROUTER-CAMPUS-YANUNCAY → PE2-CENTRAL | **Media.** Similar a E1: requiere segundo circuito MPLS para Campus Yanuncay. PE2-CENTRAL ya existe en el backbone. Depende de disponibilidad de puertos en ambos extremos. | Más viable que E2 porque es un circuito WAN estándar. |
| E4: CP-ODONTOLOGIA-D4 → CP-EADMINA1-D6 | **Alta.** Ambos nodos están en Campus Paraíso, probablemente en el mismo edificio o campus. Requiere cable de par trenzado o fibra corta (~100 m). Costo mínimo. | El obstáculo principal es verificar disponibilidad de puertos en los switches de agregación. |
| E5: BAL-EADM-D3 → DT-0A-C13 | **Alta.** Ambos nodos están en Campus Balzay. BAL-EADM-D3 tiene solo grado 2, probablemente tiene puertos libres. Requiere cableado dentro del campus. | Obra civil mínima. Alta viabilidad técnica. |

En resumen: E4 y E5 son inmediatamente ejecutables con recursos internos de TI. E1 y E3 requieren negociación con el ISP. E2 es la propuesta de mayor impacto pero también la de mayor inversión, y podría reemplazarse por una solución lógica (VPN entre campus) mientras se planifica el tendido físico.

### Ítem 5 · Limitaciones del estudio

**Lo que el modelo no captura:**

El grafo de la red UCuenca fue construido a partir de diagramas de red, no de mediciones en tiempo real. Por tanto, los valores de tráfico (Mbps) son nominales — representan capacidades de enlace contratadas, no el tráfico real cursado. Un análisis de criticidad operativo requeriría datos de NetFlow o SNMP en producción para identificar qué enlaces están cerca de saturación.

El modelo de betweenness como proxy de carga asume enrutamiento por caminos más cortos, pero la red UCuenca usa OSPF y MPLS, donde el enrutamiento depende de métricas configuradas (cost). Un enlace de baja capacidad puede tener OSPF cost alto y casi no recibir tráfico incluso si topológicamente sería el camino más corto.

El modelo de cascadas de Motter-Lai supone redistribución instantánea y uniforme de carga, lo que no ocurre en redes reales con protocolos de convergencia (OSPF puede tardar segundos en recalcular rutas). Además, el modelo no contempla mecanismos de protección como Spanning Tree, HSRP/VRRP ni Fast Reroute MPLS, que en la práctica limitan las cascadas.

La propuesta de cinco enlaces asume disponibilidad de puertos y ausencia de restricciones físicas entre edificios. En la red real puede que algunos switches de agregación no tengan puertos libres, o que los ductos entre edificios estén al límite de capacidad.

**Qué datos harían falta:**

Para un análisis más preciso sería necesario: matrices de tráfico origen-destino por campus y por hora, logs de incidentes de los últimos 2–3 años (qué nodos han fallado y cuánto duraron las afectaciones), topología completa incluyendo redundancias lógicas (VLANs, túneles VPN, rutas OSPF alternativas), e inventario de puertos disponibles por switch.

**Conclusiones que NO pueden extraerse de este análisis:**

No es posible predecir cuándo fallará un nodo específico — el modelo es estructural, no temporal. No se puede concluir que la red sea insegura en términos de ciberseguridad: alta betweenness y criticidad topológica son problemas de disponibilidad, no de confidencialidad. Tampoco se puede afirmar que la propuesta de cinco enlaces sea la solución óptima combinatoria — encontrar el conjunto óptimo de $k$ enlaces es un problema NP-difícil que aquí se resuelve con heurística guiada por el ICC.

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

## Fase 5 — Propuesta de Rediseño

> *Peso: 3 puntos | Contenido 5.1 del sílabo — ver Problema P11 arriba*

El contenido completo de la Fase 5 se encuentra en la sección **Problema P11 — Intervención acotada y justificada** (cinco enlaces propuestos, tabla antes/después/variación, comparación de alternativas, factibilidad y limitaciones).

---

*Scripts: `src/problema1.py` – `src/problema11.py` · Última actualización: Fases 1–5 completas.*
