# Flujo máximo: Ford-Fulkerson vs. Edmonds-Karp

Actividad práctica del módulo de Redes Complejas — Universidad de Cuenca.
Capítulo de Optimización en Redes.

**→ [INFORME.md](INFORME.md)** — el informe completo con tablas, respuestas y análisis
**→ [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md)** — avance, checklist de la rúbrica y decisiones

## Qué encontramos

Los dos algoritmos llegan siempre al mismo flujo máximo; lo que cambia es cuánto cuesta. En nuestra red, Edmonds-Karp necesita 5 iteraciones y Ford-Fulkerson con DFS necesita 8, para el mismo flujo de 24.

El resultado que más nos sorprendió: **el peor caso de 2M iteraciones de la red zigzag no lo alcanza ninguna DFS razonable** — la del repositorio termina en 2 iteraciones para cualquier M, incluido M = 10 000. Hizo falta construir un adversario que alterna los dos caminos que cruzan el arco trampa (el segundo usa un retroceso que *reabre* la trampa) para llegar a las 2M exactas: 20 000 iteraciones donde BFS necesita 2.

La conclusión: el peor caso no es culpa de DFS, sino de la libertad de elegir mal que Ford-Fulkerson deja abierta y que BFS cierra por construcción.

## Ejecutar

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'

julia --project=. src/parte1_exploracion.jl    # red CLRS: tablas, onda BFS, GIFs
julia --project=. src/parte2_zigzag.jl         # escalado en M, el adversario 2M
julia --project=. src/parte3_red_propia.jl     # nuestra red: corte mínimo, GIFs
julia --project=. src/parte4_comparacion.jl    # tabla comparativa, sensibilidad
julia --project=. src/busqueda_red.jl          # cómo diseñamos la red propia
```

Paso a paso en el REPL:

```julia
include("src/motor.jl")
red, s, t = red_propia()
ford_fulkerson_interactivo(red, s, t)               # BFS, [Enter] para avanzar
ford_fulkerson_interactivo(red, s, t; metodo=:dfs)  # DFS
```

## Estructura

```
src/
  ford_fulkerson.jl      código base del profesor (sin modificar)
  edmonds_karp.jl        código base del profesor (sin modificar)
  redes.jl               red CLRS, red zigzag(M), nuestra red
  motor.jl               instrumentación + variantes de búsqueda propias
  busqueda_red.jl        el proceso de diseño de nuestra red
  parte{1,2,3,4}_*.jl    un script por parte de la guía
results/
  data/*.json            todos los números del informe
  animations/*.gif       animaciones
  report/*.csv           tablas de aristas
presentacion/            diapositivas
```

El código base (`ford_fulkerson.jl`, `edmonds_karp.jl`) viene de
[fabianastudillo/ComplexNetworks](https://github.com/fabianastudillo/ComplexNetworks)
y se mantiene sin modificar; todo lo que añadimos vive en `motor.jl` y en los
scripts por parte.
