# Dijkstra en Grafos de Ataque — Explicación del Proyecto

## Escenario y pregunta central

El proyecto responde a una pregunta concreta de ciberseguridad:

> **Si un adversario intenta comprometer una red usando técnicas reales documentadas,
> ¿qué secuencia de pasos representa el menor esfuerzo para él? ¿Y qué técnica,
> si se defiende correctamente, corta la mayor cantidad de rutas posibles de ataque?**

La idea es tratar los ataques informáticos como un **problema de camino mínimo en grafos**.
Un grafo de ataque tiene nodos que representan técnicas de ataque, y aristas que representan
la posibilidad de progresar de una técnica a la siguiente. Los pesos de las aristas codifican
cuánto le cuesta al atacante usar cada técnica: más defensas documentadas = mayor costo.

---

## Caso de estudio: SolarWinds Compromise

### Escenario

SolarWinds Compromise (2019-2020) es uno de los ataques más documentados de la historia.
El grupo APT29 comprometió la cadena de suministro de SolarWinds Orion, afectando a
~18,000 organizaciones incluyendo agencias del gobierno de EE.UU. MITRE ATT&CK lo
documentó exhaustivamente como campaña G0118, registrando con evidencia técnica cada
técnica que el atacante usó. Los datos son **100% reales**.

La pregunta de investigación concreta es:

> **¿Cuál es la secuencia de técnicas de menor resistencia defensiva desde el
> acceso inicial hasta el impacto en SolarWinds? ¿Y qué técnicas son los cuellos
> de botella universales del grafo de ataque real?**

### De dónde salen los datos

La fuente es el **bundle STIX 2.1 de ATT&CK Enterprise** (~40 MB de JSON), descargado
desde el repositorio oficial de MITRE en GitHub. Este bundle contiene:

- Todas las técnicas de ATT&CK (con nombre, descripción, tácticas asociadas)
- Las relaciones entre campañas y técnicas (qué técnicas usó qué grupo)
- Las mitigaciones documentadas para cada técnica

El pipeline (`src/dataset_real.py`) descarga el bundle y lo cachea en `data/mitre_attack.json`.
De los ~14,000 objetos del bundle, extrae únicamente los **71 documentados para SolarWinds
Compromise** (campaña G0118).

### Cómo se usan los datos: los pesos

La fórmula de peso no usa CVEs. El peso refleja la **resistencia defensiva** de cada técnica
según ATT&CK:

```
w = max(0.05, n_mitigaciones / max_mitigaciones)
```

Donde `n_mitigaciones` es el número de mitigaciones que ATT&CK documenta para esa técnica
y `max_mitigaciones = 8` (el máximo entre las 71 técnicas de la campaña). El piso de 0.05
evita pesos cero (Dijkstra requiere pesos no negativos).

Más controles de defensa documentados = mayor costo para el atacante = mayor resistencia.
Una técnica sin mitigaciones documentadas tiene peso mínimo (0.05): no hay controles
establecidos para detectarla o prevenirla, así que es trivial para el adversario.

Pesos reales de las técnicas en la ruta crítica encontrada:

| Técnica    | Nombre                              | Mitig./max | Peso  |
|------------|-------------------------------------|------------|-------|
| T1078.003  | Local Accounts                      | 4/8        | 0.500 |
| T1606.001  | Web Cookies                         | 2/8        | 0.250 |
| T1550.004  | Web Session Cookie                  | 1/8        | 0.125 |
| T1016.001  | Internet Connection Discovery       | 0/8        | 0.050 |
| T1074.002  | Remote Data Staging                 | 0/8        | 0.050 |
| T1665      | Hide Infrastructure                 | 0/8        | 0.050 |
| T1048.002  | Exfiltración cifrada no-C2          | 4/8        | 0.500 |

### Cómo se forma el grafo

El grafo tiene **73 nodos** y **653 aristas**.

**Nodos**: las 71 técnicas ATT&CK documentadas para SolarWinds, más dos nodos de frontera:
`ATTACKER` (punto de entrada) e `IMPACT` (objetivo logrado).

**Aristas**: representan la **progresión táctica real del atacante**. Si SolarWinds usó
la técnica A (en táctica i) y la técnica B (en táctica i+1), existe la arista A→B. Las
15 tácticas están ordenadas según la kill chain:

```
reconnaissance → resource-development → initial-access → execution →
persistence → privilege-escalation → defense-impairment → stealth →
credential-access → discovery → lateral-movement → collection →
command-and-control → exfiltration → impact
```

`ATTACKER` se conecta a todos los nodos de la primera táctica. `IMPACT` recibe aristas
desde todos los nodos de la última. Esto crea un grafo dirigido que modela todas las
progresiones posibles dentro de la campaña real.

### Qué representa cada elemento del grafo

| Elemento   | Representa en el mundo real                                              |
|------------|--------------------------------------------------------------------------|
| Nodo       | Una técnica de ataque real usada por APT29 en SolarWinds                 |
| Arista A→B | La posibilidad de progresar de la técnica A a la B en la kill chain      |
| Peso w     | Resistencia defensiva de esa técnica (más peso = más difícil de explotar)|
| Camino     | Una secuencia completa de ataque desde acceso inicial hasta impacto      |
| Costo total| La resistencia defensiva acumulada que el atacante debe superar          |

---

## Métodos algorítmicos

El proyecto implementa cuatro algoritmos para responder distintas preguntas sobre el mismo grafo:

### Dijkstra — "¿Cuál es LA ruta óptima?"

Camino mínimo de fuente única con heap binario. Solo requiere pesos no negativos.

- **Complejidad**: O((V+E)·log V) = O((73+653)·log 73) ≈ 4,500 operaciones
- **Tiempo real**: 0.98 ms en el grafo SolarWinds
- **Salida**: 1 ruta + distancias acumuladas desde `ATTACKER`
- **Limitación**: reporta una sola ruta, aunque existan varias óptimas equivalentes

### Floyd-Warshall — "¿Qué nodo bloquear?"

Todos los pares de caminos mínimos. Itera sobre todos los posibles intermedios k:
`d[i][j] = min(d[i][j], d[i][k] + d[k][j])`.

- **Complejidad**: O(V³) = O(73³) = 389,017 operaciones
- **Tiempo real**: 5.4 ms (5× más lento que Dijkstra, pero aún trivial para 73 nodos)
- **Salida**: matriz 73×73 con distancia mínima entre todo par (i,j)
- **Uso**: a partir de la matriz se calcula el **FW-betweenness** de cada nodo: cuántos
  pares (i,j) tienen su camino óptimo pasando por ese nodo. Betweenness alto = cuello de
  botella estructural = objetivo defensivo prioritario.
- **Limitación**: O(V³) crece cúbicamente; impracticable para grafos de miles de nodos.

### Algoritmos de validación

Para verificar que las implementaciones propias son correctas:

| Algoritmo           | Por qué se incluye                                              |
|---------------------|-----------------------------------------------------------------|
| Bellman-Ford propio | Acepta pesos negativos; sirve de cross-check independiente      |
| Dijkstra NetworkX   | Implementación de referencia de la industria                    |
| BFS sin pesos       | Caso base: qué pasa si el atacante ignora las defensas          |

---

## Resultados

### Ruta crítica (Dijkstra)

```
ATTACKER → T1078.003 → T1606.001 → T1016.001 → T1550.004 → T1074.002 → T1665 → T1048.002 → IMPACT
```

| Paso | Técnica    | Nombre                              | Táctica             | Peso  | Costo acum. |
|------|------------|-------------------------------------|---------------------|-------|-------------|
| 0    | ATTACKER   | —                                   | —                   | —     | 0.000       |
| 1    | T1078.003  | Local Accounts                      | persistence/stealth | 0.500 | 0.500       |
| 2    | T1606.001  | Web Cookies                         | credential-access   | 0.250 | 0.750       |
| 3    | T1016.001  | Internet Connection Discovery       | discovery           | 0.050 | 0.800       |
| 4    | T1550.004  | Web Session Cookie                  | lateral-movement    | 0.125 | 0.925       |
| 5    | T1074.002  | Remote Data Staging                 | collection          | 0.050 | 0.975       |
| 6    | T1665      | Hide Infrastructure                 | command-and-control | 0.050 | 1.025       |
| 7    | T1048.002  | Exfiltración cifrada no-C2          | exfiltration        | 0.500 | 1.525       |
| 8    | IMPACT     | —                                   | —                   | 0.010 | **1.535**   |

El bajo costo total (1.535) refleja que la mayoría de las técnicas en la ruta tienen 0 o
muy pocas mitigaciones documentadas. El atacante racional elige exactamente estas técnicas
porque son las que el defensor tiene menos cubiertas.

### Rutas óptimas equivalentes (Floyd-Warshall + enumeración)

Dijkstra reporta 1 ruta. La enumeración a partir de la matriz FW revela que existen
**7 rutas distintas con exactamente el mismo costo 1.535**. El atacante tiene 7 caminos
igualmente eficientes.

De los 71 nodos técnicos, **6 aparecen en TODAS las 7 rutas** — son los nodos obligatorios.
Bloquear cualquiera de los seis garantiza que no existe ninguna de las 7 rutas óptimas:

| Nodo obligatorio | Nombre                              | FW-betweenness |
|------------------|-------------------------------------|----------------|
| T1606.001        | Web Cookies                         | 1,044          |
| T1550.004        | Web Session Cookie                  | 702            |
| T1074.002        | Remote Data Staging                 | 420            |
| T1078.003        | Local Accounts                      | 357            |
| T1665            | Hide Infrastructure                 | 132            |
| T1048.002        | Exfiltración cifrada no-C2          | 71             |

T1016.001 está en la ruta que Dijkstra encontró pero **no es obligatorio**: en algunas de
las 7 rutas equivalentes aparece T1057 (Process Discovery) en su lugar. Ambos tienen el
mismo peso 0.05. Defender solo T1016.001 no elimina todas las rutas óptimas.

### FW-betweenness: cuellos de botella globales

El FW-betweenness mide cuántos pares (i,j) del grafo completo tienen su camino óptimo
pasando por cada nodo. Los 5 primeros entre las 71 técnicas:

| Rk | Técnica    | Nombre                              | FW-Betweenness | % del máximo |
|----|------------|-------------------------------------|----------------|--------------|
| 1  | T1606.001  | Web Cookies                         | 1,044          | 100.0%       |
| 2  | T1018      | Remote System Discovery             | 836            | 80.1%        |
| 3  | T1069.002  | Domain Groups                       | 836            | 80.1%        |
| 4  | T1016.001  | Internet Connection Discovery       | 836            | 80.1%        |
| 5  | T1550.004  | Web Session Cookie                  | 702            | 67.2%        |

La correlación de Spearman entre FW-betweenness y la betweenness estándar de NetworkX
(algoritmo de Brandes) es **ρ = 0.973**, validando que el FW-betweenness es consistente
con la medida clásica de centralidad.

### Cross-validación Dijkstra ↔ Floyd-Warshall

```
d_Dijkstra(ATTACKER → IMPACT) = FW[ATTACKER][IMPACT] = 1.535 ✓
```

Dos algoritmos completamente distintos, implementaciones independientes, mismo resultado.

### Comparación de algoritmos

| Algoritmo         | Costo | Tiempo   | Ruta idéntica a Dijkstra           |
|-------------------|-------|----------|------------------------------------|
| Dijkstra propio   | 1.535 | 0.22 ms  | — (referencia)                     |
| Bellman-Ford      | 1.535 | 0.63 ms  | No (T1057 en paso 3, igual peso)   |
| NetworkX Dijkstra | 1.535 | 0.90 ms  | Sí                                 |
| BFS sin pesos     | 2.925 | 0.04 ms  | No (+90.55% de sobrecoste)         |

El BFS sin pesos halla la ruta más corta en saltos, pero su costo real es 2.925 — un
sobrecoste del **+90.55%**. Esto demuestra que los pesos son informativos: ignorarlos
lleva al modelo de amenaza a una ruta significativamente peor para el atacante.

### Análisis de sensibilidad de pesos

| Esquema         | Descripción                         | Costo | Jaccard vs base |
|-----------------|-------------------------------------|-------|-----------------|
| Base (lineal)   | w = max(0.05, n_mit/8) — canónico   | 1.535 | 1.000           |
| −20% (×0.8)     | Todos los pesos × 0.8               | 1.260 | 1.000           |
| +20% (×1.2)     | Todos los pesos × 1.2               | 1.840 | 1.000           |
| Binario         | w ∈ {0, 1} según mediana            | 1.910 | 0.125           |

Los esquemas ±20% producen exactamente la misma ruta (Jaccard = 1.0): el modelo es
robusto a variaciones moderadas. Solo el esquema binario, que destruye la información
ordinal, produce una ruta diferente (solo 2 nodos compartidos de 16 en la unión = 0.125).

---

## Interpretación defensiva

Dijkstra y Floyd-Warshall responden dos preguntas complementarias:

**Dijkstra** → *Si el atacante opera hoy de forma racional, ¿qué ruta toma?*
La secuencia T1078.003 → T1606.001 → T1016.001 → T1550.004 → T1074.002 → T1665 → T1048.002.

**Floyd-Warshall** → *¿Qué técnica, si se defiende, elimina la mayor cantidad de rutas
posibles en el grafo completo?*
T1606.001 (1,044 rutas), T1550.004 (702), T1074.002 (420).

La concordancia en **T1606.001** es el hallazgo más robusto: está en la ruta crítica de
Dijkstra (resultado táctico) Y es el nodo con mayor FW-betweenness (resultado estratégico).
Ningún otro nodo aparece tan claramente en ambos análisis.

La **recomendación defensiva** es bloquear cualquiera de los 6 nodos obligatorios para
eliminar el 100% de las rutas óptimas. T1016.001 no es suficiente por sí solo porque tiene
un sustituto equivalente (T1057, mismo peso). T1606.001 es la prioridad máxima.
