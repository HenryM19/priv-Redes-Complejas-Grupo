from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


CLUSTER_TO_STATE = {
    0: ("OPTIMO", "✅", "Operacion normal"),
    1: ("FUNCIONAL", "✅", "Mantenimiento rutinario"),
    2: ("CRITICO", "🔴", "Investigar inmediatamente / posible reemplazo"),
    3: ("DEGRADADO", "🟠", "Mantenimiento en 30-60 dias"),
}

# En empates se prioriza la severidad operativa.
TIE_BREAK_PRIORITY = [2, 3, 1, 0]


@dataclass
class DecisionResult:
    actuador: str
    cluster_dominante: int
    estado: str
    emoji: str
    accion: str
    prevalencia_pct: float
    conteo_clusters: Dict[int, int]
    asignacion_variables: Dict[str, int]



def _validar_columnas(df: pd.DataFrame, columnas: List[str]) -> None:
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")



def _cluster_por_cuartiles(valor: float, p25: float, p50: float, p75: float) -> int:
    if valor <= p25:
        return 0
    if valor <= p50:
        return 1
    if valor <= p75:
        return 2
    return 3



def _resolver_dominante(conteo: Counter) -> int:
    max_count = max(conteo.values())
    empatados = [k for k, v in conteo.items() if v == max_count]
    if len(empatados) == 1:
        return empatados[0]
    for c in TIE_BREAK_PRIORITY:
        if c in empatados:
            return c
    return empatados[0]



def calcular_prevalencia_clusters(
    df: pd.DataFrame,
    variables: List[str],
    id_col: str = "id_actuador",
    agg: str = "mean",
    referencia_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Dict]:
    """Calcula estado final por actuador usando prevalencia de clusters por variable.

    Args:
        df: Datos con mediciones por actuador.
        variables: Lista de variables numericas a evaluar.
        id_col: Columna identificadora del actuador.
        agg: Agregacion por actuador para convertir N mediciones en 1 perfil.
             Soportado: 'mean', 'median', 'last'.
        referencia_df: DataFrame opcional para calcular percentiles globales.
                      Si es None, usa `df`.

    Returns:
        Diccionario indexado por actuador con estado, prevalencia y detalle.
    """
    if id_col not in df.columns:
        raise ValueError(f"No existe la columna de actuador: {id_col}")

    _validar_columnas(df, variables)

    base_ref = referencia_df if referencia_df is not None else df
    _validar_columnas(base_ref, variables)

    percentiles = {
        v: np.percentile(base_ref[v].dropna().values, [25, 50, 75]) for v in variables
    }

    if agg == "mean":
        perfil = df.groupby(id_col, as_index=False)[variables].mean(numeric_only=True)
    elif agg == "median":
        perfil = df.groupby(id_col, as_index=False)[variables].median(numeric_only=True)
    elif agg == "last":
        perfil = df.sort_index().groupby(id_col, as_index=False).tail(1)
        perfil = perfil[[id_col] + variables]
    else:
        raise ValueError("Parametro 'agg' no soportado. Usa: 'mean', 'median' o 'last'.")

    resultados: Dict[str, Dict] = {}

    for _, row in perfil.iterrows():
        actuador = str(row[id_col])

        asignacion_variables: Dict[str, int] = {}
        conteo = Counter({0: 0, 1: 0, 2: 0, 3: 0})

        for var in variables:
            p25, p50, p75 = percentiles[var]
            cluster_var = _cluster_por_cuartiles(float(row[var]), p25, p50, p75)
            asignacion_variables[var] = cluster_var
            conteo[cluster_var] += 1

        cluster_dominante = _resolver_dominante(conteo)
        estado, emoji, accion = CLUSTER_TO_STATE[cluster_dominante]
        prevalencia = round((conteo[cluster_dominante] / len(variables)) * 100.0, 1)

        decision = DecisionResult(
            actuador=actuador,
            cluster_dominante=cluster_dominante,
            estado=estado,
            emoji=emoji,
            accion=accion,
            prevalencia_pct=prevalencia,
            conteo_clusters=dict(conteo),
            asignacion_variables=asignacion_variables,
        )

        resultados[actuador] = {
            "cluster_dominante": decision.cluster_dominante,
            "estado": decision.estado,
            "emoji": decision.emoji,
            "accion": decision.accion,
            "prevalencia_pct": decision.prevalencia_pct,
            "conteo_clusters": decision.conteo_clusters,
            "asignacion_variables": decision.asignacion_variables,
        }

    return resultados
