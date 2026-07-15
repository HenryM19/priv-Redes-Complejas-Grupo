# ============================================================
# Parte 1 — Exploración guiada (red CLRS)
# ============================================================
#
#   julia --project=. src/parte1_exploracion.jl
#
# Produce:
#   results/data/parte1_clrs.json   — tablas de iteraciones BFS y DFS
#   results/animations/*.gif        — animaciones de ambos métodos
#   results/animations/*_final.png  — último fotograma (corte mínimo)

include("motor.jl")

const OUT_D = joinpath(@__DIR__, "..", "results", "data")
const OUT_A = joinpath(@__DIR__, "..", "results", "animations")

red, s, t = red_clrs()

println("="^70)
println("PARTE 1 — Exploración guiada · red CLRS (flujo máximo esperado: 23)")
println("="^70)

# ------------------------------------------------------------
# 1.1 — Tablas por iteración para BFS y DFS
# ------------------------------------------------------------
bfs = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_bfs,
                           etiqueta = "BFS (Edmonds-Karp)")
dfs = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_dfs,
                           etiqueta = "DFS (Ford-Fulkerson clásico)")

tabla_iteraciones(red, bfs)
tabla_iteraciones(red, dfs)

# ------------------------------------------------------------
# 1.2 — ¿Qué iteraciones usan un arco de retroceso?
# ------------------------------------------------------------
println("\n── Arcos de retroceso ──")
for c in (bfs, dfs)
    idx = findall(c.usa_retroceso)
    if isempty(idx)
        println("$(c.etiqueta): ninguna iteración usa arcos de retroceso.")
    else
        for i in idx
            # Identificar exactamente qué arco es de retroceso
            cam = c.caminos[i]
            arcos = [(cam[k], cam[k+1]) for k in 1:length(cam)-1
                     if red.C[cam[k], cam[k+1]] == 0]
            det = join(["$(red.nombres[u])→$(red.nombres[v]) (cancela flujo $(red.nombres[v])→$(red.nombres[u]))"
                        for (u, v) in arcos], ", ")
            println("$(c.etiqueta) · iteración $i: $(ruta_str(red, cam))")
            println("    arco de retroceso: $det")
        end
    end
end

# ------------------------------------------------------------
# 1.3 — Onda BFS: niveles d(v) de la primera iteración
# ------------------------------------------------------------
println("\n── Onda BFS (niveles de la primera iteración de Edmonds-Karp) ──")
let F0 = zeros(Int, size(red.C))
    cam, nivel, arbol = let
        # bfs_niveles vive en edmonds_karp.jl; se replica aquí para no
        # incluir dos veces las definiciones de RedFlujo (conflicto de tipos).
        n = size(red.C, 1)
        niv = fill(-1, n); padre = zeros(Int, n)
        niv[s] = 0; padre[s] = s; cola = [s]; arb = Tuple{Int,Int}[]
        while !isempty(cola)
            u = popfirst!(cola)
            for v in 1:n
                if niv[v] == -1 && red.C[u, v] - F0[u, v] > 0
                    niv[v] = niv[u] + 1; padre[v] = u
                    push!(arb, (u, v)); push!(cola, v)
                end
            end
        end
        (_reconstruir(padre, s, t), niv, arb)
    end
    for i in 1:length(red.nombres)
        @printf("  d(%s) = %d\n", red.nombres[i], nivel[i])
    end
    println("  camino BFS = $(ruta_str(red, cam)) · longitud = $(length(cam)-1) = d(t) ✓")
end

# ------------------------------------------------------------
# 1.4 — Comparación final: corte mínimo, flujo, flujos arco por arco
# ------------------------------------------------------------
println("\n── Estado final ──")
S_b, ar_b, cap_b, txt_b = resumen_corte(red, bfs.F, s)
S_d, ar_d, cap_d, txt_d = resumen_corte(red, dfs.F, s)
println("BFS · corte: $txt_b")
println("DFS · corte: $txt_d")
println("¿Mismo flujo máximo?      ", bfs.flujo == dfs.flujo ? "SÍ ($(bfs.flujo))" : "NO")
println("¿Mismo corte mínimo?      ", Set(S_b) == Set(S_d) ? "SÍ" : "NO")
println("¿Mismos flujos por arco?  ", bfs.F == dfs.F ? "SÍ" : "NO (asignaciones distintas, mismo valor total)")

if bfs.F != dfs.F
    println("\n  Arcos donde difiere la asignación de flujo:")
    for u in 1:size(red.C, 1), v in 1:size(red.C, 1)
        if red.C[u, v] > 0 && bfs.F[u, v] != dfs.F[u, v]
            @printf("    %-8s BFS: %2d/%-2d   DFS: %2d/%-2d\n",
                    "$(red.nombres[u])→$(red.nombres[v])",
                    max(bfs.F[u,v],0), red.C[u,v], max(dfs.F[u,v],0), red.C[u,v])
        end
    end
end

# ------------------------------------------------------------
# Guardar resultados
# ------------------------------------------------------------
println("\nGuardando resultados...")
guardar_json(joinpath(OUT_D, "parte1_clrs.json"), Dict{String,Any}(
    "red"          => "CLRS",
    "nodos"        => red.nombres,
    "flujo_maximo" => bfs.flujo,
    "bfs"          => a_dict(red, bfs),
    "dfs"          => a_dict(red, dfs),
    "corte_bfs"    => Dict{String,Any}("S" => red.nombres[S_b], "capacidad" => cap_b,
                        "aristas" => ["$(red.nombres[u])→$(red.nombres[v])" for (u,v) in ar_b]),
    "corte_dfs"    => Dict{String,Any}("S" => red.nombres[S_d], "capacidad" => cap_d,
                        "aristas" => ["$(red.nombres[u])→$(red.nombres[v])" for (u,v) in ar_d]),
    "mismo_flujo"  => bfs.flujo == dfs.flujo,
    "mismo_corte"  => Set(S_b) == Set(S_d),
    "mismos_flujos_por_arco" => bfs.F == dfs.F,
))

# ------------------------------------------------------------
# Animaciones
# ------------------------------------------------------------
println("\nGenerando animaciones (puede tardar)...")
animar_ford_fulkerson(red, s, t; metodo = :bfs, verbose = false,
                      archivo = joinpath(OUT_A, "clrs_bfs.gif"))
println("  ✓ clrs_bfs.gif")
animar_ford_fulkerson(red, s, t; metodo = :dfs, verbose = false,
                      archivo = joinpath(OUT_A, "clrs_dfs.gif"))
println("  ✓ clrs_dfs.gif")

for (c, nom) in ((bfs, "bfs"), (dfs, "dfs"))
    frames = _fotogramas(red, s, t, c.historia)
    savefig(dibujar_fotograma(red, frames[end]; s = s, t = t),
            joinpath(OUT_A, "clrs_$(nom)_final.png"))
    println("  ✓ clrs_$(nom)_final.png")
end

println("\nParte 1 completada.")
