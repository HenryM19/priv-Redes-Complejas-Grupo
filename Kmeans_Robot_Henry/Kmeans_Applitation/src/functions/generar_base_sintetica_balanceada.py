from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _clip(v: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip(v, lo, hi)


def generar_dataset_balanceado(output_csv: Path, random_state: int = 42) -> None:
    rng = np.random.default_rng(random_state)

    actuadores = {
        "A1_Cadera_Derecha": {"perfil": "critico", "uso": 3400, "temp": 61.0, "dias_srv": 320},
        "A2_Rodilla_Derecha": {"perfil": "degradado", "uso": 2500, "temp": 55.5, "dias_srv": 250},
        "A3_Tobillo_Derecha": {"perfil": "optimo", "uso": 700, "temp": 45.5, "dias_srv": 70},
        "A4_Cadera_Izquierda": {"perfil": "funcional", "uso": 1250, "temp": 48.0, "dias_srv": 120},
        "A5_Rodilla_Izquierda": {"perfil": "degradado", "uso": 2650, "temp": 56.2, "dias_srv": 265},
        "A6_Tobillo_Izquierda": {"perfil": "funcional", "uso": 1400, "temp": 48.8, "dias_srv": 130},
    }

    fechas = pd.date_range("2024-01-01", periods=100, freq="D")
    filas: list[dict] = []

    for act, meta in actuadores.items():
        uso_base = meta["uso"]
        temp_base = meta["temp"]
        dserv_base = meta["dias_srv"]

        perfil = meta["perfil"]
        if perfil == "optimo":
            rep_lambda = 0.10
            fallos_base = 0.8
            logs_base = 3.0
            dcal_base = 55
        elif perfil == "funcional":
            rep_lambda = 0.45
            fallos_base = 1.6
            logs_base = 8.0
            dcal_base = 95
        elif perfil == "degradado":
            rep_lambda = 1.6
            fallos_base = 5.2
            logs_base = 23.0
            dcal_base = 185
        else:  # critico
            rep_lambda = 3.0
            fallos_base = 9.2
            logs_base = 52.0
            dcal_base = 245

        uso = _clip(rng.normal(uso_base, 180, size=100), 120, 5200)
        ciclos = _clip(uso / 110 + rng.normal(0, 1.0, size=100), 0.8, 50)

        reparaciones = rng.poisson(rep_lambda, size=100)
        reparaciones = _clip(reparaciones, 0, 5).astype(int)

        temp_op = _clip(rng.normal(temp_base, 1.6, size=100), 25, 72)
        temp_max = _clip(temp_op + rng.normal(10.5, 1.9, size=100), 40, 85)

        dias_cal = _clip(rng.normal(dcal_base, 22, size=100), 0, 365).astype(int)
        dias_srv = _clip(rng.normal(dserv_base, 28, size=100), 0, 365).astype(int)

        fallos_mu = fallos_base + 0.12 * (temp_max - 58) + 1.1 * reparaciones
        fallos = _clip(rng.normal(fallos_mu, 1.2, size=100), 0, 20)
        fallos = np.rint(fallos).astype(int)

        logs_mu = logs_base + 2.8 * fallos + 3.6 * reparaciones
        logs = _clip(rng.normal(logs_mu, 3.4, size=100), 0, 100)
        logs = np.rint(logs).astype(int)

        for i in range(100):
            filas.append(
                {
                    "id_actuador": act,
                    "fecha_medicion": fechas[i].strftime("%Y-%m-%d"),
                    "tiempo_uso_acumulado_h": round(float(uso[i]), 2),
                    "ciclos_activacion_M": round(float(ciclos[i]), 2),
                    "numero_reparaciones": int(reparaciones[i]),
                    "fallos_temporales": int(fallos[i]),
                    "temp_operacional_promedio_C": round(float(temp_op[i]), 2),
                    "temp_maxima_alcanzada_C": round(float(temp_max[i]), 2),
                    "dias_ultima_calibracion": int(dias_cal[i]),
                    "dias_ultimo_servicio": int(dias_srv[i]),
                    "numero_logs_error": int(logs[i]),
                }
            )

    df = pd.DataFrame(filas)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[2]
    out = base_dir / "src" / "data" / "exoesqueleto_actuadores.csv"
    generar_dataset_balanceado(out)
    print(f"Dataset balanceado generado en: {out.as_posix()}")
