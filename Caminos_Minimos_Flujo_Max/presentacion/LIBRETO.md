# Libreto de la presentación

**Flujo máximo: Ford-Fulkerson vs. Edmonds-Karp** · 13 láminas · ~14 minutos

Abre `presentacion/main.html` en el navegador. `←` `→` o espacio para avanzar, `ESC` para el índice de láminas, `P` para imprimir.

> **El hilo conductor de toda la charla:** los dos algoritmos dan la misma respuesta; lo único que cambia es el precio. Y el hallazgo que hace la charla interesante es que **el peor caso famoso no es culpa de DFS** — nos costó trabajo provocarlo, y esa dificultad *es* el resultado.

---

## 01 · Portada — 40 s

> Vamos a comparar dos algoritmos de flujo máximo que, en el fondo, son el mismo algoritmo. Ford-Fulkerson y Edmonds-Karp ejecutan exactamente el mismo ciclo y llegan siempre al mismo resultado. Lo único que cambia entre ellos es **cómo eligen el camino** por el que empujan flujo.
>
> Nosotros medimos cuánto cuesta esa diferencia. Dos números que van a ver toda la charla: en nuestra red, BFS necesita 5 iteraciones y DFS necesita 8. Y en la red zigzag, la diferencia se vuelve brutal: 2 iteraciones contra 20 000.
>
> Pero el hallazgo que más nos costó, y del que más aprendimos, es que ese 20 000 **no lo produce DFS**. Tuvimos que construirlo a mano.

*(La red de la derecha se anima sola: el flujo corre por las aristas azules, el naranja es un arco de retroceso, y abajo está la red zigzag con su arco trampa de capacidad 1.)*

---

## 02 · El problema — 70 s

> Rápidamente, el vocabulario. Una red de flujo es un grafo dirigido con capacidades, una fuente `s` y un sumidero `t`. Queremos mandar lo máximo posible de s a t.
>
> La herramienta central es la **red residual**: para cada arco, lo que *todavía cabe*. Un **camino aumentante** es un camino de s a t por la red residual. Su **cuello de botella Δ** es la mínima capacidad residual del camino — lo máximo que podemos empujar por ahí de una vez.
>
> A la derecha tienen el ciclo completo, ejecutándose de verdad sobre la red de CLRS: buscar un camino, calcular Δ, aumentar. Repetir hasta que no queden caminos.
>
> Y aquí está el punto: **los dos algoritmos hacen exactamente esto**. La única diferencia está en la primera caja, en «buscar». Todo lo demás es idéntico.

*(La animación de la derecha ejecuta Ford-Fulkerson real; los caminos y los Δ salen del algoritmo, no están escritos a mano.)*

---

## 03 · La pregunta — 55 s

> Esta es la pregunta que organiza toda la actividad. Si los dos ejecutan el mismo ciclo y llegan al mismo flujo máximo, ¿por qué la forma de elegir el camino cambia la complejidad de `O(E·|f*|)` a `O(V·E²)`?
>
> Fíjense en lo pequeña que es la diferencia. Ford-Fulkerson, 1956: toma el primer camino que encuentre — el método **no especifica cuál**, y esa libertad es justo el problema. Edmonds-Karp, 1972: toma siempre el camino más corto en número de arcos.
>
> En el código del repositorio, las dos versiones son literalmente **la misma función**. Lo único que cambia es qué estructura guarda los nodos por visitar: una pila o una cola. Una línea.

---

## 04 · La onda BFS — 65 s

> Antes de comparar, hay que entender qué hace BFS por dentro, porque de ahí sale todo.
>
> BFS explora la red residual **por capas**. El número `d` bajo cada nodo es su distancia desde s **en número de arcos** — no en capacidad. Eso es importante: BFS no mira las capacidades para decidir por dónde ir.
>
> A la derecha ven la onda creciendo: primero s, luego los nodos a un arco, luego a dos, hasta llegar a t.
>
> ¿Por qué el camino que sale tiene exactamente `d(t)` arcos? Porque cuando BFS descubre t, lo hace desde un nodo de capa `d(t)−1`, que vino de uno de capa `d(t)−2`, y así hasta s. Un arco por capa. Y no puede haber uno más corto: si existiera un camino de `k < d(t)` arcos, BFS habría llegado a t en la capa k.
>
> **Esta propiedad —el camino elegido es siempre el más corto— es toda la diferencia** entre los dos algoritmos. Guárdenla, porque vuelve al final.

---

## 05 · Parte 1 · La red CLRS — 80 s

> Empezamos con la red clásica de CLRS, la que trae el repositorio. Y aquí nos llevamos la primera sorpresa: **las dos tablas son idénticas**. Mismos tres caminos, mismos Δ, mismo todo.
>
> No es casualidad. La DFS del repositorio usa una pila, y como la pila devuelve el último insertado, acaba visitando primero los índices bajos — que es el mismo orden que sigue la BFS. En una red pequeña como esta, los dos tropiezan con los mismos caminos. **La red CLRS es demasiado benigna para separarlos.**
>
> A la derecha, las tres coincidencias del estado final. Y quiero que noten que tienen explicaciones **distintas**, no hay que confundirlas:
>
> — El **flujo máximo** coincide siempre, en cualquier red, con cualquier estrategia. Lo garantiza max-flow min-cut.
> — El **corte mínimo** coincide aquí, pero no tiene por qué: si hay varios cortes de capacidad mínima, distintas ejecuciones pueden reportar distintos.
> — Los **flujos arco por arco** coinciden solo porque las trazas son idénticas. Esa es la más frágil, y en la lámina 8 la vamos a ver romperse.
>
> Abajo, el arco de retroceso. Y aquí hay que ser honestos: **ninguna variante estándar usa retroceso en esta red**. Verificamos las tres. Para poder responder la pregunta de la guía tuvimos que forzarlo con una DFS que prefiere caminos largos.
>
> La idea del retroceso: mandar 4 unidades por v₃→v₂ crea, en la residual, el arco v₂→v₃ — la opción de **deshacer** ese envío. Cancelar no es hacer trampa, es **reencaminar**: las 4 unidades no desaparecen, entran por s→v₂ y salen por v₃→t. Se conserva el flujo y el total sube. Sin arcos de retroceso el algoritmo se atascaría en decisiones tempranas malas; con ellos, toda decisión es reversible.

---

## 06 · Parte 2 · El zigzag — 110 s ★ *lámina clave*

> Esta es la lámina más importante de la charla.
>
> La red zigzag: dos rutas de capacidad M unidas por un arco trampa de capacidad 1. La teoría dice que un Ford-Fulkerson que insistiera en cruzar la trampa necesitaría **2M iteraciones** — o sea, avanzar de uno en uno.
>
> Nuestra medición está en la tabla. Miren las cuatro primeras filas: **BFS, la DFS del repositorio y la DFS de orden invertido terminan en 2 iteraciones**, para cualquier M. Incluso M = 10 000. La DFS profunda llega a 4. Ninguna se acerca a 2M.
>
> ¿Por qué? Por una razón **geométrica**: el camino trampa `s→u→v→t` tiene 3 arcos, y el atajo `s→u→t` solo 2. Cualquier búsqueda que se detenga al descubrir t tropieza antes con el atajo. Para caer en la trampa hay que **querer** el camino largo.
>
> Y aquí está lo interesante: ni siquiera queriéndolo basta. La DFS profunda cruza la trampa una vez con Δ=1, pero en la iteración siguiente toma el atajo y se lleva M−1 unidades de golpe. **El daño se limita solo.**
>
> Por cierto: la guía sugería invertir el orden de los vecinos para empeorar el comportamiento. Lo implementamos. **No empeora nada** — sigue en 2 iteraciones, solo cambia qué ruta toma primero. Lo reportamos como resultado negativo.
>
> Lo que sí funciona está a la izquierda, animándose. Un adversario que **alterna los dos caminos largos**: `s→u→v→t` satura la trampa, y `s→v→u→t` usa el retroceso `v→u`, que cancela ese flujo y **reabre la trampa**. Miren el contador `r(u→v)`: 0, 1, 0, 1… El par se repite M veces, avanzando de uno en uno. Y clava las 2M exactas: 20 000 para M = 10 000.
>
> **Aquí está nuestra conclusión principal: el peor caso no es culpa de DFS.** DFS es solo una forma de elegir, y resulta ser una razonablemente afortunada. Pero Ford-Fulkerson *permite* elegir así, y su cota tiene que contemplar al peor elector posible. Por eso la cota depende de `|f*|`: **no describe lo que DFS hace, describe lo que el método no prohíbe.**
>
> ¿Y por qué BFS es inmune? Porque **jamás elegiría esos caminos**. El adversario necesita caminos de 3 arcos; BFS siempre encuentra el de 2. El arco trampa nunca se usa.

*(Si hay poco tiempo: quédense con la tabla y con la frase «el peor caso no es culpa de DFS».)*

---

## 07 · Parte 3 · El diseño — 75 s

> Para la red propia, la guía pedía cuatro requisitos. Nuestro primer intento fue fijar las capacidades a ojo. **Falló dos de cuatro**: BFS y DFS daban ambos 7 iteraciones, y nadie usaba arcos de retroceso. Encima el corte mínimo salía trivial — todos los nodos menos t —, lo que hace la verificación aburrida.
>
> Así que separamos las dos cosas: la **topología** se dibuja a mano, pensando dónde queremos el cuello de botella. Fíjense en `a→e`: tiene 15 de ancho, pero `e→t` solo 3. La ruta norte promete mucho y entrega poco.
>
> Las **capacidades**, en cambio, no se pueden ajustar por intuición. Escribimos una búsqueda que explora el espacio y exige seis condiciones a la vez.
>
> Y el resultado de esa búsqueda es, para mí, lo más interesante de la lámina. De 400 000 combinaciones: el **77.5% falla porque DFS no resulta peor que BFS**. Un 22% más falla porque BFS no usa retroceso. **Solo el 0.02% cumple las seis.**
>
> Ese número es un resultado por sí mismo. Con capacidades al azar, **DFS iguala o supera a BFS tres de cada cuatro veces**. Por eso la red CLRS no logra separarlos. Y sugiere algo incómodo, que retomo al final.

---

## 08 · Parte 3 · Resultados — 75 s ★ *lámina clave*

> Con esa red, los resultados. Mismo flujo: 24. BFS en 5 iteraciones, DFS en 8.
>
> Pero lo que quiero que miren son las **barras de arriba a la derecha**, porque son la evidencia central de toda la actividad.
>
> Las longitudes de BFS: 3, 3, 3, 5, 7. **Nunca bajan.** Las de DFS: 3, 4, 3, 4, 3, 4, 5, 6. **Bajan tres veces** — las marcadas en naranja.
>
> Misma red. Misma implementación. Solo cambia la línea que elige el camino. Y la demostración de `O(V·E²)` se apoya **exactamente** en que las longitudes no pueden decrecer. Aquí la vemos decrecer.
>
> El desperdicio, en números: DFS gasta dos iteraciones enteras en aumentos de **Δ=1**. BFS nunca baja de Δ=2. Mismo resultado, 60% más de trabajo.
>
> Los arcos de retroceso: uno por método, y ambos en la **última** iteración. En BFS, el arco `f→b` cancela 2 de las 8 unidades que la iteración 2 mandó por `b→f`; esas 2 salen ahora por otra ruta y el hueco lo llena otro tráfico. Sin ese retroceso, los algoritmos se habrían detenido en 22 y 23 — **por debajo del óptimo**. El retroceso es lo que permite exprimir las últimas unidades.

---

## 09 · Parte 3 · El corte mínimo — 60 s

> La verificación a mano que pedía la guía. El conjunto S — los alcanzables desde s en la red residual final — es `{s, a, c, e}`. Las aristas que salen de S son cuatro, y suman **8 + 5 + 8 + 3 = 24**, que es exactamente el flujo máximo. Teorema verificado.
>
> Dos comprobaciones que confirman que está bien: **las cuatro están saturadas** — tienen que estarlo, porque si a alguna le sobrara capacidad su destino sería alcanzable y estaría dentro de S. Y **ningún arco de vuelta lleva flujo**, por el mismo tipo de argumento.
>
> Lo que me parece más bonito es la lectura de ingeniería. Este corte **atraviesa el interior** de la red, no se limita a los arcos que entran a t. Dice que la red no está limitada por la entrada ni por la salida, sino por tres estrangulamientos internos más el enlace `e→t`.
>
> Y da una recomendación concreta: **ampliar `f→t` no serviría de nada**. Tiene 14 y usa 14, parece el cuello de botella — pero mientras `c→f` siga en 8, ese ancho no se puede alimentar. **Reforzar cualquier enlace fuera del corte es dinero perdido.**

---

## 09b · Las animaciones — 35 s

> Los GIF que genera el código, por si quieren verlos con calma.
>
> Arriba a la izquierda, Edmonds-Karp con la **onda BFS** creciendo capa por capa. Abajo a la derecha, el adversario cayendo en la trampa una y otra vez.
>
> Para leerlos: naranja es el camino de esta iteración, púrpura son las aristas del corte, dorado son los nodos de S. En el panel derecho, el **rojo punteado** son los arcos de retroceso — la capacidad de deshacer.

---

## 10 · Parte 4 · El cuadro comparativo — 70 s

> Toda la evidencia junta. Recorro solo las filas que importan.
>
> **Iteraciones en el zigzag con M = 10 000**: DFS del repositorio, 2 — igual que BFS. El adversario, 20 000. La misma red, la misma cota teórica, y un factor de 10 000 de diferencia según **quién elige el camino**.
>
> **Longitudes**: oscilan vs. no decrecen. Ya lo vimos.
>
> **Sensibilidad**: aquí hay un matiz honesto. Hicimos un experimento propio — multiplicamos todas las capacidades de nuestra red por mil. El flujo escala a 24 000, pero **las iteraciones ni se mueven**: BFS sigue en 5, DFS en 8. O sea que en una red concreta DFS puede ser perfectamente insensible al valor. La diferencia es que para BFS eso está **garantizado**, y para DFS es **suerte**. El zigzag muestra qué pasa cuando la suerte se acaba.
>
> **Capacidades irracionales**: aquí no presentamos experimento propio, y quiero explicar por qué. Reproducir la red de Zwick exige aritmética exacta en `ℚ(√5)`, porque la no terminación depende de que los residuos sigan exactamente la identidad de la razón áurea. En Float64 ese invariante se rompe por redondeo y el algoritmo termina — pero **termina por el error numérico, no por el algoritmo**. Un experimento así confirmaría la terminación por el motivo equivocado. Preferimos citar la teoría y apoyarnos en el peor caso 2M, que sí es evidencia nuestra.
>
> **Nuestra recomendación**: Edmonds-Karp por defecto. El precio es cero — misma complejidad por iteración — y compra una garantía independiente de los datos.

---

## 11 · El lema y las aplicaciones — 80 s

> ¿Por qué la cota de Edmonds-Karp no menciona las capacidades? La cadena de la izquierda, en cuatro pasos.
>
> **Uno**: el lema de monotonía. Con BFS, la distancia `d(v)` nunca decrece. **Dos**: cada iteración satura al menos un arco — el crítico. **Tres**, que es el paso clave: si `(u,v)` es crítico, para volver a serlo debe reaparecer en la residual, y eso exige mandar flujo por `v→u`. Combinando con la monotonía sale que `d(u)` ha subido **al menos 2**. Como `d(u) < V`, esto pasa a lo sumo V/2 veces. **Cuatro**: E arcos por O(V) veces, por O(E) de cada BFS, da `O(V·E²)`.
>
> **En esa cuenta no aparece ninguna capacidad.** Ahí está toda la respuesta a la pregunta de la lámina 3.
>
> Y en el recuadro rojo: dónde se rompe todo si las longitudes decrecen. El paso tres usa la monotonía. Sin ella, `d(u)` sube y baja, no hay forma de acotar las reapariciones, y podría ser `|f*|` veces. **Ahí reaparece la dependencia de las capacidades.** Nuestra tabla de DFS es exactamente esa situación; el zigzag es esa situación llevada al extremo.
>
> Dos aplicaciones, rápido. **Robustez**: el corte mínimo es el conjunto más barato de enlaces cuya eliminación desconecta s de t. Es la medida natural de fragilidad de una red.
>
> Y aquí el giro que más me gusta: si en vez del ancho de banda ponemos **capacidad 1** en cada enlace, el flujo máximo pasa a contar **caminos disjuntos** — por el teorema de Menger — es decir, cuántos fallos simultáneos tolera la red. **El mismo algoritmo responde una pregunta completamente distinta**, solo cambiando qué significa la capacidad.
>
> La segunda: detección de comunidades. Si dos grupos están poco conectados entre sí, el corte mínimo cae justo en la frontera.

---

## 12 · Conclusiones — 60 s

> Cinco cosas.
>
> **Una**: la elección del camino no afecta el resultado, solo el costo. Max-flow min-cut explica por qué — la demostración solo usa la condición de parada, nunca cómo se eligieron los caminos.
>
> **Dos**: el peor caso es real pero cuesta provocarlo. Ninguna DFS razonable lo alcanza.
>
> **Tres**, la que más nos costó entender: **por eso el peor caso no es culpa de DFS**. La cota `O(E·|f*|)` no describe lo que DFS hace; describe lo que Ford-Fulkerson **no prohíbe**. Edmonds-Karp no es «DFS arreglado» — es Ford-Fulkerson **con la libertad de elegir mal eliminada**.
>
> **Cuatro**: la monotonía de las longitudes es la bisagra de todo, y nuestra red la exhibe en las dos direcciones a la vez.
>
> **Cinco**, y con esto cierro: encontrar una red donde DFS se vea mal es **estadísticamente difícil**. El 77.5% de nuestras 400 000 pruebas daba DFS igual o mejor. Eso explica por qué CLRS no separa los métodos — pero sugiere algo que va más allá de esta actividad: **medir un algoritmo en unos pocos casos y concluir que va bien es exactamente el error que la teoría del peor caso existe para prevenir.**
>
> Un cambio de una línea — una pila por una cola — convierte una garantía que depende de los datos en una que depende solo del tamaño del grafo. Y el precio es cero.

---

## Preguntas que pueden caer

**«¿Por qué su DFS no da el peor caso si el libro dice que sí?»**
El libro dice que *existe una elección de caminos* que da 2M, no que DFS la haga. Son cosas distintas. Nosotros construimos esa elección explícitamente (`buscar_camino_alternante`) y da exactamente 2M. La DFS del repositorio no la hace porque corta al descubrir t, y el atajo de 2 arcos aparece antes que el camino trampa de 3.

**«¿Entonces DFS es igual de buena?»**
No: es igual de buena *en las redes que probamos*, y eso es precisamente el problema. Su garantía depende de los datos, que suelen venir de fuera y cambian. Una red que hoy va bien puede degradarse mañana porque un enlace pasó de 1 a 10 Gb/s. BFS no tiene ese riesgo, y no cuesta nada más.

**«¿El corte mínimo siempre es único?»**
No. El *valor* del flujo máximo sí es único; el corte que lo alcanza puede no serlo. En nuestra red BFS y DFS coinciden en el corte, pero eso no está garantizado. De hecho reparten el flujo de forma distinta por dentro llegando al mismo total.

**«¿Por qué no midieron el caso irracional?»**
Porque en Float64 el resultado sería falso. La construcción de Zwick necesita que los residuos sigan exactamente `r^(k+2) = r^k − r^(k+1)`; con redondeo eso se rompe y el algoritmo termina por el error numérico. Habríamos "demostrado" terminación por el motivo equivocado. Requiere aritmética exacta en `ℚ(√5)`, fuera del alcance de la actividad.

**«¿La búsqueda de la red no es hacer trampa?»**
La topología la diseñamos a mano con intención — dónde queríamos el cuello de botella. Lo que buscamos son las capacidades, porque su efecto sobre los cuatro requisitos no es intuitivo. Y el resultado de la búsqueda es información valiosa en sí misma: el 77.5% de fallos por «DFS no es peor» dice algo real sobre lo difícil que es exhibir el peor caso.

**«¿Cuánto tardan realmente?»**
Los tiempos están en `results/data/*.json`. Pero para M = 10 000 la comparación relevante no es el reloj sino las iteraciones: 2 contra 20 000. El reloj solo confirma lo obvio.
