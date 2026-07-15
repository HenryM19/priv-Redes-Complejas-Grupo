# ============================================================
# 03_parte1_exploracion_guiada.jl
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Resuelve la PARTE 1 — Exploración guiada de la Guía_Actividad
# (Flujo máximo: Ford-Fulkerson vs. Edmonds-Karp).
#
# Sobre la red clásica de Cormen et al. (CLRS, flujo máximo = 23),
# este script:
#   1. Ejecuta Ford-Fulkerson con búsqueda DFS y con búsqueda BFS
#      (Edmonds-Karp) por separado.
#   2. Tabula, para cada método, cada iteración: camino aumentante,
#      longitud (número de arcos), cuello de botella Δ y flujo
#      acumulado, indicando si el camino usó un arco de retroceso.
#   3. Calcula y verifica el corte mínimo de ambas ejecuciones.
#   4. Genera las imágenes finales y las animaciones GIF de ambos
#      métodos.
#   5. Guarda las tablas en formato CSV (con DataFrames.jl/CSV.jl)
#      en `results/files/`, las imágenes en `results/images/` y los
#      GIF en `results/animations/`.
#
# Este script depende de los módulos 01 y 02 (deben ejecutarse antes
# en el orden de la práctica, o simplemente incluirse aquí).
#
# Ejecutar desde la carpeta `src/`:
#   julia --project=.. 03_parte1_exploracion_guiada.jl

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
include("01_ford_fulkerson.jl")   # ford_fulkerson, corte_minimo, animar_ford_fulkerson, ...
include("02_edmonds_karp.jl")     # (reexporta los mismos nombres; se usa por edmonds_karp())
using CSV
using DataFrames
using Printf

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

"""
    red_clrs() -> (RedFlujo, Int, Int)

Construye la red clásica de Cormen, Leiserson, Rivest y Stein
(CLRS), usada como caso de referencia en toda la actividad (flujo
máximo conocido = 23).

# Salida
- `RedFlujo`: la red con 6 nodos (s, v1, v2, v3, v4, t).
- `Int`, `Int`: índices del nodo fuente `s` y del nodo sumidero `t`.
"""
function red_clrs()
    nombres = ["s", "v₁", "v₂", "v₃", "v₄", "t"]
    pos = [(0.0, 1.0), (1.0, 2.0), (1.0, 0.0), (2.2, 2.0), (2.2, 0.0), (3.2, 1.0)]
    C = zeros(Int, 6, 6)
    C[1, 2] = 16   # s  → v₁
    C[1, 3] = 13   # s  → v₂
    C[2, 4] = 12   # v₁ → v₃
    C[3, 2] = 4    # v₂ → v₁
    C[3, 5] = 14   # v₂ → v₄
    C[4, 3] = 9    # v₃ → v₂
    C[4, 6] = 20   # v₃ → t
    C[5, 4] = 7    # v₄ → v₃
    C[5, 6] = 4    # v₄ → t
    return RedFlujo(C, nombres, pos), 1, 6
end

"""
    tabla_iteraciones(red, s, t, historia) -> DataFrame

Construye la tabla pedida en la Parte 1: por cada iteración,
camino aumentante, longitud (número de arcos), cuello de botella Δ,
flujo acumulado y si el camino usó algún arco de retroceso (arco
residual inverso, es decir un arco (u,v) con capacidad original
`C[u,v] == 0`).

# Argumentos
- `red::RedFlujo`: la red usada.
- `s::Int`, `t::Int`: fuente y sumidero (no se usan directamente,
  se mantienen por claridad de la interfaz).
- `historia::Vector{Paso}`: historial devuelto por `ford_fulkerson`.

# Salida
- `DataFrame` con columnas `iteracion`, `camino_aumentante`,
  `longitud_arcos`, `delta`, `flujo_acumulado`, `usa_arco_retroceso`.
"""
function tabla_iteraciones(red::RedFlujo, s::Int, t::Int, historia::Vector{Paso})
    filas = DataFrame(iteracion=Int[], camino_aumentante=String[],
                      longitud_arcos=Int[], delta=Int[],
                      flujo_acumulado=Int[], usa_arco_retroceso=Bool[])
    for (i, p) in enumerate(historia)
        cam = p.camino
        retro = any(red.C[cam[k], cam[k+1]] == 0 for k in 1:length(cam)-1)
        push!(filas, (i, join(red.nombres[cam], " → "), length(cam) - 1,
                      p.Δ, p.flujo_total, retro))
    end
    return filas
end

# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Construir la red CLRS.
# 2) Ejecutar Ford-Fulkerson con DFS y con BFS (Edmonds-Karp) por
#    separado, tabulando cada ejecución.
# 3) Verificar el corte mínimo de cada ejecución.
# 4) Generar imágenes finales y animaciones GIF.
# 5) Guardar las tablas en CSV.
mkpath("../results/files")
mkpath("../results/images")
mkpath("../results/animations")

red, s, t = red_clrs()

println("="^60)
println("PARTE 1 — Exploración guiada (red CLRS, flujo máximo = 23)")
println("="^60)

resultados = Dict{Symbol,Any}()
for metodo in (:dfs, :bfs)
    etiqueta = metodo == :dfs ? "Ford-Fulkerson (DFS)" : "Edmonds-Karp (BFS)"
    println("\n--- ", etiqueta, " ---")
    flujo, F, historia = ford_fulkerson(red, s, t; metodo=metodo, verbose=true)
    tabla = tabla_iteraciones(red, s, t, historia)
    println(tabla)

    S, aristas_corte = corte_minimo(red.C, F, s)
    cap_corte = sum(red.C[u, v] for (u, v) in aristas_corte)
    @printf("Corte mínimo: S = {%s}, capacidad = %d (debe igualar el flujo máximo)\n",
            join(red.nombres[S], ", "), cap_corte)
    @assert cap_corte == flujo "La capacidad del corte mínimo no coincide con el flujo máximo"

    sufijo = metodo == :dfs ? "ford_fulkerson_dfs" : "edmonds_karp_bfs"
    CSV.write("../results/files/parte1_tabla_$(sufijo).csv", tabla)

    frames = _fotogramas(red, s, t, historia)
    savefig(dibujar_fotograma(red, frames[end]; s=s, t=t),
            "../results/images/parte1_$(sufijo)_final.png")
    animar_ford_fulkerson(red, s, t; metodo=metodo,
                          archivo="../results/animations/parte1_$(sufijo).gif",
                          fps=1.0, verbose=false)

    resultados[metodo] = (flujo=flujo, iteraciones=length(historia), S=S, cap_corte=cap_corte)
end

println("\nResumen comparativo Parte 1:")
for (metodo, r) in resultados
    println("  ", metodo, " → flujo = ", r.flujo, ", iteraciones = ", r.iteraciones)
end

# ------------------------------------------------------------
# Animación de la "ond