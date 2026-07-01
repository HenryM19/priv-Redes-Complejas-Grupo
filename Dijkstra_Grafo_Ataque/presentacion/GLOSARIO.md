# Glosario de términos — Grafos de Ataque · SolarWinds

---

## Conceptos de grafo

**Grafo dirigido**
Red donde las aristas tienen dirección: A→B no implica que exista B→A. En este proyecto
cada arista representa "desde la técnica A se puede progresar a la técnica B en la
kill chain", pero no al revés.

**Nodo**
Elemento del grafo. Aquí cada nodo es una técnica de ataque real documentada por MITRE
ATT&CK, más los dos nodos de frontera: `ATTACKER` (origen) e `IMPACT` (destino final).

**Arista**
Conexión dirigida entre dos nodos. Existe la arista A→B si SolarWinds usó la técnica A
en una táctica y la técnica B en la táctica inmediatamente siguiente.

**Peso (w)**
Valor numérico asociado a cada nodo que mide su resistencia defensiva. Formula canónica:
`w = max(0.05, n_mitigaciones / 8)`. Un nodo con más mitigaciones documentadas tiene peso
más alto, lo que lo hace más costoso de atravesar para el atacante.

**Resistencia defensiva**
Lo que el peso representa en términos de seguridad: qué tan bien defendida está una
técnica según los controles documentados en ATT&CK. Resistencia alta = difícil para el
atacante. Resistencia baja (peso 0.05) = sin mitigaciones conocidas = camino trivial.

**Costo acumulado**
Suma de los pesos de todos los nodos en un camino desde `ATTACKER` hasta un nodo dado.
En la tabla de la ruta crítica, la columna "acum." muestra cuánta resistencia total ha
superado el atacante en cada paso. El costo total de la ruta óptima es **1.535**.

**Ruta crítica**
La secuencia de nodos con el menor costo acumulado desde `ATTACKER` hasta `IMPACT`. Es
la ruta que un adversario racional elegiría. Dijkstra la encuentra en 0.22 ms.

**Camino mínimo**
En teoría de grafos, el camino entre dos nodos cuya suma de pesos es la menor posible.
Este proyecto aplica camino mínimo para encontrar la secuencia de ataque más fácil.

**Densidad del grafo**
Proporción de aristas existentes respecto al máximo posible (n×(n−1) en un grafo
dirigido). El grafo de SolarWinds tiene densidad 0.124: relativamente denso, lo que
implica que existen muchos caminos alternativos entre origen y destino.

**Grado medio**
Promedio del número de aristas que entran o salen de cada nodo. En este grafo es 8.9:
cada técnica está conectada en promedio con casi 9 otras. Un grado alto indica que el
grafo tiene muchas rutas alternativas.

**DAG (Directed Acyclic Graph)**
Grafo dirigido sin ciclos. El grafo de ataque de SolarWinds **no es un DAG**: tiene
ciclos porque es posible regresar a tácticas anteriores. Esto es relevante porque
Floyd-Warshall maneja ciclos de pesos positivos sin problemas, pero Dijkstra también
los maneja siempre que todos los pesos sean no negativos.

**Nodo obligatorio**
Nodo que aparece en **todas** las rutas óptimas equivalentes. Bloquear un nodo
obligatorio garantiza que ninguna de las rutas óptimas queda viable. En este proyecto
hay 6 nodos obligatorios de las 71 técnicas.

---

## Algoritmos

**Dijkstra**
Algoritmo de camino mínimo desde una sola fuente hacia todos los demás nodos del grafo.
Usa una cola de prioridad (heap binario) para expandir siempre el nodo más barato
primero. Complejidad: O((V+E)·log V). Requiere que todos los pesos sean ≥ 0. Responde
la pregunta táctica: "¿qué ruta toma el atacante hoy?".

**Floyd-Warshall**
Algoritmo de camino mínimo entre **todos los pares** de nodos. Itera sobre cada nodo k
como posible intermediario y actualiza: `d[i][j] = min(d[i][j], d[i][k] + d[k][j])`.
Complejidad: O(V³). Produce una matriz n×n de distancias mínimas. Responde la pregunta
estratégica: "¿qué nodo, si se defiende, corta la mayor cantidad de rutas?".

**Heap binario**
Estructura de datos que permite extraer siempre el elemento de menor valor en O(log n).
Dijkstra lo usa para procesar los nodos en orden de costo creciente, lo que garantiza
que cuando un nodo es extraído del heap su distancia ya es la definitiva.

**Bellman-Ford**
Algoritmo de camino mínimo alternativo a Dijkstra. Más lento (O(V·E)) pero acepta pesos
negativos. Se usa aquí como validación cruzada. En este grafo produce el mismo costo
(1.535) que Dijkstra pero puede encontrar un nodo distinto en el paso 3 (T1057 en lugar
de T1016.001) porque ambos tienen exactamente el mismo peso 0.05 — son equivalentes.

**BFS (Breadth-First Search / Búsqueda en anchura)**
Recorre el grafo nivel por nivel sin considerar pesos, encontrando la ruta de menor
número de saltos (no de menor costo). En este proyecto sirve de caso base para demostrar
que ignorar los pesos degrada el resultado: la ruta BFS tiene un costo real de 2.925,
un sobrecoste del +90.55% respecto al óptimo.

**NetworkX**
Biblioteca estándar de Python para análisis de grafos. Se usa su implementación de
Dijkstra como referencia industrial para validar que la implementación propia es correcta.
Ambas producen exactamente la misma ruta y costo.

---

## Métricas de red

**FW-betweenness**
Medida de centralidad calculada a partir de la matriz de Floyd-Warshall. Para cada nodo k
se cuenta cuántos pares (i, j) del grafo tienen su camino óptimo pasando por k, es decir,
cuántos pares cumplen d(i,k) + d(k,j) = d(i,j). Un valor alto significa que ese nodo
es un puente estructural: aparece en muchas rutas óptimas del grafo completo.

**Betweenness (centralidad de intermediación)**
Concepto clásico de redes complejas que mide la importancia de un nodo según cuántos
caminos más cortos lo atraviesan. La betweenness estándar (algoritmo de Brandes) cuenta
caminos entre todos los pares en grafos no ponderados o ponderados. En este proyecto se
calcula una versión basada en Floyd-Warshall (FW-betweenness) que considera los pesos.

**Algoritmo de Brandes**
Implementación eficiente de la betweenness estándar, disponible en NetworkX. Se usa aquí
para validar que el FW-betweenness es consistente con la medida clásica. La correlación
entre ambas métricas es ρ = 0.973 (Spearman), confirmando que el FW-betweenness es un
sustituto válido y basado en los pesos reales del modelo.

**Correlación de Spearman (ρ)**
Medida de correlación que compara el **orden** de dos rankings, no sus valores absolutos.
ρ = 1.0 significa que ambos rankings son idénticos en orden; ρ = 0 indica independencia.
Un ρ = 0.973 entre FW-betweenness y Brandes-betweenness significa que los nodos más
centrales según un método también lo son según el otro, en casi el mismo orden.

**Cuello de botella**
Nodo por el que pasan muchas rutas óptimas del grafo. En términos defensivos: bloquear
un cuello de botella interrumpe simultáneamente muchas rutas de ataque. T1606.001 es el
cuello de botella máximo con 1,044 pares de nodos que dependen de él.

---

## Conceptos de seguridad y MITRE ATT&CK

**MITRE ATT&CK**
Base de conocimiento pública mantenida por MITRE que cataloga técnicas de ataque reales
observadas en campo. Organiza las técnicas en tácticas que siguen la kill chain del
adversario. Es el estándar de la industria para documentar comportamiento adversario.

**Bundle STIX 2.1**
Formato estándar de intercambio de inteligencia de amenazas (Structured Threat Information
Expression). El bundle de ATT&CK Enterprise es un archivo JSON de ~40 MB que contiene
~14,000 objetos: técnicas, grupos, campañas, mitigaciones y sus relaciones. De él se
extraen los datos del proyecto.

**Técnica ATT&CK**
Acción concreta que un adversario puede ejecutar. Tiene un ID con formato `TXXXX` o
`TXXXX.YYY` (subtécnica). Por ejemplo, T1606.001 es "Forge Web Credentials: Web Cookies",
una subtécnica de T1606 (Forge Web Credentials). Cada técnica tiene tácticas asociadas,
descripción, ejemplos y mitigaciones.

**Táctica**
Categoría de alto nivel que agrupa técnicas con el mismo objetivo adversario (ej.
"credential-access", "lateral-movement", "exfiltration"). Las tácticas están ordenadas
según la kill chain: el atacante progresa de tácticas tempranas (initial-access) a
tardías (impact).

**Kill chain**
Secuencia ordenada de fases que un adversario sigue desde el reconocimiento inicial hasta
el logro del objetivo final. En MITRE ATT&CK la kill chain tiene 15 tácticas. Las aristas
del grafo de este proyecto siguen este orden: solo se conectan técnicas de tácticas
consecutivas.

**APT29 / Cozy Bear**
Grupo de amenaza persistente avanzada (APT) atribuido a servicios de inteligencia rusos.
Responsable de SolarWinds Compromise. MITRE lo cataloga como grupo G0016.

**SolarWinds Compromise (G0118)**
Campaña de ataque documentada por MITRE como G0118. APT29 comprometió el software
SolarWinds Orion entre 2019 y 2020, insertando el malware SUNBURST en actualizaciones
legítimas del producto. Afectó a ~18,000 organizaciones. El proyecto usa las 71 técnicas
documentadas para esta campaña como datos base.

**Mitigación**
Control de seguridad documentado por ATT&CK que reduce la probabilidad de que un atacante
use con éxito una técnica. Ejemplos: "Multi-Factor Authentication", "Privileged Account
Management". El número de mitigaciones por técnica define el peso en este modelo: más
mitigaciones = mayor resistencia = peso más alto.

**Cadena de suministro (Supply Chain)**
Vector de ataque que compromete el software o hardware de un proveedor para infectar a
sus clientes. SolarWinds es el ejemplo más notable: APT29 insertó código malicioso en
las actualizaciones del producto antes de que llegaran a los clientes.

---

## Validación y evaluación

**Cross-validación (de algoritmos)**
Verificación de que dos o más algoritmos independientes producen el mismo resultado sobre
los mismos datos. En este proyecto: Dijkstra propio, Bellman-Ford, NetworkX Dijkstra y
Floyd-Warshall todos confirman que el costo óptimo ATTACKER→IMPACT es 1.535.

**Índice de Jaccard**
Medida de solapamiento entre dos conjuntos: `|A ∩ B| / |A ∪ B|`. Se usa en el análisis
de sensibilidad para comparar qué nodos tiene la ruta óptima bajo distintos esquemas de
pesos respecto a la ruta base. Jaccard = 1.0 significa rutas idénticas; Jaccard = 0.125
significa que solo 2 de 16 nodos en la unión son compartidos.

**Análisis de sensibilidad**
Experimento que varía los parámetros del modelo (aquí los pesos) para ver si los
resultados cambian. Si el resultado es estable frente a perturbaciones razonables (±20%),
el modelo es robusto. Si solo cambia con perturbaciones extremas (esquema binario), la
estabilidad queda validada.

**Esquema binario de pesos**
Alternativa de ponderación donde los pesos se discretizan en solo dos valores (0 o 1)
según si la técnica supera o no la mediana de mitigaciones. Destruye la información
ordinal de las mitigaciones y produce una ruta completamente diferente (Jaccard = 0.125
respecto a la base), demostrando que la granularidad de los pesos importa.

**Rutas óptimas equivalentes**
Rutas distintas con exactamente el mismo costo mínimo. Dijkstra reporta solo una porque
devuelve la primera que encuentra, pero pueden existir varias. Floyd-Warshall + enumeración
revela que en este grafo hay **7 rutas distintas** con costo 1.535.

**Sobrecoste**
Diferencia porcentual entre el costo de una ruta subóptima y el costo óptimo. La ruta
BFS tiene un sobrecoste del +90.55% respecto al óptimo: `(2.925 − 1.535) / 1.535 = 90.55%`.
Cuantifica cuánto peor es la decisión de ignorar los pesos.

---

## Notación y convenciones

| Símbolo / término | Significado |
|---|---|
| `ATTACKER` | Nodo artificial de entrada (el adversario externo) |
| `IMPACT` | Nodo artificial de salida (objetivo logrado) |
| `T1078.003` | ID de técnica ATT&CK · formato TXXXX.YYY (subtécnica) |
| `w` | Peso de un nodo = resistencia defensiva |
| `d(i,j)` | Distancia mínima (costo acumulado) entre los nodos i y j |
| `FW[i][j]` | Entrada (i,j) de la matriz de Floyd-Warshall |
| `V` | Número de nodos del grafo (aquí: 73) |
| `E` | Número de aristas del grafo (aquí: 653) |
| `O(f(n))` | Notación de complejidad algorítmica: orden de magnitud del número de operaciones |
| `ρ` | Coeficiente de correlación de Spearman (rango entre −1 y 1) |
| `bw` | Abreviatura de betweenness en tablas de la presentación |
