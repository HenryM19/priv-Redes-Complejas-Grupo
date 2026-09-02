"""
P8 · Ítem complementario — Curvas de percolación: red UCuenca vs. modelos nulos
==============================================================================

Compara la robustez de la red real frente a los modelos nulos de P2
(Erdős–Rényi y Modelo de Configuración) bajo dos estrategias de ataque:
aleatorio y dirigido por grado.

Genera:
  results/tablas/p8_percolacion_modelos_nulos.csv
  results/imagenes/p8_percolacion_modelos_nulos.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from problema8 import (
    cargar_red, percolacion_nodos, generar_modelo_nulo, eficiencia_global,
    DIR_TAB, DIR_IMG,
)

PASOS       = 40
N_REALIZ    = 20     # realizaciones por modelo nulo (se promedian)
ESTRATEGIAS = ["aleatorio", "grado_desc"]

ETIQUETAS = {
    "aleatorio":  "Fallo aleatorio",
    "grado_desc": "Ataque dirigido (grado)",
}
COLORES = {
    "UCuenca": "#c0392b",
    "ER":      "#2980b9",
    "CM":      "#27ae60",
}


def curva_normalizada(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza el tamaño de la componente gigante respecto a su valor inicial."""
    cgc0 = df["tamanio_cgc"].iloc[0] or 1
    out = df[["fraccion_eliminada", "tamanio_cgc"]].copy()
    out["S_rel"] = out["tamanio_cgc"] / cgc0
    return out


def umbral_critico(df: pd.DataFrame, umbral: float = 0.05):
    """Fracción eliminada en que la componente gigante cae por debajo del umbral."""
    cgc0 = df["tamanio_cgc"].iloc[0] or 1
    for _, fila in df.iterrows():
        if fila["tamanio_cgc"] / cgc0 < umbral:
            return fila["fraccion_eliminada"]
    return np.nan


def main() -> None:
    G = cargar_red()
    print(f"Red UCuenca: n={G.number_of_nodes()}, m={G.number_of_edges()}")

    filas, curvas = [], {}

    for estrategia in ESTRATEGIAS:
        # ── Red real ──────────────────────────────────────────────
        df_real = percolacion_nodos(G, estrategia, pasos=PASOS)
        curvas[("UCuenca", estrategia)] = curva_normalizada(df_real)
        filas.append({
            "modelo": "UCuenca", "estrategia": estrategia,
            "eficiencia_inicial": eficiencia_global(G),
            "f_critica": umbral_critico(df_real),
        })

        # ── Modelos nulos (promedio sobre N_REALIZ realizaciones) ──
        for modelo in ["ER", "CM"]:
            acumulado, efs, fcs = [], [], []
            for r in range(N_REALIZ):
                H = generar_modelo_nulo(G, modelo, semilla=1000 + r)
                df_h = percolacion_nodos(H, estrategia, pasos=PASOS)
                acumulado.append(curva_normalizada(df_h)["S_rel"].values)
                efs.append(eficiencia_global(H))
                fcs.append(umbral_critico(df_h))

            largo = min(len(a) for a in acumulado)
            media = np.mean([a[:largo] for a in acumulado], axis=0)
            base  = curva_normalizada(df_h)["fraccion_eliminada"].values[:largo]

            curvas[(modelo, estrategia)] = pd.DataFrame(
                {"fraccion_eliminada": base, "S_rel": media})
            filas.append({
                "modelo": modelo, "estrategia": estrategia,
                "eficiencia_inicial": float(np.mean(efs)),
                "f_critica": float(np.nanmean(fcs)),
            })
            print(f"  {modelo:8s} {estrategia:12s} "
                  f"E0={np.mean(efs):.4f}  fc={np.nanmean(fcs):.3f}")

    # ── Tabla resumen ─────────────────────────────────────────────
    df_resumen = pd.DataFrame(filas)
    ruta_csv = os.path.join(DIR_TAB, "p8_percolacion_modelos_nulos.csv")
    df_resumen.to_csv(ruta_csv, index=False)
    print(f"\n[OK] {ruta_csv}")
    print(df_resumen.to_string(index=False))

    # ── Figura: dos paneles (una estrategia por panel) ────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)

    for ax, estrategia in zip(axes, ESTRATEGIAS):
        for modelo in ["UCuenca", "ER", "CM"]:
            df_c = curvas[(modelo, estrategia)]
            ax.plot(df_c["fraccion_eliminada"], df_c["S_rel"],
                    label=modelo, color=COLORES[modelo],
                    lw=2.4 if modelo == "UCuenca" else 1.8,
                    ls="-" if modelo == "UCuenca" else "--",
                    marker="o" if modelo == "UCuenca" else None,
                    markersize=3.5, markevery=4)
        ax.set_title(ETIQUETAS[estrategia], fontsize=11, fontweight="bold")
        ax.set_xlabel("Fracción de nodos eliminados $f$")
        ax.grid(alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)

    axes[0].set_ylabel("Componente gigante relativa $S/S_0$")
    axes[0].legend(frameon=False)
    fig.suptitle("Percolación: red UCuenca frente a modelos nulos "
                 f"(promedio de {N_REALIZ} realizaciones)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()

    ruta_img = os.path.join(DIR_IMG, "p8_percolacion_modelos_nulos.png")
    fig.savefig(ruta_img, dpi=150, bbox_inches="tight")
    print(f"[OK] {ruta_img}")


if __name__ == "__main__":
    main()
