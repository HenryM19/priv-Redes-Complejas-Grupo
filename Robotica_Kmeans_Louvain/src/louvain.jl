using LinearAlgebra, Random, Statistics, DataFrames

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  LOUVAIN — Detección de comunidades por optimización de modularidad           ║
# ║                                                                                ║
# ║  Implementado desde cero en Julia. A diferencia de K-Means (que parte el       ║
# ║  espacio por distancia a centroides y necesita K a priori), Louvain trabaja    ║
# ║  sobre un GRAFO y descubre el número de comunidades automáticamente            ║
# ║  maximizando la modularidad Q.                                                 ║
# ║                                                                                ║
# ║  Pipeline:  features (n×p)  →  grafo k-NN ponderado  →  Louvain  →  comunidades ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── 1. Construcción del grafo k-NN ──────────────────────────────────────────────

"""
    build_knn_graph(X; k, sigma) -> W::Matrix{Float64}

Construye una matriz de adyacencia ponderada (simétrica) a partir de la matriz
de features `X` (n×p). Cada nodo = una pieza/actuador.

- Para cada nodo se conectan sus `k` vecinos más cercanos (distancia euclidiana).
- El grafo se simetriza (si i→j o j→i, la arista existe).
- El peso de la arista usa un kernel gaussiano:  w_ij = exp(-d²_ij / (2σ²)).
  Vecinos cercanos → peso alto; lejanos → peso bajo. σ = mediana de las
  distancias k-NN (heurística estándar, escala-adaptativa).

Devuelve W (n×n), W[i,i]=0, W simétrica.
"""
function build_knn_graph(X::Matrix{Float64}; k::Int=10, sigma::Float64=-1.0)::Matrix{Float64}
    n = size(X, 1)
    k = min(k, n - 1)

    # Matriz de distancias al cuadrado (n×n)
    D2 = zeros(Float64, n, n)
    for i in 1:n, j in i+1:n
        d = sum((X[i, :] .- X[j, :]).^2)
        D2[i, j] = d
        D2[j, i] = d
    end

    # σ adaptativo: mediana de la distancia al k-ésimo vecino
    if sigma <= 0.0
        kth = Float64[]
        for i in 1:n
            ds = sort(D2[i, :])
            push!(kth, sqrt(ds[k+1]))   # ds[1]=0 (self); k-ésimo vecino = índice k+1
        end
        sigma = max(median(kth), 1e-8)
    end
    twoσ2 = 2 * sigma^2

    # Adyacencia dirigida k-NN → simetrizar
    W = zeros(Float64, n, n)
    for i in 1:n
        order = sortperm(D2[i, :])                 # incluye self en pos 1
        neighbors = order[2:k+1]                    # k vecinos más cercanos
        for j in neighbors
            w = exp(-D2[i, j] / twoσ2)
            W[i, j] = max(W[i, j], w)
            W[j, i] = max(W[j, i], w)               # simetrización por OR
        end
    end
    return W
end

# ── 2. Modularidad ──────────────────────────────────────────────────────────────

"""
    modularity(W, communities) -> Q::Float64

Modularidad de Newman-Girvan para un grafo ponderado:

    Q = (1 / 2m) · Σ_ij [ W_ij − (k_i · k_j) / 2m ] · δ(c_i, c_j)

donde k_i = Σ_j W_ij (grado ponderado), m = (1/2) Σ_ij W_ij.
Q ∈ [-0.5, 1]; valores altos = estructura comunitaria fuerte.
"""
function modularity(W::Matrix{Float64}, communities::Vector{Int})::Float64
    n = size(W, 1)
    deg = vec(sum(W, dims=2))
    m2  = sum(deg)                       # = 2m
    m2 == 0.0 && return 0.0
    Q = 0.0
    for i in 1:n, j in 1:n
        if communities[i] == communities[j]
            Q += W[i, j] - deg[i] * deg[j] / m2
        end
    end
    return Q / m2
end

# ── 3. Algoritmo de Louvain ─────────────────────────────────────────────────────

"""
Fase 1 (local moving): cada nodo se mueve a la comunidad vecina que produce
la mayor ganancia de modularidad ΔQ, iterando hasta que ningún movimiento mejora.
"""
function _local_moving!(W::Matrix{Float64}, comm::Vector{Int}, deg::Vector{Float64}, m2::Float64)
    n = size(W, 1)
    # Σ_tot[c] = suma de grados de la comunidad c
    Σ_tot = Dict{Int,Float64}()
    for i in 1:n
        Σ_tot[comm[i]] = get(Σ_tot, comm[i], 0.0) + deg[i]
    end

    improved_any = false
    improved = true
    while improved
        improved = false
        for i in 1:n
            ci = comm[i]
            # peso de i hacia cada comunidad vecina
            k_i_in = Dict{Int,Float64}()
            for j in 1:n
                W[i, j] == 0.0 && continue
                cj = comm[j]
                k_i_in[cj] = get(k_i_in, cj, 0.0) + W[i, j]
            end

            # remover i de su comunidad
            Σ_tot[ci] -= deg[i]
            comm[i] = -1

            best_c    = ci
            best_gain = 0.0
            for (c, ki_c) in k_i_in
                c == -1 && continue
                # ΔQ de insertar i en c (forma incremental estándar de Louvain)
                gain = ki_c - Σ_tot[c] * deg[i] / m2
                if gain > best_gain
                    best_gain = gain
                    best_c    = c
                end
            end

            comm[i] = best_c
            Σ_tot[best_c] = get(Σ_tot, best_c, 0.0) + deg[i]
            if best_c != ci
                improved = true
                improved_any = true
            end
        end
    end
    return improved_any
end

"""
Renumera etiquetas de comunidad a 1:C consecutivos (orden por tamaño desc).
"""
function _relabel(comm::Vector{Int})::Vector{Int}
    counts = Dict{Int,Int}()
    for c in comm
        counts[c] = get(counts, c, 0) + 1
    end
    ordered = sort(collect(keys(counts)); by=c -> -counts[c])
    remap   = Dict(c => i for (i, c) in enumerate(ordered))
    return [remap[c] for c in comm]
end

"""
    louvain(W; seed, max_passes) -> (communities, Q, n_communities, history)

Louvain completo con agregación multinivel.

- `communities` : Vector{Int} (1..C) de longitud n — comunidad de cada nodo.
- `Q`           : modularidad final.
- `history`     : Vector de NamedTuple (level, n_comm, Q) — para animar la evolución.

El número de comunidades NO se fija de antemano: emerge de maximizar Q.
"""
function louvain(W::Matrix{Float64}; seed::Int=42, max_passes::Int=20)
    Random.seed!(seed)
    n0 = size(W, 1)

    # node_comm[i] = super-nodo (comunidad) al que pertenece el nodo original i.
    # Empieza 1:n0 (cada nodo su propia comunidad) y se va refinando por nivel.
    node_comm = collect(1:n0)

    Wcur = copy(W)
    history = NamedTuple[]

    for _ in 1:max_passes
        ncur = size(Wcur, 1)
        deg  = vec(sum(Wcur, dims=2))
        m2   = sum(deg)
        comm = collect(1:ncur)          # cada super-nodo en su propia comunidad

        moved = _local_moving!(Wcur, comm, deg, m2)
        comm  = _relabel(comm)          # comm[s] = nueva comunidad del super-nodo s

        # Propagar: el nodo original i estaba en super-nodo node_comm[i];
        # ese super-nodo ahora pertenece a la comunidad comm[node_comm[i]].
        node_comm = [comm[node_comm[i]] for i in 1:n0]

        Qlevel = modularity(W, node_comm)
        push!(history, (level=length(history)+1,
                        n_comm=length(unique(node_comm)),
                        Q=round(Qlevel, digits=4)))

        # Fase 2: agregar comunidades en super-nodos para el siguiente nivel
        Csuper = length(unique(comm))
        if !moved || Csuper == ncur
            break
        end
        Wcur = _aggregate(Wcur, comm, Csuper)
    end

    final = _relabel(node_comm)
    return (communities=final, Q=modularity(W, final),
            n_communities=length(unique(final)), history=history)
end

"""
Construye el grafo de super-nodos: nodo = comunidad, peso = suma de aristas
internas/entre comunidades (incluye auto-aristas = enlaces intra-comunidad).
"""
function _aggregate(W::Matrix{Float64}, comm::Vector{Int}, C::Int)::Matrix{Float64}
    Wnew = zeros(Float64, C, C)
    n = size(W, 1)
    for i in 1:n, j in 1:n
        W[i, j] == 0.0 && continue
        Wnew[comm[i], comm[j]] += W[i, j]
    end
    return Wnew
end

"""
    louvain_animated(W; seed, snap_every) -> (snapshots, Qs, communities, Q)

Variante instrumentada de la **fase de movimiento local** sobre el grafo original.
Captura el estado de las comunidades (asignación por nodo) cada `snap_every`
movimientos de nodo, para animar cómo el algoritmo va fusionando nodos en
comunidades iteración por iteración.

- `snapshots` : Vector{Vector{Int}} — etiqueta de comunidad de cada nodo en cada frame.
- `Qs`        : Vector{Float64} — modularidad en cada frame.

Para el grafo k-NN denso (k≈30% n) la fase local de un nivel ya converge a la
partición final, así que esta animación muestra el descubrimiento completo de
las comunidades.
"""
function louvain_animated(W::Matrix{Float64}; seed::Int=42, snap_every::Int=6)
    Random.seed!(seed)
    n   = size(W, 1)
    deg = vec(sum(W, dims=2))
    m2  = sum(deg)

    comm  = collect(1:n)               # cada nodo en su propia comunidad
    Σ_tot = Dict{Int,Float64}(i => deg[i] for i in 1:n)

    snapshots = Vector{Vector{Int}}()
    Qs        = Float64[]
    push!(snapshots, _relabel(copy(comm)))
    push!(Qs, modularity(W, comm))

    moves = 0
    improved = true
    sweep = 0
    while improved && sweep < 100
        improved = false
        sweep += 1
        for i in 1:n
            ci = comm[i]
            k_i_in = Dict{Int,Float64}()
            for j in 1:n
                W[i, j] == 0.0 && continue
                cj = comm[j]
                k_i_in[cj] = get(k_i_in, cj, 0.0) + W[i, j]
            end
            Σ_tot[ci] -= deg[i]
            comm[i] = -1
            best_c, best_gain = ci, 0.0
            for (c, ki_c) in k_i_in
                c == -1 && continue
                gain = ki_c - Σ_tot[c] * deg[i] / m2
                if gain > best_gain
                    best_gain, best_c = gain, c
                end
            end
            comm[i] = best_c
            Σ_tot[best_c] = get(Σ_tot, best_c, 0.0) + deg[i]
            if best_c != ci
                improved = true
                moves += 1
                if moves % snap_every == 0
                    push!(snapshots, _relabel(copy(comm)))
                    push!(Qs, modularity(W, comm))
                end
            end
        end
    end

    # frame final
    push!(snapshots, _relabel(copy(comm)))
    push!(Qs, modularity(W, comm))
    return (snapshots=snapshots, Qs=Qs,
            communities=_relabel(comm), Q=modularity(W, comm))
end
