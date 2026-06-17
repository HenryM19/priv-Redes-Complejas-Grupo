using DataFrames, Statistics

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  COMPARACIÓN  K-MEANS  vs  LOUVAIN                                             ║
# ║                                                                                ║
# ║  Mismos actuadores, dos paradigmas distintos de agrupamiento:                  ║
# ║    K-Means  → particional, geométrico, requiere K, minimiza inercia.           ║
# ║    Louvain  → comunidades en grafo, K emergente, maximiza modularidad.         ║
# ║                                                                                ║
# ║  Métricas de acuerdo entre dos particiones (y contra ground truth):           ║
# ║    ARI  — Adjusted Rand Index   (1 = idénticas, 0 = azar)                      ║
# ║    NMI  — Normalized Mutual Information (1 = idénticas, 0 = independientes)     ║
# ║    Purity — fracción mayoritaria por cluster contra la etiqueta de referencia. ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── Matriz de contingencia ──────────────────────────────────────────────────────

function contingency(a::Vector{Int}, b::Vector{Int})::Matrix{Int}
    ua, ub = sort(unique(a)), sort(unique(b))
    ia = Dict(v => i for (i, v) in enumerate(ua))
    ib = Dict(v => i for (i, v) in enumerate(ub))
    M = zeros(Int, length(ua), length(ub))
    for (x, y) in zip(a, b)
        M[ia[x], ib[y]] += 1
    end
    return M
end

# ── Adjusted Rand Index ─────────────────────────────────────────────────────────

"""
    adjusted_rand_index(a, b) -> Float64

ARI compara dos particiones contando pares de elementos que ambas agrupan
igual / distinto, corregido por azar:

    ARI = (Σ C(n_ij,2) − [Σ C(a_i,2)·Σ C(b_j,2)]/C(n,2))
          ─────────────────────────────────────────────────────────────
          (½[Σ C(a_i,2)+Σ C(b_j,2)] − [Σ C(a_i,2)·Σ C(b_j,2)]/C(n,2))
"""
function adjusted_rand_index(a::Vector{Int}, b::Vector{Int})::Float64
    M = contingency(a, b)
    n = sum(M)
    n < 2 && return 1.0
    comb2(x) = x * (x - 1) / 2

    sum_ij = sum(comb2(M[i, j]) for i in 1:size(M, 1), j in 1:size(M, 2))
    ai     = sum(comb2(sum(M[i, :])) for i in 1:size(M, 1))
    bj     = sum(comb2(sum(M[:, j])) for j in 1:size(M, 2))
    cn     = comb2(n)

    expected = ai * bj / cn
    maxidx   = (ai + bj) / 2
    denom    = maxidx - expected
    return denom == 0.0 ? 1.0 : (sum_ij - expected) / denom
end

# ── Normalized Mutual Information ───────────────────────────────────────────────

"""
    nmi(a, b) -> Float64

NMI = I(A;B) / sqrt(H(A)·H(B)).  Mide información compartida entre particiones.
"""
function nmi(a::Vector{Int}, b::Vector{Int})::Float64
    M = contingency(a, b)
    n = sum(M)
    n == 0 && return 0.0
    Pi = vec(sum(M, dims=2)) ./ n
    Pj = vec(sum(M, dims=1)) ./ n

    H(p) = -sum(x > 0 ? x * log(x) : 0.0 for x in p)
    Ha, Hb = H(Pi), H(Pj)

    I = 0.0
    for i in 1:size(M, 1), j in 1:size(M, 2)
        pij = M[i, j] / n
        pij == 0.0 && continue
        I += pij * log(pij / (Pi[i] * Pj[j]))
    end
    den = sqrt(Ha * Hb)
    return den == 0.0 ? 1.0 : I / den
end

# ── Purity contra etiqueta de referencia ────────────────────────────────────────

"""
    purity(pred, ref) -> Float64

Para cada cluster predicho, fracción que corresponde a su clase mayoritaria
en la referencia (ground truth). Promedio ponderado por tamaño.
"""
function purity(pred::Vector{Int}, ref::Vector{Int})::Float64
    n = length(pred)
    n == 0 && return 0.0
    total = 0
    for c in unique(pred)
        idx = findall(==(c), pred)
        labs = ref[idx]
        total += maximum(count(==(l), labs) for l in unique(labs))
    end
    return total / n
end

# ── Tabla comparativa completa ──────────────────────────────────────────────────

"""
    compare_partitions(kmeans_labels, louvain_labels, ground_truth; Q, inertia) -> DataFrame

Devuelve un DataFrame de una fila por método con sus métricas, más una fila de
acuerdo K-Means↔Louvain.
"""
function compare_partitions(
    kmeans_labels  ::Vector{Int},
    louvain_labels ::Vector{Int},
    ground_truth   ::Vector{Int};
    kmeans_silhouette ::Float64 = NaN,
    louvain_Q         ::Float64 = NaN
)::DataFrame
    df = DataFrame(
        metodo         = String[],
        n_clusters     = Int[],
        purity_vs_gt   = Float64[],
        ari_vs_gt      = Float64[],
        nmi_vs_gt      = Float64[],
        metrica_propia = String[],
    )
    push!(df, ("K-Means",
        length(unique(kmeans_labels)),
        round(purity(kmeans_labels, ground_truth), digits=3),
        round(adjusted_rand_index(kmeans_labels, ground_truth), digits=3),
        round(nmi(kmeans_labels, ground_truth), digits=3),
        isnan(kmeans_silhouette) ? "—" : "silhouette=$(round(kmeans_silhouette,digits=3))"))
    push!(df, ("Louvain",
        length(unique(louvain_labels)),
        round(purity(louvain_labels, ground_truth), digits=3),
        round(adjusted_rand_index(louvain_labels, ground_truth), digits=3),
        round(nmi(louvain_labels, ground_truth), digits=3),
        isnan(louvain_Q) ? "—" : "modularidad Q=$(round(louvain_Q,digits=3))"))
    return df
end

"""
    agreement(kmeans_labels, louvain_labels) -> NamedTuple(ari, nmi, contingency)

Acuerdo directo entre ambos métodos (sin ground truth).
"""
function agreement(kmeans_labels::Vector{Int}, louvain_labels::Vector{Int})
    return (
        ari = round(adjusted_rand_index(kmeans_labels, louvain_labels), digits=3),
        nmi = round(nmi(kmeans_labels, louvain_labels), digits=3),
        contingency = contingency(kmeans_labels, louvain_labels),
    )
end
