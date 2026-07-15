# ============================================================
# 01_ford_fulkerson.jl
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Módulo base del algoritmo de FORD-FULKERSON para el problema de
# flujo máximo en redes de flujo dirigidas. Es el primer archivo en
# el orden de ejecución de la práctica: los scripts 03 a 06 lo
# cargan con `include("01_ford_fulkerson.jl")` y reutilizan sus
# tipos y funciones.
#
# Contenido de este archivo:
#   1. Carga de librerías.
#   2. Estructuras de datos: `RedFlujo` (la red) y `Paso` (registro
#      de una iteración del algoritmo).
#   3. Búsqueda de caminos aumentantes en la red residual, con dos
#      estrategias intercambiables: BFS (equivalente a Edmonds-Karp)
#      y DFS (la variante "clásica" de Ford-Fulkerson).
#   4. El algoritmo de Ford-Fulkerson en sí (bucle de aumento de
#      flujo) y el cálculo del corte mínimo (teorema max-flow
#      min-cut).
#   5. Funciones de dibujo de la red de flujo y de la red residual.
#   6. Generación de animaciones GIF y modo interactivo paso a paso.
#
# Fundamento teórico: ver results/report/report.md, sección "Teoría".
#
# Fuente base: repositorio fabianastudillo/ComplexNetworks
#   (optimization/ford-fulkerson/ford_fulkerson.jl), adaptado y
#   redocumentado para esta actividad.
#
# Uso típico (ver 03_parte1_exploracion_guiada.jl):
#   include("01_ford_fulkerson.jl")
#   flujo, F, historia = ford_fulkerson(red, s, t; metodo=:bfs)
#   animar_ford_fulkerson(red, s, t; archivo="ff.gif")
#   ford_fulkerson_interactivo(red, s, t)   # [Enter] para avanzar

# ------------------------------------------------------------
# 1. Carga de librerías
# ------------------------------------------------------------
using Plots   # Dibujo de la red de flujo, la red residual y animaciones GIF
using Printf  # Formato de las trazas impresas en consola (@printf)

# ------------------------------------------------------------
# 2. Estructuras de datos
# ------------------------------------------------------------

"""
    RedFlujo(C, nombres, pos)

Representa una red de flujo dirigida con `n` nodos.

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades; `C[u,v]` es la capacidad
  del arco u→v (0 si el arco no existe).
- `nombres::Vector{String}`: etiqueta de cada nodo (para graficar).
- `pos::Vector{Tuple{Float64,Float64}}`: posición fija (x, y) de
  cada nodo en el plano, usada por las funciones de dibujo.
"""
# Guardas `if !@isdefined(...)`: 01 y 02 comparten el tipo `RedFlujo`
# (y cada uno define su propio registro de iteración). Como varios
# scripts de la práctica hacen `include` de ambos archivos en la
# misma sesión, sin esta guarda Julia lanzaría un error fatal de
# "invalid redefinition" la segunda vez que se definiera el mismo
# `struct`. Las funciones no necesitan esta guarda: Julia permite
# redefinirlas libremente (solo emite una advertencia informativa).
if !@isdefined(RedFlujo)
struct RedFlujo
    C::Matrix{Int}
    nombres::Vector{String}
    pos::Vector{Tuple{Float64,Float64}}
end
end

"""
    Paso

Registro de una iteración del algoritmo de Ford-Fulkerson.

# Campos
- `camino::Vector{Int}`: secuencia de nodos del camino aumentante
  encontrado en esa iteración.
- `Δ::Int`: cuello de botella (mínima capacidad residual a lo largo
  del camino), es decir, cuánto flujo se envió en esta iteración.
- `F::Matrix{Int}`: copia de la matriz de flujo *después* de
  aumentar. Es antisimétrica (`F[u,v] = -F[v,u]`), convención que
  hace que la capacidad residual sea `r(u,v) = C[u,v] - F[u,v]`
  para cualquier par de nodos (incluidos los arcos de retroceso).
- `flujo_total::Int`: valor acumulado del flujo tras esta iteración.
"""
if !@isdefined(Paso)
struct Paso
    camino::Vector{Int}
    Δ::Int
    F::Matrix{Int}
    flujo_total::Int
end
end

# ------------------------------------------------------------
# 3. Búsqueda de caminos aumentantes en la red residual
# ------------------------------------------------------------

"""
    _reconstruir(padre, s, t) -> Vector{Int}

Reconstruye el camino s→t a partir del vector de padres producido
por una búsqueda (BFS o DFS).

# Argumentos
- `padre::Vector{Int}`: `padre[v]` es el nodo desde el que se
  descubrió `v` durante la búsqueda.
- `s::Int`, `t::Int`: nodo fuente y nodo sumidero.

# Salida
- `Vector{Int}`: lista ordenada de nodos desde `s` hasta `t`.
"""
function _reconstruir(padre::Vector{Int}, s::Int, t::Int)
    camino = [t]
    while camino[1] != s
        pushfirst!(camino, padre[camino[1]])
    end
    return camino
end

"""
    buscar_camino_bfs(C, F, s, t) -> Vector{Int}

Busca un camino aumentante s→t en la red residual usando BFS. Esta
es la estrategia de Edmonds-Karp: siempre encuentra el camino
aumentante con MENOS arcos, lo que garantiza complejidad O(V·E²).

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades originales.
- `F::Matrix{Int}`: matriz de flujo actual (antisimétrica).
- `s::Int`, `t::Int`: nodo fuente y sumidero.

# Salida
- `Vector{Int}`: camino s→t en la red residual, o `Int[]` si `t` no
  es alcanzable desde `s`.
"""
function buscar_camino_bfs(C::Matrix{Int}, F::Matrix{Int}, s::Int, t::Int)
    n = size(C, 1)
    padre = zeros(Int, n)
    padre[s] = s
    cola = [s]
    while !isempty(cola)
        u = popfirst!(cola)
        for v in 1:n
            # r(u,v) = C - F > 0 ⇒ el arco residual u→v existe
            if padre[v] == 0 && C[u, v] - F[u, v] > 0
                padre[v] = u
                v == t && return _reconstruir(padre, s, t)
                push!(cola, v)
            end
        end
    end
    return Int[]
end

"""
    buscar_camino_dfs(C, F, s, t) -> Vector{Int}

Busca un camino aumentante s→t en la red residual usando DFS. Es la
versión "clásica" de Ford-Fulkerson: funciona, pero puede necesitar
muchas más iteraciones que BFS (con capacidades irracionales incluso
podría no terminar).

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades originales.
- `F::Matrix{Int}`: matriz de flujo actual (antisimétrica).
- `s::Int`, `t::Int`: nodo fuente y sumidero.

# Salida
- `Vector{Int}`: camino s→t en la red residual, o `Int[]` si `t` no
  es alcanzable desde `s`.
"""
function buscar_camino_dfs(C::Matrix{Int}, F::Matrix{Int}, s::Int, t::Int)
    n = size(C, 1)
    padre = zeros(Int, n)
    padre[s] = s
    pila = [s]
    while !isempty(pila)
        u = pop!(pila)
        for v in n:-1:1   # orden inverso para explorar primero los índices bajos
            if padre[v] == 0 && C[u, v] - F[u, v] > 0
                padre[v] = u
                v == t && return _reconstruir(padre, s, t)
                push!(pila, v)
            end
        end
    end
    return Int[]
end

# ------------------------------------------------------------
# 4. Algoritmo de Ford-Fulkerson y corte mínimo
# ------------------------------------------------------------

"""
    ford_fulkerson(red, s, t; metodo=:bfs, verbose=true)
        -> (flujo_max, F, historia)

Calcula el flujo máximo de `s` a `t` en la red `red` mediante el
método de Ford-Fulkerson: mientras exista un camino aumentante en la
red residual, aumenta el flujo en su cuello de botella Δ.

# Argumentos
- `red::RedFlujo`: la red de flujo.
- `s::Int`, `t::Int`: nodo fuente y sumidero.
- `metodo::Symbol`: `:bfs` usa Edmonds-Karp; `:dfs` usa la variante
  clásica. Por defecto `:bfs`.
- `verbose::Bool`: si es `true`, imprime una traza por iteración.

# Salida
- `flujo_max::Int`: valor del flujo máximo encontrado.
- `F::Matrix{Int}`: matriz de flujo final (antisimétrica).
- `historia::Vector{Paso}`: registro de cada iteración, usado por
  las funciones de animación.
"""
function ford_fulkerson(red::RedFlujo, s::Int, t::Int;
                        metodo::Symbol=:bfs, verbose::Bool=true)
    C = red.C
    n = size(C, 1)
    F = zeros(Int, n, n)
    historia = Paso[]
    flujo_total = 0
    buscar = metodo == :bfs ? buscar_camino_bfs : buscar_camino_dfs

    while true
        camino = buscar(C, F, s, t)
        isempty(camino) && break   # no hay más caminos aumentantes

        Δ = minimum(C[camino[i], camino[i+1]] - F[camino[i], camino[i+1]]
                    for i in 1:length(camino)-1)

        for i in 1:length(camino)-1
            u, v = camino[i], camino[i+1]
            F[u, v] += Δ
            F[v, u] -= Δ
        end
        flujo_total += Δ

        push!(historia, Paso(camino, Δ, copy(F), flujo_total))
        if verbose
            @printf("Iteración %d: camino %s,  Δ = %d,  flujo total = %d\n",
                    length(historia), join(red.nombres[camino], " → "),
                    Δ, flujo_total)
        end
    end

    verbose && @printf("\nFlujo máximo: %d (en %d iteraciones)\n",
                       flujo_total, length(historia))
    return flujo_total, F, historia
end

"""
    corte_minimo(C, F, s) -> (S, aristas_corte)

Con el flujo máximo `F`, calcula el corte mínimo (S, V∖S) según el
teorema max-flow min-cut: `S` es el conjunto de nodos alcanzables
desde `s` en la red residual.

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades originales.
- `F::Matrix{Int}`: matriz de flujo (se espera que sea el flujo
  máximo, aunque la función es válida para cualquier flujo).
- `s::Int`: nodo fuente.

# Salida
- `S::Vector{Int}`: nodos alcanzables desde `s` en la red residual.
- `aristas_corte::Vector{Tuple{Int,Int}}`: arcos originales que
  cruzan de `S` hacia `V∖S`. La suma de sus capacidades es
  exactamente el flujo máximo.
"""
function corte_minimo(C::Matrix{Int}, F::Matrix{Int}, s::Int)
    n = size(C, 1)
    visitado = falses(n)
    visitado[s] = true
    cola = [s]
    while !isempty(cola)
        u = popfirst!(cola)
        for v in 1:n
            if !visitado[v] && C[u, v] - F[u, v] > 0
                visitado[v] = true
                push!(cola, v)
            end
        end
    end
    S = findall(visitado)
    aristas = [(u, v) for u in S, v in findall(.!visitado) if C[u, v] > 0]
    return S, vec(aristas)
end

# ------------------------------------------------------------
# 5. Funciones de dibujo
# ------------------------------------------------------------

"""
    _flecha!(plt, p1, p2; color, lw, estilo, etiqueta, lab_color, offset, radio)

Dibuja sobre `plt` una flecha de `p1` a `p2`, acortada para no tapar
los nodos, con un desplazamiento perpendicular `offset` (para poder
separar arcos antiparalelos) y una etiqueta de texto opcional junto
al punto medio.

# Argumentos
- `plt`: objeto de gráfico de Plots.jl sobre el que se dibuja.
- `p1::Tuple`, `p2::Tuple`: coordenadas (x, y) de origen y destino.
- `color`, `lw::Real`, `estilo::Symbol`: estilo de la línea.
- `etiqueta::String`: texto a mostrar (p. ej. "flujo/capacidad").
- `lab_color`: color del texto.
- `offset::Real`: desplazamiento perpendicular para separar arcos.
- `radio::Real`: distancia de acortamiento respecto a los nodos.

# Salida
- `plt`: el mismo objeto de gráfico, modificado en el lugar.
"""
function _flecha!(plt, p1, p2; color=:gray55, lw=1.5, estilo=:solid,
                  etiqueta="", lab_color=:gray30, offset=0.0, radio=0.17)
    dx, dy = p2[1] - p1[1], p2[2] - p1[2]
    L = hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    ax, ay = p1[1] + ux * radio + nx * offset, p1[2] + uy * radio + ny * offset
    bx, by = p2[1] - ux * radio + nx * offset, p2[2] - uy * radio + ny * offset
    plot!(plt, [ax, bx], [ay, by];
          color=color, lw=lw, linestyle=estilo, arrow=true)
    if etiqueta != ""
        mx = (ax + bx) / 2 + nx * 0.14
        my = (ay + by) / 2 + ny * 0.14
        annotate!(plt, mx, my, text(etiqueta, 9, lab_color, :center))
    end
    return plt
end

"""
    _nodos!(plt, red, s, t, S) -> plt

Dibuja los nodos de `red` con sus nombres. Colorea de dorado los
nodos de `S` (lado fuente del corte mínimo), de verde el nodo `s`,
de salmón el nodo `t`, y de celeste el resto.

# Argumentos
- `plt`: objeto de gráfico.
- `red::RedFlujo`: la red.
- `s::Int`, `t::Int`: fuente y sumidero.
- `S::Vector{Int}`: nodos del lado fuente del corte (vacío si no se
  quiere resaltar ningún corte).

# Salida
- `plt`: el mismo objeto de gráfico, modificado en el lugar.
"""
function _nodos!(plt, red::RedFlujo, s::Int, t::Int, S::Vector{Int})
    n = length(red.nombres)
    for i in 1:n
        color = i in S       ? :gold :
                i == s       ? :palegreen :
                i == t       ? :lightsalmon : :lightblue
        scatter!(plt, [red.pos[i][1]], [red.pos[i][2]];
                 markersize=17, color=color, markerstrokecolor=:black,
                 markerstrokewidth=1.5)
        annotate!(plt, red.pos[i][1], red.pos[i][2],
                  text(red.nombres[i], 10, :black, :center))
    end
    return plt
end

"""
    _lienzo(red, titulo) -> Plots.Plot

Crea el lienzo base (ejes ocultos, proporción 1:1) con límites
calculados automáticamente a partir de las posiciones de los nodos.

# Argumentos
- `red::RedFlujo`: la red (se usan sus posiciones para los límites).
- `titulo::String`: título del gráfico.

# Salida
- `Plots.Plot`: lienzo vacío listo para dibujar arcos y nodos.
"""
function _lienzo(red::RedFlujo, titulo::String)
    xs = [p[1] for p in red.pos]; ys = [p[2] for p in red.pos]
    return plot(; legend=false, axis=false, grid=false, ticks=false,
                aspect_ratio=:equal, title=titulo, titlefontsize=10,
                xlims=(minimum(xs) - 0.45, maximum(xs) + 0.45),
                ylims=(minimum(ys) - 0.45, maximum(ys) + 0.45))
end

"""
    dibujar_red(red, F; camino, titulo, S, s, t) -> Plots.Plot

Dibuja la red de flujo completa con etiquetas "flujo/capacidad" en
cada arco. Los arcos con flujo positivo se pintan de azul, los arcos
sin flujo de gris. El `camino` aumentante (si se pasa) se resalta en
naranja; si usa un arco residual inverso (de retroceso), se dibuja
punteado. Si `S` no está vacío, se resaltan en púrpura las aristas
del corte mínimo.

# Argumentos
- `red::RedFlujo`: la red.
- `F::Matrix{Int}`: matriz de flujo a graficar.
- `camino::Vector{Int}`: camino a resaltar (opcional).
- `titulo::String`: título del gráfico.
- `S::Vector{Int}`: lado fuente del corte mínimo a resaltar (opcional).
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `Plots.Plot`: gráfico completo de la red de flujo.
"""
function dibujar_red(red::RedFlujo, F::Matrix{Int};
                     camino::Vector{Int}=Int[], titulo::String="",
                     S::Vector{Int}=Int[], s::Int=0, t::Int=0)
    plt = _lienzo(red, titulo)
    n = size(red.C, 1)
    arcos_camino = Set(zip(camino[1:max(end - 1, 0)], camino[2:end]))

    for u in 1:n, v in 1:n
        red.C[u, v] > 0 || continue
        off = red.C[v, u] > 0 ? 0.07 : 0.0
        f = max(F[u, v], 0)
        en_camino = (u, v) in arcos_camino
        en_corte  = !isempty(S) && (u in S) && !(v in S)
        color = en_camino ? :orangered :
                en_corte  ? :purple :
                f > 0     ? :steelblue : :gray60
        lw = (en_camino || en_corte) ? 4 : (f > 0 ? 2.5 : 1.5)
        _flecha!(plt, red.pos[u], red.pos[v];
                 color=color, lw=lw, offset=off,
                 etiqueta="$f/$(red.C[u, v])",
                 lab_color=f > 0 ? :steelblue : :gray45)
    end

    for (u, v) in arcos_camino
        if red.C[u, v] == 0
            _flecha!(plt, red.pos[u], red.pos[v];
                     color=:orangered, lw=3, estilo=:dash, offset=0.09)
        end
    end

    return _nodos!(plt, red, s, t, S)
end

"""
    dibujar_residual(red, F; titulo, s, t) -> Plots.Plot

Dibuja la red residual: cada arco con capacidad residual r > 0. Los
arcos "de avance" (capacidad original sin usar) se pintan de gris
sólido; los arcos "de retroceso" (permiten cancelar flujo ya
enviado) se pintan punteados en rojo.

# Argumentos
- `red::RedFlujo`: la red.
- `F::Matrix{Int}`: matriz de flujo actual.
- `titulo::String`: título del gráfico.
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `Plots.Plot`: gráfico de la red residual.
"""
function dibujar_residual(red::RedFlujo, F::Matrix{Int};
                          titulo::String="Red residual", s::Int=0, t::Int=0)
    plt = _lienzo(red, titulo)
    n = size(red.C, 1)
    for u in 1:n, v in 1:n
        r = red.C[u, v] - F[u, v]
        r > 0 || continue
        off = (red.C[v, u] - F[v, u] > 0) ? 0.07 : 0.0
        if red.C[u, v] > 0
            _flecha!(plt, red.pos[u], red.pos[v];
                     color=:gray50, lw=1.8, offset=off,
                     etiqueta="$r", lab_color=:gray35)
        else
            _flecha!(plt, red.pos[u], red.pos[v];
                     color=:indianred, lw=1.8, estilo=:dash, offset=off,
                     etiqueta="$r", lab_color=:indianred)
        end
    end
    return _nodos!(plt, red, s, t, Int[])
end

# ------------------------------------------------------------
# 6. Animación y modo interactivo
# ------------------------------------------------------------

"""
    _fotogramas(red, s, t, historia) -> Vector{NamedTuple}

Genera la secuencia de "fotogramas" lógicos de una ejecución: estado
inicial, luego (camino resaltado, flujo actualizado) por cada
iteración, y finalmente el corte mínimo.

# Argumentos
- `red::RedFlujo`: la red.
- `s::Int`, `t::Int`: fuente y sumidero.
- `historia::Vector{Paso}`: historial devuelto por `ford_fulkerson`.

# Salida
- `Vector{NamedTuple}`: un fotograma por cada paso de la animación,
  con campos `F`, `camino`, `S` y `titulo`.
"""
function _fotogramas(red::RedFlujo, s::Int, t::Int, historia::Vector{Paso})
    n = size(red.C, 1)
    frames = NamedTuple[]
    F_prev = zeros(Int, n, n)
    push!(frames, (F=F_prev, camino=Int[], S=Int[],
                   titulo="Red inicial — flujo = 0"))
    for (i, p) in enumerate(historia)
        ruta = join(red.nombres[p.camino], " → ")
        push!(frames, (F=F_prev, camino=p.camino, S=Int[],
                       titulo="Iteración $i: camino $ruta   (Δ = $(p.Δ))"))
        push!(frames, (F=p.F, camino=Int[], S=Int[],
                       titulo="Iteración $i: flujo total = $(p.flujo_total)"))
        F_prev = p.F
    end
    S, _ = corte_minimo(red.C, F_prev, s)
    flujo = isempty(historia) ? 0 : historia[end].flujo_total
    push!(frames, (F=F_prev, camino=Int[], S=S,
                   titulo="Flujo máximo = $flujo = capacidad del corte mínimo (S en dorado)"))
    return frames
end

"""
    dibujar_fotograma(red, fr; s, t, residual=true) -> Plots.Plot

Dibuja un fotograma de la animación: la red de flujo y,
opcionalmente, la red residual al lado.

# Argumentos
- `red::RedFlujo`: la red.
- `fr::NamedTuple`: un fotograma producido por `_fotogramas`.
- `s::Int`, `t::Int`: fuente y sumidero.
- `residual::Bool`: si es `true`, agrega el panel de la red residual.

# Salida
- `Plots.Plot`: figura combinada (uno o dos paneles).
"""
function dibujar_fotograma(red::RedFlujo, fr; s::Int, t::Int, residual::Bool=true)
    p1 = dibujar_red(red, fr.F; camino=fr.camino, titulo=fr.titulo,
                     S=fr.S, s=s, t=t)
    residual || return plot(p1, size=(680, 500))
    p2 = dibujar_residual(red, fr.F; s=s, t=t)
    return plot(p1, p2; layout=(1, 2), size=(1250, 500))
end

"""
    animar_ford_fulkerson(red, s, t; metodo=:bfs, archivo="ford_fulkerson.gif",
                          fps=0.6, residual=true, verbose=true) -> Plots.AnimatedGif

Ejecuta el algoritmo y guarda un GIF animado: cada iteración muestra
primero el camino aumentante resaltado y luego el flujo actualizado,
junto con la red residual. El último fotograma muestra el corte
mínimo.

# Argumentos
- `red::RedFlujo`, `s::Int`, `t::Int`: la red, fuente y sumidero.
- `metodo::Symbol`: `:bfs` o `:dfs`.
- `archivo::String`: ruta de salida del GIF.
- `fps::Real`: cuadros por segundo del GIF.
- `residual::Bool`: incluir panel de red residual.
- `verbose::Bool`: imprimir traza en consola.

# Salida
- `Plots.AnimatedGif`: objeto GIF (también queda escrito en `archivo`).
"""
function animar_ford_fulkerson(red::RedFlujo, s::Int, t::Int;
                               metodo::Symbol=:bfs,
                               archivo::String="ford_fulkerson.gif",
                               fps::Real=0.6, residual::Bool=true,
                               verbose::Bool=true)
    _, _, historia = ford_fulkerson(red, s, t; metodo=metodo, verbose=verbose)
    frames = _fotogramas(red, s, t, historia)
    anim = @animate for fr in frames
        dibujar_fotograma(red, fr; s=s, t=t, residual=residual)
    end
    return gif(anim, archivo; fps=fps)
end

"""
    ford_fulkerson_interactivo(red, s, t; metodo=:bfs, residual=true) -> Nothing

Modo interactivo para clase: muestra la ejecución fotograma a
fotograma en la ventana de gráficos; se presiona [Enter] en la
consola para avanzar al siguiente paso.

# Argumentos
- `red::RedFlujo`, `s::Int`, `t::Int`: la red, fuente y sumidero.
- `metodo::Symbol`: `:bfs` o `:dfs`.
- `residual::Bool`: incluir panel de red residual.

# Salida
- `Nothing`.
"""
function ford_fulkerson_interactivo(red::RedFlujo, s::Int, t::Int;
                                    metodo::Symbol=:bfs, residual::Bool=true)
    _, _, historia = ford_fulkerson(red, s, t; metodo=metodo, verbose=false)
    frames = _fotogramas(red, s, t, historia)
    for (k, fr) in enumerate(frames)
        display(dibujar_fotograma(red, fr; s=s, t=t, residual=residual))
        println("[$k/$(length(frames))] ", fr.titulo)
        if k < length(frames)
            print("    [Enter] para continuar... ")
            readline()
        end
    end
    return nothing
end

# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# Este archivo es un módulo de librería: no ejecuta ningún ejemplo
# por sí mismo. Los scripts numerados 03_parte1_exploracion_guiada.jl
# a 06_parte4_analisis_comparativo.jl hacen
# `include("01_ford_fulkerson.jl")` y son los que ejecutan el
# algoritmo sobre redes concretas. Aquí solo se deja una
# autocomprobación mínima cuando el archivo se ejecuta directamente
# (`julia --project=. 01_ford_fulkerson.jl`), para ver