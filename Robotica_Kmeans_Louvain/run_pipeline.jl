"""
Pipeline UNIFICADO: Clustering de Actuadores Robóticos
    K-Means  (particional)  +  Louvain  (comunidades en grafo)

Unifica los proyectos Kmeans_Comparacion / Kmeans_Robot_Henry / Kmeans_Robot_Jean
en un único enfoque: sobre el MISMO dataset de actuadores se ejecutan los dos
paradigmas y se comparan cuantitativamente (ARI / NMI / Purity / modularidad).

Uso:
  julia --project=. run_pipeline.jl [opciones]

Opciones:
  --n-piezas N     Total de piezas sintéticas (default: 120)
  --seed N         Semilla RNG (default: 42)
  --k-min N        K mínimo K-Means (default: 2)
  --k-max N        K máximo K-Means (default: 6)
  --k-fixed N      K-Means con K fijo
  --n-init N       Corridas K-means por K (default: 10)
  --knn-k N        Vecinos k del grafo Louvain (default: auto ≈ sqrt(n)+ )
  --train-ratio F  Fracción de entrenamiento (default: 0.70)
  --output DIR     Directorio de salida (default: results)
  --no-anim        Omitir generación de GIFs
"""

using Pkg
Pkg.activate(@__DIR__)
isfile(joinpath(@__DIR__, "Manifest.toml")) || Pkg.instantiate()

include(joinpath(@__DIR__, "src", "synthesis.jl"))
include(joinpath(@__DIR__, "src", "features.jl"))
include(joinpath(@__DIR__, "src", "clustering.jl"))
include(joinpath(@__DIR__, "src", "louvain.jl"))
include(joinpath(@__DIR__, "src", "comparison.jl"))
include(joinpath(@__DIR__, "src", "animation.jl"))
include(joinpath(@__DIR__, "src", "reporting.jl"))

using CSV, DataFrames, Dates

# ── Parseo de argumentos ───────────────────────────────────────────────────────

function parse_args(args)
    cfg = Dict{Symbol,Any}(
        :n_piezas    => 120,
        :seed        => 42,
        :k_min       => 2,
        :k_max       => 6,
        :k_fixed     => nothing,
        :n_init      => 10,
        :knn_k       => nothing,    # auto
        :train_ratio => 0.70,
        :output      => joinpath(@__DIR__, "results"),
        :no_anim     => false,
    )
    i = 1
    while i <= length(args)
        a = args[i]
        if     a == "--n-piezas"    cfg[:n_piezas]    = parse(Int,     args[i+1]); i += 2
        elseif a == "--seed"        cfg[:seed]        = parse(Int,     args[i+1]); i += 2
        elseif a == "--k-min"       cfg[:k_min]       = parse(Int,     args[i+1]); i += 2
        elseif a == "--k-max"       cfg[:k_max]       = parse(Int,     args[i+1]); i += 2
        elseif a == "--k-fixed"     cfg[:k_fixed]     = parse(Int,     args[i+1]); i += 2
        elseif a == "--n-init"      cfg[:n_init]      = parse(Int,     args[i+1]); i += 2
        elseif a == "--knn-k"       cfg[:knn_k]       = parse(Int,     args[i+1]); i += 2
        elseif a == "--train-ratio" cfg[:train_ratio] = parse(Float64, args[i+1]); i += 2
        elseif a == "--output"      cfg[:output]      = args[i+1];                 i += 2
        elseif a == "--no-anim"     cfg[:no_anim]     = true;                      i += 1
        else
            @warn "Argumento desconocido: $a"; i += 1
        end
    end
    return cfg
end

# ── Pipeline principal ─────────────────────────────────────────────────────────

function run_pipeline(cfg::Dict)
    println("\n" * "━"^64)
    println("  PIPELINE UNIFICADO — K-MEANS + LOUVAIN — ACTUADORES ROBÓTICOS")
    println("  Fecha: $(Dates.today())")
    println("━"^64)

    out_dir    = cfg[:output]
    anim_dir   = joinpath(out_dir, "animations")
    raw_dir    = joinpath(out_dir, "raw")
    report_dir = joinpath(out_dir, "report")
    mkpath(anim_dir); mkpath(raw_dir); mkpath(report_dir)

    # ── 1. Datos sintéticos ───────────────────────────────────────────────────
    println("\n[1/8] Generando dataset sintético…")
    df = generate_actuators(cfg[:n_piezas]; seed=cfg[:seed])
    println("  Total piezas: $(nrow(df))")
    train_df, test_df = train_test_split(df; train_ratio=cfg[:train_ratio], seed=cfg[:seed])
    println("  Train: $(nrow(train_df))  |  Test: $(nrow(test_df))")
    CSV.write(joinpath(raw_dir, "piezas_completo.csv"), df)
    CSV.write(joinpath(raw_dir, "piezas_train.csv"),   train_df)
    CSV.write(joinpath(raw_dir, "piezas_test.csv"),    test_df)

    # ── 2. Features ───────────────────────────────────────────────────────────
    println("\n[2/8] Extrayendo features…")
    X_train, _, fit_stats = compute_features(train_df)
    X_test,  _, _         = compute_features(test_df; fit_stats=fit_stats)
    println("  Matriz train: $(size(X_train))  |  test: $(size(X_test))")

    # ── 3. K-Means + selección de K ───────────────────────────────────────────
    println("\n[3/8] K-Means — seleccionando K óptimo…")
    best_k, k_stats, best_run = if !isnothing(cfg[:k_fixed])
        k = cfg[:k_fixed]
        r = kmeans_best(X_train, k; n_init=cfg[:n_init])
        k, DataFrame(k=[k], inertia=[last(r.inertia_history)],
                     silhouette=[silhouette_score(X_train, r.labels)], elbow_score=[0.0]), r
    else
        auto_select_k(X_train; k_range=cfg[:k_min]:cfg[:k_max], n_init=cfg[:n_init])
    end
    sil = silhouette_score(X_train, best_run.labels)
    print_k_stats(k_stats, best_k)

    kmeans_labels    = best_run.labels
    test_assignments = assign_labels(X_test, best_run.centroids)

    # ── 4. Louvain sobre grafo k-NN ───────────────────────────────────────────
    println("\n[4/8] Louvain — grafo k-NN + comunidades…")
    n_train = size(X_train, 1)
    # Heurística: k ≈ 30% de n equilibra densidad del grafo y separación de
    # comunidades (k bajo fragmenta en micro-comunidades; k alto colapsa todo).
    knn_k   = isnothing(cfg[:knn_k]) ? clamp(round(Int, 0.30 * n_train), 10, n_train - 1) : cfg[:knn_k]
    W       = build_knn_graph(X_train; k=knn_k)
    lou     = louvain(W; seed=cfg[:seed])
    lou_anim = louvain_animated(W; seed=cfg[:seed])
    @printf("  k-NN k=%d  →  comunidades=%d  |  modularidad Q=%.4f\n",
            knn_k, lou.n_communities, lou.Q)

    # ── 5. Comparación K-Means vs Louvain ─────────────────────────────────────
    println("\n[5/8] Comparando K-Means vs Louvain…")
    gt        = train_df.clase_latente
    cmp_df    = compare_partitions(kmeans_labels, lou.communities, gt;
                                   kmeans_silhouette=sil, louvain_Q=lou.Q)
    agree     = agreement(kmeans_labels, lou.communities)
    show(cmp_df, allrows=true, allcols=true); println()
    @printf("  Acuerdo K-Means↔Louvain:  ARI=%.3f  NMI=%.3f\n", agree.ari, agree.nmi)
    CSV.write(joinpath(report_dir, "comparacion_metodos.csv"), cmp_df)

    # ── 6. Tablas K-Means + CSVs ──────────────────────────────────────────────
    println("\n[6/8] Generando tablas y reportes…")
    cluster_tbl = build_cluster_table(train_df, kmeans_labels; latent_ref=gt)
    piece_map   = build_piece_map(train_df, kmeans_labels)
    test_eval   = evaluate_test(kmeans_labels, test_assignments)
    save_reports(cluster_tbl, k_stats, best_k, sil, out_dir;
                 piece_map=piece_map, test_eval=test_eval, mode=:sim)
    # mapa pieza → comunidad Louvain
    CSV.write(joinpath(report_dir, "mapa_comunidades_louvain.csv"),
              DataFrame(pieza_id=train_df.pieza_id,
                        clase_latente=gt,
                        kmeans_cluster=kmeans_labels,
                        louvain_comunidad=lou.communities))

    # ── 7. Visualizaciones ────────────────────────────────────────────────────
    Z, _ = pca2d(X_train)
    if !cfg[:no_anim]
        println("\n[7/8] Generando animaciones y figuras…")
        animate_kmeans(X_train, best_k, joinpath(anim_dir, "kmeans_convergencia.gif");
                       seed=cfg[:seed], fps=3, pause_frames=8)
        animate_elbow(k_stats.k, Float64.(k_stats.inertia), Float64.(k_stats.silhouette),
                      best_k, joinpath(anim_dir, "k_selection.gif"); fps=4)
        animate_feature_scatter(train_df, kmeans_labels,
                      CLUSTER_NAMES[1:min(best_k, length(CLUSTER_NAMES))],
                      joinpath(anim_dir, "feature_scatter.gif"); fps=2)
        # Louvain
        animate_louvain(W, lou.history, lou.communities, Z,
                      joinpath(anim_dir, "louvain_grafo.gif"); fps=2)
        animate_louvain_iterations(W, lou_anim.snapshots, lou_anim.Qs, Z,
                      joinpath(anim_dir, "louvain_iteraciones.gif"); fps=6, pause_frames=10)
        plot_graph_communities(W, lou.communities, Z,
                      joinpath(report_dir, "louvain_comunidades.png"))
        plot_side_by_side(Z, kmeans_labels, lou.communities,
                      joinpath(report_dir, "comparacion_kmeans_louvain.png"))
    else
        println("\n[7/8] Animaciones omitidas (--no-anim) — generando solo PNGs…")
        plot_graph_communities(W, lou.communities, Z,
                      joinpath(report_dir, "louvain_comunidades.png"))
        plot_side_by_side(Z, kmeans_labels, lou.communities,
                      joinpath(report_dir, "comparacion_kmeans_louvain.png"))
    end

    # ── 8. reporte.md (K-Means) + apéndice Louvain ────────────────────────────
    println("\n[8/8] Generando reporte.md…")
    write_reporte_md(cluster_tbl, k_stats, piece_map, best_k, sil, out_dir;
        test_eval=test_eval, n_total=nrow(df), n_train=nrow(train_df),
        n_test=nrow(test_df), mode=:sim)
    append_louvain_section(out_dir; louvain_result=lou, knn_k=knn_k,
        compare_df=cmp_df, agreement_nt=agree, n_train=n_train)

    println("\n" * "━"^64)
    println("  ✓ Pipeline completado")
    println("  K-Means: K=$best_k (sil=$(round(sil,digits=3)))  |  " *
            "Louvain: $(lou.n_communities) comunidades (Q=$(round(lou.Q,digits=3)))")
    println("  Resultados en: $out_dir")
    println("━"^64 * "\n")
end

cfg = parse_args(ARGS)
run_pipeline(cfg)
