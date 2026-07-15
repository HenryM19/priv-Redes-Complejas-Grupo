# ============================================================
# 02_edmonds_karp.jl
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Módulo base del algoritmo de EDMONDS-KARP para el problema de
# flujo máximo. Es el segundo archivo en el orden de ejecución de la
# práctica: los scripts 03 a 06 lo cargan con
# `include("02_edmonds_karp.jl")`.
#
# Edmonds-Karp es la especialización de Ford-Fulkerson en la que el
# camino aumentante SIEMPRE se busca con BFS (el camino con MENOS
# arcos). Esto garantiza:
#   1. Terminación incluso con capacidades irracionales.
#   2. Complejidad O(V·E²): la distancia BFS de s a cada nodo nunca
#      disminuye entre iteraciones, y cada arco puede "saturarse" a
#      lo sumo O(V) veces (lema demostrado en results/report/report.md).
#
# Contenido de este archivo:
#   1. Carga de librerías.
#   2. Estructuras de datos: `RedFlujo` y `PasoEK` (registro de una
#      iteración, incluida la información de niveles BFS).
#   3. BFS con registro de niveles y árbol de exploración (el
#      corazón de Edmonds-Karp).
#   4. El algoritmo de Edmonds-Karp y el cálculo del corte mínimo.
#   5. Funciones de dibujo: red de flujo, "onda" BFS y red residual.
#   6. Generación de animaciones GIF y modo interactivo paso a paso.
#
# Fundamento teórico: ver results/report/report.md, sección "Teoría".
#
# Fuente base: repositorio fabianastudillo/ComplexNetworks
#   (optimization/edmonds-karp/edmonds_karp.jl), adaptado y
#   redocumentado para esta actividad.
#
# Uso típico (ver 03_parte1_exploracion_guiada.jl):
#   include("02_edmonds_karp.jl")
#   flujo, F, historia = edmonds_karp(red, s, t)
#   animar_edmonds_karp(red, s, t; archivo="ek.gif")
#   edmonds_karp_interactivo(red, s, t)   # [Enter] para avanzar

# ------------------------------------------------------------
# 1. Carga de librerías
# ------------------------------------------------------------
using Plots
using Printf

# `RedFlujo` (y varias funciones auxiliares de dibujo/corte mínimo)
# se reutilizan de 01_ford_fulkerson.jl. Se incluye aquí para que
# este archivo sea autosuficiente si se ejecuta solo; el `include`
# de 01 está protegido con `if !@isdefined(...)` en sus structs, así
# que es seguro incluirlo más de una vez en la misma sesión (p. ej.
# cuando un script de la práctica ya hizo `include("01_...")` antes).
include(joinpath(@__DIR__, "01_ford_fulkerson.jl"))

# ------------------------------------------------------------
# 2. Estructuras de datos
# ------------------------------------------------------------
#
# `RedFlujo` ya quedó definida por el `include` anterior (mismo tipo
# que usa 01_ford_fulkerson.jl); aquí solo se agrega el registro de
# iteración propio de Edmonds-Karp, `PasoEK`, que además de guardar
# el camino y Δ, guarda la información de niveles BFS necesaria para
# animar la "onda" de exploración.

"""
    PasoEK

Registro de una iteración de Edmonds-Karp.

# Campos
- `camino::Vector{Int}`: camino aumentante (el más corto) encontrado.
- `Δ::Int`: cuello de botella de esa iteración.
- `F::Matrix{Int}`: matriz de flujo tras aumentar (antisimétrica).
- `flujo_total::Int`: valor acumulado del flujo.
- `nivel::Vector{Int}`: `nivel[v]` = distancia BFS desde `s` en la
  red residual (`-1` si `v` no es alcanzable).
- `arbol::Vector{Tuple{Int,Int}}`: arcos (u, v) del árbol BFS, en el
  orden en que se descubrieron los nodos (permite animar la "onda").
"""
if !@isdefined(PasoEK)
struct PasoEK
    camino::Vector{Int}
    Δ::Int
    F::Matrix{Int}
    flujo_total::Int
    nivel::Vector{Int}
    arbol::Vector{Tuple{Int,Int}}
end
end

# ------------------------------------------------------------
# 3. BFS con niveles (el corazón de Edmonds-Karp)
# ------------------------------------------------------------

"""
    _reconstruir(padre, s, t) -> Vector{Int}

Reconstruye el camino s→t a partir del vector de padres de la BFS.

# Argumentos
- `padre::Vector{Int}`: `padre[v]` es el nodo desde el que se
  descubrió `v`.
- `s::Int`, `t::Int`: fuente y sumidero.

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
    bfs_niveles(C, F, s, t) -> (camino, nivel, arbol)

BFS sobre la red residual desde `s`, registrando la distancia
(`nivel`) de cada nodo y el árbol de exploración. Como la BFS visita
los nodos por capas, el camino devuelto es de longitud MÍNIMA en
número de arcos: la propiedad que define a Edmonds-Karp.

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades originales.
- `F::Matrix{Int}`: matriz de flujo actual (antisimétrica).
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `camino::Vector{Int}`: camino más corto s→t en la red residual
  (`Int[]` si no existe).
- `nivel::Vector{Int}`: distancia BFS desde `s` a cada nodo.
- `arbol::Vector{Tuple{Int,Int}}`: arcos del árbol de exploración
  BFS, en orden de descubrimiento.

Nota: para poder animar la onda completa, esta versión no se
detiene al llegar a `t`; explora todos los nodos alcanzables (una
implementación de producción se detendría en `t`).
"""
function bfs_niveles(C::Matrix{Int}, F::Matrix{Int}, s::Int, t::Int)
    n = size(C, 1)
    nivel = fill(-1, n)
    padre = zeros(Int, n)
    nivel[s] = 0
    padre[s] = s
    cola = [s]
    arbol = Tuple{Int,Int}[]
    while !isempty(cola)
        u = popfirst!(cola)
        for v in 1:n
            if nivel[v] == -1 && C[u, v] - F[u, v] > 0
                nivel[v] = nivel[u] + 1
                padre[v] = u
                push!(arbol, (u, v))
                push!(cola, v)
            end
        end
    end
    camino = nivel[t] == -1 ? Int[] : _reconstruir(padre, s, t)
    return camino, nivel, arbol
end

# ------------------------------------------------------------
# 4. Algoritmo de Edmonds-Karp y corte mínimo
# ------------------------------------------------------------

"""
    edmonds_karp(red, s, t; verbose=true) -> (flujo_max, F, historia)

Calcula el flujo máximo de `s` a `t` con Edmonds-Karp: en cada
iteración, busca con BFS el camino aumentante más corto (en número
de arcos) y aumenta el flujo en su cuello de botella Δ.

# Argumentos
- `red::RedFlujo`: la red de flujo.
- `s::Int`, `t::Int`: fuente y sumidero.
- `verbose::Bool`: si es `true`, imprime una tabla con la longitud
  de cada camino aumentante (las longitudes nunca decrecen: el lema
  central de la demostración de la cota O(V·E²)).

# Salida
- `flujo_max::Int`: valor del flujo máximo.
- `F::Matrix{Int}`: matriz de flujo final (antisimétrica).
- `historia::Vector{PasoEK}`: registro de cada iteración, usado por
  las funciones de animación.
"""
function edmonds_karp(red::RedFlujo, s::Int, t::Int; verbose::Bool=true)
    C = red.C
    n = size(C, 1)
    F = zeros(Int, n, n)
    historia = PasoEK[]
    flujo_total = 0

    verbose && @printf("%-5s %-9s %-6s %-7s %s\n",
                       "Iter", "Longitud", "Δ", "Flujo", "Camino")
    while true
        camino, nivel, arbol = bfs_niveles(C, F, s, t)
        isempty(camino) && break

        Δ = minimum(C[camino[i], camino[i+1]] - F[camino[i], camino[i+1]]
                    for i in 1:length(camino)-1)

        for i in 1:length(camino)-1
            u, v = camino[i], camino[i+1]
            F[u, v] += Δ
            F[v, u] -= Δ
        end
        flujo_total += Δ

        push!(historia, PasoEK(camino, Δ, copy(F), flujo_total, nivel, arbol))
        verbose && @printf("%-5d %-9d %-6d %-7d %s\n",
                           length(historia), length(camino) - 1, Δ, flujo_total,
                           join(red.nombres[camino], " → "))
    end

    if verbose
        longitudes = [length(p.camino) - 1 for p in historia]
        @printf("\nFlujo máximo: %d (en %d iteraciones)\n",
                flujo_total, length(historia))
        println("Longitudes de los caminos: ", join(longitudes, ", "),
                "  → no decrecientes ✓ (lema de Edmonds-Karp)")
    end
    return flujo_total, F, historia
end

"""
    corte_minimo(C, F, s) -> (S, aristas_corte)

Con el flujo máximo `F`, calcula el corte mínimo (S, V∖S): `S` es el
conjunto de nodos alcanzables desde `s` en la red residual.

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades originales.
- `F::Matrix{Int}`: matriz de flujo (típicamente el flujo máximo).
- `s::Int`: nodo fuente.

# Salida
- `S::Vector{Int}`: nodos alcanzables desde `s` en la red residual.
- `aristas_corte::Vector{Tuple{Int,Int}}`: arcos originales que
  cruzan de `S` hacia `V∖S`; la suma de sus capacidades es
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

# Paleta de colores para los niveles BFS (nivel 0 = fuente)
const PALETA_NIVELES = [:gold, :palegreen, :skyblue, :plum,
                        :lightsalmon, :khaki, :lightpink]

"""
    _flecha!(plt, p1, p2; color, lw, estilo, etiqueta, lab_color, offset, radio)

Dibuja sobre `plt` una flecha de `p1` a `p2`, acortada para no tapar
los nodos, con desplazamiento perpendicular `offset` (arcos
antiparalelos) y una etiqueta opcional en el punto medio.

# Argumentos
- `plt`: objeto de gráfico de Plots.jl.
- `p1::Tuple`, `p2::Tuple`: coordenadas de origen y destino.
- `color`, `lw::Real`, `estilo::Symbol`: estilo de línea.
- `etiqueta::String`: texto a mostrar.
- `lab_color`: color del texto.
- `offset::Real`, `radio::Real`: desplazamiento y acortamiento.

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
    _lienzo(red, titulo) -> Plots.Plot

Crea el lienzo base (ejes ocultos, proporción 1:1) con límites
calculados a partir de las posiciones de los nodos.

# Argumentos
- `red::RedFlujo`: la red.
- `titulo::String`: título del gráfico.

# Salida
- `Plots.Plot`: lienzo vacío.
"""
function _lienzo(red::RedFlujo, titulo::String)
    xs = [p[1] for p in red.pos]; ys = [p[2] for p in red.pos]
    return plot(; legend=false, axis=false, grid=false, ticks=false,
                aspect_ratio=:equal, title=titulo, titlefontsize=10,
                xlims=(minimum(xs) - 0.45, maximum(xs) + 0.45),
                ylims=(minimum(ys) - 0.55, maximum(ys) + 0.45))
end

"""
    _nodos!(plt, red, s, t, S) -> plt

Dibuja los nodos con sus nombres, coloreando de dorado los de `S`.

# Argumentos
- `plt`: objeto de gráfico.
- `red::RedFlujo`: la red.
- `s::Int`, `t::Int`: fuente y sumidero.
- `S::Vector{Int}`: nodos a resaltar en dorado (opcional).

# Salida
- `plt`: el mismo objeto de gráfico, modificado en el lugar.
"""
function _nodos!(plt, red::RedFlujo, s::Int, t::Int, S::Vector{Int})
    for i in 1:length(red.nombres)
        color = i in S ? :gold :
                i == s ? :palegreen :
                i == t ? :lightsalmon : :lightblue
        scatter!(plt, [red.pos[i][1]], [red.pos[i][2]];
                 markersize=17, color=color, markerstrokecolor=:black,
                 markerstrokewidth=1.5)
        annotate!(plt, red.pos[i][1], red.pos[i][2],
                  text(red.nombres[i], 10, :black, :center))
    end
    return plt
end

"""
    dibujar_red(red, F; camino, titulo, S, s, t) -> Plots.Plot

Dibuja la red de flujo con etiquetas "flujo/capacidad". Arcos con
flujo en azul, sin flujo en gris; el `camino` aumentante en naranja
(punteado si usa un arco residual inverso); si `S` no está vacío,
resalta el corte mínimo en púrpura.

# Argumentos
- `red::RedFlujo`: la red.
- `F::Matrix{Int}`: matriz de flujo a graficar.
- `camino::Vector{Int}`: camino a resaltar (opcional).
- `titulo::String`: título del gráfico.
- `S::Vector{Int}`: lado fuente del corte mínimo (opcional).
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `Plots.Plot`: gráfico de la red de flujo.
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
    dibujar_bfs(red, F; nivel, arbol, hasta, camino, titulo, s, t) -> Plots.Plot

Dibuja la "onda" BFS sobre la red residual: arcos residuales de
fondo en gris claro; arcos del árbol BFS descubiertos hasta el nivel
`hasta` en verde azulado; nodos coloreados según su nivel BFS
(distancia desde `s`), con la distancia anotada debajo; si se pasa
`camino`, se resalta en naranja (el camino más corto).

# Argumentos
- `red::RedFlujo`: la red.
- `F::Matrix{Int}`: matriz de flujo actual.
- `nivel::Vector{Int}`: nivel BFS de cada nodo.
- `arbol::Vector{Tuple{Int,Int}}`: arcos del árbol BFS.
- `hasta::Int`: nivel máximo a mostrar (para animar la onda).
- `camino::Vector{Int}`: camino más corto a resaltar (opcional).
- `titulo::String`: título del gráfico.
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `Plots.Plot`: gráfico de la onda BFS / red residual.
"""
function dibujar_bfs(red::RedFlujo, F::Matrix{Int};
                     nivel::Vector{Int}, arbol::Vector{Tuple{Int,Int}},
                     hasta::Int, camino::Vector{Int}=Int[],
                     titulo::String="Onda BFS en la red residual",
                     s::Int=0, t::Int=0)
    plt = _lienzo(red, titulo)
    n = size(red.C, 1)
    _off(u, v) = (red.C[v, u] - F[v, u] > 0) ? 0.07 : 0.0

    for u in 1:n, v in 1:n
        if red.C[u, v] - F[u, v] > 0
            _flecha!(plt, red.pos[u], red.pos[v];
                     color=:gray85, lw=1.2, offset=_off(u, v))
        end
    end

    for (u, v) in arbol
        nivel[v] <= hasta || continue
        r = red.C[u, v] - F[u, v]
        _flecha!(plt, red.pos[u], red.pos[v];
                 color=:teal, lw=2.5, offset=_off(u, v),
                 etiqueta="$r", lab_color=:teal)
    end

    for i in 1:length(camino)-1
        u, v = camino[i], camino[i+1]
        _flecha!(plt, red.pos[u], red.pos[v];
                 color=:orangered, lw=4, offset=_off(u, v))
    end

    for i in 1:n
        alcanzado = nivel[i] >= 0 && nivel[i] <= hasta
        color = alcanzado ? PALETA_NIVELES[mod1(nivel[i] + 1, length(PALETA_NIVELES))] :
                            :gray92
        scatter!(plt, [red.pos[i][1]], [red.pos[i][2]];
                 markersize=17, color=color, markerstrokecolor=:black,
                 markerstrokewidth=1.5)
        annotate!(plt, red.pos[i][1], red.pos[i][2],
                  text(red.nombres[i], 10, :black, :center))
        alcanzado && annotate!(plt, red.pos[i][1], red.pos[i][2] - 0.3,
                               text("d=$(nivel[i])", 8, :teal, :center))
    end
    return plt
end

"""
    dibujar_residual(red, F; titulo, s, t) -> Plots.Plot

Dibuja la red residual: gris sólido = capacidad restante de los
arcos originales; rojo punteado = arcos de retroceso.

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

Genera la secuencia de fotogramas de una ejecución: por cada
iteración, la onda BFS creciendo nivel a nivel, el camino más corto
encontrado y el flujo actualizado; al final, el corte mínimo.

# Argumentos
- `red::RedFlujo`: la red.
- `s::Int`, `t::Int`: fuente y sumidero.
- `historia::Vector{PasoEK}`: historial de `edmonds_karp`.

# Salida
- `Vector{NamedTuple}`: un fotograma por paso, con campo `tipo`
  (`:bfs`, `:camino`, `:flujo` o `:corte`).
"""
function _fotogramas(red::RedFlujo, s::Int, t::Int, historia::Vector{PasoEK})
    n = size(red.C, 1)
    frames = NamedTuple[]
    F_prev = zeros(Int, n, n)
    sin_nivel = fill(-1, n)
    push!(frames, (tipo=:flujo, F=F_prev, camino=Int[], S=Int[],
                   nivel=sin_nivel, arbol=Tuple{Int,Int}[], hasta=-1,
                   titulo="Red inicial — flujo = 0"))
    for (i, p) in enumerate(historia)
        d_t = p.nivel[t]
        for k in 1:d_t
            push!(frames, (tipo=:bfs, F=F_prev, camino=Int[], S=Int[],
                           nivel=p.nivel, arbol=p.arbol, hasta=k,
                           titulo="Iteración $i — BFS explora el nivel $k"))
        end
        ruta = join(red.nombres[p.camino], " → ")
        push!(frames, (tipo=:camino, F=F_prev, camino=p.camino, S=Int[],
                       nivel=p.nivel, arbol=p.arbol, hasta=d_t,
                       titulo="Iteración $i — camino más corto (long. $d_t): $ruta, Δ = $(p.Δ)"))
        push!(frames, (tipo=:flujo, F=p.F, camino=Int[], S=Int[],
                       nivel=sin_nivel, arbol=Tuple{Int,Int}[], hasta=-1,
                       titulo="Iteración $i — flujo total = $(p.flujo_total)"))
        F_prev = p.F
    end
    S, _ = corte_minimo(red.C, F_prev, s)
    flujo = isempty(historia) ? 0 : historia[end].flujo_total
    push!(frames, (tipo=:corte, F=F_prev, camino=Int[], S=S,
                   nivel=sin_nivel, arbol=Tuple{Int,Int}[], hasta=-1,
                   titulo="Flujo máximo = $flujo = capacidad del corte mínimo (S en dorado)"))
    return frames
end

"""
    dibujar_fotograma_ek(red, fr; s, t) -> Plots.Plot

Dibuja un fotograma completo de Edmonds-Karp: a la izquierda la red
de flujo; a la derecha, la onda BFS (fotogramas `:bfs`/`:camino`) o
la red residual (fotogramas `:flujo`/`:corte`).

Nota de nomenclatura: se llama `dibujar_fotograma_ek` (con sufijo
`_ek`), y NO `dibujar_fotograma` como en 01_ford_fulkerson.jl, a
propósito. Ambas funciones comparten la misma firma posicional
(`RedFlujo`, fotograma), pero difieren en sus argumentos de palabra
clave (`residual=true` en 01, ausente aquí); si tuvieran el mismo
nombre, incluir ambos archivos en la misma sesión haría que la
segunda definición reemplace silenciosamente a la primera, rompiendo
las llamadas de 01 que usan `residual=`.

# Argumentos
- `red::RedFlujo`: la red.
- `fr::NamedTuple`: fotograma producido por `_fotogramas`.
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `Plots.Plot`: figura combinada de dos paneles.
"""
function dibujar_fotograma_ek(red::RedFlujo, fr; s::Int, t::Int)
    izq = dibujar_red(red, fr.F;
                      camino=fr.tipo == :camino ? fr.camino : Int[],
                      titulo=fr.titulo, S=fr.S, s=s, t=t)
    der = if fr.tipo in (:bfs, :camino)
        dibujar_bfs(red, fr.F; nivel=fr.nivel, arbol=fr.arbol, hasta=fr.hasta,
                    camino=fr.tipo == :camino ? fr.camino : Int[], s=s, t=t)
    else
        dibujar_residual(red, fr.F; s=s, t=t)
    end
    return plot(izq, der; layout=(1, 2), size=(1250, 500))
end

"""
    animar_edmonds_karp(red, s, t; archivo="edmonds_karp.gif", fps=0.8,
                        verbose=true) -> Plots.AnimatedGif

Ejecuta el algoritmo y guarda un GIF animado: cada iteración muestra
la onda BFS creciendo capa por capa, el camino más corto resaltado y
el flujo actualizado; el último fotograma muestra el corte mínimo.

# Argumentos
- `red::RedFlujo`, `s::Int`, `t::Int`: la red, fuente y sumidero.
- `archivo::String`: ruta de salida del GIF.
- `fps::Real`: cuadros por segundo.
- `verbose::Bool`: imprimir traza en consola.

# Salida
- `Plots.AnimatedGif`: objeto GIF (también queda escrito en `archivo`).
"""
function animar_edmonds_karp(red::RedFlujo, s::Int, t::Int;
                             archivo::String="edmonds_karp.gif",
                             fps::Real=0.8, verbose::Bool=true)
    _, _, historia = edmonds_karp(red, s, t; verbose=verbose)
    frames = _fotogramas(red, s, t, historia)
    anim = @animate for fr in frames
        dibujar_fotograma_ek(red, fr; s=s, t=t)
    end
    return gif(anim, archivo; fps=fps)
end

"""
    edmonds_karp_interactivo(red, s, t) -> Nothing

Modo interactivo para clase: muestra la ejecución fotograma a
fotograma (incluida la onda BFS) en la ventana de gráficos; se
presiona [Enter] en la consola para avanzar al siguiente paso.

# Argumentos
- `red::RedFlujo`, `s::Int`, `t::Int`: la red, fuente y sumidero.

# Salida
- `Nothing`.
"""
function edmonds_karp_interactivo(red::RedFlujo, s::Int, t::Int)
    _, _, historia = edmonds_karp(red, s, t; verbose=false)
    frames = _fotogramas(red, s, t, historia)
    for (k, fr) in enumerate(frames)
        display(dibujar_fotograma_ek(red, fr; s=s, t=t))
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