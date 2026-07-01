# Dijkstra en Grafos de Ataque — Explicación del Proyecto

## Escenario y pregunta central

El proyecto responde a una pregunta concreta de ciberseguridad:

> **Si un adversario intenta comprometer una red usando técnicas reales documentadas,
> ¿qué secuencia de pasos representa el menor esfuerzo para él? ¿Y qué técnica,
> si se defiende correctamente, corta la mayor cantidad de rutas posibles de ataque?**

La idea es tratar los ataques informáticos como un **problema de camino mínimo en grafos**.
Un grafo de ataque tiene nodos que representan técnicas o sistemas, y aristas que representan
la posibilidad de pasar de una técnica a la siguiente. Los pesos de las aristas codifican
cuánto le cuesta al atacante usar cada técnica: más defensas documentadas = mayor costo.

Dijkstra halla la ruta de menor costo. Floyd-Warshall responde cuántas rutas de ataque
pasan por cada nodo. Juntos, los dos algoritmos dan una respuesta táctica y una estratégica.

El proyecto tiene **dos análisis**: uno con una red sintética controlada (para demostrar
el concepto) y uno con datos 100% reales del caso SolarWinds Compromise.

---

## Análisis 1 — Red sintética con CVEs reales

### Escenario y objetivo

Se modela una red corporativa ficticia pero plausible. El objetivo es demostrar el concepto
de grafo de ataque de forma controlada, donde los pesos están dados por vulnerabilidades
reales del catálogo CVE. Los datos son **parcialmente sintéticos**: la topología de la red
es inventada, pero los CVEs y sus puntajes son reales y provienen del NVD (NIST).

### De dónde salen los datos

Un **CVE** (Common Vulnerabilities and Exposures) es un identificador oficial de una
vulnerabilidad de software real. Lo asigna el NIST/MITRE. Cada CVE tiene un puntaje
**CVSS** (0–10) que mide su gravedad:

| Rango CVSS | Nivel    |
|------------|----------|
| 9.0 – 10.0 | CRITICAL |
| 7.0 – 8.9  | HIGH     |
| 4.0 – 6.9  | MEDIUM   |
| 0.1 – 3.9  | LOW      |

El pipeline descarga 20 CVEs reales desde la API pública del NVD (`nvd.nist.gov`).
Si no hay conexión, usa un dataset embebido. Los CVEs cubren cinco capas de infraestructura:

| CVE            | Nombre popular                  | CVSS | Capa     |
|----------------|---------------------------------|------|----------|
| CVE-2021-44228 | Apache Log4j (Log4Shell)        | 10.0 | web      |
| CVE-2017-5638  | Apache Struts 2                 | 10.0 | web      |
| CVE-2020-1472  | Microsoft Netlogon (Zerologon)  | 10.0 | host     |
| CVE-2018-13379 | Fortinet FortiOS SSL VPN        | 9.8  | perimeter|
| CVE-2019-0708  | Microsoft RDP (BlueKeep)        | 9.8  | service  |
| CVE-2021-26855 | Microsoft Exchange (ProxyLogon) | 9.8  | service  |
| CVE-2022-0847  | Linux Kernel (Dirty Pipe)       | 7.8  | host     |
| CVE-2012-2122  | MySQL/MariaDB auth bypass       | 5.9  | data     |
| ...            | (20 CVEs en total)              |      |          |

### Cómo se forma el grafo

La red tiene 6 capas ordenadas de afuera hacia adentro:

```
INTERNET → Perímetro → Web/App → Servicios → Hosts/SO → Datos
```

**Nodos**: hosts y servicios concretos (`FW-VPN`, `WEB-01`, `DC-01`, `DB-CRITICAL`…).

**Aristas**: solo entre capas consecutivas. Para cada nodo destino se asigna aleatoriamente
un CVE de su capa y se crea la arista. Se añaden atajos manuales basados en rutas de ataque
reales conocidas (`SMB-FILES → DC-01`, `DC-01→ DB-CRITICAL`, etc.). La semilla es 42
para reproducibilidad.

**Pesos**: `w = 10 - CVSS`. Vulnerabilidades más críticas tienen menor costo para el
atacante, representando el camino de menor resistencia.

| CVSS | Peso w | Interpretación               |
|------|--------|------------------------------|
| 10.0 | 0.1    | Trivial para el atacante      |
| 9.8  | 0.2    | Casi sin esfuerzo             |
| 7.5  | 2.5    | Moderado                      |
| 5.9  | 4.1    | Requiere más trabajo          |

### Resultado

Dijkstra encuentra la ruta que encadena los CVEs más críticos (CVSS más alto), minimizando
el esfuerzo total del atacante. El resultado muestra que el atacante racional evita siempre
los nodos con vulnerabilidades moderadas o bajas, aunque existan caminos hacia el objetivo.

---

## Análisis 2 — Caso real: SolarWinds Compromise

### Escenario

SolarWinds Compromise (2019-2020) es uno de los ataques más documentados de la historia.
El grupo APT29 comprometió la cadena de suministro de SolarWinds Orion, afectando a
~18,000 organizaciones incluyendo agencias del gobierno de EE.UU. MITRE ATT&CK lo
documentó exhaustivamente como campaña G0118, registrando con evidencia técnica cada
técnica que el atacante usó. Los datos son **100% reales**: provienen directamente del
bundle oficial de MITRE ATT&CK en formato STIX 2.1.

La pregunta de investigación es:

> **¿Cuál es la secuencia de técnicas de menor resistencia defensiva desde el
> acceso inicial hasta el impacto? ¿Y qué técnicas son los cuellos de botella
> universales del grafo de ataque real de SolarWinds?**

### De dónde salen los datos

La fuente es el **bundle STIX 2.1 de ATT&CK Enterprise** (~40 MB de JSON), descargado
desde el repositorio oficial de MITRE en GitHub. Este bundle contiene:

- Todas las técnicas de ATT&CK (con nombre, descripción, tácticas asociadas)
- Las relaciones entre campañas y técnicas (qué técnicas usó qué grupo)
- Las mitigaciones documentadas para cada técnica
- Los objetos de campaña con su período y descripción

El pipeline los descarga con `src/dataset_real.py` y cachea en `data/mitre_attack.json`.
De los ~14,000 objetos del bundle, se extraen únicamente los 71 documentados para
SolarWinds Compromise.

### Cómo se usa el dato: los pesos

La fórmula de peso **no usa CVEs**. El problema con mapear CVE↔técnica ATT&CK para una
campaña específica es que esa asociación no está en el bundle STIX y requiere juicio manual
no reproducible. En su lugar, el peso refleja la **resistencia defensiva** de cada técnica
según ATT&CK:

```
w = max(0.05, n_mitigaciones / max_mitigaciones)
```

Donde:
- `n_mitigaciones` = número de mitigaciones que ATT&CK documenta para esa técnica
- `max_mitigaciones` = 8 (el máximo entre las 71 técnicas de la campaña)
- El piso de 0.05 evita pesos cero (Dijkstra requiere pesos no negativos)

La lógica es directa: más controles de defensa documentados = mayor costo para el atacante
= mayor resistencia. Una técnica sin mitigaciones documentadas tiene el peso mínimo (0.05)
porque no hay controles establecidos para detectarla o prevenirla.

Pesos reales de las técnicas en la ruta crítica:

| Técnica    | Nombre                              | Mitig. | Peso  |
|------------|-------------------------------------|--------|-------|
| T1078.003  | Local Accounts                      | 4/8    | 0.500 |
| T1606.001  | Web Cookies                         | 2/8    | 0.250 |
| T1550.004  | Web Session Cookie                  | 1/8    | 0.125 |
| T1016.001  | Internet Connection Discovery       | 0/8    | 0.050 |
| T1074.002  | Remote Data Staging                 | 0/8    | 0.050 |
| T1665      | Hide Infrastructure                 | 0/8    | 0.050 |
| T1048.002  | Exfiltración cifrada no-C2          | 4/8    | 0.500 |

### Cómo se forma el grafo

El grafo tiene **73 nodos** y **653 aristas**.

**Nodos**: cada una de las 71 técnicas ATT&CK documentadas para SolarWinds, más dos nodos
de frontera: `ATTACKER` (punto de entrada) e `IMPACT` (objetivo logrado).

**Aristas**: representan la **progresión táctica real del atacante**. Si SolarWinds usó
técnicas A (en táctica i) y B (en táctica i+1), existe la arista A→B. Las 15 tácticas
están ordenadas según la kill chain:

```
reconnaissance → resource-development → initial-access → execution →
persistence → privilege-escalation → defense-impairment → stealth →
credential-access → discovery → lateral-movement → collection →
command-and-control → exfiltration → impact
```

`ATTACKER` se conecta a todos los nodos de la primera táctica (reconnaissance). `IMPACT`
recibe aristas desde todos los nodos de la última táctica (impact). Esto crea un grafo
dirigido que modela todas las progresiones posibles dentro de la campaña real.

### Qué representa cada elemento del grafo

| Elemento   | Representa en el mundo real                                              |
|------------|--------------------------------------------------------------------------|
| Nodo       | Una técnica de ataque real usada por APT29 en SolarWinds                 |
| Arista A→B | La posibilidad de pasar de la técnica A a la B siguiendo la kill chain   |
| Peso w     | Cuánta resistencia defensiva tiene esa técnica (más peso = más difícil)  |
| Camino     | Una secuencia completa de ataque desde acceso inicial hasta impacto      |
| Costo total| La resistencia defensiva acumulada que el atacante debe superar          |

Un camino de **menor costo** es la secuencia que el atacante racional preferiría: aquella
que atraviesa las técnicas con menos controles de defensa documentados.

---

## Métodos algorítmicos

El proyecto implementa cuatro algoritmos para responder distintas preguntas, todos sobre
el mismo grafo:

### Dijkstra — "¿Cuál es LA ruta óptima?"

Algoritmo de camino mínimo de fuente única. Explora nodos en orden de distancia creciente
usando una cola de prioridad (heap binario). Solo funciona con pesos no negativos.

- **Complejidad**: O((V+E)·log V) = O((73+653)·log 73) ≈ **4,500 operaciones**
- **Tiempo real**: 0.98 ms en el grafo SolarWinds
- **Salida**: distancia mínima desde `ATTACKER` a todos los nodos, y el predecesor de cada uno (para reconstruir la ruta)
- **Limitación**: reporta una sola ruta óptima, aunque existan varias equivalentes

### Floyd-Warshall — "¿Qué nodo bloquear?"

Algoritmo de todos los pares de caminos mínimos. Itera sobre todos los posibles nodos
intermedios k y relaja todas las distancias: `d[i][j] = min(d[i][j], d[i][k] + d[k][j])`.

- **Complejidad**: O(V³) = O(73³) = **389,017 operaciones**
- **Tiempo real**: 5.4 ms (5× más lento que Dijkstra, pero 5.4 ms sigue siendo trivial)
- **Salida**: matriz 73×73 con distancia mínima entre todo par (i,j)
- **Uso en el proyecto**: a partir de la matriz se calcula el **FW-betweenness** de cada nodo:
  cuántos pares (i,j) tienen su camino óptimo pasando por ese nodo. Nodo con betweenness
  alto = nodo que aparece en muchas rutas óptimas = cuello de botella estructural.
- **Limitación**: O(V³) crece cúbicamente. Para grafos de 1,000 nodos serían 10⁹ operaciones;
  para esos casos se prefiere Dijkstra repetido N veces.

### Algoritmos de validación

Para verificar que las implementaciones propias son correctas, se corre el mismo caso con
tres implementaciones independientes:

| Algoritmo          | Implementación  | Por qué se incluye                                           |
|--------------------|-----------------|--------------------------------------------------------------|
| Dijkstra propio    | `src/analisis_real.py` | Implementación desde cero con heap                   |
| Bellman-Ford propio| `src/analisis_real.py` | Acepta pesos negativos; sirve de cross-check         |
| Dijkstra NetworkX  | biblioteca NetworkX    | Implementación de referencia de la industria         |
| BFS sin pesos      | `src/analisis_real.py` | Caso base: qué pasa si ignoramos los pesos           |

---

## Resultados del Análisis 2 (SolarWinds)

### Ruta crítica — Dijkstra

La secuencia de técnicas de menor resistencia defensiva desde el acceso inicial hasta
el impacto es:

```
ATTACKER → T1078.003 → T1606.001 → T1016.001 → T1550.004 → T1074.002 → T1665 → T1048.002 → IMPACT
```

| Paso | Técnica    | Nombre                              | Táctica            | Peso  | Costo acum. |
|------|------------|-------------------------------------|--------------------|-------|-------------|
| 0    | ATTACKER   | —                                   | —                  | —     | 0.000       |
| 1    | T1078.003  | Local Accounts                      | persistence/stealth| 0.500 | 0.500       |
| 2    | T1606.001  | Web Cookies                         | credential-access  | 0.250 | 0.750       |
| 3    | T1016.001  | Internet Connection Discovery       | discovery          | 0.050 | 0.800       |
| 4    | T1550.004  | Web Session Cookie                  | lateral-movement   | 0.125 | 0.925       |
| 5    | T1074.002  | Remote Data Staging                 | collection         | 0.050 | 0.975       |
| 6    | T1665      | Hide Infrastructure                 | command-and-control| 0.050 | 1.025       |
| 7    | T1048.002  | Exfiltración cifrada no-C2          | exfiltration       | 0.500 | 1.525       |
| 8    | IMPACT     | —                                   | —                  | 0.010 | **1.535**   |

**Costo total óptimo: 1.535**. Esto significa que el atacante racional que sigue esta
secuencia enfrenta una resistencia defensiva acumulada de solo 1.535 (en una escala donde
el máximo por técnica es 1.0). En la práctica, el bajo costo se debe a que la mayoría
de las técnicas en la ruta tienen 0 o muy pocas mitigaciones documentadas.

### Rutas alternativas equivalentes — Floyd-Warshall

Dijkstra reporta una sola ruta. Pero la enumeración a partir de la matriz FW revela que
existen **7 rutas distintas con exactamente el mismo costo 1.535**. Esto es importante:
el atacante tiene 7 caminos igualmente eficientes, no uno solo.

De los 71 nodos técnicos, **13 aparecen en al menos una ruta óptima**, pero solo **6
aparecen en TODAS las 7 rutas** — son los nodos obligatorios:

| Nodo obligatorio | Nombre                              | FW-betweenness |
|------------------|-------------------------------------|----------------|
| T1606.001        | Web Cookies                         | 1,044          |
| T1550.004        | Web Session Cookie                  | 702            |
| T1074.002        | Remote Data Staging                 | 420            |
| T1078.003        | Local Accounts                      | 357            |
| T1665            | Hide Infrastructure                 | 132            |
| T1048.002        | Exfiltración cifrada no-C2          | 71             |

El nodo T1016.001 está en la ruta que Dijkstra encontró, pero **no es obligatorio**: en
algunas de las 7 rutas óptimas aparece T1057 (Process Discovery) en su lugar. Ambos tienen
el mismo peso 0.05 (cero mitigaciones), por lo que son intercambiables para el atacante.

### FW-betweenness: cuellos de botella globales

El FW-betweenness cuenta cuántos pares (i,j) del grafo completo tienen su camino óptimo
pasando por cada nodo. Los 5 primeros de las 71 técnicas:

| Rk | Técnica    | Nombre                              | FW-Betweenness | % del máximo |
|----|------------|-------------------------------------|----------------|--------------|
| 1  | T1606.001  | Web Cookies                         | 1,044          | 100.0%       |
| 2  | T1018      | Remote System Discovery             | 836            | 80.1%        |
| 3  | T1069.002  | Domain Groups                       | 836            | 80.1%        |
| 4  | T1016.001  | Internet Connection Discovery       | 836            | 80.1%        |
| 5  | T1550.004  | Web Session Cookie                  | 702            | 67.2%        |

T1606.001 domina con 1,044 rutas óptimas pasando por él. Esto no solo lo convierte en el
cuello de botella #1 del grafo, sino que coincide exactamente con el resultado de Dijkstra.

La correlación de Spearman entre FW-betweenness y la betweenness estándar de NetworkX
(algoritmo de Brandes) es **ρ = 0.973**, lo que confirma que el FW-betweenness basado en
distancias es consistente con la medida clásica de centralidad.

### Comparación de algoritmos de resolución

Los cuatro algoritmos producen resultados coherentes entre sí:

| Algoritmo        | Costo   | Nodos en ruta | Tiempo    | Ruta idéntica a Dijkstra |
|------------------|---------|---------------|-----------|--------------------------|
| Dijkstra propio  | 1.535   | 9             | 0.22 ms   | — (referencia)           |
| Bellman-Ford     | 1.535   | 9             | 0.63 ms   | No (T1016.001 vs T1057)  |
| NetworkX Dijkstra| 1.535   | 9             | 0.90 ms   | Sí                       |
| BFS sin pesos    | 2.925   | 9             | 0.04 ms   | No                       |

**Dijkstra vs Bellman-Ford**: ambos hallan el mismo costo óptimo (1.535), pero la ruta
difiere en el paso 3: Dijkstra elige T1016.001 y Bellman-Ford elige T1057. Ambas técnicas
tienen exactamente el mismo peso (0.05), por lo que son óptimas equivalentes. La diferencia
se debe al orden de exploración del heap. Esto es correcto y esperado.

**BFS sin pesos**: halla la ruta más corta en saltos, pero su costo acumulado real es
**2.925**, un sobrecoste del **+90.55%** respecto al óptimo. Esto demuestra que los pesos
son informativos: ignorarlos lleva al atacante (o al defensor modelando al atacante) a
elegir una ruta significativamente más costosa. La ruta BFS comienza por T1078.002
(Domain Accounts) en lugar de T1078.003, entrando a la red por técnicas con más mitigaciones.

### Cross-validación Dijkstra ↔ Floyd-Warshall

El valor FW[ATTACKER][IMPACT] de la matriz completa es exactamente **1.535**, idéntico al
resultado de Dijkstra. Esto es la cross-validación definitiva: dos algoritmos completamente
distintos, con implementaciones independientes, confirman el mismo costo óptimo.

```
d_Dijkstra(ATTACKER → IMPACT) = FW[ATTACKER][IMPACT] = 1.535 ✓
```

### Análisis de sensibilidad de pesos

Para verificar que los resultados no dependen críticamente de los valores exactos de los
pesos, se corre Dijkstra con cuatro esquemas:

| Esquema           | Descripción                        | Costo | Jaccard vs base |
|-------------------|------------------------------------|-------|-----------------|
| Base (lineal)     | w = max(0.05, n_mit/8) — canónico  | 1.535 | 1.000           |
| −20% (×0.8)       | Todos los pesos × 0.8              | 1.260 | 1.000           |
| +20% (×1.2)       | Todos los pesos × 1.2              | 1.840 | 1.000           |
| Binario (umbral)  | w ∈ {0, 1} según mediana           | 1.910 | 0.125           |

Los esquemas ±20% producen **exactamente la misma ruta** (Jaccard = 1.0). El modelo es
robusto a variaciones moderadas de los pesos. Solo el esquema binario, que destruye la
información ordinal de los pesos, produce una ruta completamente diferente (13 pasos,
Jaccard = 0.125 = solo 2 nodos compartidos de 16 en la unión). Esto valida que la
granularidad de los pesos tiene impacto real en el resultado, pero el resultado es estable
dentro de un rango razonable.

---

## Interpretación defensiva

Los resultados de Dijkstra y Floyd-Warshall juntos responden dos preguntas complementarias:

**Dijkstra responde**: *si el atacante racional opera hoy, ¿qué ruta toma?*
→ La secuencia T1078.003 → T1606.001 → T1016.001 → T1550.004 → T1074.002 → T1665 → T1048.002

**Floyd-Warshall responde**: *¿qué técnica, si se defiende, elimina la mayor cantidad
de rutas de ataque posibles en el grafo completo?*
→ T1606.001 (Web Cookies, 1,044 rutas), T1550.004 (702), T1074.002 (420)

La concordancia entre ambos análisis en T1606.001 es el hallazgo más robusto del proyecto:
esta técnica no es solo la que aparece en la ruta que Dijkstra encuentra (resultado táctico),
sino también la que aparece en la mayor cantidad de rutas óptimas de todo el grafo (resultado
estratégico). Su eliminación impacta simultáneamente la mejor ruta disponible y 1,044 rutas
alternativas del espacio de ataque.

La **recomendación defensiva principal** es bloquear cualquiera de los **6 nodos obligatorios**
(T1606.001, T1550.004, T1074.002, T1078.003, T1665, T1048.002). Bloquear cualquiera de los
seis garantiza que no existe ninguna de las 7 rutas óptimas. La prioridad debe ser T1606.001
porque además es el #1 en betweenness global.

El nodo T1016.001 (Internet Connection Discovery), que aparece en la ruta Dijkstra, **no es
obligatorio** porque tiene un sustituto equivalente (T1057). Defender solo T1016.001 no es
suficiente: el atacante simplemente usaría T1057 para alcanzar el mismo costo.

---

## Comparación entre los dos análisis

| Aspecto         | Análisis 1 (sintético)                         | Análisis 2 (SolarWinds)                              |
|-----------------|------------------------------------------------|------------------------------------------------------|
| **Datos**       | CVEs del NVD, red ficticia                     | Bundle STIX 2.1 de MITRE ATT&CK                      |
| **Son reales**  | CVEs sí, topología no                          | Ambos 100% reales                                    |
| **Nodos**       | Hosts/servicios (`FW-VPN`, `DC-01`…)           | Técnicas ATT&CK (`T1078`, `T1606.001`…)              |
| **Aristas**     | Regla de capas + atajos manuales               | Progresión táctica real documentada                  |
| **Pesos**       | `10 - CVSS` (por arista/CVE)                   | `max(0.05, n_mit/8)` (por nodo/técnica)              |
| **Tamaño grafo**| 11 nodos, ~20 aristas                          | 73 nodos, 653 aristas                                |
| **Algoritmos**  | Dijkstra                                       | Dijkstra + Floyd-Warshall + BF + BFS + NetworkX      |
| **Resultado**   | Demuestra que la ruta evita CVEs bajos         | Ruta crítica real, 7 óptimas, 6 obligatorios         |
| **Objetivo**    | Demostrar el concepto                          | Responder pregunta de investigación con datos reales |
