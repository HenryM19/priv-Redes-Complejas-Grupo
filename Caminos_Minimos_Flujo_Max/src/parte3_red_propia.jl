# ============================================================
# Parte 3 — Nuestra red
# ============================================================
#
#   julia --project=. src/parte3_red_propia.jl
#
# Ejecuta ambos algoritmos sobre la red propia, verifica el corte mínimo
# a mano y genera las animaciones con `animar_ford_fulkerson` y
# `animar_edmonds_karp` (esta última muestra la onda BFS).
#
# Nota técnica: `ford_fulkerson.jl` y `edmonds_karp.jl` definen ambos el
# tipo `RedFlujo`, así que no se pueden `include` en el mismo ámbito. El
# segundo se carga dentro de un módulo (`EK`) para aislar sus definiciones.
#
# Produce:
#   results/data/parte3_red_propia.json
#   results/animations/propia_{ff_bfs,ff_dfs,ek}.gif
#   results/animations/propia_final.png
#   results/report/propia_aristas.csv

include("motor.jl")

# Edmonds-Karp del repositorio, aislado en su propio módulo
module EK
    include("edmonds_karp.jl")
end

const OUT_D = joinpath(@__DIR__, "..", "results", "data")
const OUT_A = joinpath(@__DIR__, "..", "results", "animations")
const OUT_R = joinpath(@__DIR__, "..", "results", "report")
mkpath(OUT_R)

red, s, t = red_propia()
n = size(red.C, 1)

println("="^78)
println("PARTE 3 — Nuestra red: backbone de un proveedor de Internet")
println("="^78)

# ------------------------------------------------------------
# 3.0 — La red cumple los requisitos
# ------------------------------------------------------------
arcos = [(u, v) for u in 1:n, v in 1:n if red.C[u, v] > 0]
antiparalelos = [(u, v) for (u, v) in arcos if red.C[v, u] > 0 && u < v]

println("\n── Requisitos de la guía ──")
@printf("  nodos: %d  (se piden ≥ 8)          %s\n", n, n >= 8 ? "✓" : "✗")
@printf("  arcos: %d  (se piden ≥ 12)         %s\n", length(arcos), length(arcos) >= 12 ? "✓" : "✗")
print("  pares antiparalelos: ")
println(join(["$(red.nombres[u]) ⇄ $(red.nombres[v]) ($(red.C[u,v]) / $(red.C[v,u]))"
              for (u, v) in antiparalelos], ", "), "  ",
        isempty(antiparalelos) ? "✗" : "✓")

# ------------------------------------------------------------
# 3.1 — Ejecutar ambos algoritmos
# ------------------------------------------------------------
bfs = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_bfs,
                           etiqueta = "Edmonds-Karp (BFS)")
dfs = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_dfs,
                           etiqueta = "Ford-Fulkerson (DFS)")

tabla_iteraciones(red, bfs)
tabla_iteraciones(red, dfs)

@printf("\n  iteraciones BFS = %d ≠ DFS = %d   %s\n",
        bfs.iteraciones, dfs.iteraciones,
        bfs.iteraciones != dfs.iteraciones ? "✓ (requisito de la guía)" : "✗")

# ------------------------------------------------------------
# 3.2 — Arcos de retroceso: qué flujo se cancela
# ------------------------------------------------------------
println("\n── Arcos de retroceso ──")
for c in (bfs, dfs)
    for i in findall(c.usa_retroceso)
        cam = c.caminos[i]
        rets = [(cam[k], cam[k+1]) for k in 1:length(cam)-1
                if red.C[cam[k], cam[k+1]] == 0]
        println("$(c.etiqueta) · iteración $i: $(ruta_str(red, cam))  (Δ = $(c.deltas[i]))")
        for (u, v) in rets
            # Flujo que había en el arco directo v→u antes de esta iteración
            F_antes = i == 1 ? zeros(Int, n, n) : c.historia[i-1].F
            println("    retroceso $(red.nombres[u])→$(red.nombres[v]): " *
                    "cancela $(c.deltas[i]) de las $(F_antes[v, u]) unidades " *
                    "que fluían por $(red.nombres[v])→$(red.nombres[u]) " *
                    "(capacidad $(red.C[v, u]))")
        end
    end
end

# ------------------------------------------------------------
# 3.3 — Corte mínimo, verificado A MANO
# ------------------------------------------------------------
println("\n── Corte mínimo (verificación manual) ──")
S, aristas, cap, _ = resumen_corte(red, bfs.F, s)
S_d, aristas_d, cap_d, _ = resumen_corte(red, dfs.F, s)

println("S (alcanzables desde s en la red residual) = {", join(red.nombres[S], ", "), "}")
println("V∖S = {", join(red.nombres[setdiff(1:n, S)], ", "), "}")
println("\nAristas del corte (van de S hacia V∖S) y sus capacidades:")
suma = 0
for (u, v) in aristas
    global suma += red.C[u, v]
    @printf("    %-8s capacidad %2d   (flujo %2d/%-2d → saturada: %s)\n",
            "$(red.nombres[u])→$(red.nombres[v])", red.C[u, v],
            max(bfs.F[u, v], 0), red.C[u, v],
            bfs.F[u, v] == red.C[u, v] ? "sí" : "NO")
end
println("    " * "─"^52)
@printf("    suma de capacidades = %d\n", suma)
@printf("    flujo máximo        = %d\n", bfs.flujo)
println("    ", suma == bfs.flujo ?
        "✓ coinciden — teorema max-flow min-cut verificado a mano" :
        "✗ NO coinciden")

# Comprobación adicional: no hay arcos de V∖S hacia S con flujo
entrantes = [(u, v) for u in setdiff(1:n, S), v in S if red.C[u, v] > 0 && bfs.F[u, v] > 0]
println("\n    Arcos de V∖S hacia S con flujo positivo: ",
        isempty(entrantes) ? "ninguno ✓ (como exige el teorema)" : string(entrantes))
println("    ¿BFS y DFS llegan al mismo corte? ", Set(S) == Set(S_d) ? "SÍ ✓" : "NO")

# ------------------------------------------------------------
# 3.4 — Guardar datos y CSV de aristas
# ------------------------------------------------------------
println("\nGuardando resultados...")
guardar_json(joinpath(OUT_D, "parte3_red_propia.json"), Dict{String,Any}(
    "nodos"          => red.nombres,
    "n_nodos"        => n,
    "n_arcos"        => length(arcos),
    "antiparalelos"  => ["$(red.nombres[u])⇄$(red.nombres[v])" for (u, v) in antiparalelos],
    "capacidades"    => ["$(red.nombres[u])→$(red.nombres[v])=$(red.C[u,v])" for (u, v) in arcos],
    "posiciones"     => [[p[1], p[2]] for p in red.pos],
    "flujo_maximo"   => bfs.flujo,
    "bfs"            => a_dict(red, bfs),
    "dfs"            => a_dict(red, dfs),
    "corte"          => Dict{String,Any}(
        "S"          => red.nombres[S],
        "complemento"=> red.nombres[setdiff(1:n, S)],
        "aristas"    => ["$(red.nombres[u])→$(red.nombres[v])" for (u, v) in aristas],
        "capacidades"=> [red.C[u, v] for (u, v) in aristas],
        "capacidad_total" => cap,
        "verificado" => cap == bfs.flujo,
    ),
    "flujo_final_bfs" => ["$(red.nombres[u])→$(red.nombres[v])=$(max(bfs.F[u,v],0))/$(red.C[u,v])"
                          for (u, v) in arcos],
    "flujo_final_dfs" => ["$(red.nombres[u])→$(red.nombres[v])=$(max(dfs.F[u,v],0))/$(red.C[u,v])"
                          for (u, v) in arcos],
    "mismos_flujos_por_arco" => bfs.F == dfs.F,
))

open(joinpath(OUT_R, "propia_aristas.csv"), "w") do io
    println(io, "origen,destino,capacidad,flujo_bfs,flujo_dfs,en_corte")
    for (u, v) in arcos
        println(io, "$(red.nombres[u]),$(red.nombres[v]),$(red.C[u,v])," *
                    "$(max(bfs.F[u,v],0)),$(max(dfs.F[u,v],0))," *
                    "$((u, v) in aristas ? 1 : 0)")
    end
end
println("  ✓ results/report/propia_aristas.csv")

# ------------------------------------------------------------
# 3.5 — Animaciones
# ------------------------------------------------------------
println("\nGenerando animaciones (puede tardar un par de minutos)...")

animar_ford_fulkerson(red, s, t; metodo = :bfs, verbose = false,
                      archivo = joinpath(OUT_A, "propia_ff_bfs.gif"))
println("  ✓ propia_ff_bfs.gif")
animar_ford_fulkerson(red, s, t; metodo = :dfs, verbose = false,
                      archivo = joinpath(OUT_A, "propia_ff_dfs.gif"))
println("  ✓ propia_ff_dfs.gif")

# Edmonds-Karp con la onda BFS (módulo aislado ⇒ hay que reconstruir la red)
let redEK = EK.RedFlujo(red.C, red.nombres, red.pos)
    EK.animar_edmonds_karp(redEK, s, t; verbose = false,
                           archivo = joinpath(OUT_A, "propia_ek.gif"))
    println("  ✓ propia_ek.gif (con onda BFS)")
end

frames = _fotogramas(red, s, t, bfs.historia)
savefig(dibujar_fotograma(red, frames[end]; s = s, t = t),
        joinpath(OUT_A, "propia_final.png"))
println("  ✓ propia_final.png")
savefig(dibujar_red(red, zeros(Int, n, n); titulo = "Nuestra red — capacidades (Gb/s)", s = s, t = t),
        joinpath(OUT_A, "propia_topologia.png"))
println("  ✓ propia_topologia.png")

println("\nParte 3 completada.")
