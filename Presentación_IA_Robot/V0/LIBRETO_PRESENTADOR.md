# LIBRETO DEL PRESENTADOR
**Presentación: Resolviendo problemas de robótica clásica en tiempos de IA**
Jean Aucapiña · Henry Maldonado — Universidad de Cuenca
Duración estimada: 13–16 minutos (≈ 1–1.5 min por diapositiva)

> **Regla de oro:** la diapositiva es el apoyo visual, no el guion. No leer los textos en pantalla; decir la idea con sus propias palabras. Este libreto da la *idea fuerza*, el *guion sugerido* y la *transición* hacia la siguiente diapositiva.

> **Aclaración clave que debe quedar clara desde el inicio:** esta NO es una presentación sobre la competencia Intrinsic Challenge. El challenge es solo el **escenario** que usamos para contar cómo se resuelven hoy los problemas de la robótica clásica con herramientas de IA.

---

## DIAPOSITIVA 1 — Portada
**Idea fuerza:** presentarnos y plantear el tema en una frase.

**Guion sugerido:**
> "Buenos días/tardes. Somos Jean Aucapiña y Henry Maldonado, de la Universidad de Cuenca. Hoy queremos contarles cómo problemas que la robótica clásica llevaba décadas resolviendo a mano, hoy se pueden abordar de una forma completamente distinta gracias a la inteligencia artificial. Para contarlo vamos a usar un escenario concreto: un reto de manipulación robótica. Pero ojo — la presentación no es sobre la competencia; el reto es solo nuestra excusa para mostrar una nueva forma de trabajar."

**Señalar:** la línea inferior *Problema → Aprendizaje → Simulación → Mundo real* — "este es el recorrido que vamos a seguir".

**Transición:** "Empecemos por el problema real."

---

## DIAPOSITIVA 2 — El problema real (Intrinsic Challenge)
**Idea fuerza:** una tarea trivial para un humano es frontera de investigación para un robot.

**Guion sugerido:**
> "El punto de partida es una problemática real de la industria: un brazo robótico tiene que tomar un cable e insertarlo en su puerto. Cualquiera de nosotros lo hace sin pensar. Para un robot, esto es uno de los problemas abiertos más difíciles de la manipulación."

**Recorrer el esquema** (de izquierda a derecha):
- La cámara: el robot solo "ve" píxeles, no sabe dónde está el cable.
- El cable: es deformable — cada vez que lo toma, cambia de forma. Infinitos grados de libertad.
- El puerto: la holgura es menor a 1 milímetro (señalar el zoom de tolerancia).
- La luz: cambia, y la percepción no puede depender de condiciones fijas.
- El contacto: fricción y fuerzas casi imposibles de escribir en ecuaciones.

**Frase de cierre:** "Lo trivial para un humano es frontera de investigación para un robot."

**Transición:** "¿Y cómo se hubiera atacado esto hace unos años, sin las herramientas de hoy? Pues así..."

---

## DIAPOSITIVA 3 — Cómo se hacía antes (enfoque clásico)
**Idea fuerza:** sin estas herramientas, todo se modela a mano y la complejidad explota.

**Guion sugerido:**
> "El camino clásico — el que nos enseñan en la carrera — es modelarlo todo: matrices de rotación, transformaciones homogéneas, cuaterniones, parámetros de Denavit-Hartenberg, cinemática inversa... Y eso funciona, pero solo hasta cierto punto."

**Señalar la curva:**
> "Para un brazo rígido, el modelado a mano es viable. Si agregamos el gripper y los objetos, ya cuesta semanas. Pero cuando llegamos al cable deformable y al contacto con el puerto, la complejidad explota: ya no hay ecuación que escribir. Es intratable a mano."

**Señalar las tarjetas de la derecha:**
- Semanas de modelado por cada elemento.
- Frágil: otro cable u otro puerto, y empezamos de cero.
- Se necesita un experto por cada tarea — el conocimiento no se transfiere.

**Transición:** "Cuando nos topamos con esa pared, buscamos alternativas. Y descubrimos que el mundo ya había cambiado."

---

## DIAPOSITIVA 4 — El giro: encontramos herramientas que integran todo
**Idea fuerza:** existe un ecosistema donde la física ya viene resuelta; el comportamiento se aprende, no se programa.

**Guion sugerido:**
> "Encontramos un ecosistema de herramientas que integran todo lo que antes había que construir a mano. La física ya está resuelta dentro del simulador — nadie tiene que volver a deducir las ecuaciones de contacto. Lo que falta, el comportamiento, se aprende."

**Presentar los tres pilares (breve, 15 s cada uno):**
- **MuJoCo** (DeepMind): física de contactos precisa — el estándar en investigación.
- **LeRobot** (Hugging Face): aprendizaje por imitación — el robot aprende viendo demostraciones. *Este es el que usamos para el reto.*
- **Isaac Lab** (NVIDIA): miles de robots entrenando en paralelo sobre GPU.

**Frase de cierre:** "Las semanas de ecuaciones se convierten en horas de simulación."

**Transición:** "Con estas piezas armamos un pipeline de trabajo. Este es el que vamos a seguir el resto de la presentación."

---

## DIAPOSITIVA 5 — El pipeline en acción (reto resuelto con imitación)
**Idea fuerza:** este es el pipeline que se sigue; el robot aprende viendo, no calculando — y aquí está la evidencia.

**Guion sugerido:**
> "Este es el pipeline: primero, demostraciones — un humano teleopera el brazo y realiza la tarea unas decenas de veces. Eso genera un dataset con las imágenes de cámara y las posiciones de las articulaciones sincronizadas. Con eso entrenamos ACT, una política de LeRobot que va de imagen a acción. El resultado: el cable se inserta — y nadie escribió ni una sola ecuación del cable."

**Señalar los videos:**
> "A la izquierda, el modelo corriendo en una Jetson — hardware embebido, en el borde. A la derecha, el mismo modelo en una laptop común: sin GPU de servidor, sin nube. Esto ya es una validación en el entorno del reto."

**Frase de cierre:** "Lo que era inviable de modelar, se aprende en horas y corre en cualquier máquina."

**Transición:** "Ahora, alguien podría decir: 'pero el modelo 3D del robot y del entorno alguien lo tuvo que construir'. Cierto. Y ahí también entra la IA."

---

## DIAPOSITIVA 6 — Armar los entornos desde cero con IA (Claude + Blender)
**Idea fuerza:** hasta el modelado 3D del robot y su entorno se puede generar con IA, desde texto.

**Guion sugerido:**
> "Estos entornos también se pueden armar desde cero usando herramientas de IA. Le damos una instrucción en lenguaje natural — 'crea un brazo de 6 grados de libertad con gripper paralelo' — y un agente como Claude la interpreta, genera el código y lo ejecuta directamente dentro de Blender a través de un servidor MCP. El resultado es un modelo 3D con su URDF: masas, joints, fricción — listo para llevar al simulador o a ROS 2."

**Señalar el video:** "Esta es una demostración real nuestra: el brazo que ven se generó solo con instrucciones de texto."

**Señalar la fila de logos:** "Y el mismo agente se conecta a muchas herramientas: Blender, Fusion, VS Code, GitHub... es un patrón general, no un truco puntual."

**Frase de cierre:** "Prototipado: de semanas a horas."

**Transición:** "Y con ese modelo generado, ¿qué hacemos? Lo mandamos a entrenar."

---

## DIAPOSITIVA 7 — Cargar el modelo a entrenamiento (Isaac Sim)
**Idea fuerza:** el modelo generado con IA se entrena por refuerzo, masivamente, sin escribir su cinemática.

**Guion sugerido:**
> "El URDF que generamos con Claude y Blender se convierte a USD y se carga en Isaac Sim. Ahí entrenamos por aprendizaje por refuerzo con PPO: la política propone acciones, 64 copias del robot las ejecutan en paralelo sobre la GPU, y la recompensa le dice qué tan bien va. Iteración tras iteración, el brazo aprende a alcanzar el punto objetivo — y nadie escribió su cinemática."

**Señalar los videos:**
> "A la izquierda ven el entrenamiento masivo: 64 brazos aprendiendo a la vez. A la derecha, la política ya entrenada, exportada a ONNX, lista para desplegar."

**Transición:** "Y esto no sirve solo para un brazo que inserta cables. La misma receta se aplica a otras plantas."

---

## DIAPOSITIVA 8 — Aplicado a otra planta: banda transportadora con clasificador
**Idea fuerza:** el mismo patrón percibir → decidir → actuar funciona en una celda industrial distinta.

**Guion sugerido:**
> "Tomamos la esencia del reto — percibir, decidir, actuar — y la llevamos a una celda industrial: una banda transportadora con un clasificador. La simulamos en Godot, la conectamos por rosbridge vía websocket, y del otro lado ROS 2 hace de cerebro: percepción aprendida, decisión, y cinemática inversa clásica para mover el brazo."

**Señalar el esquema:** recorrer Godot → rosbridge → ROS 2, mencionando que viajan imágenes en un sentido y comandos en el otro.

**Señalar los videos:** "Clasificación por color con empuje al bin correcto, y robustez ante iluminación variable — el mismo problema de percepción del reto."

**Punto importante (píldoras de abajo):**
> "Probamos tres enfoques: el clásico puro con HSV, el híbrido donde la IA percibe y la IK mueve, y RL de extremo a extremo. El ganador práctico fue el híbrido: la IA aporta donde el método clásico es frágil — la percepción — y lo clásico aporta donde es sólido — el movimiento."

**Transición:** "¿Y esto escala más allá de nuestros experimentos? Sí — y hay ejemplos de clase mundial."

---

## DIAPOSITIVA 9 — Ejemplos reales: cómo aporta la IA
**Idea fuerza:** la receta *simular masivamente → aprender → transferir* ya funciona en la industria real.

**Guion sugerido (15–20 s por tarjeta):**
> "Esta receta — modelo, simulador GPU, aprendizaje — ya está en producción en el mundo real:"
- **ANYmal, ETH Zürich:** "un cuadrúpedo cuya locomoción se aprendió 100 % en simulación y se transfirió al robot real — hace parkour sin que nadie programara cómo caminar."
- **Wandercraft + NVIDIA:** "exoesqueletos de marcha asistida: la marcha se entrena en simulación antes de tocar a un solo paciente."
- **BMW + Omniverse:** "fábricas completas como gemelos digitales — reportan un 30 % menos de costo de planificación."

**Señalar la tarjeta de educación:**
> "Y para nosotros, lo más cercano: cualquier universidad puede entrenar robots sin comprarlos. Con una GPU y un URDF basta — este proyecto es la prueba, hecho en la Universidad de Cuenca."

**Frase de cierre:** "No resolvimos un problema — adoptamos una forma de resolverlos."

**Transición:** "Para cerrar: ¿qué tan maduro está esto? Pongámoslo en la escala formal."

---

## DIAPOSITIVA 10 — Madurez tecnológica: TRL 5
**Idea fuerza:** estamos en TRL 5 — validación en entorno relevante — porque el escenario del challenge ES un entorno relevante.

**Guion sugerido:**
> "En la escala de Niveles de Maduración Tecnológica estamos en TRL 5: validación en entorno relevante. ¿Por qué 5 y no 4? Porque no nos quedamos en el laboratorio ni en la simulación: el sistema de inserción de cable se validó en el escenario físico del challenge — un entorno relevante real, con hardware embebido, una Jetson, ejecutando la política."

**Recorrer la escalera:**
- TRL 1–3: concepto y prueba de concepto — completados.
- TRL 4: validación en laboratorio y simulación masiva — completado.
- **TRL 5: donde estamos — inserción real sobre Jetson en el entorno del reto.**
- TRL 6+: lo pendiente — un prototipo integrado en condiciones de planta real.

**Reiterar la aclaración (importante):**
> "Insistimos: no vinimos a hablar de la competencia. El challenge fue nuestro entorno relevante de validación — el escenario que nos permitió demostrar que esta forma de trabajar funciona."

**Transición:** "El siguiente salto es del entorno relevante a la planta real. Con eso cerramos."

---

## DIAPOSITIVA 11 — Gracias
**Guion sugerido:**
> "Esa es la historia: un problema real, la pared del modelado a mano, y un ecosistema de IA que convierte semanas de ecuaciones en horas de simulación. Muchas gracias — quedamos atentos a sus preguntas."

---

## ANEXO — Preguntas probables y respuestas cortas

**"¿Cuántas demostraciones necesita el aprendizaje por imitación?"**
Del orden de decenas de episodios teleoperados (~50). Más demostraciones y más variadas → política más robusta.

**"¿Por qué imitación para el cable y refuerzo para el brazo?"**
Imitación cuando es fácil demostrar la tarea y difícil definir una recompensa (insertar un cable). Refuerzo cuando la recompensa es clara (distancia al objetivo) y se puede simular masivamente.

**"¿El modelo generado por Claude/Blender es confiable para simular?"**
Se valida en el simulador: si masas o límites de joints están mal, el entrenamiento lo evidencia. El agente genera; el simulador y el entrenamiento verifican.

**"¿Qué falta para TRL 6–7?"**
Integrar el sistema completo en condiciones cercanas a planta: hardware industrial, ciclos largos, variabilidad real de piezas e iluminación, y métricas de confiabilidad sostenidas.

**"¿Esto reemplaza la robótica clásica?"**
No — la complementa. Nuestro mejor resultado en la banda fue el híbrido: la IA percibe (donde lo clásico es frágil), la cinemática clásica mueve (donde es sólida y verificable).

---

## Reparto sugerido (ajustar a gusto)

| Bloque | Diapositivas | Presentador |
|---|---|---|
| Apertura + problema + enfoque clásico | 1–3 | Presentador A |
| Giro + pipeline + reto resuelto | 4–5 | Presentador B |
| Modelado con IA + entrenamiento | 6–7 | Presentador A |
| Banda clasificadora + ejemplos | 8–9 | Presentador B |
| TRL + cierre | 10–11 | Ambos (A inicia, B cierra) |

**Recordatorios finales:**
- Tecla `T` cambia el tema claro/oscuro; flechas ← → navegan.
- Verificar que los videos con autoplay arrancaron antes de empezar a hablar de ellos.
- Si un video no carga, describir lo que muestra y seguir — no detenerse a arreglarlo.
