# ============================================================
# motor.jl — Instrumentación de Ford-Fulkerson / Edmonds-Karp
# ============================================================
#
# Carga las implementaciones del repositorio del profesor y añade:
#
#   1. `buscar_camino_dfs_adversaria` — la DFS modificada de la Parte 2.3
#      (invierte el orden de exploración de los vecinos).
#   2. `ford_fulkerson_instr` — misma mecánica que `ford_fulkerson`, pero
#      admite cualquier función de búsqueda y devuelve métricas (número de
#      iteraciones, longitudes de los caminos, tiempo, nodos visitados).
#   3. Utilidades de reporte: `tabla_iteraciones`, `resumen_corte`, `a_dict`.
#
# El código base NO se modifica: se incluye tal cual y se extiende aquí.
# Esto mantiene la trazabilidad con el repositorio original.

include("ford_fulkerson.jl")   # RedFlujo, Paso, buscar_camino_bfs/dfs, corte_minimo, dibujos
include("redes.jl")

using Printf

# ------------------------------------------------------------
# 1. La DFS adversaria (Parte 2.3)
# ------------------------------------------------------------

"""
    buscar_camino_dfs_adversaria(C, F, s, t) -> Vector{Int}

Variante de `buscar_camino_dfs` con el orden de exploración INVERTIDO.

El original recorre `for v in n:-1:1` empujando a una pila; como la pila
saca el último insertado, el efecto neto es visitar primero los vecinos de
índice BAJO. Esta versión recorre `for v in 1:n`, de modo que la pila saca
primero los vecinos de índice ALTO.

En la red zigzag (s=1, u=2, v=3, t=4) el cambio es decisivo: desde `s` se
apila u y luego v, y la pila devuelve v... pero desde `u` el vecino de
índice más alto es `t`, no `v`. La DFS por sí sola no basta para forzar el
peor caso; por eso `buscar_camino_zigzag` (abajo) implementa el adversario
explícito que la guía describe en teoría.
"""
function buscar_camino_dfs_adversaria(C::Matrix{Int}, F::Matrix{Int}, s::Int, t::Int)
    n = size(C, 1)
    padre = zeros(Int, n)
    padre[s] = s
    pila = [s]
    while !isempty(pila)
        u = pop!(pila)
        for v in 1:n   # ORDEN INVERTIDO respecto al original (n:-1:1)
            if padre[v] == 0 && C[u, v] - F[u, v] > 0
                padre[v] = u
                v == t && return _reconstruir(padre, s, t)
                push!(pila, v)
            end
        end
    end
    return Int[]
end

"""
    buscar_camino_zigzag(C, F, s, t) -> Vector{Int}

El ADVERSARIO del peor caso: DFS que prefiere explícitamente el arco
trampa. Prioriza, para cada nodo, el vecino residual que NO lleva
directamente a `t`; solo cuando no hay otra opción avanza hacia `t`.

Esto reproduce el comportamiento patológico que la guía menciona en teoría
(2M iteraciones en la red zigzag) y que ni la DFS del repositorio ni la
adversaria por índices alcanzan. Sirve como cota superior experimental:
demuestra que el problema NO está en DFS-vs-BFS por sí mismo, sino en el
poder de elegir mal el camino, que BFS elimina por construcción.
"""
function buscar_camino_zigzag(C::Matrix{Int}, F::Matrix{Int}, s::Int, t::Int)
    n = size(C, 1)
    padre = zeros(Int, n)
    padre[s] = s
    pila = [s]
    while !isempty(pila)
        u = pop!(pila)
        # Vecinos residuales de u, con los que llevan a t al final:
        # la pila saca el último ⇒ ponemos t primero para sacarlo último.
        vecinos = [v for v in 1:n if padre[v] == 0 && C[u, v] - F[u, v] > 0]
        sort!(vecinos; by = v -> (v == t ? 0 : 1))   # t primero en la lista
        for v in vecinos
            padre[v] = u
            push!(pila, v)
        end
        # Si t quedó descubierto y ya no hay alternativas más profundas,
        # la pila lo alcanzará al final. Comprobamos si se cerró el camino.
        if padre[t] != 0 && isempty([v for v in pila if v != t])
            return _reconstruir(padre, s, t)
        end
    end
    return padre[t] != 0 ? _reconstruir(padre, s, t) : Int[]
end

# ------------------------------------------------------------
# 2. Ford-Fulkerson instrumentado
# ------------------------------------------------------------

"""
    Corrida

Resultado completo de una ejecución, con todo lo que la guía pide tabular.
"""
struct Corrida
    etiqueta::String            # "BFS (Edmonds-Karp)", "DFS (clásico)", ...
    flujo::Int
    iteraciones::Int
    caminos::Vector{Vector{Int}}    # caminos aumentantes (índices de nodo)
    longitudes::Vector{Int}         # nº de arcos de cada camino
    deltas::Vector{Int}             # cuello de botella de cada iteración
    acumulado::Vector{Int}          # flujo total tras cada iteración
    usa_retroceso::Vector{Bool}     # ¿la iteración usó un arco de retroceso?
    F::Matrix{Int}
    historia::Vector{Paso}
    tiempo_ms::Float64
    no_decrecientes::Bool           # ¿las longitudes nunca decrecen?
end

"""
    ford_fulkerson_instr(red, s, t; buscar, etiqueta, limite) -> Corrida

Mismo ciclo que `ford_fulkerson` del repositorio, con `buscar` inyectable
(BFS, DFS, DFS adversaria o el adversario zigzag) y registro de métricas.

`limite` corta la ejecución si se superan esas iteraciones (protección para
los experimentos con M grande).
"""
function ford_fulkerson_instr(red::RedFlujo, s::Int, t::Int;
                              buscar::Function = buscar_camino_bfs,
                              etiqueta::String = "BFS",
                              limite::Int = 1_000_000)
    C = red.C
    n = size(C, 1)
    F = zeros(Int, n, n)
    historia = Paso[]
    caminos = Vector{Int}[]; longitudes = Int[]; deltas = Int[]
    acumulado = Int[]; retroceso = Bool[]
    flujo_total = 0

    t0 = time_ns()
    while length(historia) < limite
        camino = buscar(C, F, s, t)
        isempty(camino) && break

        Δ = minimum(C[camino[i], camino[i+1]] - F[camino[i], camino[i+1]]
                    for i in 1:length(camino)-1)

        # ¿Alguno de los arcos del camino es de retroceso? (C original = 0)
        usa_ret = any(C[camino[i], camino[i+1]] == 0 for i in 1:length(camino)-1)

        for i in 1:length(camino)-1
            u, v = camino[i], camino[i+1]
            F[u, v] += Δ
            F[v, u] -= Δ
        end
        flujo_total += Δ

        push!(historia, Paso(camino, Δ, copy(F), flujo_total))
        push!(caminos, camino); push!(longitudes, length(camino) - 1)
        push!(deltas, Δ); push!(acumulado, flujo_total); push!(retroceso, usa_ret)
    end
    tiempo_ms = (time_ns() - t0) / 1e6

    no_dec = all(longitudes[i] <= longitudes[i+1] for i in 1:length(longitudes)-1)

    return Corrida(etiqueta, flujo_total, length(historia), caminos, longitudes,
                   deltas, acumulado, retroceso, F, historia, tiempo_ms, no_dec)
end

# ------------------------------------------------------------
# 3. Reporte
# ------------------------------------------------------------

"Nombre legible de un camino: s → v₁ → v₃ → t"
ruta_str(red::RedFlujo, camino::Vector{Int}) = join(red.nombres[camino], " → ")

"""
    tabla_iteraciones(red, c::Corrida; io=stdout)

Imprime la tabla que pide la Parte 1.1: iteración, camino, longitud,
cuello de botella Δ y flujo acumulado.
"""
function tabla_iteraciones(red::RedFlujo, c::Corrida; io::IO = stdout)
    println(io, "\n── $(c.etiqueta) ──")
    @printf(io, "%-5s %-34s %-9s %-5s %-8s %s\n",
            "Iter", "Camino aumentante", "Longitud", "Δ", "Flujo", "Retroceso")
    for i in 1:c.iteraciones
        @printf(io, "%-5d %-34s %-9d %-5d %-8d %s\n",
                i, ruta_str(red, c.caminos[i]), c.longitudes[i],
                c.deltas[i], c.acumulado[i], c.usa_retroceso[i] ? "sí" : "—")
    end
    @printf(io, "→ flujo máximo = %d en %d iteraciones · longitudes: %s %s\n",
            c.flujo, c.iteraciones, join(c.longitudes, ", "),
            c.no_decrecientes ? "(no decrecientes ✓)" : "(DECRECEN ✗)")
    return nothing
end

"""
    resumen_corte(red, F, s) -> (S, aristas, capacidad, texto)

Calcula el corte mínimo y verifica a mano su capacidad (Parte 3).
"""
function resumen_corte(red::RedFlujo, F::Matrix{Int}, s::Int)
    S, aristas = corte_minimo(red.C, F, s)
    cap = isempty(aristas) ? 0 : sum(red.C[u, v] for (u, v) in aristas)
    detalle = join(["$(red.nombres[u])→$(red.nombres[v]) ($(red.C[u,v]))"
                    for (u, v) in aristas], " + ")
    texto = "S = {" * join(red.nombres[S], ", ") * "}   |   " *
            detalle * " = " * string(cap)
    return S, aristas, cap, texto
end

# ------------------------------------------------------------
# 4. Serialización a JSON (sin dependencias externas)
# ------------------------------------------------------------

_json(x::String) = "\"" * replace(x, "\\" => "\\\\", "\"" => "\\\"") * "\""
_json(x::Bool) = x ? "true" : "false"
_json(x::Integer) = string(x)
_json(x::AbstractFloat) = string(round(x; digits = 4))
_json(x::Nothing) = "null"
_json(x::AbstractVector) = "[" * join(map(_json, x), ",") * "]"
_json(x::Tuple) = "[" * join(map(_json, collect(x)), ",") * "]"
function _json(d::AbstractDict)
    partes = ["$(_json(string(k))):$(_json(v))" for (k, v) in d]
    return "{" * join(partes, ",") * "}"
end

"Convierte una `Corrida` en un diccionario listo para serializar."
function a_dict(red::RedFlujo, c::Corrida)
    return Dict{String,Any}(
        "etiqueta"        => c.etiqueta,
        "flujo"           => c.flujo,
        "iteraciones"     => c.iteraciones,
        "longitudes"      => c.longitudes,
        "deltas"          => c.deltas,
        "acumulado"       => c.acumulado,
        "usa_retroceso"   => c.usa_retroceso,
        "caminos"         => [ruta_str(red, p) for p in c.caminos],
        "tiempo_ms"       => c.tiempo_ms,
        "no_decrecientes" => c.no_decrecientes,
    )
end

"Escribe `obj` como JSON indentado mínimo en `ruta`."
function guardar_json(ruta::String, obj)
    open(ruta, "w") do io
        write(io, _json(obj))
    end
    println("  ✓ $ruta")
    return ruta
end
