"""Punto de entrada principal para ejecutar el pipeline de analisis."""

from src.functions.pipeline_kmeans_exoesqueleto import parse_args, run_pipeline


def main() -> None:
    args = parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
