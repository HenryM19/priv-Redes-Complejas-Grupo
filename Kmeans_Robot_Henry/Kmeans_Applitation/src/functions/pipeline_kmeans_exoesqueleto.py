from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import webbrowser

from matplotlib.animation import FuncAnimation, PillowWriter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans, kmeans_plusplus
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

try:
    from .decision_matrix import calcular_prevalencia_clusters
except ImportError:
    from decision_matrix import calcular_prevalencia_clusters


DEFAULT_VARIABLES = [
    "tiempo_uso_acumulado_h",
    "ciclos_activacion_M",
    "numero_reparaciones",
    "fallos_temporales",
    "temp_operacional_promedio_C",
    "temp_maxima_alcanzada_C",
    "dias_ultima_calibracion",
    "dias_ultimo_servicio",
    "numero_logs_error",
]

VARIABLE_LABELS = {
    "tiempo_uso_acumulado_h": "tiempo de uso acumulado",
    "ciclos_activacion_M": "ciclos de activacion",
    "numero_reparaciones": "numero de reparaciones",
    "fallos_temporales": "fallos temporales",
    "temp_operacional_promedio_C": "temperatura operacional promedio",
    "temp_maxima_alcanzada_C": "temperatura maxima alcanzada",
    "dias_ultima_calibracion": "dias desde ultima calibracion",
    "dias_ultimo_servicio": "dias desde ultimo servicio",
    "numero_logs_error": "numero de logs de error",
}


# Keep plotting style in one place so the script is easy to tune.
sns.set_theme(style="whitegrid", context="talk")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline completo de K-means + PCA para actuadores de exoesqueleto."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="src/data/exoesqueleto_actuadores.csv",
        help="CSV de entrada con datos crudos.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Carpeta base de salida. Se generan subcarpetas images/ y reports/.",
    )
    parser.add_argument(
        "--k-min",
        type=int,
        default=2,
        help="K minimo para evaluar en metodo del codo.",
    )
    parser.add_argument(
        "--k-max",
        type=int,
        default=9,
        help="K maximo para evaluar en metodo del codo.",
    )
    parser.add_argument(
        "--k-final",
        type=int,
        default=4,
        help="K usado para el modelo final de K-means.",
    )
    parser.add_argument(
        "--id-col",
        type=str,
        default="id_actuador",
        help="Columna identificadora del actuador para graficas de distribucion.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Semilla para reproducibilidad.",
    )
    parser.add_argument(
        "--dataset-origin",
        type=str,
        default="sintetica",
        choices=["real", "sintetica", "mixta", "desconocida"],
        help="Origen de la base de datos para documentacion del reporte.",
    )
    parser.add_argument(
        "--open-centroid-evolution",
        action="store_true",
        help="Abre el GIF de evolucion de centroides al terminar el pipeline.",
    )
    return parser.parse_args()


def validar_columnas(df: pd.DataFrame, columnas: list[str]) -> None:
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


def evaluar_kmeans(
    x_scaled: np.ndarray,
    k_values: list[int],
    random_state: int,
) -> dict[str, list[float]]:
    inertias: list[float] = []
    silhouettes: list[float] = []
    db_scores: list[float] = []

    for k in k_values:
        model = KMeans(n_clusters=k, random_state=random_state, n_init=20)
        labels = model.fit_predict(x_scaled)

        inertias.append(float(model.inertia_))
        silhouettes.append(float(silhouette_score(x_scaled, labels)))
        db_scores.append(float(davies_bouldin_score(x_scaled, labels)))

    return {
        "inertias": inertias,
        "silhouettes": silhouettes,
        "db_scores": db_scores,
    }


def plot_metodo_codo(
    k_values: list[int],
    inertias: list[float],
    silhouettes: list[float],
    db_scores: list[float],
    k_final: int,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(22, 6))

    axes[0].plot(k_values, inertias, marker="o", linewidth=2)
    axes[0].axvline(k_final, color="red", linestyle="--", label=f"K final={k_final}")
    axes[0].set_title("Metodo del Codo (Inercia)")
    axes[0].set_xlabel("K")
    axes[0].set_ylabel("Inercia")
    axes[0].legend()

    axes[1].plot(k_values, silhouettes, marker="o", linewidth=2, color="#2ca02c")
    axes[1].axvline(k_final, color="red", linestyle="--", label=f"K final={k_final}")
    axes[1].set_title("Silhouette Score")
    axes[1].set_xlabel("K")
    axes[1].set_ylabel("Score")
    axes[1].legend()

    axes[2].plot(k_values, db_scores, marker="o", linewidth=2, color="#ff7f0e")
    axes[2].axvline(k_final, color="red", linestyle="--", label=f"K final={k_final}")
    axes[2].set_title("Davies-Bouldin Index")
    axes[2].set_xlabel("K")
    axes[2].set_ylabel("Score")
    axes[2].legend()

    fig.suptitle("Seleccion de numero de clusters", y=1.02, fontsize=16)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _generar_gif_evolucion_k(
    k_values: list[int],
    y_values: list[float],
    title: str,
    y_label: str,
    out_path: Path,
    color: str,
    k_final: int,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    (line,) = ax.plot([], [], marker="o", color=color, linewidth=2)

    ax.set_xlim(min(k_values) - 0.2, max(k_values) + 0.2)
    y_min = min(y_values)
    y_max = max(y_values)
    pad = (y_max - y_min) * 0.15 if y_max > y_min else 1.0
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.set_xlabel("K")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.axvline(k_final, color="red", linestyle="--", label=f"K final={k_final}")
    ax.legend(loc="best")

    def update(frame: int):
        x = k_values[: frame + 1]
        y = y_values[: frame + 1]
        line.set_data(x, y)
        return (line,)

    anim = FuncAnimation(fig, update, frames=len(k_values), interval=700, blit=True)
    anim.save(out_path, writer=PillowWriter(fps=1.2))
    plt.close(fig)


def generar_gifs_seleccion_k(
    k_values: list[int],
    inertias: list[float],
    silhouettes: list[float],
    db_scores: list[float],
    k_final: int,
    images_dir: Path,
) -> None:
    _generar_gif_evolucion_k(
        k_values=k_values,
        y_values=inertias,
        title="Evolucion Metodo del Codo",
        y_label="Inercia",
        out_path=images_dir / "01a_evolucion_codo.gif",
        color="#4c72b0",
        k_final=k_final,
    )
    _generar_gif_evolucion_k(
        k_values=k_values,
        y_values=silhouettes,
        title="Evolucion Silhouette Score",
        y_label="Score",
        out_path=images_dir / "01b_evolucion_silhouette.gif",
        color="#2ca02c",
        k_final=k_final,
    )
    _generar_gif_evolucion_k(
        k_values=k_values,
        y_values=db_scores,
        title="Evolucion Davies-Bouldin",
        y_label="Score",
        out_path=images_dir / "01c_evolucion_davies.gif",
        color="#ff7f0e",
        k_final=k_final,
    )


def calcular_historial_centroides(
    x_scaled: np.ndarray,
    n_clusters: int,
    random_state: int,
    max_iter: int = 30,
    tol: float = 1e-4,
) -> list[np.ndarray]:
    centroids, _ = kmeans_plusplus(
        x_scaled,
        n_clusters=n_clusters,
        random_state=random_state,
    )
    history: list[np.ndarray] = [centroids.copy()]
    rng = np.random.default_rng(random_state)

    for _ in range(max_iter):
        distances = np.linalg.norm(x_scaled[:, None, :] - centroids[None, :, :], axis=2)
        labels = np.argmin(distances, axis=1)

        new_centroids = centroids.copy()
        for k in range(n_clusters):
            points = x_scaled[labels == k]
            if len(points) > 0:
                new_centroids[k] = points.mean(axis=0)
            else:
                new_centroids[k] = x_scaled[rng.integers(0, x_scaled.shape[0])]

        history.append(new_centroids.copy())
        shift = np.linalg.norm(new_centroids - centroids)
        centroids = new_centroids
        if shift < tol:
            break

    return history


def plot_evolucion_centroides_3d(
    pca_3d: np.ndarray,
    labels: np.ndarray,
    centroid_history: list[np.ndarray],
    pca: PCA,
    out_gif: Path,
    out_png: Path,
) -> None:
    history_pca = [pca.transform(c) for c in centroid_history]
    n_clusters = history_pca[0].shape[0]
    colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    def draw_frame(frame: int) -> None:
        ax.clear()
        ax.scatter(
            pca_3d[:, 0],
            pca_3d[:, 1],
            pca_3d[:, 2],
            c=labels,
            cmap="tab10",
            alpha=0.22,
            s=14,
        )

        current = history_pca[frame]
        ax.scatter(
            current[:, 0],
            current[:, 1],
            current[:, 2],
            c=colors,
            marker="X",
            s=260,
            edgecolor="black",
            linewidth=1.0,
        )

        for k in range(n_clusters):
            traj = np.array([history_pca[t][k] for t in range(frame + 1)])
            ax.plot(traj[:, 0], traj[:, 1], traj[:, 2], color=colors[k], linewidth=2)

        ax.set_title(f"Evolucion de centroides en PCA 3D (iteracion {frame})")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_zlabel("PC3")

    def update(frame: int):
        draw_frame(frame)
        return ()

    anim = FuncAnimation(fig, update, frames=len(history_pca), interval=700, blit=False)
    anim.save(out_gif, writer=PillowWriter(fps=1.25))

    draw_frame(len(history_pca) - 1)
    fig.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_pca_3d(pca_3d: np.ndarray, labels: np.ndarray, out_path: Path) -> None:
    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")

    scatter = ax.scatter(
        pca_3d[:, 0],
        pca_3d[:, 1],
        pca_3d[:, 2],
        c=labels,
        cmap="tab10",
        alpha=0.75,
        s=35,
    )

    ax.set_title("K-means en espacio PCA 3D")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("PC3")
    legend = ax.legend(*scatter.legend_elements(), title="Cluster", loc="upper right")
    ax.add_artist(legend)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_estadisticas_clusters(
    cluster_means: pd.DataFrame,
    out_path: Path,
) -> None:
    # Z-score by variable improves visual comparison between clusters.
    means_for_plot = cluster_means.copy()
    means_z = (means_for_plot - means_for_plot.mean()) / means_for_plot.std(ddof=0)

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(
        means_z.T,
        cmap="coolwarm",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Z-score"},
        ax=ax,
    )
    ax.set_title("Perfil de variables por cluster (media estandarizada)")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Variable")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_distribucion_actuadores(
    df: pd.DataFrame,
    id_col: str,
    out_path: Path,
) -> None:
    if id_col not in df.columns:
        return

    conteo = (
        df.groupby([id_col, "cluster"]).size().reset_index(name="conteo")
        .sort_values([id_col, "cluster"])
    )

    fig, ax = plt.subplots(figsize=(14, 7))
    sns.barplot(data=conteo, x=id_col, y="conteo", hue="cluster", palette="tab10", ax=ax)
    ax.set_title("Distribucion de registros por cluster y actuador")
    ax.set_xlabel("Actuador")
    ax.set_ylabel("Cantidad de registros")
    ax.tick_params(axis="x", rotation=20)
    ax.legend(title="Cluster")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_matriz_correlacion(df: pd.DataFrame, variables: list[str], out_path: Path) -> None:
    corr = df[variables].corr(numeric_only=True)

    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        corr,
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        square=True,
        cbar_kws={"label": "Correlacion"},
        ax=ax,
    )
    ax.set_title("Matriz de correlacion")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_varianza_pca(var_exp: np.ndarray, out_path: Path) -> None:
    componentes = np.arange(1, len(var_exp) + 1)
    var_acum = np.cumsum(var_exp)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(componentes, var_exp * 100, alpha=0.8, label="Varianza individual")
    ax.plot(componentes, var_acum * 100, marker="o", linewidth=2, label="Varianza acumulada")

    ax.set_title("Varianza explicada por PCA")
    ax.set_xlabel("Componente principal")
    ax.set_ylabel("Varianza explicada (%)")
    ax.set_xticks(componentes)
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def construir_resumen(
    variables: list[str],
    k_values: list[int],
    evaluacion: dict[str, list[float]],
    k_final: int,
    model: KMeans,
    x_scaled: np.ndarray,
    pca_var: np.ndarray,
    labels: np.ndarray,
) -> dict[str, Any]:
    sil_final = float(silhouette_score(x_scaled, labels))
    db_final = float(davies_bouldin_score(x_scaled, labels))
    ch_final = float(calinski_harabasz_score(x_scaled, labels))

    return {
        "variables": variables,
        "k_values": k_values,
        "inertias": evaluacion["inertias"],
        "silhouettes": evaluacion["silhouettes"],
        "db_scores": evaluacion["db_scores"],
        "k_final": k_final,
        "sil_score": sil_final,
        "db_score": db_final,
        "ch_score": ch_final,
        "inercia": float(model.inertia_),
        "var_exp_pca": [float(v) for v in pca_var],
        "labels": [int(l) for l in labels.tolist()],
    }


def _analizar_casos_mixtos_prevalencia(
    decisiones: dict[str, dict],
    id_col: str,
) -> pd.DataFrame:
    filas: list[dict[str, Any]] = []

    for actuador, info in decisiones.items():
        conteo = info["conteo_clusters"]
        c0 = int(conteo.get(0, 0))
        c1 = int(conteo.get(1, 0))
        c2 = int(conteo.get(2, 0))
        c3 = int(conteo.get(3, 0))
        max_count = max(c0, c1, c2, c3)

        mezcla_opuesta = c1 >= 3 and c3 >= 3
        diferencia_opuesta = abs(c1 - c3)
        empate_fuerte = sum(v == max_count for v in [c0, c1, c2, c3]) > 1

        if mezcla_opuesta and diferencia_opuesta <= 1:
            accion_especial = "Inspeccion diagnostica en 7-14 dias y seguimiento semanal"
            prioridad = "MEDIA-ALTA"
            bandera = "AMBIGUO C1-C3"
        elif mezcla_opuesta:
            accion_especial = "Mantenimiento preventivo anticipado y monitoreo intensivo"
            prioridad = "MEDIA"
            bandera = "MIXTO C1-C3"
        elif empate_fuerte:
            accion_especial = "Revisar tendencia temporal antes de decidir reemplazo"
            prioridad = "MEDIA"
            bandera = "EMPATE"
        else:
            accion_especial = info["accion"]
            prioridad = "NORMAL"
            bandera = "DOMINIO CLARO"

        filas.append(
            {
                id_col: actuador,
                "estado": info["estado"],
                "prevalencia_pct": info["prevalencia_pct"],
                "c0": c0,
                "c1": c1,
                "c2": c2,
                "c3": c3,
                "bandera": bandera,
                "prioridad": prioridad,
                "accion_recomendada": accion_especial,
            }
        )

    out = pd.DataFrame(filas).sort_values(["prioridad", "prevalencia_pct"], ascending=[True, False])
    return out


def _crear_reporte_markdown(
    report_path: Path,
    resumen: dict[str, Any],
    df: pd.DataFrame,
    variables: list[str],
    id_col: str,
    cluster_means: pd.DataFrame,
    decisiones_df: pd.DataFrame,
    decisiones_raw: dict[str, dict],
    dataset_origin: str,
    pca_components: np.ndarray,
    pca_var_exp: np.ndarray,
) -> None:
    n_reg = len(df)
    n_var = len(variables)
    n_act = df[id_col].nunique() if id_col in df.columns else 0

    cluster_share = (df["cluster"].value_counts(normalize=True).sort_index() * 100).round(1)

    top_corr = (
        df[variables]
        .corr(numeric_only=True)
        .where(lambda x: ~np.eye(x.shape[0], dtype=bool))
        .stack()
        .sort_values(key=lambda s: s.abs(), ascending=False)
        .head(5)
    )

    cluster_summary_lines = []
    for c in sorted(cluster_means.index.tolist()):
        p = cluster_share.get(c, 0.0)
        cluster_summary_lines.append(f"- Cluster {c}: {p:.1f}% de registros")

    corr_lines = []
    for (v1, v2), corr in top_corr.items():
        corr_lines.append(f"- {v1} ↔ {v2}: r={corr:.2f}")

    q = df[variables].quantile([0.25, 0.50, 0.75], numeric_only=True)
    p25_fallos = float(q.loc[0.25, "fallos_temporales"])
    p50_fallos = float(q.loc[0.50, "fallos_temporales"])
    p75_fallos = float(q.loc[0.75, "fallos_temporales"])

    decisiones_md = decisiones_df[[
        id_col,
        "estado",
        "prevalencia_pct",
        "bandera",
        "accion_recomendada",
    ]].copy()
    decisiones_md.rename(
        columns={
            id_col: "Actuador",
            "estado": "Estado",
            "prevalencia_pct": "Prevalencia (%)",
            "bandera": "Clasificacion",
            "accion_recomendada": "Accion",
        },
        inplace=True,
    )

    headers = list(decisiones_md.columns)
    header_row = "| " + " | ".join(headers) + " |"
    sep_row = "|" + "|".join(["---" for _ in headers]) + "|"
    body_rows = []
    for _, row in decisiones_md.iterrows():
        body_rows.append("| " + " | ".join([str(row[h]) for h in headers]) + " |")
    decisiones_table = "\n".join([header_row, sep_row, *body_rows])

    head_df = df[[id_col] + variables + ["cluster"]].head(8).copy()
    head_headers = list(head_df.columns)
    head_row = "| " + " | ".join(head_headers) + " |"
    head_sep = "|" + "|".join(["---" for _ in head_headers]) + "|"
    head_body = []
    for _, row in head_df.iterrows():
        head_body.append("| " + " | ".join([str(row[h]) for h in head_headers]) + " |")
    head_table = "\n".join([head_row, head_sep, *head_body])

    z_map = {var: f"z{idx + 1}" for idx, var in enumerate(variables)}
    z_reference = "\n".join([f"- {z_map[v]}: {v}" for v in variables])

    pca_sections: list[str] = []
    for i in range(min(3, pca_components.shape[0])):
        coefs = pca_components[i]
        terms = []
        for j, coef in enumerate(coefs):
            sign = "+" if coef >= 0 else "-"
            terms.append(f" {sign} {abs(coef):.4f}\\cdot {z_map[variables[j]]}")
        ecuacion = "".join(terms).strip()
        if ecuacion.startswith("+"):
            ecuacion = ecuacion[1:].strip()

        idx_top = np.argsort(np.abs(coefs))[::-1][:3]
        pesos = []
        for idx in idx_top:
            direccion = "positivo" if coefs[idx] >= 0 else "negativo"
            pesos.append(f"{VARIABLE_LABELS.get(variables[idx], variables[idx])} ({direccion})")

        pca_sections.append(
            "\n".join(
                [
                    f"### PC{i + 1} ({pca_var_exp[i] * 100:.2f}% varianza)",
                    "",
                    "$$",
                    f"\\mathbf{{PC_{i + 1}}} = {ecuacion}",
                    "$$",
                    "",
                    f"Interpretacion sugerida: componente dominada por {', '.join(pesos)}.",
                ]
            )
        )

    pca_equations_block = "\n\n".join(pca_sections)

    ejemplo_actuador = sorted(decisiones_raw.keys())[0]
    asignacion = decisiones_raw[ejemplo_actuador]["asignacion_variables"]
    conteo = decisiones_raw[ejemplo_actuador]["conteo_clusters"]
    asign_headers = ["Variable", "Cluster asignado"]
    asign_row = "| " + " | ".join(asign_headers) + " |"
    asign_sep = "|---|---|"
    asign_body = []
    for var in variables:
        asign_body.append(f"| {var} | C{asignacion[var]} |")
    asign_table = "\n".join([asign_row, asign_sep, *asign_body])

    reporte = f"""# Reporte K-means para Monitoreo de Actuadores

## 1. Planteamiento del problema

Se busca clasificar el estado operativo de actuadores de exoesqueleto para priorizar acciones de mantenimiento o reemplazo, usando patrones multivariables en lugar de reglas de umbral aisladas.

## 2. Datos disponibles

- Registros: {n_reg}
- Variables de monitoreo: {n_var}
- Actuadores unicos: {n_act}
- Origen de la base: **{dataset_origin.upper()}**

### Muestra de datos (head)

{head_table}

### Variables analizadas

{chr(10).join([f"- {v}" for v in variables])}

## 3. Metodo aplicado y matematica del algoritmo

### 3.1 Estandarizacion

Antes de calcular cualquier distancia, cada variable $x_i$ se transforma a z-score para que ninguna domine por escala:

$$
z_i = \\frac{{x_i - \\mu_i}}{{\\sigma_i}}
$$

Con {n_reg} registros y {n_var} variables, el vector de entrada de cada medicion queda $\\mathbf{{z}} \\in \\mathbb{{R}}^{n_var}$.

### 3.2 K-means: distancia euclidiana y asignacion

Para cada medicion $\\mathbf{{z}}$ y cada centroide $\\boldsymbol{{\\mu}}_k$ (con $k = 1 \\ldots K$), se calcula la distancia euclidiana:

$$
d(\\mathbf{{z}}, \\boldsymbol{{\\mu}}_k) = \\sqrt{{\\sum_{{j=1}}^{n_var} (z_j - \\mu_{{kj}})^2}}
$$

La medicion se asigna al cluster cuyo centroide esta mas cerca:

$$
c^* = \\underset{{k}}{{\\arg\\min}} \\; d(\\mathbf{{z}}, \\boldsymbol{{\\mu}}_k)
$$

Esto responde directamente por que la distancia importa: **un registro pertenece al cluster cuya media multivariable es geometricamente mas proxima en el espacio estandarizado**. Si un actuador tiene temperatura alta, muchos fallos y logs elevados, su vector $\\mathbf{{z}}$ estara lejos de los centroides de clusters "sanos" y cerca del centroide critico.

### 3.3 Actualizacion de centroides

Despues de asignar todos los registros, cada centroide se recalcula como la media de los puntos asignados a ese cluster:

$$
\\boldsymbol{{\\mu}}_k = \\frac{{1}}{{|C_k|}} \\sum_{{\\mathbf{{z}} \\in C_k}} \\mathbf{{z}}
$$

Este proceso de asignar → recalcular se repite hasta que los centroides no se desplazan mas de una tolerancia $\\varepsilon$ (convergencia). El GIF `07_centroides_3d_evolucion.gif` muestra este movimiento iteracion a iteracion.

### 3.4 Funcion objetivo (inercia)

El algoritmo minimiza la suma de distancias al cuadrado intra-cluster (inercia total $J$):

$$
J = \\sum_{{k=1}}^{{K}} \\sum_{{\\mathbf{{z}} \\in C_k}} \\| \\mathbf{{z}} - \\boldsymbol{{\\mu}}_k \\|^2
$$

En esta corrida: $J = {resumen['inercia']:.2f}$ (con $K={resumen['k_final']}$ clusters).

### 3.5 Evaluacion de K

Para elegir el numero optimo de clusters se evaluo $K \\in [{min(resumen['k_values'])}, {max(resumen['k_values'])}]$ con tres criterios:

- Inercia (metodo del codo)
- Silhouette Score
- Davies-Bouldin Index

Luego se entrenó el modelo final con $K={resumen['k_final']}$ y se proyectaron los datos con PCA de 3 componentes para visualizacion.

Finalmente se aplico analisis de prevalencia por actuador para decision operativa.

## 4. Ecuaciones PCA e interpretacion

Normalizacion previa:

$$
z_i = \\frac{{x_i - \\mu_i}}{{\\sigma_i}}
$$

Convencion de variables:

{z_reference}

{pca_equations_block}

## 5. Asignacion de cluster por variable (matriz de decision)

Despues de que K-means clasifica cada registro por distancia euclidiana, la etapa de prevalencia traduce esos clusters en una decision operativa por actuador usando percentiles globales como regla interpretable.

Para cada variable $v$ y valor medido $x_v$, se calculan $P25_v$, $P50_v$, $P75_v$ sobre todo el dataset y se aplica:

$$
C_v(x_v)=
\\begin{{cases}}
0 \\;(\\text{{Optimo}}), & x_v \\le P25_v \\\\
1 \\;(\\text{{Funcional}}), & P25_v < x_v \\le P50_v \\\\
2 \\;(\\text{{Critico}}), & P50_v < x_v \\le P75_v \\\\
3 \\;(\\text{{Degradado}}), & x_v > P75_v
\\end{{cases}}
$$

Se repite para las {n_var} variables. El estado final del actuador se determina por mayoria:

$$
\\text{{Estado}}(\\text{{actuador}}) = \\underset{{k}}{{\\arg\\max}} \\; \\text{{count}}(C_v = k,\\; v \\in \\text{{variables}})
$$

**Ejemplo concreto — variable `fallos_temporales` en esta corrida:**

| Percentil | Valor |
|---|---|
| P25 | {p25_fallos:.2f} |
| P50 | {p50_fallos:.2f} |
| P75 | {p75_fallos:.2f} |

$$
C_{{fallos}}(x)=
\\begin{{cases}}
0, & x \\le {p25_fallos:.2f} \\\\
1, & {p25_fallos:.2f} < x \\le {p50_fallos:.2f} \\\\
2, & {p50_fallos:.2f} < x \\le {p75_fallos:.2f} \\\\
3, & x > {p75_fallos:.2f}
\\end{{cases}}
$$

Por ejemplo: si un registro tiene $fallos\\_temporales = {p75_fallos + 1:.0f}$ (mayor que P75 = {p75_fallos:.2f}), cae en $C_{{fallos}} = 3$ (Degradado) para esa variable.

## 6. Seleccion de K (imagenes y GIFs)

### Curvas de seleccion

![Selección de K por codo/silhouette/davies](../images/01_metodo_codo.png)

### Avance en GIF por metodo

![GIF Metodo del Codo](../images/01a_evolucion_codo.gif)

![GIF Silhouette](../images/01b_evolucion_silhouette.gif)

![GIF Davies-Bouldin](../images/01c_evolucion_davies.gif)

## 7. Metricas del modelo: ecuaciones, interpretacion y valores obtenidos

### 7.1 Inercia (suma de distancias intra-cluster)

$$
J = \\sum_{{k=1}}^{{K}} \\sum_{{\\mathbf{{z}} \\in C_k}} \\| \\mathbf{{z}} - \\boldsymbol{{\\mu}}_k \\|^2
$$

Mide que tan compactos son los clusters. Cuanto menor, mas juntos estan los puntos alrededor de su centroide. Se usa para el metodo del codo: se busca el K donde la reduccion marginal cae significativamente.

**Valor obtenido:** $J = {resumen['inercia']:.2f}$ con $K={resumen['k_final']}$.

### 7.2 Silhouette Score

Para cada punto $i$ con distancia promedio intra-cluster $a_i$ y distancia promedio al cluster vecino mas cercano $b_i$:

$$
s_i = \\frac{{b_i - a_i}}{{\\max(a_i,\\, b_i)}}
$$

El score global es el promedio de $s_i$ sobre todos los puntos. Rango: $[-1, 1]$.

- Cercano a 1: puntos bien asignados y separados del vecino.
- Cercano a 0: puntos en la frontera entre clusters.
- Negativo: posiblemente asignados al cluster incorrecto.

**Valor obtenido:** $s = {resumen['sil_score']:.4f}$ → {'separacion buena' if resumen['sil_score'] > 0.35 else 'separacion moderada' if resumen['sil_score'] > 0.20 else 'clusters solapados'}.

### 7.3 Davies-Bouldin Index

Para cada cluster $k$ con dispersion interna $S_k$ (desviacion promedio al centroide) y separacion entre centroides $d(\\boldsymbol{{\\mu}}_k, \\boldsymbol{{\\mu}}_l)$:

$$
DB = \\frac{{1}}{{K}} \\sum_{{k=1}}^{{K}} \\max_{{l \\ne k}} \\frac{{S_k + S_l}}{{d(\\boldsymbol{{\\mu}}_k, \\boldsymbol{{\\mu}}_l)}}
$$

Valores mas bajos indican clusters compactos y bien separados. No tiene limite superior; un valor cercano a 0 es ideal.

**Valor obtenido:** $DB = {resumen['db_score']:.4f}$ → {'separacion muy buena' if resumen['db_score'] < 1.0 else 'separacion aceptable' if resumen['db_score'] < 1.5 else 'clusters con solapamiento'}.

### 7.4 Calinski-Harabasz Index (Variance Ratio Criterion)

Compara la dispersion entre clusters (traza de la matriz de dispersion inter-cluster $B_K$) contra la dispersion intra-cluster (traza de $W_K$):

$$
CH = \\frac{{\\text{{tr}}(B_K) \\,/\\, (K-1)}}{{\\text{{tr}}(W_K) \\,/\\, (N-K)}}
$$

Valores mas altos indican mejor separacion relativa. Util para comparar distintos valores de K.

**Valor obtenido:** $CH = {resumen['ch_score']:.2f}$ → {'separacion muy definida' if resumen['ch_score'] > 500 else 'separacion moderada-alta' if resumen['ch_score'] > 200 else 'separacion moderada'}.

### 7.5 Varianza explicada PCA

$$
\\text{{VE}} = \\frac{{\\sum_{{i=1}}^{{3}} \\lambda_i}}{{\\sum_{{i=1}}^{{p}} \\lambda_i}} \\times 100\\%
$$

donde $\\lambda_i$ son los autovalores de la matriz de covarianza. Indica cuanta informacion se conserva al reducir de {n_var} dimensiones a 3.

**Valor obtenido:** VE = {(np.sum(resumen['var_exp_pca']) * 100):.2f}% → {'representacion muy fiel' if np.sum(resumen['var_exp_pca']) > 0.90 else 'representacion aceptable' if np.sum(resumen['var_exp_pca']) > 0.75 else 'representacion parcial'} del espacio original.

### 7.6 Resumen de metricas

| Metrica | Valor | Interpretacion |
|---|---|---|
| K final | {resumen['k_final']} | Numero de clusters elegido |
| Inercia $J$ | {resumen['inercia']:.2f} | Compacidad total (menor = mejor) |
| Silhouette $s$ | {resumen['sil_score']:.4f} | Separacion [-1,1] (mayor = mejor) |
| Davies-Bouldin | {resumen['db_score']:.4f} | Compacidad/separacion (menor = mejor) |
| Calinski-Harabasz | {resumen['ch_score']:.2f} | Separacion relativa (mayor = mejor) |
| Varianza PCA (PC1-3) | {(np.sum(resumen['var_exp_pca']) * 100):.2f}% | Informacion retenida en 3D |

### Distribucion por clusters

{chr(10).join(cluster_summary_lines)}

### Correlaciones mas fuertes

{chr(10).join(corr_lines)}

## 8. Visualizaciones de resultado

### Clusters en espacio PCA 3D

![Clusters en PCA 3D](../images/02_pca_3d_scatter.png)

### Perfil por cluster (media estandarizada)

![Perfil de variables por cluster](../images/03_estadisticas_clusters.png)

### Distribucion por actuador y cluster

![Distribucion por actuador](../images/04_distribucion_actuadores.png)

### Matriz de correlacion

![Matriz de correlacion](../images/05_matriz_correlacion.png)

### Varianza explicada PCA

![Varianza PCA](../images/06_varianza_pca.png)

### Evolucion de centroides en PCA 3D

![Evolucion centroides GIF](../images/07_centroides_3d_evolucion.gif)

![Trayectoria centroides (final)](../images/07_centroides_3d_trayectoria.png)

### Como interpretar el perfil estandarizado por cluster

- El valor 0 representa la media global de la variable.
- Valores positivos indican que el cluster esta por encima de la media en esa variable.
- Valores negativos indican que el cluster esta por debajo de la media.
- Cuanto mas lejos de 0 (en valor absoluto), mayor diferencia respecto al comportamiento promedio.
- Filas con rojo intenso en variables de riesgo (fallos, temperatura, logs) suelen describir clusters de mayor severidad.

## 9. Casos extremos y accion recomendada

Cuando un actuador cae a la vez en perfiles opuestos (por ejemplo C1 y C3), **no conviene tratarlo como perfecto ni como reemplazo inmediato**. Es una zona de inestabilidad/heterogeneidad y la accion recomendada es inspeccion diagnostica temprana con seguimiento corto.

Regla aplicada en este reporte:
- Si C1>=3 y C3>=3 (sobre 9 variables) y diferencia <=1: **AMBIGUO C1-C3** → inspeccion 7-14 dias.
- Si mezcla C1-C3 sin equilibrio fuerte: mantenimiento preventivo anticipado + monitoreo.
- Si hay predominio claro: seguir accion del cluster dominante.

Interpretacion de la columna "Clasificacion":
- **DOMINIO CLARO**: un cluster domina de forma consistente el perfil del actuador.
- **AMBIGUO C1-C3**: mezcla casi equilibrada entre funcional y degradado; requiere inspeccion temprana.
- **MIXTO C1-C3**: coexistencia de señales opuestas, pero con algo de predominio.
- **EMPATE**: no hay dominancia robusta, conviene revisar tendencia temporal.

## 10. Matriz de decision por actuador

{decisiones_table}

## 11. Ejemplo de asignacion por variable para un motor

**Motor ejemplo:** {ejemplo_actuador}

{asign_table}

**Conteo por cluster:** C0={conteo.get(0, 0)}, C1={conteo.get(1, 0)}, C2={conteo.get(2, 0)}, C3={conteo.get(3, 0)}

**Estado final:** {decisiones_raw[ejemplo_actuador]['estado']} ({decisiones_raw[ejemplo_actuador]['prevalencia_pct']}%)

## 12. Conclusiones

K-means fue util en este caso porque separa patrones operativos con multiples indicadores y permite pasar de una lectura por sensor aislado a una **decision por perfil**. El uso combinado de PCA y prevalencia por variable mejora interpretabilidad y evita decisiones ambiguas cuando el motor muestra comportamientos mixtos.
"""

    report_path.write_text(reporte, encoding="utf-8")


def run_pipeline(args: argparse.Namespace) -> None:
    project_root = Path(__file__).resolve().parents[2]

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = project_root / input_path

    out_root = Path(args.output_dir)
    if not out_root.is_absolute():
        out_root = project_root / out_root

    images_dir = out_root / "images"
    reports_dir = out_root / "reports"
    images_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    variables = list(DEFAULT_VARIABLES)
    validar_columnas(df, variables)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df[variables])

    k_values = list(range(args.k_min, args.k_max + 1))
    if args.k_final not in k_values:
        raise ValueError("k-final debe estar dentro del rango [k-min, k-max].")

    evaluacion = evaluar_kmeans(x_scaled, k_values, args.random_state)

    model = KMeans(n_clusters=args.k_final, random_state=args.random_state, n_init=20)
    labels = model.fit_predict(x_scaled)
    df["cluster"] = labels

    pca = PCA(n_components=3, random_state=args.random_state)
    pca_3d = pca.fit_transform(x_scaled)
    centroid_history = calcular_historial_centroides(
        x_scaled,
        n_clusters=args.k_final,
        random_state=args.random_state,
        max_iter=30,
    )

    # Export tabular outputs for easier downstream modifications.
    df.to_csv(reports_dir / "exoesqueleto_con_clusters.csv", index=False)
    cluster_stats = df.groupby("cluster")[variables].agg(["mean", "std", "min", "max"])
    cluster_stats.to_csv(reports_dir / "estadisticas_clusters_detalle.csv")

    cluster_means = df.groupby("cluster")[variables].mean(numeric_only=True)

    plot_metodo_codo(
        k_values,
        evaluacion["inertias"],
        evaluacion["silhouettes"],
        evaluacion["db_scores"],
        args.k_final,
        images_dir / "01_metodo_codo.png",
    )
    generar_gifs_seleccion_k(
        k_values=k_values,
        inertias=evaluacion["inertias"],
        silhouettes=evaluacion["silhouettes"],
        db_scores=evaluacion["db_scores"],
        k_final=args.k_final,
        images_dir=images_dir,
    )
    plot_pca_3d(pca_3d, labels, images_dir / "02_pca_3d_scatter.png")
    plot_estadisticas_clusters(cluster_means, images_dir / "03_estadisticas_clusters.png")
    plot_distribucion_actuadores(df, args.id_col, images_dir / "04_distribucion_actuadores.png")
    plot_matriz_correlacion(df, variables, images_dir / "05_matriz_correlacion.png")
    plot_varianza_pca(pca.explained_variance_ratio_, images_dir / "06_varianza_pca.png")
    plot_evolucion_centroides_3d(
        pca_3d=pca_3d,
        labels=labels,
        centroid_history=centroid_history,
        pca=pca,
        out_gif=images_dir / "07_centroides_3d_evolucion.gif",
        out_png=images_dir / "07_centroides_3d_trayectoria.png",
    )

    resumen = construir_resumen(
        variables=variables,
        k_values=k_values,
        evaluacion=evaluacion,
        k_final=args.k_final,
        model=model,
        x_scaled=x_scaled,
        pca_var=pca.explained_variance_ratio_,
        labels=labels,
    )

    with open(reports_dir / "analisis_kmeans.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    decisiones = calcular_prevalencia_clusters(df, variables, id_col=args.id_col)
    decisiones_df = _analizar_casos_mixtos_prevalencia(decisiones, id_col=args.id_col)
    decisiones_df.to_csv(reports_dir / "decision_por_actuador.csv", index=False)

    _crear_reporte_markdown(
        report_path=reports_dir / "reporte_exoesqueleto_kmeans.md",
        resumen=resumen,
        df=df,
        variables=variables,
        id_col=args.id_col,
        cluster_means=cluster_means,
        decisiones_df=decisiones_df,
        decisiones_raw=decisiones,
        dataset_origin=args.dataset_origin,
        pca_components=pca.components_,
        pca_var_exp=pca.explained_variance_ratio_,
    )

    print("Pipeline completado.")
    print(f"- Dataset con clusters: {(reports_dir / 'exoesqueleto_con_clusters.csv').as_posix()}")
    print(f"- Resumen JSON: {(reports_dir / 'analisis_kmeans.json').as_posix()}")
    print(f"- Estadisticas detalladas: {(reports_dir / 'estadisticas_clusters_detalle.csv').as_posix()}")
    print(f"- Decision por actuador: {(reports_dir / 'decision_por_actuador.csv').as_posix()}")
    print(f"- Reporte markdown: {(reports_dir / 'reporte_exoesqueleto_kmeans.md').as_posix()}")
    print("- GIFs de seleccion K: 01a_evolucion_codo.gif, 01b_evolucion_silhouette.gif, 01c_evolucion_davies.gif")
    print("- Evolucion de centroides: 07_centroides_3d_evolucion.gif")
    print(f"- Graficas: {images_dir.as_posix()}")

    if args.open_centroid_evolution:
        webbrowser.open((images_dir / "07_centroides_3d_evolucion.gif").as_uri())


if __name__ == "__main__":
    argumentos = parse_args()
    run_pipeline(argumentos)
