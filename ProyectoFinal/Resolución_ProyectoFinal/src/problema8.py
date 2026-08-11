"""
problema8.py — Problema P8: Percolación de Nodos y Aristas (Fase 4)
====================================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Analiza la robustez de la red UCuenca ante fallas usando percolación:
eliminación secuencial de nodos o aristas bajo 4 estrategias de ataque
y observando el colapso de la componente gigante.

Métrica principal:
  Eficiencia global  E(G) = (1/(n(n-1))) · Σ_{i≠j} 1/d(i,j)
  donde d(i,j) = ∞ si no hay camino ⟹ 0 en la suma.

Estrategias implementadas:
  1. Aleatorio         : eliminación aleatoria (promedio de 10 semillas)
  2. Grado-descendente : eliminar primero el nodo/arista de mayor grado
  3. Betweenness       : eliminar primero el nodo de mayor betweenness
  4. Grado-ascendente  : eliminar primero el nodo de menor grado (comparación)

Los cinco ítems resueltos son:
  Ítem 1 · Función de eficiencia global E(G)
  Ítem 2 · Percolación de nodos bajo 4 estrategias
  Ítem 3 · Percolación de aristas bajo 2 estrategias
  Ítem 4 · Comparación con modelos nulos (ER, CM, BA)
  Ítem 5 · Identificación del umbral de percolación

Uso:
    python problema8.py

Salidas:
    results/tablas/p8_percolacion_nodos.csv
    results/tablas/p8_percolacion_aristas.csv
    results/imagenes/p8_robustez_nodos.png
    results/imagenes/p8_robustez_aristas.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, random, copy
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

DIR_SRC   = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL = os.path.dirname(DIR_SRC)
DIR_ROOT  = os.path.dirname(DIR_RESOL)
DIR_BASE  = os.path.join(DIR_ROOT, "codigo_base")
DIR_TAB   = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG   = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar  # noqa


def _crear_dirs():
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


# ============================================================
# Definición de funciones
# ============================================================

# ------------------------------------------------------------
# Ítem 1 — Eficiencia global
# ------------------------------------------------------------

def eficiencia_global(G: nx.Graph) -> float:
    """
    Calcula la eficiencia global de un grafo.
    E(G) = 1/(n(n-1)) * Σ_{i≠j} 1/d(i,j)
    Si no hay camino entre i y j, su contribución es 0.

    Argumentos:
        G (nx.Graph): grafo (puede ser disconexo).

    Salida:
        float: eficiencia global ∈ [0, 1].
    """
    n = G.number_of_nodes()
    if n <= 1:
        return 0.0
    total = 0.0
    for u in G.nodes():
        lengths = nx.single_source_shortest_path_length(G, u)
        for v, d in lengths.items():
            if v != u and d > 0:
                total += 1.0 / d
    return total / (n * (n - 1))


# ------------------------------------------------------------
# Ítem 2 — Percolación de nodos
# ------------------------------------------------------------

def _orden_nodos(G: nx.Graph, estrategia: str, semilla: int = 42) -> list:
    """
    Genera el orden de eliminación de nodos según la estrategia.

    Argumentos:
        G          (nx.Graph): grafo actual.
        estrategia (str)     : 'aleatorio'|'grado_desc'|'betweenness'|'btw_recalc'.
        semilla    (int)     : semilla para aleatoriedad.

    Salida:
        list: nodos en orden de eliminación (para estrategias estáticas).
              Para 'btw_recalc' devuelve lista vacía (orden se recalcula en línea).
    """
    nodos = list(G.nodes())
    if estrategia == "aleatorio":
        rng = random.Random(semilla)
        rng.shuffle(nodos)
        return nodos
    elif estrategia == "grado_desc":
        return sorted(nodos, key=lambda n: G.degree(n), reverse=True)
    elif estrategia == "betweenness":
        btw = nx.betweenness_centrality(G)
        return sorted(nodos, key=lambda n: btw[n], reverse=True)
    elif estrategia == "btw_recalc":
        return []   # orden se decide dinámicamente tras cada eliminación
    else:
        raise ValueError(f"Estrategia desconocida: {estrategia}")


def percolacion_nodos(G: nx.Graph, estrategia: str,
                      semilla: int = 42, pasos: int = 30) -> pd.DataFrame:
    """
    Simula la percolación de nodos eliminando secuencialmente según la estrategia.
    Para 'btw_recalc', recalcula betweenness tras cada eliminación (ataque adaptativo).

    Argumentos:
        G          (nx.Graph): grafo original.
        estrategia (str)     : 'aleatorio'|'grado_desc'|'betweenness'|'btw_recalc'.
        semilla    (int)     : semilla para estrategia aleatoria.
        pasos      (int)     : número de puntos de muestreo.

    Salida:
        pd.DataFrame con columnas [fraccion_eliminada, eficiencia, n_componentes, tamanio_cgc].
    """
    Gc = G.copy()
    n_total = Gc.number_of_nodes()
    orden = _orden_nodos(G, estrategia, semilla)

    muestras = np.linspace(0, 1, pasos + 1)
    fracs_objetivo = [int(f * n_total) for f in muestras]
    filas = []
    eliminados = 0

    # Estado inicial
    filas.append({
        "fraccion_eliminada": 0.0,
        "eficiencia"        : eficiencia_global(Gc),
        "n_componentes"     : nx.number_connected_components(Gc),
        "tamanio_cgc"       : max(len(c) for c in nx.connected_components(Gc)),
    })

    for frac, objetivo in zip(muestras[1:], fracs_objetivo[1:]):
        while eliminados < objetivo and Gc.number_of_nodes() > 0:
            if estrategia == "btw_recalc":
                # Recalcula betweenness en el grafo actual
                btw = nx.betweenness_centrality(Gc)
                nodo = max(btw, key=btw.get)
            else:
                nodo = orden[eliminados] if eliminados < len(orden) else None
            if nodo and nodo in Gc:
                Gc.remove_node(nodo)
            eliminados += 1

        if Gc.number_of_nodes() == 0:
            filas.append({"fraccion_eliminada": round(frac, 4), "eficiencia": 0.0,
                           "n_componentes": 0, "tamanio_cgc": 0})
            continue
        comps = list(nx.connected_components(Gc))
        filas.append({
            "fraccion_eliminada": round(frac, 4),
            "eficiencia"        : eficiencia_global(Gc),
            "n_componentes"     : len(comps),
            "tamanio_cgc"       : max(len(c) for c in comps),
        })
    return pd.DataFrame(filas)


def percolacion_aleatoria_media(G: nx.Graph, n_semillas: int = 100,
                                 pasos: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Promedia la percolación aleatoria sobre 100 realizaciones y calcula
    la desviación estándar por fracción, como exige la guía.

    Argumentos:
        G          (nx.Graph): grafo.
        n_semillas (int)     : número de realizaciones (mínimo 100).
        pasos      (int)     : puntos de muestreo.

    Salida:
        tuple: (df_media, df_std) — DataFrames con media y std por fracción.
    """
    dfs = [percolacion_nodos(G, "aleatorio", semilla=s, pasos=pasos)
           for s in range(n_semillas)]
    df_concat = pd.concat(dfs)
    df_media = df_concat.groupby("fraccion_eliminada").mean().reset_index()
    df_std   = df_concat.groupby("fraccion_eliminada").std().reset_index()
    return df_media, df_std


# ------------------------------------------------------------
# Ítem 3 — Percolación de aristas
# ------------------------------------------------------------

def percolacion_aristas(G: nx.Graph, estrategia: str = "aleatorio",
                         semilla: int = 42, pasos: int = 30) -> pd.DataFrame:
    """
    Simula la percolación de aristas eliminando secuencialmente.

    Argumentos:
        G          (nx.Graph): grafo original.
        estrategia (str)     : 'aleatorio' | 'betweenness_arista' | 'puentes_primero'.
        semilla    (int)     : semilla aleatoria.
        pasos      (int)     : puntos de muestreo.

    Salida:
        pd.DataFrame con [fraccion_eliminada, eficiencia, n_componentes, tamanio_cgc].

    Nota 'puentes_primero': elimina primero los puentes identificados en P1
    (aristas cuya eliminación desconecta la red), luego el resto aleatoriamente.
    Modela un ataque dirigido a los enlaces más críticos estructuralmente.
    """
    Gc = G.copy()
    aristas = list(G.edges())
    m_total = len(aristas)

    if estrategia == "aleatorio":
        rng = random.Random(semilla)
        rng.shuffle(aristas)
        orden_aristas = aristas
    elif estrategia == "puentes_primero":
        # Puentes de P1: aristas cuya eliminación desconecta la red
        puentes = set(nx.bridges(G))
        puentes_norm = set()
        for u, v in puentes:
            puentes_norm.add((u, v))
            puentes_norm.add((v, u))
        # Ordenar puentes por betweenness de arista (más críticos primero)
        btw_e = nx.edge_betweenness_centrality(G)
        lista_puentes = sorted(
            [(u, v) for u, v in aristas if (u, v) in puentes_norm or (v, u) in puentes_norm],
            key=lambda e: btw_e.get(e, btw_e.get((e[1], e[0]), 0)), reverse=True
        )
        resto = [e for e in aristas if (e[0], e[1]) not in puentes_norm
                 and (e[1], e[0]) not in puentes_norm]
        rng = random.Random(semilla)
        rng.shuffle(resto)
        orden_aristas = lista_puentes + resto
    else:
        btw_e = nx.edge_betweenness_centrality(G)
        orden_aristas = sorted(aristas, key=lambda e: btw_e.get(e, btw_e.get((e[1],e[0]),0)),
                               reverse=True)

    muestras = np.linspace(0, 1, pasos + 1)
    filas = []
    eliminados = 0

    filas.append({
        "fraccion_eliminada": 0.0,
        "eficiencia"        : eficiencia_global(Gc),
        "n_componentes"     : nx.number_connected_components(Gc),
        "tamanio_cgc"       : max(len(c) for c in nx.connected_components(Gc)),
    })

    for frac in muestras[1:]:
        objetivo = int(frac * m_total)
        while eliminados < objetivo and eliminados < len(orden_aristas):
            u, v = orden_aristas[eliminados]
            if Gc.has_edge(u, v):
                Gc.remove_edge(u, v)
            eliminados += 1
        if Gc.number_of_nodes() == 0:
            filas.append({"fraccion_eliminada": frac, "eficiencia": 0.0,
                           "n_componentes": 0, "tamanio_cgc": 0})
            continue
        comps = list(nx.connected_components(Gc))
        filas.append({
            "fraccion_eliminada": round(frac, 4),
            "eficiencia"        : eficiencia_global(Gc),
            "n_componentes"     : len(comps),
            "tamanio_cgc"       : max(len(c) for c in comps),
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Ítem 4 — Comparación con modelos nulos
# ------------------------------------------------------------

def generar_modelo_nulo(G: nx.Graph, modelo: str, semilla: int = 42) -> nx.Graph:
    """
    Genera un modelo nulo para comparación.

    Argumentos:
        G      (nx.Graph): grafo de referencia.
        modelo (str)     : 'ER' | 'CM'.
        semilla (int)    : semilla aleatoria.

    Salida:
        nx.Graph: grafo del modelo nulo.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    rng = np.random.default_rng(semilla)
    if modelo == "ER":
        p = 2 * m / (n * (n - 1))
        H = nx.erdos_renyi_graph(n, p, seed=int(rng.integers(0, 10000)))
        return H
    elif modelo == "CM":
        grados = [d for _, d in G.degree()]
        try:
            H = nx.configuration_model(grados, seed=int(rng.integers(0, 10000)))
            H = nx.Graph(H)  # remover multi-aristas y auto-lazos
            H.remove_edges_from(nx.selfloop_edges(H))
        except Exception:
            H = nx.erdos_renyi_graph(n, 2*m/(n*(n-1)),
                                      seed=int(rng.integers(0, 10000)))
        return H
    raise ValueError(f"Modelo desconocido: {modelo}")


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_robustez_nodos(resultados: dict, df_std: pd.DataFrame = None) -> None:
    """
    Curvas de E(f) y S(f) vs fracción de nodos eliminados para las 4 estrategias.
    Incluye banda de ±1 std para la estrategia aleatoria (100 realizaciones).

    Argumentos:
        resultados (dict)        : {estrategia: df_media}.
        df_std     (pd.DataFrame): std de la estrategia aleatoria.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colores   = {"aleatorio": "steelblue", "grado_desc": "red",
                 "betweenness": "darkorange", "btw_recalc": "purple"}
    etiquetas = {"aleatorio"  : "Fallo aleatorio (media ± std, 100 realiz.)",
                 "grado_desc" : "(b) Ataque por grado descendente",
                 "betweenness": "(c) Ataque por betweenness (estático)",
                 "btw_recalc" : "(d) Ataque por betweenness recalculada"}

    for est, df in resultados.items():
        c = colores.get(est, "gray")
        lbl = etiquetas.get(est, est)
        ax1.plot(df["fraccion_eliminada"], df["eficiencia"],
                 color=c, label=lbl, linewidth=2)
        ax2.plot(df["fraccion_eliminada"],
                 df["tamanio_cgc"] / df["tamanio_cgc"].iloc[0],
                 color=c, label=lbl, linewidth=2)

    # Banda ±std para aleatoria
    if df_std is not None and "aleatorio" in resultados:
        df_m = resultados["aleatorio"]
        ax1.fill_between(df_m["fraccion_eliminada"],
                         df_m["eficiencia"] - df_std["eficiencia"].fillna(0),
                         df_m["eficiencia"] + df_std["eficiencia"].fillna(0),
                         alpha=0.2, color="steelblue")

    for ax in (ax1, ax2):
        ax.set_xlabel("Fracción de nodos eliminados (f)")
        ax.legend(fontsize=7); ax.grid(alpha=0.3)
    ax1.set_ylabel("Eficiencia global E(f)"); ax1.set_title("Eficiencia global E(f)")
    ax2.set_ylabel("S(f) = tamaño relativo CGC"); ax2.set_title("Componente gigante S(f)")

    plt.suptitle("P8 · Percolación de nodos — Red UCuenca", fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p8_robustez_nodos.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_robustez_aristas(res_aleat: pd.DataFrame, res_btw: pd.DataFrame,
                               res_puentes: pd.DataFrame) -> None:
    """
    Curvas de E(f) y S(f) vs fracción de aristas eliminadas.
    Incluye ataque a puentes de P1.

    Argumentos:
        res_aleat   (pd.DataFrame): percolación aleatoria de aristas.
        res_btw     (pd.DataFrame): ataque por betweenness de arista.
        res_puentes (pd.DataFrame): ataque dirigido a puentes de P1 primero.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    for ax in (ax1, ax2):
        ax.plot(res_aleat["fraccion_eliminada"],
                res_aleat["eficiencia"] if ax == ax1
                else res_aleat["tamanio_cgc"] / res_aleat["tamanio_cgc"].iloc[0],
                "b-", linewidth=2, label="Aleatorio")
        ax.plot(res_btw["fraccion_eliminada"],
                res_btw["eficiencia"] if ax == ax1
                else res_btw["tamanio_cgc"] / res_btw["tamanio_cgc"].iloc[0],
                "r--", linewidth=2, label="Mayor betweenness de arista")
        ax.plot(res_puentes["fraccion_eliminada"],
                res_puentes["eficiencia"] if ax == ax1
                else res_puentes["tamanio_cgc"] / res_puentes["tamanio_cgc"].iloc[0],
                "g:", linewidth=2, label="Puentes de P1 primero")
        ax.set_xlabel("Fracción de aristas eliminadas (q)")
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax1.set_ylabel("Eficiencia global E(q)"); ax1.set_title("Eficiencia global E(q)")
    ax2.set_ylabel("S(q) = tamaño relativo CGC"); ax2.set_title("Componente gigante S(q)")

    plt.suptitle("P8 · Percolación de aristas — Red UCuenca", fontweight="bold")
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p8_robustez_aristas.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P8 — Percolación de Nodos y Aristas ===\n")

    G = cargar_red(fuente="csv"); verificar(G)
    E0 = eficiencia_global(G)
    print(f"  Eficiencia global inicial E₀ = {E0:.4f}\n")

    PASOS = 20  # resolución de la curva

    # ── Ítem 1: percolación de nodos — 4 estrategias ──────────────────
    print("[Ítem 1] Percolación de nodos — 4 estrategias...")
    print("  (a) Fallo aleatorio — 100 realizaciones...")
    df_aleat, df_std = percolacion_aleatoria_media(G, n_semillas=100, pasos=PASOS)
    print(f"      std media eficiencia: {df_std['eficiencia'].mean():.5f}")
    print("  [OK] aleatorio (100 realizaciones, std reportada)")

    print("  (b) Ataque por grado descendente...")
    df_gdesc = percolacion_nodos(G, "grado_desc", pasos=PASOS)
    print("  [OK] grado_desc")

    print("  (c) Ataque por betweenness (estático)...")
    df_btw   = percolacion_nodos(G, "betweenness", pasos=PASOS)
    print("  [OK] betweenness")

    print("  (d) Ataque por betweenness recalculada tras cada eliminación...")
    df_btwR  = percolacion_nodos(G, "btw_recalc", pasos=PASOS)
    print("  [OK] btw_recalc")

    resultados_nodos = {
        "aleatorio"  : df_aleat,
        "grado_desc" : df_gdesc,
        "betweenness": df_btw,
        "btw_recalc" : df_btwR,
    }

    # Guardar CSV con media + std
    df_todos = pd.concat([df.assign(estrategia=k) for k, df in resultados_nodos.items()])
    df_std_save = df_std.assign(estrategia="aleatorio_std")
    pd.concat([df_todos, df_std_save]).to_csv(
        os.path.join(DIR_TAB, "p8_percolacion_nodos.csv"), index=False)

    graficar_robustez_nodos(resultados_nodos, df_std)

    # ── Ítem 2: estimar fc (fracción donde S(f) < 0.05) ──────────────
    print("\n  Umbral de percolación fc (S(f) < 5% de la CGC inicial):")
    n0 = G.number_of_nodes()
    for est, df in resultados_nodos.items():
        cgc0 = df["tamanio_cgc"].iloc[0]
        fc = None
        for _, row in df.iterrows():
            if row["tamanio_cgc"] / cgc0 < 0.05:
                fc = row["fraccion_eliminada"]; break
        f_e50 = None
        for _, row in df.iterrows():
            if df["eficiencia"].iloc[0] > 0 and \
               row["eficiencia"] / df["eficiencia"].iloc[0] < 0.5:
                f_e50 = row["fraccion_eliminada"]; break
        print(f"    {est:15s}: fc(S<5%)≈{fc if fc else '>1.0':>4}  "
              f"f(E<50%)≈{f_e50 if f_e50 else '>1.0'}")

    # ── Ítem 3: percolación de aristas ───────────────────────────────
    print("\n[Ítem 3] Percolación de aristas...")
    df_ar_aleat   = percolacion_aristas(G, "aleatorio", pasos=PASOS)
    print("  [OK] aleatorio")
    df_ar_btw     = percolacion_aristas(G, "betweenness_arista", pasos=PASOS)
    print("  [OK] betweenness de arista")
    n_puentes = len(list(nx.bridges(G)))
    df_ar_puentes = percolacion_aristas(G, "puentes_primero", pasos=PASOS)
    print(f"  [OK] puentes primero ({n_puentes} puentes de P1 eliminados al inicio)")

    pd.concat([
        df_ar_aleat.assign(estrategia="aleatorio"),
        df_ar_btw.assign(estrategia="betweenness_arista"),
        df_ar_puentes.assign(estrategia="puentes_primero"),
    ]).to_csv(os.path.join(DIR_TAB, "p8_percolacion_aristas.csv"), index=False)

    graficar_robustez_aristas(df_ar_aleat, df_ar_btw, df_ar_puentes)

    # ── Ítem 4-5: comparación con modelos nulos ───────────────────────
    print("\n[Ítem 5] Comparación con modelos nulos (ER, CM) — ataque por grado...")
    for modelo in ["ER", "CM"]:
        H    = generar_modelo_nulo(G, modelo)
        e_h  = eficiencia_global(H)
        df_h = percolacion_nodos(H, "grado_desc", pasos=PASOS)
        cgc0 = df_h["tamanio_cgc"].iloc[0] if df_h["tamanio_cgc"].iloc[0] > 0 else 1
        fc_h = next((row["fraccion_eliminada"] for _, row in df_h.iterrows()
                     if row["tamanio_cgc"] / cgc0 < 0.05), ">1.0")
        print(f"  Modelo {modelo}: E₀={e_h:.4f}  fc(S<5%)≈{fc_h}")

    print(f"  Red UCuenca:    E₀={E0:.4f}  (ver tabla arriba)")

    print("\n=== P8 completado ===\n")
