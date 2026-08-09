# ============================================================
# 05_comparacion.py
# ============================================================
#
# DOCUMENTACIÓN GENERAL
# ------------------------------------------------------------
# Genera la gráfica comparativa de las dos curvas de robustez
# (fallo aleatorio vs. ataque dirigido) sobre la misma figura,
# permitiendo visualizar directamente la brecha de fragilidad
# de la red propia ante cada tipo de perturbación.
#
# Lee los resultados ya generados por los scripts 03 y 04 desde
# los CSV en results/files/, por lo que ambos deben ejecutarse
# antes que este script.
#
# Adicionalmente calcula el Área Bajo la Curva (AUC) para cada
# escenario: un AUC alto indica mayor robustez global.
#
# Salida:
#   results/files/05_comparacion.csv   — AUC y f_c por escenario
#   results/images/05_comparacion.png  — gráfica comparativa
#
# Ejecutar desde src/:
#   python 05_comparacion.py

# ------------------------------------------------------------
# Carga de librerías
# ------------------------------------------------------------
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from red_propia import construir_red_propia

# ------------------------------------------------------------
# Definición de funciones
# ------------------------------------------------------------

def cargar_curva(ruta: str) -> tuple:
    """
    Carga una curva de robustez desde un CSV generado por los
    scripts 03 o 04.

    Argumentos:
        ruta (str): ruta completa al CSV con columnas [f, P_inf].

    Salida:
        tuple: (f_vals (list[float]), p_inf (list[float]))
    """
    df = pd.read_csv(ruta)
    return df["f"].tolist(), df["P_inf"].tolist()


def calcular_auc(f_vals: list, p_inf: list) -> float:
    """
    Calcula el Área Bajo la Curva P∞(f) usando la regla del
    trapecio. Un AUC más alto indica mayor robustez global.

    Argumentos:
        f_vals (list[float]): eje x (fracción removida).
        p_inf (list[float]): eje y (P∞).

    Salida:
        float: AUC ∈ [0, 1].
    """
    return float(np.trapz(p_inf, f_vals))


def calcular_fc_empirico(f_vals: list, p_inf: list) -> float:
    """
    Estima el umbral crítico empírico como el primer f donde
    P∞ cae por debajo de 0.5.

    Argumentos:
        f_vals (list[float]): fracciones de remoción.
        p_inf (list[float]): valores de P∞.

    Salida:
        float: f_c empírico, o el último f si P∞ nunca baja de 0.5.
    """
    for f, p in zip(f_vals, p_inf):
        if p < 0.5:
            return f
    return f_vals[-1]


def graficar_comparacion(f_ale: list, p_ale: list,
                          f_dir: list, p_dir: list,
                          fc_teo: float, ruta: str) -> None:
    """
    Genera la gráfica comparativa de ambas curvas de robustez.

    Argumentos:
        f_ale (list[float]): fracciones — fallo aleatorio.
        p_ale (list[float]): P∞ — fallo aleatorio.
        f_dir (list[float]): fracciones — ataque dirigido.
        p_dir (list[float]): P∞ — ataque dirigido.
        fc_teo (float): f_c teórico de Molloy–Reed.
        ruta (str): ruta completa del PNG de salida.

    Salida:
        None (guarda imagen en disco).
    """
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.plot(f_ale, p_ale, color="#2980b9", linewidth=2.5,
            marker="o", markersize=7, label="Fallo aleatorio")
    ax.fill_between(f_ale, p_ale, alpha=0.10, color="#2980b9")

    ax.plot(f_dir, p_dir, color="#e74c3c", linewidth=2.5,
            marker="s", markersize=7, label="Ataque dirigido (hubs primero)")
    ax.fill_between(f_dir, p_dir, alpha=0.10, color="#e74c3c")

    ax.axvline(fc_teo, color="#7f8c8d", linestyle="--", linewidth=1.6,
               label=f"f_c teórico = {fc_teo:.3f}")

    # Sombrear la "brecha de fragilidad"
    f_common = sorted(set(f_ale) & set(f_dir))
    p_ale_d  = dict(zip(f_ale, p_ale))
    p_dir_d  = dict(zip(f_dir, p_dir))
    fc_shared = [f for f in f_common]
    ax.fill_between(fc_shared,
                    [p_dir_d[f] for f in fc_shared],
                    [p_ale_d[f] for f in fc_shared],
                    alpha=0.15, color="#8e44ad",
                    label="Brecha de fragilidad")

    ax.set_xlabel("Fracción removida f", fontsize=12)
    ax.set_ylabel("P∞ = GCC / N", fontsize=12)
    ax.set_title("Comparación de robustez: fallo aleatorio vs. ataque dirigido\nRed Propia (backbone ISP)", fontsize=13)
    ax.legend(fontsize=10, loc="upper right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=180)
    plt.close(fig)
    print(f"  [OK] Imagen guardada en {ruta}")


def guardar_resumen(resultados: dict, ruta: str) -> None:
    """
    Guarda el resumen comparativo (AUC y f_c) en CSV.

    Argumentos:
        resultados (dict): {escenario: {auc, fc_empirico}}.
        ruta (str): ruta completa del CSV de salida.

    Salida:
        None.
    """
    filas = [{"escenario": k, "AUC": v["auc"], "f_c_empirico": v["fc"]}
             for k, v in resultados.items()]
    df = pd.DataFrame(filas)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df.to_csv(ruta, index=False)


# ------------------------------------------------------------
# CÓDIGO MAIN
# ------------------------------------------------------------
# 1) Cargar curvas de los scripts 03 y 04.
# 2) Calcular AUC y f_c empírico para cada escenario.
# 3) Calcular f_c teórico (Molloy–Reed) para referencia.
# 4) Imprimir resumen comparativo.
# 5) Guardar CSV e imagen comparativa.

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

f_ale, p_ale = cargar_curva(os.path.join(BASE, "results", "files", "03_robustez_aleatoria.csv"))
f_dir, p_dir = cargar_curva(os.path.join(BASE, "results", "files", "04_robustez_dirigida.csv"))

# f_c teórico
G_dir, s, t = construir_red_propia()
G_ud  = __import__("networkx").to_undirected(G_dir)
k_v   = [k for _, k in G_ud.degree()]
kappa = (sum(k**2 for k in k_v)/len(k_v)) / (sum(k_v)/len(k_v))
fc_teo = 1.0 - 1.0 / (kappa - 1.0)

auc_ale = calcular_auc(f_ale, p_ale)
auc_dir = calcular_auc(f_dir, p_dir)
fc_ale  = calcular_fc_empirico(f_ale, p_ale)
fc_dir  = calcular_fc_empirico(f_dir, p_dir)

print("=" * 60)
print("COMPARACIÓN DE ROBUSTEZ — Red Propia (backbone ISP)")
print("=" * 60)
print(f"\n  {'Escenario':<25}  {'AUC':>6}  {'f_c empírico':>13}")
print(f"  {'─'*25}  {'─'*6}  {'─'*13}")
print(f"  {'Fallo aleatorio':<25}  {auc_ale:>6.4f}  {fc_ale:>13.3f}")
print(f"  {'Ataque dirigido':<25}  {auc_dir:>6.4f}  {fc_dir:>13.3f}")
print(f"\n  f_c teórico (Molloy–Reed) = {fc_teo:.4f}")
print(f"\n  Reducción de robustez ante ataque dirigido:")
print(f"    ΔAUC = {auc_ale - auc_dir:.4f}  ({(1 - auc_dir/auc_ale)*100:.1f}% menos área)")
print(f"    Δf_c = {fc_ale - fc_dir:.3f}  (colapsa {(fc_ale-fc_dir)*100:.0f}% antes)")
print(f"\nInterpretación:")
print(f"  La red resiste hasta f={fc_ale:.2f} bajo fallo aleatorio,")
print(f"  pero colapsa ya en f={fc_dir:.2f} si se atacan los hubs primero.")
print("=" * 60)

resultados = {
    "Fallo aleatorio": {"auc": auc_ale, "fc": fc_ale},
    "Ataque dirigido": {"auc": auc_dir, "fc": fc_dir},
}
guardar_resumen(resultados, os.path.join(BASE, "results", "files", "05_comparacion.csv"))
graficar_comparacion(f_ale, p_ale, f_dir, p_dir, fc_teo,
    os.path.join(BASE, "results", "images", "05_comparacion.png"))
