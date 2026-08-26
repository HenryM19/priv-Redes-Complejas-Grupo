"""
run_all.py — Script maestro de ejecución
=========================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Ejecuta todos los scripts del proyecto en orden (P1–P11) sin intervención
manual. Cada script genera sus propias figuras y tablas en results/.

Uso:
    python run_all.py              # ejecuta P1–P11
    python run_all.py --desde 5   # reanuda desde P5
    python run_all.py --solo 3 7  # ejecuta solo P3 y P7

Requisitos:
    pip install -r requirements.txt   (desde la raíz del repositorio)
"""

# ── Carga de librerías ──────────────────────────────────────────────────────
import argparse
import subprocess
import sys
import time
from pathlib import Path


# ── Definición de funciones ─────────────────────────────────────────────────

def ejecutar_script(ruta: Path, numero: int) -> bool:
    """
    Ejecuta un script individual con el intérprete actual.

    Args:
        ruta    (Path): Ruta absoluta al archivo .py a ejecutar.
        numero   (int): Número de problema (para el log).

    Returns:
        bool: True si el script terminó con código 0, False en caso contrario.
    """
    print(f"\n{'='*60}")
    print(f"  Ejecutando P{numero}: {ruta.name}")
    print(f"{'='*60}")
    t0 = time.time()
    resultado = subprocess.run([sys.executable, str(ruta)])
    elapsed = time.time() - t0
    if resultado.returncode == 0:
        print(f"  ✔ P{numero} completado en {elapsed:.1f}s")
        return True
    else:
        print(f"  ✘ P{numero} falló con código {resultado.returncode}")
        return False


def parsear_args() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.

    Returns:
        argparse.Namespace: Namespace con atributos 'desde' y 'solo'.
    """
    parser = argparse.ArgumentParser(description="Ejecuta todos los problemas P1–P11")
    parser.add_argument("--desde", type=int, default=1, metavar="N",
                        help="Número de problema desde el que comenzar (default: 1)")
    parser.add_argument("--solo", type=int, nargs="+", metavar="N",
                        help="Ejecutar solo los problemas indicados (ej: --solo 3 7)")
    return parser.parse_args()


# ── Código principal ────────────────────────────────────────────────────────

def main() -> None:
    """
    Punto de entrada: resuelve la secuencia P1–P11 llamando a cada script.
    Imprime un resumen final indicando qué problemas pasaron y cuáles fallaron.
    """
    args = parsear_args()

    # Directorio donde vive este script
    dir_src = Path(__file__).parent.resolve()

    # Orden canónico de ejecución
    todos = list(range(1, 12))          # [1, 2, ..., 11]

    if args.solo:
        seleccion = sorted(set(args.solo))
    else:
        seleccion = [n for n in todos if n >= args.desde]

    print(f"\nProblemas a ejecutar: {seleccion}")
    print(f"Directorio src: {dir_src}\n")

    resultados: dict[int, bool] = {}

    for n in seleccion:
        script = dir_src / f"problema{n}.py"
        if not script.exists():
            print(f"  ⚠ {script.name} no encontrado — omitido")
            resultados[n] = False
            continue
        resultados[n] = ejecutar_script(script, n)

    # Resumen final
    print(f"\n{'='*60}")
    print("  RESUMEN")
    print(f"{'='*60}")
    ok  = [n for n, v in resultados.items() if v]
    err = [n for n, v in resultados.items() if not v]
    print(f"  Exitosos : {ok if ok  else '—'}")
    print(f"  Fallidos : {err if err else '—'}")
    if err:
        sys.exit(1)


if __name__ == "__main__":
    main()
