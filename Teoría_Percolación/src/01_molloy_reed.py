# ============================================================
# 01_molloy_reed.py
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Aplica el criterio de Molloy–Reed a la red propia (backbone
# ISP) para determinar:
#   1. La distribución de grados de la red no dirigida.
#   2. El parámetro κ = ⟨k²⟩ / ⟨k⟩ y si existe componente
#      gigante (κ > 2).
#   3. La fracción crítica de remoción f_c = 1 − 1/(κ₀ − 1)
#      (Cohen et al., 2000): máxima fracción de nodos que puede
#      fallar aleatoriamente antes de que el GCC desaparezca.
#
# Salida:
#   results/files/01_molloy_reed.csv  — tabla de grados por nodo
#   results/images/01_distribucion_grados.png
#
# Ejecutar desde src/:
#   python 01_molloy_reed.py

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

def convertir_no_dirigida(G: nx.DiGraph) -> nx.Graph:
    """
    Convierte el dígrafo de la red propia a un grafo no dirigido.
    Los arcos antiparalelos (c→d y d→c) se fusionan en una sola
    arista no dirigida c–d, tal como requiere el análisis de
    percolación de sitios.

    Argumentos:
        G (nx.DiGraph): dígrafo original de la red propia.

    Salida:
        nx.Graph: grafo no dirigido equivalente.
    """
    return nx.to_undirected(G)


def calcular_grados(G_ud: nx.Graph) -> dict:
    """
    Calcula el grado de cada nodo en el grafo no dirigido.

    Argumentos:
        G_ud (nx.Graph): grafo no dirigido.

    Salida:
        dict: {nodo (str): grado (int)}.
    """
    return dict(G_ud.degree())


def calcular_momentos(grados: dict) -> tuple:
    """
    Calcula los momentos de la distribución de grados necesarios
    para el criterio de Molloy–Reed.

    Argumentos:
        grados (dict): {nodo: grado}.

    Salida:
        tuple: (k_medio (float), k2_medio (float), kappa (float))
            k_medio  = ⟨k⟩  = (1/N) Σ kᵢ
            k2_medio = ⟨k²⟩ = (1/N) Σ kᵢ²
            kappa    = ⟨k²⟩ / ⟨k⟩
    """
    k_vals = list(grados.values())
    n = len(k_vals)
    k_medio  = sum(k_vals) / n
    k2_medio = sum(k**2 for k in k_vals) / n
    kappa    = k2_medio / k_medio
    return k_medio, k2_medio, kappa


def calcular_fc(kappa: float) -> float:
    """
    Calcula la fracción crítica de remoción aleatoria f_c según
    la fórmula de Cohen et al. (2000):
        f_c = 1 − 1 / (κ₀ − 1)

    Argumentos:
        kappa (float): κ = ⟨k²⟩/⟨k⟩ de la red original.

    Salida:
        float: f_c ∈ (0, 1). Si κ ≤ 2, retorna 0.0 (sin GCC).
    """
    if kappa <= 2:
        return 0.0
    return 1.0 - 1.0 / (kappa - 1.0)


def guardar_tabla(grados: dict, ruta: str) -> pd.DataFrame:
    """
    Construye y guarda la tabla de grados en CSV.

    Argumentos:
        grados (dict): {nodo: grado}.
        ruta (str): ruta completa del archivo CSV de salida.

    Salida:
        pd.DataFrame: tabla con columnas [nodo, grado].
    """
    df = pd.DataFrame(
        sorted(grados.items(), key=lambda x: -x[1]),
        columns=["nodo", "grado"]
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df.to_csv(ruta, index=False)
    return df


def graficar_distribucion(grados: dict, ruta: str) -> None:
    """
    Genera y guarda el histograma de la distribución de grados.

    Argumentos:
        grados (dict): {nodo: grado}.
        ruta (str): ruta completa del PNG de salida.

    Salida:
        None (guarda imagen en disco).
    """
    nodos = list(grados.keys())
    degs  = [grados[n] for n in nodos]
    colores = ["#c0392b" if d == max(degs) else "#2980b9" for d in degs]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(nodos, degs, color=colores, edgecolor="white", linewidth=0.8)
    ax.axhline(sum(degs)/len(degs), color="gray", linestyle="--",
               linewidth=1.2, label=f"⟨k⟩ = {sum(degs)/len(degs):.2f}")
    for bar, d in zip(bars, degs):
        ax.text(bar.get_x() + bar.get_width()/2, d + 0.05, str(d),
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xlabel("Nodo", fontsize=12)
    ax.set_ylabel("Grado k", fontsize=12)
    ax.set_title("Distribución de grados — Red Propia (no dirigida)", fontsize=13)
    ax.legend(fontsize=11)
    ax.set_ylim(0, max(degs) + 1.5)
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=180)
    plt.close(fig)
    print(f"  [OK] Imagen guardada en {ruta}")


# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Construir la red y convertirla a no dirigida.
# 2) Calcular grados, momentos y κ.
# 3) Verificar existencia de GCC con criterio Molloy–Reed.
# 4) Calcular f_c.
# 5) Guardar tabla CSV e imagen.

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

G_dir, s, t = construir_red_propia()
G_ud = convertir_no_dirigida(G_dir)

grados = calcular_grados(G_ud)
k_medio, k2_medio, kappa = calcular_momentos(grados)
fc = calcular_fc(kappa)

print("=" * 55)
print("CRITERIO DE MOLLOY–REED — Red Propia (backbone ISP)")
print("=" * 55)
print(f"\nNodos (N)   : {G_ud.number_of_nodes()}")
print(f"Aristas (E) : {G_ud.number_of_edges()}")
print(f"\nGrados por nodo:")
for nodo, g in sorted(grados.items(), key=lambda x: -x[1]):
    hub = "  ← HUB (máximo)" if g == max(grados.values()) else ""
    print(f"  {nodo:4s}: k = {g}{hub}")
print(f"\n⟨k⟩  = {k_medio:.4f}")
print(f"⟨k²⟩ = {k2_medio:.4f}")
print(f"κ    = {kappa:.4f}")
print(f"\n¿Existe GCC? {'SÍ (κ > 2)' if kappa > 2 else 'NO (κ ≤ 2)'}")
print(f"\nFracción crítica de remoción aleatoria:")
print(f"  f_c = 1 − 1/(κ₀ − 1) = 1 − 1/({kappa:.4f} − 1) = {fc:.4f}")
print(f"\nInterpretación: se pueden remover aleatoriamente hasta el")
print(f"  {fc*100:.1f}% de los nodos antes de que el GCC desaparezca.")
print("=" * 55)

df = guardar_tabla(grados, os.path.join(BASE, "results", "files", "01_molloy_reed.csv"))
graficar_distribucion(grados, os.path.join(BASE, "results", "images", "01_distribucion_grados.png"))
