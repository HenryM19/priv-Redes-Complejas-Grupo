# ============================================================
# 03_robustez_aleatoria.py
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Simula la percolación de sitios bajo FALLO ALEATORIO sobre
# la red propia (backbone ISP) y genera la curva de robustez
# P∞(f) vs f.
#
# Procedimiento (algoritmo del slide "Del algoritmo al parámetro
# de orden"):
#   Para cada fracción f en {0, 1/N, 2/N, …, 1}:
#     Repetir R realizaciones:
#       1. Seleccionar aleatoriamente ⌊f·N⌋ nodos a remover.
#       2. Construir subgrafo con los nodos restantes.
#       3. Medir GCC = componente conexa más grande / N.
#     Promediar P∞ sobre las R realizaciones.
#
# La red es pequeña (N=9), por lo que se usan R=5000
# realizaciones para obtener una curva suave.
#
# Salida:
#   results/files/03_robustez_aleatoria.csv
#   results/images/03_robustez_aleatoria.png
#
# Ejecutar desde src/:
#   python 03_robustez_aleatoria.py

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
import os
import sys
import random
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from red_propia import construir_red_propia

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

def medir_gcc(G_ud: nx.Graph, nodos_activos: list) -> float:
    """
    Mide el tamaño del componente gigante (GCC) en el subgrafo
    inducido por los nodos activos, normalizado por el total N.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido original.
        nodos_activos (list): lista de nodos que sobreviven.

    Salida:
        float: P∞ = |GCC| / N, donde N = número total de nodos
               en G_ud. Retorna 0.0 si no quedan nodos activos.
    """
    N = G_ud.number_of_nodes()
    if len(nodos_activos) == 0:
        return 0.0
    subgrafo = G_ud.subgraph(nodos_activos)
    componentes = list(nx.connected_components(subgrafo))
    if not componentes:
        return 0.0
    gcc = max(len(c) for c in componentes)
    return gcc / N


def simular_fallo_aleatorio(G_ud: nx.Graph, R: int = 5000,
                             semilla: int = 42) -> tuple:
    """
    Ejecuta la simulación de fallo aleatorio (percolación de sitios
    con remoción aleatoria).

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido.
        R (int): número de realizaciones por valor de f.
        semilla (int): semilla aleatoria para reproducibilidad.

    Salida:
        tuple: (f_vals (list[float]), p_inf (list[float]))
            f_vals: fracciones de remoción, de 0 a 1.
            p_inf: P∞ promediado sobre R realizaciones por cada f.
    """
    rng   = random.Random(semilla)
    nodos = list(G_ud.nodes())
    N     = len(nodos)

    f_vals = [i / N for i in range(N + 1)]
    p_inf  = []

    for f in f_vals:
        n_remover = round(f * N)
        acum = 0.0
        for _ in range(R):
            removidos    = rng.sample(nodos, n_remover)
            activos      = [n for n in nodos if n not in set(removidos)]
            acum        += medir_gcc(G_ud, activos)
        p_inf.append(acum / R)

    return f_vals, p_inf


def guardar_resultados(f_vals: list, p_inf: list, ruta: str) -> pd.DataFrame:
    """
    Guarda los resultados de la simulación en CSV.

    Argumentos:
        f_vals (list[float]): fracciones de remoción.
        p_inf (list[float]): valores de P∞.
        ruta (str): ruta completa del CSV de salida.

    Salida:
        pd.DataFrame: tabla con columnas [f, P_inf].
    """
    df = pd.DataFrame({"f": f_vals, "P_inf": p_inf})
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df.to_csv(ruta, index=False)
    return df


def graficar_curva(f_vals: list, p_inf: list, fc: float, ruta: str) -> None:
    """
    Genera y guarda la curva de robustez P∞ vs f para fallo aleatorio.

    Argumentos:
        f_vals (list[float]): fracciones de remoción.
        p_inf (list[float]): valores de P∞.
        fc (float): fracción crítica teórica (Molloy–Reed).
        ruta (str): ruta completa del PNG de salida.

    Salida:
        None (guarda imagen en disco).
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(f_vals, p_inf, color="#2980b9", linewidth=2.5,
            marker="o", markersize=7, label="Fallo aleatorio (simulación)")
    ax.axvline(fc, color="#e74c3c", linestyle="--", linewidth=1.8,
               label=f"f_c teórico = {fc:.3f} (Molloy–Reed)")
    ax.fill_between(f_vals, p_inf, alpha=0.12, color="#2980b9")
    ax.set_xlabel("Fracción removida f", fontsize=12)
    ax.set_ylabel("P∞ = GCC / N", fontsize=12)
    ax.set_title("Curva de robustez — Fallo aleatorio\nRed Propia (backbone ISP)", fontsize=13)
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
# 2) Calcular f_c teórico (Molloy–Reed) para referencia.
# 3) Simular fallo aleatorio con R=5000 realizaciones.
# 4) Mostrar resultados por consola.
# 5) Guardar CSV e imagen.

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R    = 5000

G_dir, s, t = construir_red_propia()
G_ud = nx.to_undirected(G_dir)
N    = G_ud.number_of_nodes()

# f_c teórico
grados   = dict(G_ud.degree())
k_vals   = list(grados.values())
k_medio  = sum(k_vals) / N
k2_medio = sum(k**2 for k in k_vals) / N
kappa    = k2_medio / k_medio
fc       = 1.0 - 1.0 / (kappa - 1.0)

print("=" * 55)
print("ROBUSTEZ — Fallo Aleatorio — Red Propia (backbone ISP)")
print("=" * 55)
print(f"  N = {N} nodos  |  R = {R} realizaciones por punto")
print(f"  f_c teórico (Molloy–Reed) = {fc:.4f}")
print(f"\nSimulando...")

f_vals, p_inf = simular_fallo_aleatorio(G_ud, R=R)

print(f"\n  f      P∞(f)")
print(f"  {'─'*5}  {'─'*6}")
for f, p in zip(f_vals, p_inf):
    print(f"  {f:.3f}  {p:.4f}")

# f_c empírico: primer f donde P∞ < 0.5
fc_emp = next((f for f, p in zip(f_vals, p_inf) if p < 0.5), f_vals[-1])
print(f"\nf_c empírico (P∞ < 0.5) ≈ {fc_emp:.3f}")
print(f"f_c teórico (Molloy–Reed)  = {fc:.4f}")
print("=" * 55)

guardar_resultados(f_vals, p_inf,
    os.path.join(BASE, "results", "files", "03_robustez_aleatoria.csv"))
graficar_curva(f_vals, p_inf, fc,
    os.path.join(BASE, "results", "images", "03_robustez_aleatoria.png"))
