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

#### Análisis — ¿Cola pesada? ¿Red libre de escala?

Una **red libre de escala** sigue $P(k) \sim k^{-\gamma}$ con $2 < \gamma < 3$. En el gráfico log-log esto aparece como una línea recta.

La distribución de UCuenca muestra una **cola derecha** clara: 113 de 177 nodos (64%) tienen grado 1 (switches de acceso conectados a un único switch de agregación), mientras que un único nodo tiene grado 17 (el switch de core `DATCC-2A-C3`).

Sin embargo, **no es correcto afirmar** que la red es libre de escala porque:
1. Con $n = 177$ nodos el rango de grados es solo $[1, 17]$: insuficiente para ajustar una ley de potencia con rigor estadístico.
2. La cola no es producida por crecimiento preferencial sino por **diseño deliberado**: los switches de core tienen muchas conexiones porque el arquitecto de red así lo especificó.
3. Un test formal (Kolmogorov-Smirnov, método de Clauset et al. 2009) sería necesario antes de proclamar libre de escala.

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

#### Visualización 1 — Coloreada por campus (Spring / Fruchterman-Reingold)

![Visualización por campus](results/imagenes/p2_visualizacion_campus.png)

**Algoritmo:** Spring (Fruchterman-Reingold), parámetros: $k=0.55$, 80 iteraciones, semilla 7.

**Justificación del algoritmo:** El layout de Fruchterman-Reingold modela el grafo como un sistema físico donde las aristas actúan como resortes (atracción) y los nodos como cargas eléctricas (repulsión). El equilibrio minimiza el cruce de aristas y distribuye los nodos respetando la estructura de vecindad. Se eligió porque, sin imponer coordenadas fijas, los campus tienden a agruparse naturalmente al compartir muchas aristas internas.

**Qué revela:** los campus aparecen como grupos semi-separados, conectados entre sí a través de los nodos WAN/MPLS centrales. Los switches de core de cada campus actúan como "pegamento" entre los nodos de agregación y acceso de su cluster.

#### Visualización 2 — Tamaño ∝ betweenness, color = capa (Kamada-Kawai)

![Visualización por betweenness](results/imagenes/p2_visualizacion_betweenness.png)

**Algoritmo:** Kamada-Kawai.

**Justificación del algoritmo:** Kamada-Kawai asigna a cada par de nodos una longitud ideal de arco proporcional a su distancia en el grafo. El layout minimiza la energía de deformación entre las distancias ideales y las euclídeas. Esto hace que nodos cercanos en el grafo queden cerca en el dibujo, revelando la estructura jerárquica: los switches de core aparecen en el centro (equidistantes de todos) y los switches de acceso en la periferia.

**Qué revela:** los nodos de mayor intermediación (círculos más grandes) son switches de core y WAN, confirmando que son los cuellos de botella de la red. Los switches de acceso (azules, círculos pequeños) forman la periferia densa; los de core (rojos) y los nodos WAN (morados) ocupan la zona central.

---

## Preguntas del enunciado — Respuestas

### P1 — Preguntas clave del enunciado

**¿Por qué el clustering medio es tan bajo comparado con el de una red social?**

Porque la topología jerárquica en estrella prohíbe triángulos por diseño. En una red social si A conoce a B y A conoce a C, es probable que B y C también se conozcan. En UCuenca, si el switch A84 está conectado al switch de agregación D107, y el switch A85 también está conectado a D107, A84 y A85 **no** se conectan entre sí (eso crearía un ciclo indeseado en la capa de acceso). El enunciado lo advierte: el clustering bajo es la huella matemática de la estrella jerárquica.

**¿Por qué la asortatividad es negativa, y qué dice sobre la jerarquía?**

$r = -0.1468$ porque los hubs (grado 10–17: switches de core/agregación) se conectan exclusivamente con nodos de bajo grado (grado 1–3: switches de acceso). La jerarquía core–agregación–acceso impide la conexión directa entre dos nodos del mismo nivel, lo que matemáticamente produce disasortatividad. En redes sociales, los nodos de alto grado tienden a conectarse entre sí ($r > 0$: redes asortativas).

**¿Coinciden los nodos más centrales por grado con los de intermediación?**

Parcialmente. `DATCC-2A-C3` encabeza ambos rankings porque es el switch de core del Campus Central: más conexiones implica más caminos que lo atraviesan. Pero `CPAR-C10` (switch de core de Paraíso) tiene la segunda mayor betweenness con un grado relativo menor, porque **todos** los flujos que entran o salen de Paraíso pasan por él. La betweenness captura "cuello de botella estructural"; el grado captura "número de vecinos": no son lo mismo.

**¿Se observa redundancia core–agregación en Balzay y Paraíso?**

- **Balzay: SÍ.** 4 de 5 switches de agregación están doblemente conectados a `DT-0A-C12` y `DT-0A-C13`.
- **Paraíso: NO.** El informe técnico afirma redundancia, pero los datos muestran un único switch de core (`CPAR-C10`). Los "dobles enlaces" son LAG (agregación de puertos), no redundancia de núcleo.
- **Campus Central: SÍ**, y más de lo que el informe declara: 13/14 switches de agregación tienen doble enlace a `DATCC-2A-C2` y `DATCC-2A-C3`.

### P2 — Preguntas clave del enunciado

**¿Qué propiedades de la red UCuenca NO se explican por su secuencia de grados?**

El **clustering** y la **distancia media** no son reproducibles por el CM. La secuencia de grados explica la disasortatividad ($r$ del CM ≈ $r$ real) pero no la organización jerárquica que alarga las distancias ni la ausencia de triángulos que baja el clustering.

**¿Por qué una red de infraestructura física se parece o no a un modelo BA?**

Se parece superficialmente (cola pesada, clustering bajo, asortatividad negativa) pero el mecanismo generativo es opuesto. BA es orgánico e incremental; UCuenca es planificada y jerárquica. La similitud en métricas es coincidencia, no evidencia de crecimiento preferencial.

---

*Documento generado automáticamente a partir de los scripts `src/problema1.py` y `src/problema2.py`.*  
*Última actualización: Fase 1 completa.*
