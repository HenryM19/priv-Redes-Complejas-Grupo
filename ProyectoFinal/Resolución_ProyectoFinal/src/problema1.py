"""
problema1.py — Problema P1: Medidas Fundamentales (Fase 1)
===========================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Calcula e interpreta las medidas estructurales fundamentales de la red
de datos de la Universidad de Cuenca (177 nodos, 209 aristas).

Los seis ítems resueltos son:
  Ítem 1 · Métricas básicas del grafo
  Ítem 2 · Distribución de grado (histograma + log-log)
  Ítem 3 · Centralidades: grado, betweenness, closeness, eigenvector
  Ítem 4 · Clustering, diámetro, distancia media y asortatividad
  Ítem 5 · Puntos de articulación y puentes (por campus y capa)
  Ítem 6 · Contraste con el informe técnico (redundancia core–agregación)

Uso:
    python problema1.py

Salidas (relativas a Resolución_ProyectoFinal/):
    results/tablas/p1_metricas_basicas.txt
    results/tablas/p1_centralidades_top10.csv
    results/tablas/p1_articulacion_campus.csv
    results/tablas/p1_articulacion_capa.csv
    results/tablas/p1_puentes_campus.csv
    results/tablas/p1_redundancia.txt
    results/imagenes/p1_distribucion_grado.png
    results/imagenes/p1_centralidades_top10.png
    results/imagenes/p1_articulacion_puentes.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os
import sys
import warnings
import collections

import networkx as nx
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from scipy.special import zeta as hurwitz_zeta

warnings.filterwarnings("ignore")

# --- Rutas del proyecto ---
DIR_SRC    = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL  = os.path.dirname(DIR_SRC)                      # Resolución_ProyectoFinal/
DIR_ROOT   = os.path.dirname(DIR_RESOL)                    # ProyectoFinal/
DIR_BASE   = os.path.join(DIR_ROOT, "codigo_base")         # codigo_base/
DIR_TAB    = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG    = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar           # noqa: E402  (importación local)


# ============================================================
# Definición de funciones
# ============================================================

# ------------------------------------------------------------
# Utilidades internas
# ------------------------------------------------------------

def _crear_dirs() -> None:
    """
    Crea los directorios de salida si no existen.

    Argumentos: ninguno
    Salida: None
    """
    for d in (DIR_TAB, DIR_IMG):
        os.makedirs(d, exist_ok=True)


def _guardar_tabla(texto: str, nombre: str) -> None:
    """
    Escribe un bloque de texto como archivo .txt en results/tablas/.

    Argumentos:
        texto  (str): contenido a guardar.
        nombre (str): nombre del archivo, sin ruta.

    Salida: None
    """
    ruta = os.path.join(DIR_TAB, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"  [OK] {ruta}")


def _guardar_csv(df: pd.DataFrame, nombre: str) -> None:
    """
    Guarda un DataFrame como CSV en results/tablas/.

    Argumentos:
        df     (pd.DataFrame): tabla a guardar.
        nombre (str): nombre del archivo, sin ruta.

    Salida: None
    """
    ruta = os.path.join(DIR_TAB, nombre)
    df.to_csv(ruta, index=False, encoding="utf-8")
    print(f"  [OK] {ruta}")


def _guardar_figura(fig: plt.Figure, nombre: str) -> None:
    """
    Guarda una figura matplotlib en results/imagenes/.

    Argumentos:
        fig    (plt.Figure): figura a guardar.
        nombre (str): nombre del archivo, sin ruta.

    Salida: None
    """
    ruta = os.path.join(DIR_IMG, nombre)
    fig.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {ruta}")


# ------------------------------------------------------------
# Ítem 1 · Métricas básicas
# ------------------------------------------------------------

def metricas_basicas(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Calcula las métricas básicas del grafo: nodos, aristas, densidad,
    componentes conexas y tamaño de la mayor.

    Argumentos:
        G        (nx.Graph)    : grafo de la red UCuenca.
        nodos_df (pd.DataFrame): tabla de nodos con columnas campus y capa.

    Salida:
        dict: {
            'n'              (int)  : número de nodos,
            'm'              (int)  : número de aristas,
            'densidad'       (float): densidad del grafo 2m / n(n-1),
            'n_componentes'  (int)  : número de componentes conexas,
            'tam_mayor'      (int)  : tamaño de la componente más grande,
        }
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    componentes = list(nx.connected_components(G))

    resultado = {
        "n"             : n,
        "m"             : m,
        "densidad"      : nx.density(G),
        "n_componentes" : len(componentes),
        "tam_mayor"     : max(len(c) for c in componentes),
    }

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 1 · MÉTRICAS BÁSICAS",
        "=" * 60,
        f"  Nodos (n)                     : {resultado['n']}",
        f"  Aristas (m)                   : {resultado['m']}",
        f"  Densidad                      : {resultado['densidad']:.6f}",
        f"  Componentes conexas           : {resultado['n_componentes']}",
        f"  Tamaño de la mayor componente : {resultado['tam_mayor']}",
        "",
        "  INTERPRETACIÓN:",
        "  La densidad es muy baja (~0.013), lo que es esperable en una",
        "  red de infraestructura jerárquica: cada equipo se conecta solo",
        "  a sus vecinos inmediatos en la jerarquía (core → agregación →",
        "  acceso), no a todos los demás. Una red completa tendría",
        f"  densidad 1.0 y requeriría {n*(n-1)//2} aristas.",
        "  El grafo es conexo (1 componente), confirmando que todos los",
        "  campus tienen al menos un camino hacia el resto de la red.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_metricas_basicas.txt")
    return resultado


# ------------------------------------------------------------
# Ítem 2 · Distribución de grado
# ------------------------------------------------------------

def distribucion_grado(G: nx.Graph) -> dict:
    """
    Calcula la distribución de grado y genera el histograma más el
    gráfico log-log para discutir si la red tiene cola pesada.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca.

    Salida:
        dict: {
            'grados'     (list[int])  : lista de grados de todos los nodos,
            'grado_medio'(float)      : grado medio <k>,
            'grado_max'  (int)        : grado máximo,
            'grado_min'  (int)        : grado mínimo,
            'conteo'     (dict)       : {grado: frecuencia},
        }
    """
    grados = [d for _, d in G.degree()]
    conteo = collections.Counter(grados)

    resultado = {
        "grados"      : grados,
        "grado_medio" : float(np.mean(grados)),
        "grado_max"   : max(grados),
        "grado_min"   : min(grados),
        "conteo"      : dict(conteo),
    }

    # --- Figura: barras discretas (izq) + log-log (der) ---
    ks      = sorted(conteo.keys())
    freqs   = [conteo[k] for k in ks]
    pk      = [conteo[k] / len(grados) for k in ks]
    n_total = len(grados)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "P1 · Distribución de grado — Red UCuenca",
        fontsize=13, fontweight="bold"
    )

    # ── Panel izquierdo: barras discretas, una por cada grado k ──────────
    ax = axes[0]
    bars = ax.bar(
        ks, freqs,
        color="#2980b9", edgecolor="white", linewidth=0.7, width=0.7
    )
    # Etiqueta encima de cada barra con el conteo exacto
    for bar, freq in zip(bars, freqs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            str(freq),
            ha="center", va="bottom", fontsize=7.5, fontweight="bold",
            color="#1a252f"
        )
    # Línea de grado medio
    ax.axvline(resultado["grado_medio"], color="#e74c3c", linestyle="--",
               linewidth=1.8, label=f"$\\langle k \\rangle = {resultado['grado_medio']:.2f}$")
    # Eje X con ticks solo en los grados que existen
    ax.set_xticks(ks)
    ax.set_xticklabels([str(k) for k in ks], fontsize=8)
    ax.set_xlabel("Grado $k$", fontsize=11)
    ax.set_ylabel("Número de nodos", fontsize=11)
    ax.set_title("Frecuencia por grado (discreta)", fontsize=11)
    ax.legend(fontsize=10)
    ax.set_ylim(0, max(freqs) * 1.15)
    ax.grid(axis="y", alpha=0.35)

    # ── Panel derecho: P(k) en escala log-log con etiquetas (k, P(k)) ───
    ax = axes[1]
    ax.scatter(ks, pk, color="#2980b9", s=55, zorder=3, label="$P(k)$ observada")

    # Etiquetar cada punto con su valor de k y P(k)
    for k, p in zip(ks, pk):
        ax.annotate(
            f"k={k}\n({conteo[k]}n)",
            xy=(k, p),
            xytext=(5, 3), textcoords="offset points",
            fontsize=6.5, color="#1a252f",
            arrowprops=dict(arrowstyle="-", color="gray", lw=0.5)
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    # Ticks manuales en los k reales para claridad
    ax.set_xticks(ks)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_xlabel("Grado $k$ (escala log)", fontsize=11)
    ax.set_ylabel("$P(k)$ (escala log)", fontsize=11)
    ax.set_title("Distribución log-log", fontsize=11)
    ax.grid(True, which="both", alpha=0.3)
    ax.text(
        0.97, 0.97,
        f"$k_{{\\min}}={resultado['grado_min']}$  "
        f"$k_{{\\max}}={resultado['grado_max']}$\n"
        f"$\\langle k \\rangle={resultado['grado_medio']:.2f}$  "
        f"$n={n_total}$",
        transform=ax.transAxes, fontsize=8.5,
        ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fef9e7", alpha=0.9)
    )
    ax.legend(fontsize=10)

    fig.tight_layout()
    _guardar_figura(fig, "p1_distribucion_grado.png")

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 2 · DISTRIBUCIÓN DE GRADO",
        "=" * 60,
        f"  Grado medio <k>  : {resultado['grado_medio']:.4f}",
        f"  Grado máximo     : {resultado['grado_max']}",
        f"  Grado mínimo     : {resultado['grado_min']}",
        "",
        "  Frecuencias por grado:",
    ]
    for k in sorted(conteo):
        lineas.append(f"    k={k:2d} → {conteo[k]:3d} nodos")
    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "  La distribución muestra una cola derecha: unos pocos nodos",
        "  (switches de core y agregación) concentran la mayoría de",
        "  conexiones. Sin embargo, con solo 177 nodos, el rango de",
        "  grados (1–" + str(resultado['grado_max']) + ") es insuficiente",
        "  para ajustar una ley de potencia P(k) ~ k^{-γ} con rigor.",
        "  Un test Kolmogorov-Smirnov o powerlaw (Clauset et al. 2009)",
        "  sería necesario antes de proclamar 'red libre de escala'.",
        "  Lo que sí se observa: nodos de grado 1 (hojas de acceso) son",
        "  la mayoría, y el nodo de mayor grado es un switch de core.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_distribucion_grado.txt")
    return resultado


# ------------------------------------------------------------
# Ítem 2b · MLE — Ley de potencia (Clauset, Shalizi & Newman 2009)
# ------------------------------------------------------------

def _muestrear_powerlaw_discreta(gamma: float, kmin: int, n: int,
                                  rng: np.random.Generator) -> np.ndarray:
    """
    Genera n muestras de una ley de potencia discreta P(k) ∝ k^{-γ} para
    k ≥ kmin, por muestreo por inversión de la CDF (Clauset et al. 2009,
    Apéndice D): aproxima la ley de potencia continua y redondea, método
    estándar y suficientemente preciso para el test de bootstrap.

    Argumentos:
        gamma (float)              : exponente de la ley de potencia.
        kmin  (int)                : valor mínimo de la cola.
        n     (int)                : número de muestras a generar.
        rng   (np.random.Generator): generador aleatorio.

    Salida:
        np.ndarray de enteros ≥ kmin.
    """
    u = rng.uniform(0, 1, size=n)
    # Inversión de la CDF de la ley de potencia continua equivalente,
    # luego redondeo al entero más cercano (Clauset et al. 2009, D.6).
    muestras = (kmin - 0.5) * (1 - u) ** (-1.0 / (gamma - 1.0)) + 0.5
    return np.round(muestras).astype(int)


def _bootstrap_pvalue_powerlaw(grados: np.ndarray, kmin_opt: int,
                                gamma_mle: float, ks_observado: float,
                                n_boot: int = 1000, semilla: int = 42) -> float:
    """
    p-value por bootstrap del ajuste de ley de potencia (Clauset, Shalizi
    & Newman 2009, sección 4). Genera n_boot redes sintéticas: cada una
    reemplaza la cola observada (k ≥ kmin_opt) por muestras sintéticas de
    una ley de potencia con el γ estimado, conservando el resto de la
    distribución empírica por debajo de kmin_opt. Para cada sintética se
    re-ajusta γ y k_min por MLE/KS (igual que sobre los datos reales) y se
    calcula su propio KS. El p-value es la fracción de sintéticas cuyo KS
    iguala o supera el KS observado.

    p > 0.1 → la ley de potencia es un modelo estadísticamente plausible.
    p ≤ 0.1 → se rechaza la ley de potencia como generador de estos datos.

    Argumentos:
        grados       (np.ndarray): grados de todos los nodos (muestra real).
        kmin_opt     (int)       : k_min óptimo estimado sobre los datos reales.
        gamma_mle    (float)     : γ MLE estimado sobre los datos reales.
        ks_observado (float)     : estadístico KS del ajuste real.
        n_boot       (int)       : número de redes sintéticas a generar.
        semilla      (int)       : semilla del generador aleatorio.

    Salida:
        float: p-value ∈ [0, 1].
    """
    rng = np.random.default_rng(semilla)
    n_total = len(grados)
    cuerpo = grados[grados < kmin_opt]  # se conserva tal cual (no es la cola)
    n_cola = int(np.sum(grados >= kmin_opt))

    ks_sinteticos = []
    for _ in range(n_boot):
        cola_sint = _muestrear_powerlaw_discreta(gamma_mle, kmin_opt, n_cola, rng)
        cola_sint = np.clip(cola_sint, kmin_opt, None)  # por seguridad numérica
        muestra_sint = np.concatenate([cuerpo, cola_sint])

        # Reajuste MLE/KS sobre la muestra sintética, igual que sobre los
        # datos reales: se busca su propio k_min óptimo, no se reutiliza
        # kmin_opt de los datos reales (así el test es honesto).
        k_vals_s = np.sort(np.unique(muestra_sint.astype(int)))
        mejor_ks_s = None
        for kmin_s in k_vals_s[:-1] if len(k_vals_s) > 1 else []:
            tail_s = muestra_sint[muestra_sint >= kmin_s]
            n_t_s = len(tail_s)
            if n_t_s < 5:
                break
            try:
                gamma_s = 1.0 + n_t_s * (np.sum(np.log(tail_s / (kmin_s - 0.5)))) ** -1
                k_sorted_s = np.sort(np.unique(tail_s.astype(int)))
                cdf_emp_s = np.array([np.sum(tail_s >= k) / n_t_s for k in k_sorted_s])
                z_kmin_s = hurwitz_zeta(gamma_s, float(kmin_s))
                if z_kmin_s <= 0 or not np.isfinite(z_kmin_s):
                    continue
                cdf_teo_s = np.array([hurwitz_zeta(gamma_s, float(k)) / z_kmin_s
                                       for k in k_sorted_s])
                ks_s = np.max(np.abs(cdf_emp_s - cdf_teo_s))
                if mejor_ks_s is None or ks_s < mejor_ks_s:
                    mejor_ks_s = ks_s
            except Exception:
                continue
        if mejor_ks_s is not None:
            ks_sinteticos.append(mejor_ks_s)

    if not ks_sinteticos:
        return float("nan")
    ks_sinteticos = np.array(ks_sinteticos)
    return float(np.mean(ks_sinteticos >= ks_observado))


def mle_ley_potencia(G: nx.Graph) -> dict:
    """
    Análisis de Máxima Verosimilitud (MLE) para distribución de ley de
    potencia discreta, siguiendo Clauset, Shalizi & Newman (2009).

    Para cada k_min candidato (desde k_min=1 hasta k_max-1):
      1. Filtra los grados k_i >= k_min.
      2. Estima el exponente MLE:
             γ = 1 + n · [Σ ln(k_i / (k_min − 0.5))]^{-1}
      3. Calcula el estadístico KS entre la CDF empírica y la CDF teórica
         P(K ≥ k) = ζ(γ, k) / ζ(γ, k_min)  (ζ = Hurwitz zeta).
    El k_min óptimo es el que minimiza el KS.

    Genera `p1_mle_ley_potencia.png` con:
      - Panel principal (log-log): P(k) empírica + curvas γ ∈ {1.5, 2.0,
        2.5, 3.0, 3.5} y el ajuste MLE óptimo.
      - Panel secundario: KS vs k_min con marcador en el óptimo.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca.

    Salida:
        dict con claves:
            'gamma_mle' (float) : exponente MLE óptimo.
            'kmin_opt'  (int)   : k_min que minimiza el KS.
            'ks_stat'   (float) : estadístico KS del ajuste óptimo.
            'n_tail'    (int)   : número de nodos con k >= k_min óptimo.
            'log_ratio' (float) : log-verosimilitud power law vs exponencial
                                  (>0 favorece power law).
    """
    grados = np.array([d for _, d in G.degree()], dtype=float)
    k_vals = np.sort(np.unique(grados.astype(int)))
    k_max  = int(grados.max())

    # ---- Distribución empírica P(k) ----
    conteo = collections.Counter(grados.astype(int))
    n_total = len(grados)
    pk_emp  = {k: conteo[k] / n_total for k in k_vals}

    # ---- Barrido k_min para encontrar el óptimo KS ----
    candidatos = [k for k in k_vals if k < k_max]
    resultados_ks = []

    for kmin in candidatos:
        tail = grados[grados >= kmin]
        n_t  = len(tail)
        if n_t < 5:
            break
        # MLE discreta (Clauset 2009 ec. B.17)
        gamma_est = 1.0 + n_t * (np.sum(np.log(tail / (kmin - 0.5)))) ** -1

        # CDF empírica de la cola
        k_sorted = np.sort(np.unique(tail.astype(int)))
        cdf_emp  = np.array([np.sum(tail >= k) / n_t for k in k_sorted])

        # CDF teórica con Hurwitz zeta
        try:
            z_kmin = hurwitz_zeta(gamma_est, float(kmin))
            if z_kmin <= 0 or not np.isfinite(z_kmin):
                continue
            cdf_teo = np.array([hurwitz_zeta(gamma_est, float(k)) / z_kmin
                                 for k in k_sorted])
        except Exception:
            continue

        ks = np.max(np.abs(cdf_emp - cdf_teo))
        resultados_ks.append((kmin, gamma_est, ks, n_t))

    if not resultados_ks:
        return {}

    # k_min óptimo = menor KS
    kmin_opt, gamma_mle, ks_opt, n_tail = min(resultados_ks, key=lambda x: x[2])

    # ---- p-value por bootstrap (Clauset, Shalizi & Newman 2009, sec. 4) ----
    # El KS mínimo por sí solo no dice si el ajuste es *plausible*, solo cuál
    # candidato es *menos malo*. El test correcto: generar muchas muestras
    # sintéticas de una ley de potencia discreta con el γ y k_min estimados
    # (mismo tamaño de cola que la muestra real), reajustar γ y k_min sobre
    # cada una y calcular su propio KS. Si la fracción de muestras con KS
    # sintético ≥ KS observado es baja (p < 0.1), la ley de potencia se
    # rechaza como modelo generador de los datos reales.
    p_value_bootstrap = _bootstrap_pvalue_powerlaw(
        grados, kmin_opt, gamma_mle, ks_opt, n_boot=1000, semilla=42
    )

    # ---- Log-verosimilitud power law vs exponencial ----
    tail_opt = grados[grados >= kmin_opt]
    # Log-verosim. power law
    z_kmin_opt = hurwitz_zeta(gamma_mle, float(kmin_opt))
    ll_pl = (-gamma_mle * np.sum(np.log(tail_opt))
             - len(tail_opt) * np.log(z_kmin_opt))
    # Log-verosim. exponencial p(k) = (1−e^{-λ})·e^{−λ(k−k_min)} con MLE λ
    lambda_exp = 1.0 / (np.mean(tail_opt) - kmin_opt + 0.5)
    ll_exp = (len(tail_opt) * np.log(1 - np.exp(-lambda_exp))
              - lambda_exp * np.sum(tail_opt - kmin_opt))
    log_ratio = ll_pl - ll_exp

    # ---- Figura comparativa ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "P1 · MLE Ley de Potencia vs Distribución Empírica — Red UCuenca",
        fontsize=12, fontweight="bold"
    )

    # Panel 1: P(k) empírico vs curvas γ
    k_cont = np.arange(1, k_max + 1, dtype=float)
    colores_curvas = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db"]
    gammas_test    = [1.5, 2.0, 2.5, 3.0, 3.5]

    for gamma_t, col in zip(gammas_test, colores_curvas):
        try:
            z0 = hurwitz_zeta(gamma_t, 1.0)
            pk_teo = k_cont ** (-gamma_t) / z0
            ax1.plot(k_cont, pk_teo, "-", color=col, alpha=0.7, linewidth=1.4,
                     label=f"γ = {gamma_t}")
        except Exception:
            pass

    # Ajuste MLE óptimo (sobre la cola completa desde k=1 para visualización)
    try:
        z0_mle = hurwitz_zeta(gamma_mle, 1.0)
        pk_mle = k_cont ** (-gamma_mle) / z0_mle
        ax1.plot(k_cont, pk_mle, "k--", linewidth=2.2,
                 label=f"MLE γ={gamma_mle:.3f} (k_min={kmin_opt})")
    except Exception:
        pass

    # Datos empíricos
    k_emp_arr = np.array(list(pk_emp.keys()))
    p_emp_arr = np.array(list(pk_emp.values()))
    ax1.scatter(k_emp_arr, p_emp_arr, color="#1a4a7a", s=55, zorder=5,
                label="P(k) empírica", edgecolors="white", linewidths=0.5)

    ax1.set_xscale("log"); ax1.set_yscale("log")
    ax1.set_xlabel("Grado k", fontsize=11)
    ax1.set_ylabel("P(k)", fontsize=11)
    ax1.set_title("Comparación: datos reales vs curvas de ley de potencia", fontsize=10)
    ax1.legend(fontsize=8.5, loc="upper right")
    ax1.grid(True, which="both", linestyle="--", alpha=0.35)

    # Panel 2: KS vs k_min
    kmins_arr  = np.array([r[0] for r in resultados_ks])
    ks_arr     = np.array([r[2] for r in resultados_ks])
    gammas_arr = np.array([r[1] for r in resultados_ks])

    ax2_twin = ax2.twinx()
    ax2.plot(kmins_arr, ks_arr, "o-", color="#2980b9", linewidth=1.5,
             markersize=5, label="KS (eje izq.)")
    ax2_twin.plot(kmins_arr, gammas_arr, "s--", color="#e74c3c", linewidth=1.2,
                  markersize=4, alpha=0.7, label="γ MLE (eje der.)")
    ax2.axvline(kmin_opt, color="#1a4a7a", linestyle=":", linewidth=1.8,
                label=f"k_min óptimo = {kmin_opt}")
    ax2.scatter([kmin_opt], [ks_opt], color="gold", s=90, zorder=6,
                edgecolors="#1a4a7a", linewidths=1.2)

    ax2.set_xlabel("k_min candidato", fontsize=11)
    ax2.set_ylabel("Estadístico KS", fontsize=11, color="#2980b9")
    ax2_twin.set_ylabel("Exponente γ estimado", fontsize=11, color="#e74c3c")
    ax2.set_title("Selección de k_min y γ por mínimo KS", fontsize=10)

    lines1, labs1 = ax2.get_legend_handles_labels()
    lines2, labs2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labs1 + labs2, fontsize=8.5, loc="upper right")
    ax2.grid(True, linestyle="--", alpha=0.35)

    fig.tight_layout()
    _guardar_figura(fig, "p1_mle_ley_potencia.png")

    # ---- Texto reporte ----
    if np.isnan(p_value_bootstrap):
        veredicto_p = "no calculable (bootstrap sin muestras válidas)"
    elif p_value_bootstrap > 0.1:
        veredicto_p = f"p={p_value_bootstrap:.3f} > 0.1 → ley de potencia PLAUSIBLE como modelo"
    else:
        veredicto_p = f"p={p_value_bootstrap:.3f} ≤ 0.1 → ley de potencia SE RECHAZA como modelo"

    lineas = [
        "=" * 60,
        "ÍTEM 2b · MLE — LEY DE POTENCIA (Clauset et al. 2009)",
        "=" * 60,
        f"  k_min óptimo     : {kmin_opt}",
        f"  γ MLE            : {gamma_mle:.4f}",
        f"  Estadístico KS   : {ks_opt:.4f}",
        f"  Nodos en la cola : {n_tail} / {n_total}",
        f"  p-value bootstrap: {p_value_bootstrap:.4f}  (1000 redes sintéticas, Clauset et al. 2009 §4)",
        f"  log R (PL vs Exp): {log_ratio:.4f}  "
        + ("(favorece PL)" if log_ratio > 0 else "(favorece Exponencial)"),
        "",
        "  INTERPRETACIÓN:",
        f"  Con k_min={kmin_opt} y γ={gamma_mle:.3f} el KS mínimo es {ks_opt:.4f}.",
        "  El KS mínimo por sí solo solo dice cuál candidato ajusta MEJOR,",
        "  no si el ajuste es en sí mismo plausible. El p-value bootstrap",
        "  responde eso: es la fracción de redes sintéticas generadas con",
        "  el γ estimado cuyo propio KS iguala o supera al observado.",
        f"  Resultado: {veredicto_p}.",
        "",
        "  Los dos criterios dan lecturas distintas y hay que ser honestos",
        "  con eso: el p-value bootstrap NO rechaza la ley de potencia como",
        "  forma funcional para la cola (k≥kmin), pero log R favorece",
        "  (débilmente) la exponencial como alternativa, y la cola tiene",
        "  solo n_tail nodos — muy poco para que cualquiera de los dos",
        "  tests tenga poder estadístico real. Con este tamaño de cola NO",
        "  se puede afirmar con rigor que la red sea scale-free, pero",
        "  tampoco descartarlo solo con log R: el resultado correcto es",
        "  'no hay evidencia suficiente para decidir', no 'no es scale-free'.",
        "  Lo que sí sostiene la evidencia estructural (P1 ítem 4): la",
        "  asortatividad negativa y el clustering bajo son la firma de una",
        "  red jerárquica, independientemente de si su cola de grado ajusta",
        "  o no a una ley de potencia pura.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_mle_ley_potencia.txt")

    return {
        "gamma_mle" : round(gamma_mle, 4),
        "kmin_opt"  : kmin_opt,
        "ks_stat"   : round(ks_opt, 4),
        "n_tail"    : n_tail,
        "log_ratio" : round(log_ratio, 4),
        "p_value"   : round(p_value_bootstrap, 4) if not np.isnan(p_value_bootstrap) else None,
    }


# ------------------------------------------------------------
# Ítem 3 · Centralidades
# ------------------------------------------------------------

def centralidades(G: nx.Graph) -> pd.DataFrame:
    """
    Calcula las cuatro centralidades principales y devuelve una tabla
    con el top-10 de cada una, alineadas en columnas comparativas.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca.

    Salida:
        pd.DataFrame: tabla con columnas
            ['rank', 'nodo_grado', 'grado', 'nodo_between', 'betweenness',
             'nodo_close', 'closeness', 'nodo_eigen', 'eigenvector']
    """
    # Cálculo de las cuatro centralidades
    c_grado     = nx.degree_centrality(G)
    c_between   = nx.betweenness_centrality(G, normalized=True)
    c_close     = nx.closeness_centrality(G)
    c_eigen     = nx.eigenvector_centrality(G, max_iter=1000)

    top_n = 10

    def _top(d: dict, n: int = top_n) -> list:
        return sorted(d.items(), key=lambda x: -x[1])[:n]

    top_g = _top(c_grado)
    top_b = _top(c_between)
    top_c = _top(c_close)
    top_e = _top(c_eigen)

    # Tabla comparativa
    filas = []
    for i in range(top_n):
        filas.append({
            "rank"         : i + 1,
            "nodo_grado"   : top_g[i][0],
            "grado"        : round(top_g[i][1], 4),
            "nodo_between" : top_b[i][0],
            "betweenness"  : round(top_b[i][1], 4),
            "nodo_close"   : top_c[i][0],
            "closeness"    : round(top_c[i][1], 4),
            "nodo_eigen"   : top_e[i][0],
            "eigenvector"  : round(top_e[i][1], 4),
        })
    df = pd.DataFrame(filas)
    _guardar_csv(df, "p1_centralidades_top10.csv")

    # --- Figura: gráfico de barras horizontal por centralidad ---
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "P1 · Top-10 nodos por centralidad — Red UCuenca",
        fontsize=13, fontweight="bold"
    )

    configs = [
        (axes[0, 0], top_g, "Centralidad de Grado",           "#2980b9"),
        (axes[0, 1], top_b, "Centralidad de Intermediación",   "#e67e22"),
        (axes[1, 0], top_c, "Centralidad de Cercanía",         "#27ae60"),
        (axes[1, 1], top_e, "Centralidad de Vector Propio",    "#8e44ad"),
    ]

    for ax, top, titulo, color in configs:
        nodos  = [t[0] for t in reversed(top)]
        valores = [t[1] for t in reversed(top)]
        # Nombres cortos para legibilidad
        nodos_cortos = [n[-14:] if len(n) > 14 else n for n in nodos]
        bars = ax.barh(nodos_cortos, valores, color=color, alpha=0.85,
                       edgecolor="white", linewidth=0.5)
        ax.set_title(titulo, fontsize=11, fontweight="bold")
        ax.set_xlabel("Valor normalizado", fontsize=9)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", alpha=0.3)
        # Etiqueta de valor al final de cada barra
        for bar, val in zip(bars, valores):
            ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", fontsize=7.5)

    fig.tight_layout()
    _guardar_figura(fig, "p1_centralidades_top10.png")

    # --- Texto de reporte ---
    print("\n" + "=" * 60)
    print("ÍTEM 3 · CENTRALIDADES — TOP-10 COMPARATIVO")
    print("=" * 60)
    print(df.to_string(index=False))
    print()
    print("  INTERPRETACIÓN:")
    print("  Los nodos de mayor grado suelen ser switches de core o")
    print("  agregación. La intermediación (betweenness) identifica los")
    print("  cuellos de botella del enrutamiento: si un nodo con alta")
    print("  intermediación falla, muchos caminos quedan interrumpidos.")
    print("  La cercanía (closeness) señala qué nodo puede alcanzar")
    print("  cualquier otro en menos saltos: útil para ubicar servicios")
    print("  centralizados (DNS, NTP). El vector propio pondera la")
    print("  calidad de los vecinos: un nodo de acceso conectado a un")
    print("  core potente tiene alta centralidad de vector propio.")
    print("=" * 60)
    return df


# ------------------------------------------------------------
# Ítem 4 · Clustering, diámetro, distancia media y asortatividad
# ------------------------------------------------------------

def metricas_cohesion(G: nx.Graph) -> dict:
    """
    Calcula el coeficiente de clustering medio, el diámetro, la
    distancia media entre pares y la asortatividad por grado.

    Argumentos:
        G (nx.Graph): grafo de la red UCuenca (debe ser conexo).

    Salida:
        dict: {
            'clustering_medio' (float): coeficiente de clustering promedio,
            'diametro'         (int)  : máxima distancia más corta,
            'distancia_media'  (float): promedio de todas las distancias,
            'asortatividad'    (float): correlación de Pearson de grados,
        }
    """
    resultado = {
        "clustering_medio" : nx.average_clustering(G),
        "diametro"         : nx.diameter(G),
        "distancia_media"  : nx.average_shortest_path_length(G),
        "asortatividad"    : nx.degree_assortativity_coefficient(G),
    }

    lineas = [
        "=" * 60,
        "ÍTEM 4 · CLUSTERING, DIÁMETRO, DISTANCIA MEDIA Y ASORTATIVIDAD",
        "=" * 60,
        f"  Clustering medio <C>          : {resultado['clustering_medio']:.6f}",
        f"  Diámetro                      : {resultado['diametro']}",
        f"  Distancia media               : {resultado['distancia_media']:.4f}",
        f"  Asortatividad por grado (r)   : {resultado['asortatividad']:.4f}",
        "",
        "  INTERPRETACIÓN:",
        "  El clustering medio es muy bajo: en una red jerárquica los",
        "  equipos de acceso se conectan solo hacia arriba (a su switch",
        "  de agregación), no entre sí, por lo que hay muy pocos",
        "  triángulos. Las redes sociales, en cambio, tienen clustering",
        "  alto porque 'los amigos de mis amigos son mis amigos'.",
        "",
        "  La asortatividad negativa es la firma de una red jerárquica:",
        "  los nodos de alto grado (core) se conectan con nodos de bajo",
        "  grado (acceso), no entre sí. Esto implica que los hubs son",
        "  resistentes a fallos aleatorios pero vulnerables si se ataca",
        "  específicamente un switch de core o agregación.",
        "",
        "  El diámetro y la distancia media son relativamente bajos",
        "  gracias a la jerarquía: cualquier equipo llega a cualquier",
        "  otro en pocos saltos atravesando la cadena acceso→agg→core.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_cohesion.txt")
    return resultado


# ------------------------------------------------------------
# Ítem 5 · Puntos de articulación y puentes
# ------------------------------------------------------------

def articulacion_y_puentes(G: nx.Graph, nodos_df: pd.DataFrame,
                            aristas_df: pd.DataFrame) -> dict:
    """
    Identifica los puntos de articulación (nodos cuya eliminación
    desconecta el grafo) y los puentes (aristas equivalentes), y
    los contabiliza por campus y por capa.

    Argumentos:
        G         (nx.Graph)    : grafo de la red UCuenca.
        nodos_df  (pd.DataFrame): tabla de nodos con columnas id, campus, capa.
        aristas_df(pd.DataFrame): tabla de aristas con columnas source, target.

    Salida:
        dict: {
            'articulacion'       (list[str])          : nodos de articulación,
            'puentes'            (list[tuple])         : aristas puente (u, v),
            'art_por_campus'     (pd.DataFrame)        : conteo por campus,
            'art_por_capa'       (pd.DataFrame)        : conteo por capa,
            'puentes_por_campus' (pd.DataFrame)        : conteo puentes por campus,
        }
    """
    # Puntos de articulación
    art_set = set(nx.articulation_points(G))
    art_lista = sorted(art_set)

    # Puentes
    puentes = list(nx.bridges(G))

    # Mapa nodo → campus/capa
    nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))
    nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))

    # Conteo de articulación por campus y capa
    campus_art = collections.Counter(nodo_campus.get(n, "?") for n in art_lista)
    capa_art   = collections.Counter(nodo_capa.get(n, "?")   for n in art_lista)

    df_art_campus = pd.DataFrame(
        sorted(campus_art.items(), key=lambda x: -x[1]),
        columns=["campus", "puntos_articulacion"]
    )
    df_art_capa = pd.DataFrame(
        sorted(capa_art.items(), key=lambda x: -x[1]),
        columns=["capa", "puntos_articulacion"]
    )

    # Puentes: asignar a campus y capa del nodo de menor capa jerárquica
    jerarquia = {"core": 0, "wan": 1, "interconexion": 1,
                 "agregacion": 2, "acceso": 3}
    campus_puentes = []
    capa_puentes   = []
    for u, v in puentes:
        j_u = jerarquia.get(nodo_capa.get(u, "acceso"), 3)
        j_v = jerarquia.get(nodo_capa.get(v, "acceso"), 3)
        nodo_ref = u if j_u <= j_v else v
        campus_puentes.append(nodo_campus.get(nodo_ref, "?"))
        capa_puentes.append(nodo_capa.get(nodo_ref, "?"))

    df_puentes_campus = pd.DataFrame(
        sorted(collections.Counter(campus_puentes).items(), key=lambda x: -x[1]),
        columns=["campus", "puentes"]
    )
    df_puentes_capa = pd.DataFrame(
        sorted(collections.Counter(capa_puentes).items(), key=lambda x: -x[1]),
        columns=["capa", "puentes"]
    )

    _guardar_csv(df_art_campus,    "p1_articulacion_campus.csv")
    _guardar_csv(df_art_capa,      "p1_articulacion_capa.csv")
    _guardar_csv(df_puentes_campus,"p1_puentes_campus.csv")
    _guardar_csv(df_puentes_capa,  "p1_puentes_capa.csv")

    # --- Figura: 2×2 — articulaciones y puentes por capa y campus ---
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(
        "P1 · Puntos de articulación y puentes — Red UCuenca",
        fontsize=13, fontweight="bold"
    )

    def _barh_labeled(ax, etiquetas, valores, color, titulo, xlabel):
        """Dibuja barras horizontales con etiqueta de valor al final."""
        bars = ax.barh(etiquetas, valores, color=color,
                       edgecolor="white", linewidth=0.6)
        x_max = max(valores) if len(valores) else 1
        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_width() + x_max * 0.02,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center", ha="left",
                fontsize=9, fontweight="bold", color="#333333"
            )
        ax.set_xlim(0, x_max * 1.18)
        ax.set_title(titulo, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=9)
        ax.grid(axis="x", alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)

    # Subgráfico 1 (arriba-izq): articulaciones por capa
    df_ac = df_art_capa.sort_values("puntos_articulacion")
    _barh_labeled(
        axes[0, 0],
        df_ac["capa"].tolist(),
        df_ac["puntos_articulacion"].tolist(),
        "#e74c3c",
        f"Puntos de articulación por capa (total: {len(art_lista)})",
        "Cantidad"
    )

    # Subgráfico 2 (arriba-der): articulaciones por campus
    df_acamp = df_art_campus.sort_values("puntos_articulacion")
    _barh_labeled(
        axes[0, 1],
        df_acamp["campus"].tolist(),
        df_acamp["puntos_articulacion"].tolist(),
        "#c0392b",
        f"Puntos de articulación por campus (total: {len(art_lista)})",
        "Cantidad"
    )

    # Subgráfico 3 (abajo-izq): puentes por capa
    df_pc = df_puentes_capa.sort_values("puentes")
    _barh_labeled(
        axes[1, 0],
        df_pc["capa"].tolist(),
        df_pc["puentes"].tolist(),
        "#e67e22",
        f"Puentes por capa (total: {len(puentes)})",
        "Cantidad"
    )

    # Subgráfico 4 (abajo-der): puentes por campus
    df_pcamp = df_puentes_campus.sort_values("puentes")
    _barh_labeled(
        axes[1, 1],
        df_pcamp["campus"].tolist(),
        df_pcamp["puentes"].tolist(),
        "#d35400",
        f"Puentes por campus (total: {len(puentes)})",
        "Cantidad"
    )

    fig.tight_layout()
    _guardar_figura(fig, "p1_articulacion_puentes.png")

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 5 · PUNTOS DE ARTICULACIÓN Y PUENTES",
        "=" * 60,
        f"  Total puntos de articulación  : {len(art_lista)}",
        f"  Total puentes                 : {len(puentes)}",
        "",
        "  Articulaciones por campus:",
    ]
    for _, fila in df_art_campus.iterrows():
        lineas.append(f"    {fila['campus']:<42} {fila['puntos_articulacion']:>4}")
    lineas += ["", "  Articulaciones por capa:"]
    for _, fila in df_art_capa.iterrows():
        lineas.append(f"    {fila['capa']:<20} {fila['puntos_articulacion']:>4}")
    lineas += ["", "  Puentes por campus:"]
    for _, fila in df_puentes_campus.iterrows():
        lineas.append(f"    {fila['campus']:<42} {fila['puentes']:>4}")
    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "  Un punto de articulación es un nodo cuya falla desconecta",
        "  al menos a un subconjunto de la red. En una jerarquía sin",
        "  redundancia (un solo switch de agregación por edificio) ese",
        "  switch ES un punto de articulación. Los puentes son la",
        "  versión de arista: un único enlace que, si falla, aísla a",
        "  un segmento. Campus con muchos puentes carecen de caminos",
        "  alternativos y son más vulnerables a fallos de enlace.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_articulacion_puentes.txt")

    return {
        "articulacion"       : art_lista,
        "puentes"            : puentes,
        "art_por_campus"     : df_art_campus,
        "art_por_capa"       : df_art_capa,
        "puentes_por_campus" : df_puentes_campus,
    }


# ------------------------------------------------------------
# Ítem 6 · Contraste con el informe técnico (redundancia)
# ------------------------------------------------------------

def contraste_redundancia(G: nx.Graph, nodos_df: pd.DataFrame) -> dict:
    """
    Verifica empíricamente si cada campus tiene redundancia
    core–agregación usando el atributo capa del grafo.

    La redundancia core–agregación existe cuando un switch de
    agregación está conectado a MÁS DE UN switch de core del
    mismo campus. Si todos los switches de agregación de un campus
    solo tienen un vecino de capa core, el campus NO tiene
    redundancia de núcleo — contradiga o confirme lo que afirma
    el informe técnico.

    Argumentos:
        G        (nx.Graph)    : grafo de la red UCuenca.
        nodos_df (pd.DataFrame): tabla con columnas id, campus, capa.

    Salida:
        dict: {campus: {'agg_nodes': list, 'con_redundancia': int,
                        'sin_redundancia': int, 'tiene_redundancia': bool}}
    """
    # Mapas de apoyo
    nodo_campus = dict(zip(nodos_df["id"], nodos_df["campus"]))
    nodo_capa   = dict(zip(nodos_df["id"], nodos_df["capa"]))

    # Para cada campus, analizar sus switches de agregación
    campus_unicos = [c for c in nodos_df["campus"].unique()
                     if c != "Nube MPLS"]

    resultado = {}
    for campus in sorted(campus_unicos):
        nodos_agg = [n for n in G.nodes()
                     if nodo_campus.get(n) == campus
                     and nodo_capa.get(n) == "agregacion"]

        con_red = 0
        sin_red = 0
        for agg in nodos_agg:
            vecinos_core = [v for v in G.neighbors(agg)
                            if nodo_capa.get(v) == "core"]
            if len(vecinos_core) > 1:
                con_red += 1
            else:
                sin_red += 1

        resultado[campus] = {
            "agg_nodes"        : nodos_agg,
            "con_redundancia"  : con_red,
            "sin_redundancia"  : sin_red,
            "tiene_redundancia": con_red > 0,
        }

    # --- Texto de reporte ---
    lineas = [
        "=" * 60,
        "ÍTEM 6 · CONTRASTE CON EL INFORME TÉCNICO",
        "         Redundancia core–agregación por campus",
        "=" * 60,
        f"  {'Campus':<42} {'Nodos agg':>9} {'Con red.':>8} {'Sin red.':>8} {'Redundancia':>11}",
        "  " + "-" * 80,
    ]
    for campus, datos in resultado.items():
        n_agg = len(datos["agg_nodes"])
        con   = datos["con_redundancia"]
        sin   = datos["sin_redundancia"]
        tiene = "SÍ ✓" if datos["tiene_redundancia"] else "NO ✗"
        lineas.append(
            f"  {campus:<42} {n_agg:>9} {con:>8} {sin:>8} {tiene:>11}"
        )

    lineas += [
        "",
        "  INTERPRETACIÓN:",
        "  Balzay: el informe afirma redundancia core–agregación. Los",
        "  datos deben confirmarla (switches de agregación conectados a",
        "  DT-0A-C12 Y DT-0A-C13 simultáneamente).",
        "",
        "  Paraíso: el informe también afirma redundancia, pero los",
        "  datos revelan un solo switch de core (CPAR-C10). Los dobles",
        "  enlaces de sus switches de agregación van ambos al MISMO",
        "  core → es agregación de puertos (LAG), no redundancia de",
        "  núcleo. La afirmación del informe es incorrecta.",
        "",
        "  Campus Central: el informe describe enlaces simples agg–core,",
        "  pero los datos muestran que los 13 switches CC-* están",
        "  doblemente conectados a DATCC-2A-C2 y DATCC-2A-C3.",
        "=" * 60,
    ]
    texto = "\n".join(lineas)
    print(texto)
    _guardar_tabla(texto, "p1_redundancia.txt")
    return resultado


# ============================================================
# CÓDIGO MAIN
# ============================================================
# 1) Crear directorios de salida.
# 2) Cargar y verificar el grafo UCuenca.
# 3) Cargar los DataFrames de nodos y aristas para atributos.
# 4) Ejecutar los seis ítems del Problema P1 en orden.

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PROBLEMA P1 — MEDIDAS FUNDAMENTALES")
    print("Red de datos · Universidad de Cuenca")
    print("=" * 60 + "\n")

    # 1) Directorios
    _crear_dirs()

    # 2) Cargar grafo y verificar pipeline
    G = cargar_red(fuente="csv")
    ok = verificar(G)
    if not ok:
        sys.exit("Pipeline fallido: corrija la carga antes de continuar.")

    # 3) Cargar DataFrames de atributos desde los CSV
    import csv as _csv

    def _leer_csv(nombre: str) -> pd.DataFrame:
        ruta = os.path.join(DIR_ROOT, nombre)
        return pd.read_csv(ruta, dtype=str)

    nodos_df   = _leer_csv("red_ucuenca_nodes.csv")
    aristas_df = _leer_csv("red_ucuenca_edges.csv")

    # 4.1) Ítem 1 — Métricas básicas
    print("\n[1/6] Métricas básicas...")
    metricas_basicas(G, nodos_df)

    # 4.2) Ítem 2 — Distribución de grado
    print("\n[2/6] Distribución de grado...")
    distribucion_grado(G)

    # 4.2b) MLE — Ley de potencia
    print("\n[2b] MLE ley de potencia (Clauset et al. 2009)...")
    mle_resultado = mle_ley_potencia(G)
    if mle_resultado:
        print(f"     γ MLE = {mle_resultado['gamma_mle']:.4f}  "
              f"k_min = {mle_resultado['kmin_opt']}  "
              f"KS = {mle_resultado['ks_stat']:.4f}  "
              f"p-value = {mle_resultado['p_value']}")

    # 4.3) Ítem 3 — Centralidades
    print("\n[3/6] Centralidades...")
    centralidades(G)

    # 4.4) Ítem 4 — Clustering, diámetro, distancia media, asortatividad
    print("\n[4/6] Métricas de cohesión...")
    metricas_cohesion(G)

    # 4.5) Ítem 5 — Puntos de articulación y puentes
    print("\n[5/6] Puntos de articulación y puentes...")
    articulacion_y_puentes(G, nodos_df, aristas_df)

    # 4.6) Ítem 6 — Contraste con el informe técnico
    print("\n[6/6] Contraste con el informe técnico...")
    contraste_redundancia(G, nodos_df)

    print("\n" + "=" * 60)
    print("P1 completado. Resultados en:")
    print(f"  Tablas  → {DIR_TAB}")
    print(f"  Imágenes→ {DIR_IMG}")
    print("=" * 60 + "\n")
