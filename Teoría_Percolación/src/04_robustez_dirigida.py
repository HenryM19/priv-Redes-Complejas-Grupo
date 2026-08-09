# ============================================================
# 04_robustez_dirigida.py
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Simula la percolación de sitios bajo ATAQUE DIRIGIDO sobre
# la red propia (backbone ISP) y genera la curva de robustez
# P∞(f) vs f.
#
# Diferencia con el fallo aleatorio: en lugar de seleccionar
# nodos a remover al azar, el atacante elimina primero los
# nodos de MAYOR GRADO (los hubs), que son los que sostienen
# la conectividad global de la red.
#
# Procedimiento:
#   1. Ordenar nodos por grado descendente.
#   2. Para cada paso i (remover i-ésimo hub):
#        - Construir subgrafo con los N−i nodos restantes.
#        - Medir P∞ = |GCC| / N.
#   (Determinístico — sin necesidad de promediar realizaciones.)
#
# Salida:
#   results/files/04_robustez_dirigida.csv
#   results/images/04_robustez_dirigida.png
#
# Ejecutar desde src/:
#   python 04_robustez_dirigida.py

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
import os
import sys
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from red_propia import construir_red_propia

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

def medir_gcc(G_ud: nx.Graph, nodos_activos: list) -> float:
    """
    Mide el tamaño del GCC en el subgrafo inducido por los
    nodos activos, normalizado por N total.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido original.
        nodos_activos (list): nodos que aún no han sido removidos.

    Salida:
        float: P∞ = |GCC| / N. Retorna 0.0 si no quedan nodos.
    """
    N = G_ud.number_of_nodes()
    if len(nodos_activos) == 0:
        return 0.0
    subgrafo = G_ud.subgraph(nodos_activos)
    componentes = list(nx.connected_components(subgrafo))
    if not componentes:
        return 0.0
    return max(len(c) for c in componentes) / N


def simular_ataque_dirigido(G_ud: nx.Graph) -> tuple:
    """
    Ejecuta el ataque dirigido determinístico: elimina nodos en
    orden decreciente de grado.

    En caso de empate en grado, el orden se desempata
    alfabéticamente para reproducibilidad.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido.

    Salida:
        tuple: (f_vals (list[float]), p_inf (list[float]),
                orden_remocion (list[str]))
            f_vals: fracción removida en cada paso (0/N … N/N).
            p_inf: P∞ tras cada remoción.
            orden_remocion: nombre de nodo removido en cada paso.
    """
    grados = dict(G_ud.degree())
    N      = G_ud.number_of_nodes()

    # Orden de ataque: mayor grado primero; desempate alfabético
    orden = sorted(grados.keys(), key=lambda n: (-grados[n], n))

    nodos_activos = set(G_ud.nodes())
    f_vals         = [0.0]
    p_inf          = [medir_gcc(G_ud, list(nodos_activos))]
    orden_remocion = []

    for i, nodo in enumerate(orden):
        nodos_activos.remove(nodo)
        orden_remocion.append(nodo)
        f_vals.append((i + 1) / N)
        p_inf.append(medir_gcc(G_ud, list(nodos_activos)))

    return f_vals, p_inf, orden_remocion


def guardar_resultados(f_vals: list, p_inf: list,
                       orden: list, ruta: str) -> pd.DataFrame:
    """
    Guarda los resultados del ataque dirigido en CSV.

    Argumentos:
        f_vals (list[float]): fracciones de remoción.
        p_inf (list[float]): valores de P∞.
        orden (list[str]): nodo removido en cada paso
            (el primer valor corresponde a f=0, sin remoción).
        ruta (str): ruta completa del CSV de salida.

    Salida:
        pd.DataFrame: tabla con columnas [f, P_inf, nodo_removido].
    """
    nodos_col = ["(ninguno)"] + orden
    df = pd.DataFrame({"f": f_vals, "P_inf": p_inf,
                        "nodo_removido": nodos_col})
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df.to_csv(ruta, index=False)
    return df


def graficar_curva(f_vals: list, p_inf: list,
                   orden: list, ruta: str) -> None:
    """
    Genera y guarda la curva de robustez P∞ vs f para ataque
    dirigido, anotando qué nodo se removió en cada paso.

    Argumentos:
        f_vals (list[float]): fracciones de remoción.
        p_inf (list[float]): valores de P∞.
        orden (list[str]): nodo removido en cada paso (sin f=0).
        ruta (str): ruta completa del PNG de salida.

    Salida:
        None (guarda imagen en disco).
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(f_vals, p_inf, color="#e74c3c", linewidth=2.5,
            marker="s", markersize=8, label="Ataque dirigido (hubs primero)")
    ax.fill_between(f_vals, p_inf, alpha=0.12, color="#e74c3c")

    # Anotar qué nodo se removió en cada punto
    for i, (f, p, nodo) in enumerate(zip(f_vals[1:], p_inf[1:], orden)):
        ax.annotate(nodo, (f, p), textcoords="offset points",
                    xytext=(6, 4), fontsize=8, color="#922b21")

    ax.set_xlabel("Fracción removida f", fontsize=12)
    ax.set_ylabel("P∞ = GCC / N", fontsize=12)
    ax.set_title("Curva de robustez — Ataque dirigido (hubs primero)\nRed Propia (backbone ISP)", fontsize=13)
    ax.legend(fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=180)
    plt.close(fig)
    print(f"  [OK] Imagen guardada en {ruta}")


# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Construir red y convertir a no dirigida.
# 2) Ejecutar ataque dirigido (orden por grado descendente).
# 3) Mostrar resultados paso a paso por consola.
# 4) Guardar CSV e imagen.

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

G_dir, s, t = construir_red_propia()
G_ud = nx.to_undirected(G_dir)

print("=" * 55)
print("ROBUSTEZ — Ataque Dirigido — Red Propia (backbone ISP)")
print("=" * 55)

f_vals, p_inf, orden = simular_ataque_dirigido(G_ud)

grados = dict(G_ud.degree())
print(f"\n  Orden de ataque (mayor grado primero):")
print(f"  {'Paso':>4}  {'Nodo':>6}  {'Grado':>5}  {'f':>5}  {'P∞':>6}")
print(f"  {'─'*4}  {'─'*6}  {'─'*5}  {'─'*5}  {'─'*6}")
print(f"  {'  0':>4}  {'—':>6}  {'—':>5}  {0.0:>5.3f}  {p_inf[0]:>6.4f}")
for i, (nodo, f, p) in enumerate(zip(orden, f_vals[1:], p_inf[1:]), 1):
    print(f"  {i:>4}  {nodo:>6}  {grados[nodo]:>5}  {f:>5.3f}  {p:>6.4f}")

# f_c empírico: primer f donde P∞ < 0.5
fc_emp = next((f for f, p in zip(f_vals, p_inf) if p < 0.5), f_vals[-1])
print(f"\nf_c empírico (P∞ < 0.5) bajo ataque dirigido ≈ {fc_emp:.3f}")
print("=" * 55)

guardar_resultados(f_vals, p_inf, orden,
    os.path.join(BASE, "results", "files", "04_robustez_dirigida.csv"))
graficar_curva(f_vals, p_inf, orden,
    os.path.join(BASE, "results", "images", "04_robustez_dirigida.png"))
