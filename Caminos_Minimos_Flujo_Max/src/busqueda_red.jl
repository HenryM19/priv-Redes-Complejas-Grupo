# ============================================================
# busqueda_red.jl — Cómo se diseñó la red propia (Parte 3)
# ============================================================
#
#   julia --project=. src/busqueda_red.jl
#
# La guía pide documentar el proceso de diseño, incluidos los intentos
# fallidos. Este script ES ese proceso, reproducible.
#
# Método: la topología (qué arcos existen y dónde están los nodos) se fijó
# a mano, pensando dónde queríamos el cuello de botella. Lo que no se puede
# fijar a ojo son las CAPACIDADES: los cuatro requisitos de la guía dependen
# de ellas de forma nada intuitiva. Así que exploramos el espacio 2..15 por
# muestreo aleatorio con semilla fija y nos quedamos con la mejor red según
# un puntaje que premia el valor pedagógico.
#
# Requisitos duros (la red se descarta si falla alguno):
#   R1  BFS y DFS deben coincidir en el flujo máximo (control de correctitud)
#   R2  DFS debe necesitar ESTRICTAMENTE más iteraciones que BFS
#   R3  BFS y DFS deben usar, cada uno, algún arco de retroceso
#   R4  DFS debe VIOLAR la monotonía de longitudes (BFS nunca la viola)
#   R5  El corte mínimo no puede ser trivial ({s} o V∖{t}) y debe tener ≥ 2 aristas
#   R6  Ambos métodos deben llegar al mismo corte mínimo
#
# Puntaje (entre las que pasan): premia la brecha DFS−BFS, el uso de
# retroceso, un corte de ~3 aristas y un flujo cercano a 24.

include("motor.jl")
using Random

const NOMBRES = ["s", "a", "b", "c", "d", "e", "f", "g", "t"]
const POS = [(0.0, 1.5), (1.3, 3.0), (1.3, 0.0), (2.6, 2.4), (2.6, 0.6),
             (3.9, 3.2), (3.9, 1.5), (3.9, 0.0), (5.2, 1.5)]
const S_IDX, T_IDX = 1, 9

# Topología fija: 16 arcos. El par (4,5) y (5,4) es el antiparalelo c ⇄ d.
const ARCOS = [(1,2), (1,3), (1,4),
               (2,4), (2,6),
               (3,5), (3,7),
               (4,5), (5,4),          # ← par antiparalelo
               (4,6), (4,7),
               (5,7), (5,8),
               (6,9), (7,9), (8,9)]

"Construye la red a partir del vector de capacidades (en el orden de ARCOS)."
function construir(caps::Vector{Int})
    C = zeros(Int, 9, 9)
    for (k, (u, v)) in enumerate(ARCOS)
        C[u, v] = caps[k]
    end
    return RedFlujo(C, NOMBRES, POS)
end

"""
    evaluar(caps) -> (ok, motivo, datos)

Aplica los requisitos R1..R6. Devuelve el primer motivo de fallo, lo que
permite contar por qué se descartan las candidatas (los "intentos fallidos"
que la guía pide documentar).
"""
function evaluar(caps::Vector{Int})
    red = construir(caps)
    b = ford_fulkerson_instr(red, S_IDX, T_IDX; buscar = buscar_camino_bfs, etiqueta = "BFS")
    d = ford_fulkerson_instr(red, S_IDX, T_IDX; buscar = buscar_camino_dfs, etiqueta = "DFS")

    b.flujo == d.flujo                    || return (false, "R1_flujos_distintos", nothing)
    d.iteraciones > b.iteraciones         || return (false, "R2_DFS_no_es_peor", nothing)
    any(b.usa_retroceso)                  || return (false, "R3_BFS_sin_retroceso", nothing)
    any(d.usa_retroceso)                  || return (false, "R3_DFS_sin_retroceso", nothing)
    !d.no_decrecientes                    || return (false, "R4_DFS_no_viola_monotonia", nothing)

    Sb, arb, capb, _ = resumen_corte(red, b.F, S_IDX)
    (1 < length(Sb) < 8)                  || return (false, "R5_corte_trivial", nothing)
    length(arb) >= 2                      || return (false, "R5_corte_con_1_arista", nothing)
    Sd, _, _, _ = resumen_corte(red, d.F, S_IDX)
    Set(Sb) == Set(Sd)                    || return (false, "R6_cortes_distintos", nothing)

    score = 3 * (d.iteraciones - b.iteraciones) +
            2 * count(b.usa_retroceso) + count(d.usa_retroceso) -
            abs(length(arb) - 3) - abs(b.flujo - 24) / 6 - abs(length(Sb) - 4)
    return (true, "ok", (red = red, bfs = b, dfs = d, S = Sb, aristas = arb,
                         capacidad = capb, score = score))
end

"""
    buscar(intentos; semilla) -> (mejor, fallos)

Muestreo aleatorio del espacio de capacidades. Devuelve la mejor candidata
y el histograma de motivos de descarte.
"""
function buscar(intentos::Int = 400_000; semilla::Int = 777)
    Random.seed!(semilla)
    mejor = nothing
    mejor_score = -Inf
    fallos = Dict{String,Int}()
    for _ in 1:intentos
        caps = rand(2:15, length(ARCOS))
        ok, motivo, datos = evaluar(caps)
        if !ok
            fallos[motivo] = get(fallos, motivo, 0) + 1
            continue
        end
        if datos.score > mejor_score
            mejor_score = datos.score
            mejor = (caps = copy(caps), datos...)
        end
    end
    return mejor, fallos
end

# ------------------------------------------------------------
# Ejecución
# ------------------------------------------------------------
if abspath(PROGRAM_FILE) == @__FILE__
    println("="^70)
    println("PARTE 3 — Búsqueda de las capacidades de la red propia")
    println("="^70)
    println("Explorando 400 000 combinaciones de capacidades (semilla 777)...\n")

    mejor, fallos = buscar()

    total = sum(values(fallos)) + 1
    println("── Intentos fallidos (por qué se descartó cada candidata) ──")
    for (motivo, n) in sort(collect(fallos); by = x -> -x[2])
        @printf("  %-28s %7d   (%.2f %%)\n", motivo, n, 100n / total)
    end

    println("\n── Red seleccionada ──")
    println("capacidades = ", mejor.caps)
    for (k, (u, v)) in enumerate(ARCOS)
        @printf("  C[%d,%d] = %-3d  # %s → %s\n", u, v, mejor.caps[k],
                NOMBRES[u], NOMBRES[v])
    end
    @printf("\npuntaje = %.2f\n", mejor.score)

    tabla_iteraciones(mejor.red, mejor.bfs)
    tabla_iteraciones(mejor.red, mejor.dfs)
    _, _, _, txt = resumen_corte(mejor.red, mejor.bfs.F, S_IDX)
    println("\ncorte mínimo: ", txt)
    println("\nEstas capacidades son las que quedaron fijadas en `red_propia()` (redes.jl).")
end
