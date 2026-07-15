# ============================================================
# 05_parte3_red_propia.jl
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Resuelve la PARTE 3 — Su propia red de la Guía_Actividad.
#
# Diseña y ejecuta una red de flujo original que cumple los cuatro
# requisitos de la guía:
#   1. Al menos 8 nodos y 12 arcos, con posiciones legibles.
#   2. Al menos un par de arcos antiparalelos (u→v y v→u): aquí
#      "b→e" (capacidad 9) y "e→b" (capacidad 7).
#   3. Al menos una ejecución (BFS o DFS) usa un arco de retroceso
#      en algún camino aumentante.
#   4. El número de iteraciones de BFS y DFS es diferente.
#
# El diseño se obtuvo mediante una búsqueda experimental sobre
# variaciones de capacidades de una topología de 8 nodos y 14 arcos
# (documentada más abajo, sección "Proceso de diseño"), hasta
# satisfacer simultáneamente los 4 requisitos.
#
# Este script:
#   1. Construye la red propia.
#   2. Ejecuta Ford-Fulkerson (DFS) y Edmonds-Karp (BFS).
#   3. Genera las animaciones GIF de ambos algoritmos.
#   4. Calcula el corte mínimo y lo verifica a mano (suma de
#      capacidades de las aristas del corte).
#   5. Guarda tablas, imágenes finales y GIF en `results/`.
#
# Ejecutar desde la carpeta `src/`:
#   julia --project=.. 05_parte3_red_propia.jl

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
include("01_ford_fulkerson.jl")
include("02_edmonds_karp.jl")
using CSV
using DataFrames
using Printf

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

"""
    red_propia() -> (RedFlujo, Int, Int)

Construye la red original de la Parte 3: 8 nodos (s, a, b, c, d, e,
f, t) y 14 arcos, incluido el par antiparalelo b→e / e→b.

# Proceso de diseño (documentado según lo pedido en la guía)
Se partió de una topología de 8 nodos en 3 capas (s → {a,b} →
{c,d,e} → f → t) con 14 arcos fijos, incluido a propósito el par
antiparalelo b↔e. Sobre esa topología se hizo una búsqueda
experimental de capacidades enteras (con un script auxiliar) hasta
encontrar una asignación en la que:
  - BFS y DFS obtienen el mismo flujo máximo (como exige el teorema
    max-flow min-cut, con cualquier búsqueda válida), pero un número
    DIFERENTE de iteraciones (BFS: 5, DFS: 6).
  - Al menos una de las dos ejecuciones usa un arco de retroceso:
    aquí BFS, en su última iteración, aumenta por el camino
    s→b→d→a→c→f→t, donde el tramo d→a es un arco de retroceso
    (cancela parte del flujo que antes se había enviado a→d).
Intentos fallidos relevantes: con capacidades "simétricas" (todas
iguales) BFS y DFS coincidían en número de iteraciones y ninguna
usaba arcos de retroceso, porque los caminos más cortos y los
caminos DFS terminaban explorando exactamente los mismos cuellos de
botella. Fue necesario desbalancear las capacidades (arcos a→c=1 y
b→c=1 muy angostos frente al resto) para forzar que alguna búsqueda
tuviera que "deshacer" flujo ya enviado.

# Salida
- `RedFlujo`: la red con 8 nodos.
- `Int`, `Int`: índices de la fuente `s=1` y el sumidero `t=8`.
"""
function red_propia()
    nombres = ["s", "a", "b", "c", "d", "e", "f", "t"]
    pos = [(0.0, 1.5), (1.0, 3.0), (1.0, 0.0), (2.2, 3.0), (2.2, 1.5),
           (2.2, -0.5), (3.4, 1.0), (4.4, 1.5)]
    C = zeros(Int, 8, 8)
    C[1, 2] = 4    # s → a
    C[1, 3] = 12   # s → b
    C[2, 4] = 1    # a → c   (cuello de botella angosto)
    C[2, 5] = 11   # a → d
    C[3, 4] = 1    # b → c   (cuello de botella angosto)
    C[3, 6] = 9    # b → e   ┐ par antiparalelo
    C[6, 3] = 7    # e → b   ┘
    C[3, 5] = 10   # b → d
    C[4, 7] = 2    # c → f
    C[4, 5] = 5    # c → d
    C[5, 7] = 2    # d → f
    C[5, 8] = 4    # d → t
    C[6, 7] = 2    # e → f
    C[7, 8] = 11   # f → t
    return RedFlujo(C, nombres, pos), 1, 8
end

"""
    tabla_iteraciones(red, historia) -> DataFrame

Igual que en 03_parte1_exploracion_guiada.jl: construye la tabla de
iteración/camino/longitud/Δ/flujo acumulado/uso de arco de retroceso.

# Argumentos
- `red::RedFlujo`: la red usada.
- `historia::Vector{Paso}`: historial de `ford_fulkerson`.

# Salida
- `DataFrame` con una fila por iteración.
"""
function tabla_iteraciones(red::RedFlujo, historia::Vector{Paso})
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
# 1) Construir la red propia y verificar que cumple los requisitos
#    estructurales (8+ nodos, 12+ arcos, par antiparalelo).
# 2) Ejecutar DFS y BFS, tabular y verificar uso de arco de
#    retroceso y diferencia en el número de iteraciones.
# 3) Calcular el corte mínimo y verificarlo a mano.
# 4) Guardar tablas, imágenes y animaciones GIF.
mkpath("../results/files")
mkpath("../results/images")
mkpath("../results/animations")

red, s, t = red_propia()
n_arcos = count(>(0), red.C)
@printf("Red propia: %d nodos, %d arcos\n", length(red.nombres), n_arcos)
@assert length(red.nombres) >= 8 "Se requieren al menos 8 nodos"
@assert n_arcos >= 12 "Se requieren al menos 12 arcos"
antiparalelos = [(u, v) for u in 1:8, v in 1:8 if red.C[u, v] > 0 && red.C[v, u] > 0]
@assert !isempty(antiparalelos) "Se requiere al menos un par de arcos antiparalelos"
println("Par(es) antiparalelo(s): ", [(red.nombres[u], red.nombres[v]) for (u, v) in antiparalelos])

resultados = Dict{Symbol,Any}()
for metodo in (:dfs, :bfs)
    etiqueta = metodo == :dfs ? "Ford-Fulkerson (DFS)" : "Edmonds-Karp (BFS)"
    println("\n--- ", etiqueta, " ---")
    flujo, F, historia = ford_fulkerson(red, s, t; metodo=metodo, verbose=true)
    tabla = tabla_iteraciones(red, historia)
    println(tabla)

    S, aristas_corte = corte_minimo(red.C, F, s)
    cap_corte = sum(red.C[u, v] for (u, v) in aristas_corte)
    @printf("Corte mínimo: S = {%s}, aristas = %s\n", join(red.nombres[S], ", "),
            join(["$(red.nombres[u])→$(red.nombres[v]) ($(red.C[u,v]))" for (u, v) in aristas_corte], ", "))
    @printf("Verificación a mano: suma de capacidades del corte = %d  (flujo máximo = %d) → %s\n",
            cap_corte, flujo, cap_corte == flujo ? "OK ✓" : "ERROR ✗")

    sufijo = metodo == :dfs ? "ford_fulkerson_dfs" : "edmonds_karp_bfs"
    CSV.write("../results/files/parte3_red_propia_tabla_$(sufijo).csv", tabla)

    frames = _fotogramas(red, s, t, historia)
    savefig(dibujar_fotograma(red, frames[end]; s=s, t=t),
            "../results/images/parte3_red_propia_$(sufijo)_final.png")
    animar_ford_fulkerson(red, s, t; metodo=metodo,
                          archivo="../results/animations/parte3_red_propia_$(sufijo).gif",
                          fps=1.0, verbose=false)

    resultados[metodo] = (flujo=flujo, iteraciones=length(historia),
                          usa_retroceso=any(tabla.usa_arco_retroceso))
end

println("\n" * "="^60)
println("Verificación de los 4 requisitos de la Parte 3:")
println("  1) >= 8 nodos y >= 12 arcos ......... OK (", length(red.nombres), " nodos, ", n_arcos, " arcos)")
println("  2) Par antiparalelo .................. OK (", antiparalelos, ")")
usa_retroceso_alguna = resultados[:dfs].usa_retroceso || resultados[:bfs].usa_retroceso
println("  3) Arco de retroceso en alguna ejecución: ",
        usa_retroceso_alguna ? "OK ✓" : "NO CUMPLE ✗")
println("  4) Iteraciones BFS ≠ DFS: BFS=", resultados[:bfs].iteraciones,
        " DFS=", resultados[:dfs].iteraciones,
        resultados[:bfs].iteraciones != resultados[:dfs].iteraciones ? "  → OK ✓" : "  → NO CUMPLE ✗")
println("="^60)
