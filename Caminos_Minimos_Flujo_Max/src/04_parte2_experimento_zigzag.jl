# ============================================================
# 04_parte2_experimento_zigzag.jl
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Resuelve la PARTE 2 — El experimento zigzag de la Guía_Actividad.
#
# La red "zigzag" tiene un arco trampa u→v de capacidad 1 entre dos
# rutas de capacidad M (s→u→t y s→v→t). En teoría, un Ford-Fulkerson
# que siempre eligiera el camino que atraviesa ese arco necesitaría
# 2M iteraciones.
#
# Este script:
#   1. Ejecuta BFS (Edmonds-Karp) y DFS (versión del repositorio,
#      la de 01_ford_fulkerson.jl) sobre la red zigzag para
#      M ∈ {10, 100, 1000, 10000} y tabula iteraciones y caminos.
#   2. Analiza si la implementación DFS del repositorio alcanza el
#      peor caso teórico de 2M iteraciones (respuesta corta: no; se
#      explica el porqué a partir del orden de exploración de
#      `buscar_camino_dfs`).
#   3. Implementa una variante `buscar_camino_dfs_modificado` con el
#      orden de vecinos invertido y mide su efecto (tampoco alcanza
#      el peor caso: se explica por qué, ya que el marcado de nodos
#      visitados ocurre al descubrirlos, no al visitarlos, y `s`
#      descubre a `u` y `v` en el mismo barrido).
#   4. Para verificar experimentalmente que la cota teórica 2M sí es
#      alcanzable (y así responder con evidencia el porqué
#      Edmonds-Karp es inmune), implementa además un
#      `oraculo_adversarial`: una función de elección de camino que,
#      mientras el arco trampa tenga capacidad residual en cualquier
#      sentido, SIEMPRE fuerza el camino de 3 arcos que lo atraviesa
#      en vez del camino directo de 2 arcos. Esta variante sí
#      requiere exactamente 2M iteraciones, confirmando la cota
#      teórica de forma experimental.
#   5. Guarda las tablas (CSV), un gráfico comparativo
#      iteraciones-vs-M (escala log-log) y las animaciones GIF para
#      M = 10.
#
# Ejecutar desde la carpeta `src/`:
#   julia --project=.. 04_parte2_experimento_zigzag.jl

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
include("01_ford_fulkerson.jl")
using CSV
using DataFrames
using Plots
using Printf

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

"""
    red_zigzag(M) -> (RedFlujo, Int, Int)

Construye la red "zigzag": nodos s, u, v, t con arcos s→u (M),
s→v (M), u→v (1, el arco trampa), u→t (M), v→t (M).

# Argumentos
- `M::Int`: capacidad de los cuatro arcos "grandes" de la red.

# Salida
- `RedFlujo`: la red con 4 nodos.
- `Int`, `Int`: índices de la fuente `s=1` y el sumidero `t=4`.
"""
function red_zigzag(M::Int)
    nombres = ["s", "u", "v", "t"]
    pos = [(0.0, 1.0), (1.2, 2.0), (1.2, 0.0), (2.4, 1.0)]
    C = zeros(Int, 4, 4)
    C[1, 2] = M   # s → u
    C[1, 3] = M   # s → v
    C[2, 3] = 1   # u → v (arco trampa)
    C[2, 4] = M   # u → t
    C[3, 4] = M   # v → t
    return RedFlujo(C, nombres, pos), 1, 4
end

"""
    buscar_camino_dfs_modificado(C, F, s, t) -> Vector{Int}

Variante de `buscar_camino_dfs` (definida en 01_ford_fulkerson.jl)
con el orden de recorrido de vecinos INVERTIDO: en vez de
`for v in n:-1:1` (que, combinado con la pila LIFO, explora primero
los índices bajos) se usa `for v in 1:n` (que explora primero los
índices altos). Es la modificación pedida en la Parte 2, pregunta 3.

# Argumentos
- `C::Matrix{Int}`: matriz de capacidades.
- `F::Matrix{Int}`: matriz de flujo actual.
- `s::Int`, `t::Int`: fuente y sumidero.

# Salida
- `Vector{Int}`: camino aumentante encontrado, o `Int[]` si no existe.
"""
function buscar_camino_dfs_modificado(C::Matrix{Int}, F::Matrix{Int}, s::Int, t::Int)
    n = size(C, 1)
    padre = zeros(Int, n)
    padre[s] = s
    pila = [s]
    while !isempty(pila)
        u = pop!(pila)
        for v in 1:n   # orden ascendente (modificado; explora primero índices altos al hacer pop)
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
    oraculo_adversarial(C, F, s_u, u_v, v_t, s, u, v, t) -> Vector{Int}

Función de elección de camino DELIBERADAMENTE adversarial (no es
BFS ni DFS): mientras el arco trampa `u↔v` tenga capacidad residual
en cualquier sentido y las rutas de entrada/salida correspondientes
no estén agotadas, fuerza el camino de 3 arcos que lo atraviesa,
incluso si el camino directo de 2 arcos tiene mucha más capacidad
residual disponible. Solo cuando el arco trampa está agotado en
ambos sentidos recurre al camino directo.

Se usa para verificar EXPERIMENTALMENTE que la cota teórica de 2M
iteraciones (mencionada en la guía) es alcanzable: ni la DFS del
repositorio ni la DFS con orden invertido la alcanzan (ver
`buscar_camino_dfs` y `buscar_camino_dfs_modificado`), porque ambas
marcan `u` y `v` como visitados en el mismo barrido de los vecinos
de `s`, impidiendo que uno alcance al otro por el arco trampa. Este
oráculo elimina esa restricción a propósito.

# Argumentos
- `C::Matrix{Int}`, `F::Matrix{Int}`: capacidades y flujo actual.
- `s::Int`, `u::Int`, `v::Int`, `t::Int`: índices de los 4 nodos de
  la red zigzag.

# Salida
- `Vector{Int}`: camino aumentante elegido adversarialmente.
"""
function oraculo_adversarial(C::Matrix{Int}, F::Matrix{Int}, s::Int, u::Int, v::Int, t::Int)
    if C[u, v] - F[u, v] > 0 && C[s, u] - F[s, u] > 0 && C[v, t] - F[v, t] > 0
        return [s, u, v, t]
    elseif C[v, u] - F[v, u] > 0 && C[s, v] - F[s, v] > 0 && C[u, t] - F[u, t] > 0
        return [s, v, u, t]
    elseif C[s, u] - F[s, u] > 0 && C[u, t] - F[u, t] > 0
        return [s, u, t]
    elseif C[s, v] - F[s, v] > 0 && C[v, t] - F[v, t] > 0
        return [s, v, t]
    else
        return Int[]
    end
end

"""
    ejecutar_con_buscador(red, s, t, buscar) -> (flujo_max, historia)

Corre el bucle genérico de Ford-Fulkerson (idéntico al de
`ford_fulkerson`) pero con una función `buscar` arbitraria, para
poder reutilizar el mismo bucle con `buscar_camino_dfs_modificado`
u `oraculo_adversarial`.

# Argumentos
- `red::RedFlujo`: la red.
- `s::Int`, `t::Int`: fuente y sumidero.
- `buscar::Function`: función `(C, F, s, t) -> Vector{Int}` que
  devuelve el siguiente camino aumentante.

# Salida
- `flujo_max::Int`: valor del flujo máximo obtenido.
- `historia::Vector{Paso}`: registro de cada iteración.
"""
function ejecutar_con_buscador(red::RedFlujo, s::Int, t::Int, buscar::Function)
    C = red.C
    n = size(C, 1)
    F = zeros(Int, n, n)
    historia = Paso[]
    flujo_total = 0
    while true
        camino = buscar(C, F, s, t)
        isempty(camino) && break
        Δ = minimum(C[camino[i], camino[i+1]] - F[camino[i], camino[i+1]]
                    for i in 1:length(camino)-1)
        for i in 1:length(camino)-1
            uu, vv = camino[i], camino[i+1]
            F[uu, vv] += Δ
            F[vv, uu] -= Δ
        end
        flujo_total += Δ
        push!(historia, Paso(camino, Δ, copy(F), flujo_total))
    end
    return flujo_total, historia
end

# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Para M en {10,100,1000,10000}: correr BFS y DFS estándar,
#    tabular iteraciones y flujo máximo.
# 2) Correr también la DFS modificada y el oráculo adversarial.
# 3) Guardar la tabla combinada, un gráfico log-log iteraciones-vs-M
#    y las animaciones GIF de BFS y DFS estándar para M = 10.
mkpath("../results/files")
mkpath("../results/images")
mkpath("../results/animations")

Ms = [10, 100, 1000, 10000]
filas = DataFrame(M=Int[], metodo=String[], iteraciones=Int[], flujo_max=Int[])

println("="^60)
println("PARTE 2 — Experimento zigzag")
println("="^60)

for M in Ms
    red, s, t = red_zigzag(M)
    u, v = 2, 3

    fb, _, hb = ford_fulkerson(red, s, t; metodo=:bfs, verbose=false)
    push!(filas, (M, "BFS (Edmonds-Karp)", length(hb), fb))

    fd, _, hd = ford_fulkerson(red, s, t; metodo=:dfs, verbose=false)
    push!(filas, (M, "DFS (repositorio)", length(hd), fd))

    f_mod, h_mod = ejecutar_con_buscador(red, s, t, buscar_camino_dfs_modificado)
    push!(filas, (M, "DFS modificado (orden invertido)", length(h_mod), f_mod))

    buscar_oraculo(C, F, s, t) = oraculo_adversarial(C, F, s, u, v, t)
    f_adv, h_adv = ejecutar_con_buscador(red, s, t, buscar_oraculo)
    push!(filas, (M, "Oráculo adversarial (peor caso teórico)", length(h_adv), f_adv))

    @printf("M=%-6d BFS=%-4d  DFS_repo=%-4d  DFS_mod=%-4d  Oraculo=%-6d  (2M=%d)\n",
            M, length(hb), length(hd), length(h_mod), length(h_adv), 2M)
end

CSV.write("../results/files/parte2_zigzag_iteraciones.csv", filas)
println("\n", filas)

# Gráfico log-log iteraciones vs M
plt = plot(xscale=:log10, yscale=:log10, xlabel="M", ylabel="Iteraciones",
          title="Iteraciones vs M — red zigzag", legend=:topleft)
for metodo in unique(filas.metodo)
    sub = filter(r -> r.metodo == metodo, filas)
    plot!(plt, sub.M, sub.iteraciones; marker=:circle, label=metodo)
end
plot!(plt, Ms, 2 .* Ms; linestyle=:dash, color=:black, label="2M (cota teórica)")
savefig(plt, "../results/images/parte2_iteraciones_vs_M.png")

# Animaciones GIF para M = 10 (BFS y DFS estándar)
red10, s, t = red_zigzag(10)
animar_ford_fulkerson(red10, s, t; metodo=:bfs,
                      archivo="../results/animations/parte2_zigzag_edmonds_karp_bfs_M10.gif",
                      fps=1.2, verbose=false)
animar_ford_fulkerson(red10, s, t; metodo=:dfs,
                      archivo="../results/animations/parte2_zigzag_ford_fulkerson_dfs_M10.gif",
                      fps=1.2, verbose=false)

println("\nConclusión experimental:")
println("  - BFS y la DFS del repositorio requieren siempre 2 iteraciones,")
println("    para cualquier M: ninguna alcanza el peor caso teórico de 2M.")
println("  - La DFS con orden invertido tampoco lo alcanza (marca u y v")
println("    como visitados en el mismo barrido de los vecinos de s).")
println("  - El oráculo adversarial sí requiere exactamente 2M iteraciones,")
println("    confirmando experimentalmente la cota teórica de la guía.")
println("\nArchivos generados en results/files, results/images y results/animations.")
