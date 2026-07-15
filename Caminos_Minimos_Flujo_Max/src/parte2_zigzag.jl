# ============================================================
# Parte 2 — El experimento zigzag
# ============================================================
#
#   julia --project=. src/parte2_zigzag.jl
#
# La red zigzag tiene un arco trampa u→v de capacidad 1 entre dos rutas de
# capacidad M. La guía afirma que "un Ford-Fulkerson que siempre eligiera
# el camino que atraviesa ese arco necesitaría 2M iteraciones", y pregunta
# si la implementación DFS del repositorio alcanza ese peor caso.
#
# Comparamos cuatro estrategias de elección del camino aumentante:
#   1. BFS                  — Edmonds-Karp
#   2. DFS del repositorio  — `for v in n:-1:1` sobre una pila
#   3. DFS adversaria       — la misma con el orden invertido (Parte 2.3)
#   4. DFS profunda         — prueba `t` en último lugar: elige caminos largos
#   5. Adversario alternante— alterna los dos caminos que cruzan la trampa
#
# Produce: results/data/parte2_zigzag.json

include("motor.jl")

const OUT_D = joinpath(@__DIR__, "..", "results", "data")
const OUT_A = joinpath(@__DIR__, "..", "results", "animations")
const MS = [10, 100, 1000, 10000]

const METODOS = [
    (buscar_camino_bfs,            "BFS (Edmonds-Karp)"),
    (buscar_camino_dfs,            "DFS del repositorio"),
    (buscar_camino_dfs_adversaria, "DFS adversaria (orden invertido)"),
    (buscar_camino_dfs_profunda,   "DFS profunda (t al final)"),
    (buscar_camino_alternante,     "Adversario alternante"),
]

println("="^78)
println("PARTE 2 — El experimento zigzag")
println("="^78)

# ------------------------------------------------------------
# 2.1 — Iteraciones para cada M y cada método
# ------------------------------------------------------------
println("\n── 2.1 Número de iteraciones (flujo máximo = 2M en todos los casos) ──\n")
@printf("%-34s", "Método")
for M in MS; @printf("%12s", "M=$M"); end
println("\n" * "─"^(34 + 12 * length(MS)))

resultados = Dict{String,Any}()
for (buscar, etiqueta) in METODOS
    @printf("%-34s", etiqueta)
    fila = Dict{String,Any}()
    for M in MS
        red, s, t = red_zigzag(M)
        c = ford_fulkerson_instr(red, s, t; buscar = buscar, etiqueta = etiqueta,
                                 limite = 200_000)
        @printf("%12d", c.iteraciones)
        fila["M$M"] = Dict{String,Any}(
            "iteraciones" => c.iteraciones,
            "flujo"       => c.flujo,
            "correcto"    => c.flujo == 2M,
            "longitudes"  => sort(unique(c.longitudes)),
            "deltas"      => sort(unique(c.deltas)),
            "tiempo_ms"   => c.tiempo_ms,
            "razon_2M"    => round(c.iteraciones / (2M); digits = 4),
        )
    end
    println()
    resultados[etiqueta] = fila
end
println("─"^(34 + 12 * length(MS)))
@printf("%-34s", "peor caso teórico (2M)")
for M in MS; @printf("%12d", 2M); end
println("\n")

# Verificación: todos deben dar el flujo correcto
println("Control de correctitud (todos deben alcanzar flujo = 2M):")
for (_, etiqueta) in METODOS
    ok = all(resultados[etiqueta]["M$M"]["correcto"] for M in MS)
    println("  ", ok ? "✓" : "✗", "  ", etiqueta)
end

# ------------------------------------------------------------
# 2.2 — ¿Por qué la DFS del repositorio NO alcanza el peor caso?
# ------------------------------------------------------------
println("\n── 2.2 Los caminos que elige cada método (M = 10) ──")
for (buscar, etiqueta) in METODOS
    red, s, t = red_zigzag(10)
    c = ford_fulkerson_instr(red, s, t; buscar = buscar, etiqueta = etiqueta)
    println("\n$etiqueta → $(c.iteraciones) iteraciones")
    for i in 1:min(c.iteraciones, 6)
        @printf("   %2d. %-16s Δ = %-4d flujo = %d\n",
                i, ruta_str(red, c.caminos[i]), c.deltas[i], c.acumulado[i])
    end
    c.iteraciones > 6 && println("   ... y $(c.iteraciones - 6) iteraciones más (todas con Δ = 1)")
end

# ------------------------------------------------------------
# 2.3 — La traza del adversario: cómo se reabre el arco trampa
# ------------------------------------------------------------
println("\n── 2.3 Traza del adversario alternante (M = 5): el arco trampa se reabre ──")
let M = 5
    red, s, t = red_zigzag(M)
    C = red.C
    F = zeros(Int, 4, 4)
    flujo = 0
    @printf("%-5s %-16s %-5s %-7s %-10s %s\n",
            "Iter", "Camino", "Δ", "Flujo", "r(u→v)", "¿qué pasó?")
    for it in 1:(2M)
        cam = buscar_camino_alternante(C, F, s, t)
        isempty(cam) && break
        Δ = minimum(C[cam[i], cam[i+1]] - F[cam[i], cam[i+1]] for i in 1:length(cam)-1)
        usa_ret = any(C[cam[i], cam[i+1]] == 0 for i in 1:length(cam)-1)
        for i in 1:length(cam)-1
            u, v = cam[i], cam[i+1]
            F[u, v] += Δ; F[v, u] -= Δ
        end
        flujo += Δ
        @printf("%-5d %-16s %-5d %-7d %-10d %s\n", it, ruta_str(red, cam), Δ, flujo,
                C[2,3] - F[2,3],
                usa_ret ? "usa retroceso v→u ⇒ REABRE la trampa" : "satura el arco trampa u→v")
    end
    println("→ $(2M) iteraciones para transportar $(2M) unidades: avanza de 1 en 1.")
end

# ------------------------------------------------------------
# 2.4 — Escalado: ¿depende del valor de las capacidades?
# ------------------------------------------------------------
println("\n── 2.4 Escalado con M ──")
println("BFS y las DFS mantienen un número CONSTANTE de iteraciones al crecer M;")
println("el adversario alternante crece linealmente con M (2M):\n")
@printf("%-10s %-14s %-14s %-14s\n", "M", "BFS", "DFS repo", "Alternante")
for M in MS
    @printf("%-10d %-14d %-14d %-14d\n", M,
            resultados["BFS (Edmonds-Karp)"]["M$M"]["iteraciones"],
            resultados["DFS del repositorio"]["M$M"]["iteraciones"],
            resultados["Adversario alternante"]["M$M"]["iteraciones"])
end

# ------------------------------------------------------------
# Guardar
# ------------------------------------------------------------
println("\nGuardando resultados...")
guardar_json(joinpath(OUT_D, "parte2_zigzag.json"), Dict{String,Any}(
    "valores_M" => MS,
    "metodos"   => [e for (_, e) in METODOS],
    "resultados" => resultados,
    "peor_caso_teorico" => Dict("M$M" => 2M for M in MS),
))

# Animación del adversario para las diapositivas (M pequeño para que se vea)
println("\nGenerando animación del adversario (M = 3)...")
let M = 3
    red, s, t = red_zigzag(M)
    c = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_alternante,
                             etiqueta = "adversario")
    frames = _fotogramas(red, s, t, c.historia)
    anim = @animate for fr in frames
        dibujar_fotograma(red, fr; s = s, t = t)
    end
    gif(anim, joinpath(OUT_A, "zigzag_adversario.gif"); fps = 0.8)
    println("  ✓ zigzag_adversario.gif ($(c.iteraciones) iteraciones para flujo $(c.flujo))")

    cb = ford_fulkerson_instr(red, s, t; buscar = buscar_camino_bfs, etiqueta = "BFS")
    fb = _fotogramas(red, s, t, cb.historia)
    animb = @animate for fr in fb
        dibujar_fotograma(red, fr; s = s, t = t)
    end
    gif(animb, joinpath(OUT_A, "zigzag_bfs.gif"); fps = 0.8)
    println("  ✓ zigzag_bfs.gif ($(cb.iteraciones) iteraciones para flujo $(cb.flujo))")
end

println("\nParte 2 completada.")
