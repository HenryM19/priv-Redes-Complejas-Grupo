"""
problema10.py — Problema P10: Diagnóstico de puntos críticos (Fase 5)
======================================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Consolida resultados de las Fases 1-4 en un ranking único de criticidad.
Define un Índice de Criticidad Compuesto (ICC) que combina:
  - Betweenness centralidad normalizada      (peso 0.35)
  - Condición de punto de articulación       (peso 0.25)
  - Participación en el corte mínimo de flujo (peso 0.20)
  - Daño causado en la cascada (α=0.1)       (peso 0.20)

Presenta el top-10 con ficha completa por nodo: identificador, campus,
función en la jerarquía, métricas individuales y consecuencia estimada.

Uso:
    python problema10.py

Salidas:
    results/tablas/p10_icc_todos.csv
    results/tablas/p10_top10_fichas.csv
    results/imagenes/p10_ranking_icc.png
    results/imagenes/p10_radar_top5.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from math import pi

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
# Componente 1 — Betweenness normalizada
# ------------------------------------------------------------

def calcular_betweenness(G: nx.Graph) -> dict:
    """
    Calcula la betweenness centralidad normalizada para todos los nodos.

    Argumentos:
        G (nx.Graph): grafo de la red.

    Salida:
        dict: {nodo: betweenness_normalizado (float ∈ [0,1])}.
    """
    btw = nx.betweenness_centrality(G, normalized=True)
    max_btw = max(btw.values()) if btw else 1.0
    return {v: btw[v] / max_btw for v in btw}


# ------------------------------------------------------------
# Componente 2 — Punto de articulación (binario)
# ------------------------------------------------------------

def calcular_articulacion(G: nx.Graph) -> dict:
    """
    Identifica los puntos de articulación de la red.
    Un nodo es punto de articulación si su eliminación desconecta el grafo.

    Argumentos:
        G (nx.Graph): grafo de la red.

    Salida:
        dict: {nodo: 1.0 si es punto de articulación, 0.0 si no}.
    """
    art = set(nx.articulation_points(G))
    return {v: 1.0 if v in art else 0.0 for v in G.nodes()}


# ------------------------------------------------------------
# Componente 3 — Participación en corte mínimo
# ------------------------------------------------------------

def calcular_corte_minimo(G: nx.Graph, nodos_csv: pd.DataFrame) -> dict:
    """
    Determina qué nodos participan en el corte mínimo de capacidad de flujo.
    Se usa la red con capacidades reales (trafico_mbps). Si no hay capacidades
    definidas, se usa capacidad unitaria.
    El corte se calcula desde el nodo de mayor grado hacia el de mayor
    betweenness (par más representativo del backbone).

    Argumentos:
        G          (nx.Graph)     : grafo de la red.
        nodos_csv  (pd.DataFrame) : tabla de nodos con columna 'capa'.

    Salida:
        dict: {nodo: 1.0 si aparece en alguna arista del corte mínimo, 0.0 si no}.
    """
    # Construir dígrafo con capacidades
    DG = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        cap = d.get("trafico_mbps", 1) or 1
        DG.add_edge(u, v, capacity=cap)
        DG.add_edge(v, u, capacity=cap)

    # Fuente: nodo de mayor betweenness; sumidero: segundo mayor betweenness
    btw = nx.betweenness_centrality(G, normalized=False)
    ranking_btw = sorted(btw, key=btw.get, reverse=True)
    fuente   = ranking_btw[0]
    sumidero = ranking_btw[1]

    try:
        _, (S_set, T_set) = nx.minimum_cut(DG, fuente, sumidero)
        nodos_corte = set()
        for u in S_set:
            for v in T_set:
                if DG.has_edge(u, v):
                    nodos_corte.add(u)
                    nodos_corte.add(v)
    except Exception:
        nodos_corte = set()

    return {v: 1.0 if v in nodos_corte else 0.0 for v in G.nodes()}


# ------------------------------------------------------------
# Componente 4 — Daño en cascada (Motter-Lai, α=0.1)
# ------------------------------------------------------------

def calcular_danio_cascada(G: nx.Graph, alpha: float = 0.1) -> dict:
    """
    Para cada nodo, simula la cascada de fallos si ese nodo falla primero.
    Retorna la fracción de nodos que caen en cascada (daño normalizado).

    Argumentos:
        G     (nx.Graph): grafo de la red.
        alpha (float)   : tolerancia del modelo Motter-Lai.

    Salida:
        dict: {nodo: fraccion_danio (float ∈ [0,1])}.
              fraccion_danio = (nodos_caidos_en_cascada) / n_total.
    """
    n = G.number_of_nodes()
    btw0 = nx.betweenness_centrality(G, normalized=False)
    capacidad = {v: (1 + alpha) * max(btw0[v], 1.0) for v in G.nodes()}

    danio = {}
    for nodo_inicial in G.nodes():
        Gc = G.copy()
        fallidos = [nodo_inicial]
        Gc.remove_node(nodo_inicial)

        while True:
            if Gc.number_of_nodes() == 0:
                break
            btw_act = nx.betweenness_centrality(Gc, normalized=False)
            nuevos = [v for v in Gc.nodes()
                      if btw_act.get(v, 0) > capacidad.get(v, float("inf"))]
            if not nuevos:
                break
            for v in nuevos:
                Gc.remove_node(v)
                fallidos.append(v)

        danio[nodo_inicial] = len(fallidos) / n

    # Normalizar respecto al máximo
    max_d = max(danio.values()) if danio else 1.0
    return {v: danio[v] / max_d for v in danio}


# ------------------------------------------------------------
# Índice de Criticidad Compuesto (ICC)
# ------------------------------------------------------------

def calcular_icc(G: nx.Graph, nodos_csv: pd.DataFrame,
                 w_btw: float = 0.35, w_art: float = 0.25,
                 w_cut: float = 0.20, w_cas: float = 0.20) -> pd.DataFrame:
    """
    Construye el Índice de Criticidad Compuesto (ICC) para todos los nodos.

    ICC_i = w_btw·B̂_i + w_art·A_i + w_cut·C_i + w_cas·D̂_i

    Donde:
      B̂_i = betweenness normalizada al máximo
      A_i  = 1 si punto de articulación, 0 si no
      C_i  = 1 si en corte mínimo, 0 si no
      D̂_i = daño de cascada normalizado al máximo

    Argumentos:
        G         (nx.Graph)     : grafo de la red.
        nodos_csv (pd.DataFrame) : tabla de nodos con columnas id, campus, capa.
        w_btw, w_art, w_cut, w_cas (float): pesos (deben sumar 1.0).

    Salida:
        pd.DataFrame con columnas:
          nodo, campus, capa, btw_norm, es_articulacion, en_corte,
          danio_cascada_norm, ICC, rank.
    """
    print("  Calculando betweenness...")
    b = calcular_betweenness(G)
    print("  Identificando puntos de articulación...")
    a = calcular_articulacion(G)
    print("  Calculando corte mínimo...")
    c = calcular_corte_minimo(G, nodos_csv)
    print("  Simulando cascadas para cada nodo (puede tardar ~30 s)...")
    d = calcular_danio_cascada(G, alpha=0.1)

    # Mapa campus y capa desde CSV
    info = nodos_csv.set_index("id")[["campus", "capa"]].to_dict("index")

    filas = []
    for v in G.nodes():
        icc = w_btw * b[v] + w_art * a[v] + w_cut * c[v] + w_cas * d[v]
        campus = info.get(v, {}).get("campus", "Desconocido")
        capa   = info.get(v, {}).get("capa",   "desconocida")
        filas.append({
            "nodo"               : v,
            "campus"             : campus,
            "capa"               : capa,
            "btw_norm"           : round(b[v], 4),
            "es_articulacion"    : int(a[v]),
            "en_corte"           : int(c[v]),
            "danio_cascada_norm" : round(d[v], 4),
            "ICC"                : round(icc, 4),
        })

    df = pd.DataFrame(filas).sort_values("ICC", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


# ------------------------------------------------------------
# Fichas del top-10
# ------------------------------------------------------------

def _consecuencia(row: pd.Series, G: nx.Graph) -> str:
    """
    Genera texto de consecuencia estimada según las métricas del nodo.

    Argumentos:
        row (pd.Series) : fila del DataFrame ICC con métricas del nodo.
        G   (nx.Graph)  : grafo para calcular grado.

    Salida:
        str: descripción de consecuencias si el nodo falla.
    """
    partes = []
    grado = G.degree(row["nodo"])
    partes.append(f"Desconexión directa de {grado} enlace(s).")
    if row["es_articulacion"]:
        partes.append("Divide la red en componentes aislados (punto de articulación).")
    if row["en_corte"]:
        partes.append("Interrumpe el flujo máximo entre backbone y distribución.")
    danio_pct = row["danio_cascada_norm"] * 100
    partes.append(f"Puede desencadenar cascada afectando ≈{danio_pct:.0f}% de la carga máxima observada.")
    if row["capa"] in ("core", "mpls"):
        partes.append("Impacto institucional total: pérdida de conectividad inter-campus.")
    elif row["capa"] == "agregacion":
        partes.append("Impacto de campus: aísla todos los accesos del edificio o bloque.")
    return " ".join(partes)


def _funcion_jerarquia(capa: str) -> str:
    """
    Mapea la capa de red a su función jerárquica en la topología.

    Argumentos:
        capa (str): valor de la columna 'capa' del CSV de nodos.

    Salida:
        str: descripción de la función jerárquica.
    """
    mapa = {
        "core"      : "Núcleo (core) — interconexión entre campus",
        "mpls"      : "Backbone MPLS — transporte WAN",
        "agregacion": "Agregación — concentrador de accesos de campus",
        "acceso"    : "Acceso — conexión de equipos finales",
        "firewall"  : "Firewall / seguridad perimetral",
        "router"    : "Router de campus",
        "internet"  : "Punto de salida a Internet",
    }
    return mapa.get(capa, capa.capitalize())


def generar_fichas(df_icc: pd.DataFrame, G: nx.Graph, top_n: int = 10) -> pd.DataFrame:
    """
    Genera fichas detalladas para los top_n nodos más críticos.

    Argumentos:
        df_icc (pd.DataFrame): DataFrame con ICC de todos los nodos.
        G      (nx.Graph)    : grafo de la red.
        top_n  (int)         : número de nodos en el ranking.

    Salida:
        pd.DataFrame con columnas:
          rank, nodo, campus, funcion_jerarquia, grado, btw_norm,
          es_articulacion, en_corte, danio_cascada_norm, ICC,
          metricas_destacadas, consecuencia_estimada.
    """
    top = df_icc.head(top_n).copy()
    top["funcion_jerarquia"]   = top["capa"].apply(_funcion_jerarquia)
    top["grado"]               = top["nodo"].apply(lambda v: G.degree(v))
    top["consecuencia_estimada"] = top.apply(lambda r: _consecuencia(r, G), axis=1)
    top["metricas_destacadas"] = top.apply(lambda r: "; ".join(filter(None, [
        f"btw={r['btw_norm']:.3f}" if r["btw_norm"] > 0.3 else "",
        "ARTICULACIÓN" if r["es_articulacion"] else "",
        "CORTE MÍNIMO" if r["en_corte"] else "",
        f"cascada={r['danio_cascada_norm']:.2f}" if r["danio_cascada_norm"] > 0.3 else "",
    ])), axis=1)

    cols = ["rank", "nodo", "campus", "funcion_jerarquia", "grado",
            "btw_norm", "es_articulacion", "en_corte", "danio_cascada_norm",
            "ICC", "metricas_destacadas", "consecuencia_estimada"]
    return top[cols].reset_index(drop=True)


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_ranking(df_icc: pd.DataFrame, top_n: int = 15) -> None:
    """
    Gráfico de barras horizontales apiladas del ICC (top_n nodos).
    Muestra la contribución de cada componente al ICC total.

    Argumentos:
        df_icc (pd.DataFrame): DataFrame con ICC de todos los nodos.
        top_n  (int)         : número de nodos a mostrar.
    """
    top = df_icc.head(top_n).iloc[::-1]   # invertir para que el #1 quede arriba
    nodos = [n[:28] for n in top["nodo"]]

    fig, ax = plt.subplots(figsize=(11, 7))
    y = np.arange(len(nodos))
    left = np.zeros(len(nodos))
    colores = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12"]
    etiquetas = ["Betweenness (×0.35)", "Articulación (×0.25)",
                 "Corte mínimo (×0.20)", "Cascada (×0.20)"]
    componentes = [
        top["btw_norm"].values * 0.35,
        top["es_articulacion"].values * 0.25,
        top["en_corte"].values * 0.20,
        top["danio_cascada_norm"].values * 0.20,
    ]
    for comp, color, label in zip(componentes, colores, etiquetas):
        ax.barh(y, comp, left=left, color=color, label=label, height=0.7)
        left += comp

    ax.set_yticks(y)
    ax.set_yticklabels(nodos, fontsize=9)
    ax.set_xlabel("ICC (Índice de Criticidad Compuesto)")
    ax.set_title("P10 · Ranking de criticidad — Red UCuenca\n"
                 "ICC = 0.35·B̂ + 0.25·A + 0.20·C + 0.20·D̂", fontweight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p10_ranking_icc.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_radar_top5(df_fichas: pd.DataFrame) -> None:
    """
    Gráfico de radar (spider chart) para los top-5 nodos más críticos.
    Muestra sus 4 componentes normalizadas simultáneamente.

    Argumentos:
        df_fichas (pd.DataFrame): fichas del top-10 generadas por generar_fichas().
    """
    categorias = ["Betweenness", "Articulación", "Corte mín.", "Cascada"]
    N = len(categorias)
    angulos = [n / float(N) * 2 * pi for n in range(N)]
    angulos += angulos[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    colores = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]

    for i, (_, row) in enumerate(df_fichas.head(5).iterrows()):
        valores = [row["btw_norm"], float(row["es_articulacion"]),
                   float(row["en_corte"]), row["danio_cascada_norm"]]
        valores += valores[:1]
        ax.plot(angulos, valores, "o-", linewidth=2,
                color=colores[i], label=row["nodo"][:22])
        ax.fill(angulos, valores, alpha=0.08, color=colores[i])

    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_title("P10 · Perfil de criticidad — Top 5 nodos\n(valores normalizados)",
                 fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=8)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p10_radar_top5.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P10 — Diagnóstico de puntos críticos ===\n")

    # Cargar red y tabla de nodos con metadatos (campus, capa)
    G = cargar_red(fuente="csv"); verificar(G)
    ruta_nodos = os.path.join(DIR_ROOT, "red_ucuenca_nodes.csv")
    nodos_csv  = pd.read_csv(ruta_nodos)

    # Calcular ICC para todos los nodos
    print("[ICC] Calculando índice compuesto para los 177 nodos...")
    df_icc = calcular_icc(G, nodos_csv)
    df_icc.to_csv(os.path.join(DIR_TAB, "p10_icc_todos.csv"), index=False)
    print(f"  [OK] ICC calculado — {len(df_icc)} nodos\n")

    # Top-10 fichas
    print("[TOP-10] Generando fichas de nodos críticos...")
    df_fichas = generar_fichas(df_icc, G, top_n=10)
    df_fichas.to_csv(os.path.join(DIR_TAB, "p10_top10_fichas.csv"), index=False)

    # Imprimir fichas en consola
    print("\n" + "=" * 70)
    print("TOP-10 PUNTOS CRÍTICOS — RED UCUENCA")
    print("=" * 70)
    for _, row in df_fichas.iterrows():
        art_flag = "✓ ARTICULACIÓN" if row["es_articulacion"] else ""
        cut_flag = "✓ CORTE MÍNIMO" if row["en_corte"] else ""
        flags = "  ".join(f for f in [art_flag, cut_flag] if f)
        print(f"\n#{row['rank']:>2}  {row['nodo']}")
        print(f"     Campus   : {row['campus']}")
        print(f"     Función  : {row['funcion_jerarquia']}")
        print(f"     Grado    : {row['grado']}")
        print(f"     ICC      : {row['ICC']:.4f}  {flags}")
        print(f"     Métricas : {row['metricas_destacadas']}")
        print(f"     Riesgo   : {row['consecuencia_estimada']}")

    # Visualizaciones
    print("\n[VIZ] Generando gráficos...")
    graficar_ranking(df_icc, top_n=15)
    graficar_radar_top5(df_fichas)

    print("\n=== P10 completado ===\n")
