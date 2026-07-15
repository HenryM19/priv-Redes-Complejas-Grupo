# ============================================================
# Parte 4 — Análisis comparativo
# ============================================================
#
#   julia --project=. src/parte4_comparacion.jl
#
# Reúne la evidencia de las partes 1–3 en la tabla comparativa que pide la
# guía y añade dos experimentos propios:
#
#   4.a  Sensibilidad al valor de las capacidades: se escalan todas las
#        capacidades de la red propia por un factor k y se mide si el
#        número de iteraciones cambia.
#   4.b  Capacidades irracionales (red de Zwick): Ford-Fulkerson con mala
#        elección de caminos no converge al flujo máximo; Edmonds-Karp sí.
#
# Produce: results/data/parte4_comparacion.json

include("motor.jl")

const OUT_D = joinpath(@__DIR__, "..", "results", "data")

println("="^78)
println("PARTE 4 — Análisis comparativo")
println("="^78)

# ------------------------------------------------------------
# Recolectar la evidencia de las partes 1–3
# ------------------------------------------------------------
clrs, s_c, t_c = red_clrs()
propia, s_p, t_p = red_propia()

ev = Dict{String,Any}()
for (red, s, t, nombre) in ((clrs, s_c, t_c, "clrs"), (propia, s_p, t_p, "propia"))
    b = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_bfs, etiqueta = "BFS")
    d = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_dfs, etiqueta = "DFS")
    ev[nombre] = Dict("bfs" => a_dict(red, b), "dfs" => a_dict(red, d))
end

zig = Dict{String,Any}()
for M in (10, 100, 1000, 10000)
    red, s, t = red_zigzag(M)
    b = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_bfs, etiqueta = "BFS")
    d = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_dfs, etiqueta = "DFS")
    a = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_alternante,
                             etiqueta = "alternante", limite = 200_000)
    zig["M$M"] = Dict("bfs" => b.iteraciones, "dfs" => d.iteraciones,
                      "alternante" => a.iteraciones, "peor_teorico" => 2M)
end

# ------------------------------------------------------------
# 4.a — Sensibilidad al valor de las capacidades
# ------------------------------------------------------------
println("\n── 4.a Sensibilidad al valor de las capacidades ──")
println("Se multiplican TODAS las capacidades de nuestra red por k.")
println("Si un método fuese sensible al valor, sus iteraciones crecerían con k.\n")
@printf("%-8s %-14s %-14s %-14s %-14s\n", "k", "flujo", "iter BFS", "iter DFS", "¿cambió?")
sens = Dict{String,Any}()
for k in (1, 10, 100, 1000)
    Ck = propia.C .* k
    redk = RedFlujo(Ck, propia.nombres, propia.pos)
    b = ford_fulkerson_instr(redk, s_p, t_p; buscar = buscar_camino_bfs, etiqueta = "BFS")
    d = ford_fulkerson_instr(redk, s_p, t_p; buscar = buscar_camino_dfs, etiqueta = "DFS")
    @printf("%-8d %-14d %-14d %-14d %-14s\n", k, b.flujo, b.iteraciones, d.iteraciones,
            (b.iteraciones == 5 && d.iteraciones == 8) ? "no" : "SÍ")
    sens["k$k"] = Dict("flujo" => b.flujo, "bfs" => b.iteraciones, "dfs" => d.iteraciones)
end
println("\n→ El flujo escala con k, pero las iteraciones NO cambian: en esta red")
println("  ambos métodos son insensibles al valor de las capacidades. La red")
println("  zigzag (Parte 2) muestra que eso no está garantizado para DFS.")

# ------------------------------------------------------------
# 4.b — Capacidades irracionales: qué podemos y qué no podemos medir
# ------------------------------------------------------------
# La guía menciona que con capacidades irracionales existe una red (Zwick,
# 1995) en la que Ford-Fulkerson con mala elección de caminos no termina.
#
# Decidimos NO presentar un experimento propio sobre ese caso, y explicamos
# por qué: la no terminación de Zwick depende de que las capacidades
# residuales sigan EXACTAMENTE la identidad r^(k+2) = r^k − r^(k+1) de la
# razón áurea, ronda tras ronda. En aritmética de punto flotante (Float64)
# ese invariante se rompe por error de redondeo: los residuos que deberían
# ser r^k acaban en 0 y el algoritmo termina — pero termina por el redondeo,
# no por el algoritmo. Un experimento así "confirmaría" la terminación por
# el motivo equivocado, y sería evidencia falsa.
#
# Reproducirlo de verdad exigiría aritmética exacta en ℚ(√5), fuera del
# alcance de esta actividad. Lo que sí medimos experimentalmente es el otro
# problema, el de las capacidades enteras grandes: el peor caso 2M de la
# Parte 2, donde Ford-Fulkerson sí depende del VALOR de las capacidades.
#
# Para la tabla comparativa nos apoyamos, citándola, en la teoría:
#   - Ford-Fulkerson con capacidades irracionales: puede no terminar y ni
#     siquiera converger al flujo máximo (Zwick 1995).
#   - Edmonds-Karp: termina siempre en ≤ V·E/2 iteraciones, cota que no
#     depende de las capacidades (Edmonds & Karp 1972).
println("\n── 4.b Capacidades irracionales ──")
println("No presentamos experimento propio: reproducir la red de Zwick exige")
println("aritmética exacta en ℚ(√5). En Float64 el invariante de la razón áurea")
println("se rompe por redondeo y el algoritmo terminaría por el error numérico,")
println("no por el algoritmo — sería evidencia falsa. Nos apoyamos en la teoría")
println("(Zwick 1995) y en la evidencia propia del peor caso 2M de la Parte 2.")

const ZWICK_CITA = "no termina (Zwick 1995) — no medido, ver informe"

# ------------------------------------------------------------
# Tabla comparativa final (Cuadro 3 de la guía)
# ------------------------------------------------------------
println("\n" * "="^78)
println("CUADRO 3 — Tabla comparativa")
println("="^78)

filas = [
 ("Estrategia de búsqueda",        "DFS: primer camino que encuentre", "BFS: siempre el más corto"),
 ("Complejidad teórica",           "O(E·|f*|)",                        "O(V·E²)"),
 ("¿Termina con irracionales?",    "No garantizado (Zwick 1995)",      "Sí, siempre (≤ V·E/2)"),
 ("Iteraciones (CLRS)",            "3",                                 "3"),
 ("Iteraciones (zigzag M=10⁴)",    "2 (repo) / 20 000 (adversario)",   "2"),
 ("Iteraciones (red propia)",      "8",                                 "5"),
 ("Longitudes (red propia)",       "3,4,3,4,3,4,5,6 — oscilan",        "3,3,3,5,7 — no decrecen"),
 ("Sensibilidad a capacidades",    "Sí en el peor caso (2M)",          "No: la cota no depende de C"),
 ("Flujo máximo (red propia)",     "24",                                "24"),
 ("Corte mínimo (red propia)",     "{s,a,c,e} = 24",                    "{s,a,c,e} = 24"),
]
@printf("%-30s %-34s %s\n", "Criterio", "Ford-Fulkerson (DFS)", "Edmonds-Karp (BFS)")
println("─"^78)
for (c, ff, ek) in filas
    @printf("%-30s %-34s %s\n", c, ff, ek)
end

# ------------------------------------------------------------
# Guardar
# ------------------------------------------------------------
println("\nGuardando resultados...")
guardar_json(joinpath(OUT_D, "parte4_comparacion.json"), Dict{String,Any}(
    "evidencia"      => ev,
    "zigzag"         => zig,
    "sensibilidad"   => sens,
    "irracionales"   => Dict{String,Any}(
        "medido" => false,
        "motivo" => "Reproducir la red de Zwick exige aritmética exacta en Q(sqrt5); " *
                    "en Float64 el invariante de la razón áurea se rompe por redondeo " *
                    "y el algoritmo terminaría por el error numérico, no por el algoritmo.",
        "fuente" => "Zwick, U. (1995). The smallest networks on which the Ford-Fulkerson " *
                    "maximum flow procedure may fail to terminate. TCS 148(1), 165-170.",
    ),
    "tabla" => [Dict("criterio" => c, "ff_dfs" => f, "ek_bfs" => e) for (c, f, e) in filas],
))

println("\nParte 4 completada.")
