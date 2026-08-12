"""
problema11.py — Problema P11: Propuesta de Rediseño (Fase 5)
=============================================================
Módulo 1217 — Redes Complejas · Universidad de Cuenca
Dr. Fabián Astudillo-Salinas

Con el diagnóstico de P10, propone una intervención de a lo sumo cinco
enlaces nuevos sobre la red UCuenca y cuantifica la mejora.

Ítems resueltos:
  Ítem 1 · Descripción de los 5 enlaces propuestos
  Ítem 2 · Cuantificación: tabla antes/después/variación
  Ítem 3 · Comparación contra dos conjuntos alternativos
  Ítem 4 · Estimación de costo y factibilidad (texto en Informe)
  Ítem 5 · Limitaciones del estudio (texto en Informe)

Uso:
    python problema11.py

Salidas:
    results/tablas/p11_metricas_comparacion.csv
    results/tablas/p11_flujo_comparacion.csv
    results/imagenes/p11_percolacion_comparacion.png
    results/imagenes/p11_flujo_comparacion.png
"""

# ============================================================
# Carga de librerías
# ============================================================
import os, sys, random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

DIR_SRC   = os.path.dirname(os.path.abspath(__file__))
DIR_RESOL = os.path.dirname(DIR_SRC)
DIR_ROOT  = os.path.dirname(DIR_RESOL)
DIR_BASE  = os.path.join(DIR_ROOT, "codigo_base")
DIR_TAB   = os.path.join(DIR_RESOL, "results", "tablas")
DIR_IMG   = os.path.join(DIR_RESOL, "results", "imagenes")

sys.path.insert(0, DIR_BASE)
from cargar_red import cargar_red, verificar  # noqa


def _crear_dirs():
    os.makedirs(DIR_TAB, exist_ok=True)
    os.makedirs(DIR_IMG, exist_ok=True)


# ============================================================
# Definición de funciones
# ============================================================

# ------------------------------------------------------------
# Construcción de variantes de red
# ------------------------------------------------------------

def aplicar_enlaces(G: nx.Graph, enlaces: list) -> nx.Graph:
    """
    Crea una copia del grafo con los enlaces nuevos añadidos.

    Argumentos:
        G       (nx.Graph): grafo original.
        enlaces (list)    : lista de tuplas (u, v, capacidad_mbps).

    Salida:
        nx.Graph: copia con los nuevos enlaces incorporados.
    """
    Gm = G.copy()
    for u, v, cap in enlaces:
        if not Gm.has_edge(u, v):
            Gm.add_edge(u, v, trafico_mbps=cap, capacidad_mbps=cap,
                        rol="respaldo", nuevo=True)
    return Gm


# ------------------------------------------------------------
# Métricas estructurales
# ------------------------------------------------------------

def metricas_estructurales(G: nx.Graph) -> dict:
    """
    Calcula las métricas estructurales solicitadas en el Ítem 2.

    Argumentos:
        G (nx.Graph): grafo a analizar.

    Salida:
        dict con claves:
          n_aristas, n_puentes, n_articulacion,
          dist_media, eficiencia_global.
    """
    puentes    = list(nx.bridges(G))
    artic      = list(nx.articulation_points(G))
    dist_media = nx.average_shortest_path_length(G)
    # Eficiencia global: media de 1/d(u,v) para todos los pares
    n = G.number_of_nodes()
    ef = 0.0
    for v in G.nodes():
        longitudes = nx.single_source_shortest_path_length(G, v)
        ef += sum(1.0 / d for u, d in longitudes.items() if d > 0)
    ef /= (n * (n - 1))
    return {
        "n_aristas"       : G.number_of_edges(),
        "n_puentes"       : len(puentes),
        "n_articulacion"  : len(artic),
        "dist_media"      : round(dist_media, 4),
        "eficiencia_global": round(ef, 5),
    }


# ------------------------------------------------------------
# Flujo máximo por campus
# ------------------------------------------------------------

def flujo_por_campus(G: nx.Graph) -> dict:
    """
    Calcula el flujo máximo desde cada campus hacia INTERNET-MPLS.
    Usa capacidad trafico_mbps de cada arista; si no existe, asume 1000 Mbps.

    Argumentos:
        G (nx.Graph): grafo (original o modificado).

    Salida:
        dict: {campus: flujo_max_mbps}.
    """
    DG = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        cap = d.get("trafico_mbps", 1000) or 1000
        DG.add_edge(u, v, capacity=cap)
        DG.add_edge(v, u, capacity=cap)

    sumidero = "INTERNET-MPLS"
    campus_fuentes = {
        "Campus Central"  : "DATCC-2A-C3",
        "Campus Paraiso"  : "CPAR-C10",
        "Campus Balzay"   : "DT-0A-C13",
        "Campus Yanuncay" : "AGRPRI-1A-D10",
    }
    resultado = {}
    for campus, fuente in campus_fuentes.items():
        if fuente in DG and sumidero in DG:
            try:
                flujo, _ = nx.maximum_flow(DG, fuente, sumidero,
                                           capacity="capacity",
                                           flow_func=nx.algorithms.flow.edmonds_karp)
                resultado[campus] = flujo
            except Exception:
                resultado[campus] = 0
        else:
            resultado[campus] = 0
    return resultado


# ------------------------------------------------------------
# Percolación bajo ataque dirigido por grado
# ------------------------------------------------------------

def percolacion_ataque_grado(G: nx.Graph,
                              pasos: int = 30) -> pd.DataFrame:
    """
    Simula percolación eliminando nodos en orden descendente de grado
    (recalculando el grado tras cada eliminación — atacante adaptativo).

    La eficiencia se calcula sobre los n_total nodos ORIGINALES:
    los pares desconectados contribuyen 1/d = 0, lo que refleja
    honestamente el daño global de la red, sin el artefacto de medir
    solo dentro de la componente gigante superviviente.

    Argumentos:
        G     (nx.Graph): grafo a analizar.
        pasos (int)     : número de puntos de muestreo en [0, 1].

    Salida:
        pd.DataFrame [fraccion, eficiencia_global, tamanio_cgc].
    """
    n_total = G.number_of_nodes()
    n_pasos = min(pasos, n_total)

    Gaux      = G.copy()
    eliminados = 0
    filas     = []

    for idx in range(n_pasos):
        f = eliminados / n_total

        # Eficiencia GLOBAL: suma 1/d sobre todos los pares originales
        # Los nodos eliminados no aparecen en Gaux → contribuyen 0
        ef = 0.0
        componentes = list(nx.connected_components(Gaux))
        cgc_size = max(len(c) for c in componentes) if componentes else 0
        for comp in componentes:
            if len(comp) < 2:
                continue
            Gsub = Gaux.subgraph(comp)
            for v in Gsub.nodes():
                longs = nx.single_source_shortest_path_length(Gsub, v)
                ef += sum(1.0 / d for u, d in longs.items() if d > 0)
        # Normalizar sobre TODOS los pares originales n*(n-1)
        ef /= (n_total * (n_total - 1))

        # Distancia media sobre la componente gigante (pares alcanzables)
        if cgc_size > 1:
            cgc_nodes = max(componentes, key=len)
            Gcgc = Gaux.subgraph(cgc_nodes)
            suma_dist, pares = 0.0, 0
            for v in Gcgc.nodes():
                longs = nx.single_source_shortest_path_length(Gcgc, v)
                for u, d in longs.items():
                    if d > 0:
                        suma_dist += d
                        pares += 1
            dist_media = suma_dist / pares if pares > 0 else 0.0
        else:
            dist_media = 0.0

        filas.append({
            "fraccion"        : round(f, 4),
            "eficiencia_global": round(ef, 5),
            "tamanio_cgc"     : cgc_size,
            "dist_media_cgc"  : round(dist_media, 4),
        })

        # Eliminar el nodo de mayor grado actual (atacante adaptativo)
        if Gaux.number_of_nodes() > 0:
            siguiente = max(Gaux.degree(), key=lambda x: x[1])[0]
            Gaux.remove_node(siguiente)
            eliminados += 1

    return pd.DataFrame(filas)


# ------------------------------------------------------------
# Visualizaciones
# ------------------------------------------------------------

def graficar_percolacion(dfs: dict, titulo: str = "P11") -> None:
    """
    Grafica dos paneles bajo ataque dirigido por grado:
      - Panel izquierdo : eficiencia global E(f) sobre todos los pares originales
                          (pares desconectados = 0 → curva monotónicamente decreciente)
      - Panel derecho   : distancia media dentro de la componente gigante restante
                          (sube porque los fragmentos que quedan son más compactos)

    Argumentos:
        dfs   (dict): {etiqueta: pd.DataFrame con columnas fraccion,
                       eficiencia_global, tamanio_cgc, dist_media_cgc}.
        titulo (str): prefijo para el título del gráfico.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    estilos = {
        "Original"      : ("k-",  2.5),
        "Propuesta ICC" : ("r-",  2.0),
        "Alt. A (grado)": ("b--", 1.5),
        "Alt. B (btw)"  : ("g-.", 1.5),
    }
    for etiqueta, df in dfs.items():
        ls, lw = estilos.get(etiqueta, ("m:", 1.5))

        # Panel izquierdo: eficiencia global
        col_e = "eficiencia_global" if "eficiencia_global" in df.columns else "eficiencia"
        e0    = df[col_e].iloc[0]
        sub_fc = df[df[col_e] <= 0.5 * e0]
        fc    = sub_fc["fraccion"].iloc[0] if not sub_fc.empty else None
        label = f"{etiqueta} (fc≈{fc:.2f})" if fc else etiqueta
        ax1.plot(df["fraccion"], df[col_e], ls, linewidth=lw, label=label)

        # Panel derecho: distancia media en CGC
        if "dist_media_cgc" in df.columns:
            ax2.plot(df["fraccion"], df["dist_media_cgc"], ls,
                     linewidth=lw, label=etiqueta)

    ax1.set_xlabel("Fracción eliminada (ataque por grado)")
    ax1.set_ylabel("E(f) global  [pares desconectados = 0]")
    ax1.set_title("Eficiencia global bajo ataque\n(monotónicamente decreciente)",
                  fontweight="bold")
    ax1.legend(fontsize=8); ax1.grid(alpha=0.3)

    ax2.set_xlabel("Fracción eliminada (ataque por grado)")
    ax2.set_ylabel("Distancia media (dentro de CGC)")
    ax2.set_title("Distancia media en componente gigante\n(sube al fragmentarse la red)",
                  fontweight="bold")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)

    plt.suptitle(f"{titulo} · Percolación bajo ataque dirigido — Red UCuenca",
                 fontweight="bold", fontsize=11)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p11_percolacion_comparacion.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


def graficar_flujo(datos_flujo: dict) -> None:
    """
    Gráfico de barras agrupadas: flujo máximo por campus para cada variante.

    Argumentos:
        datos_flujo (dict): {variante: {campus: flujo_mbps}}.
    """
    campus_list  = ["Campus Central", "Campus Paraiso",
                    "Campus Balzay",  "Campus Yanuncay"]
    variantes    = list(datos_flujo.keys())
    x = np.arange(len(campus_list))
    ancho = 0.2
    colores = ["#555555", "#e74c3c", "#3498db", "#2ecc71"]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (var, color) in enumerate(zip(variantes, colores)):
        valores = [datos_flujo[var].get(c, 0) / 1000 for c in campus_list]
        ax.bar(x + i * ancho, valores, ancho, label=var, color=color)

    ax.set_xticks(x + ancho * 1.5)
    ax.set_xticklabels(campus_list, rotation=15, ha="right")
    ax.set_ylabel("Flujo máximo (Gbps)")
    ax.set_title("P11 · Flujo máximo por campus\nComparación original vs. propuestas",
                 fontweight="bold")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    ruta = os.path.join(DIR_IMG, "p11_flujo_comparacion.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"  [OK] {ruta}")


# ============================================================
# CÓDIGO MAIN
# ============================================================

if __name__ == "__main__":
    _crear_dirs()
    print("\n=== P11 — Propuesta de Rediseño (Fase 5) ===\n")

    G = cargar_red(fuente="csv"); verificar(G)

    # ----------------------------------------------------------
    # Definición de conjuntos de enlaces
    # ----------------------------------------------------------

    # Propuesta ICC: basada en ranking de criticidad de P10
    # Cada enlace resuelve un problema específico del diagnóstico
    enlaces_propuesta = [
        # (u, v, cap_mbps, problema_que_resuelve)
        ("CPAR-C10",              "INTERNET-MPLS",          1_000,
         "Segundo uplink de Campus Paraíso al backbone MPLS — "
         "elimina ROUTER-CAMPUS-HUAYNA-CAPAC (ICC #2) como punto de articulación"),
        ("DATCC-2A-C3",           "CPAR-C10",              10_000,
         "Enlace directo core Central ↔ core Paraíso — "
         "reduce cascada desde DATCC-2A-C3 (ICC #4) y da resiliencia a CPAR-C10 (ICC #3)"),
        ("ROUTER-CAMPUS-YANUNCAY","PE2-CENTRAL",            1_000,
         "Segundo uplink de Campus Yanuncay — "
         "elimina ROUTER-CAMPUS-YANUNCAY (ICC #5) como punto de articulación"),
        ("CP-ODONTOLOGIA-D4",     "CP-EADMINA1-D6",        1_000,
         "Cross-link entre nodos de agregación de Campus Paraíso — "
         "elimina CP-ODONTOLOGIA-D4 (ICC #10) y CP-EADMINA1-D6 (ICC #9) como articulaciones"),
        ("BAL-EADM-D3",           "DT-0A-C13",             1_000,
         "Segundo uplink del switch de administración de Balzay — "
         "elimina BAL-EADM-D3 como punto de articulación en Campus Balzay"),
    ]

    # Alternativa A — criterio ingenuo: unir los 5 pares de nodos
    # de mayor grado que no estén ya conectados
    alt_a = [
        ("DATCC-2A-C3",  "AGRPRI-1A-D10",   1_000),
        ("DATCC-2A-C3",  "BAL-AUL2-D1",     1_000),
        ("DATCC-2A-C3",  "CP-EADMINA1-D6",  1_000),
        ("DATCC-2A-C3",  "DT-0A-C13",       1_000),
        ("DATCC-2A-C3",  "INTERNET-MPLS",   1_000),
    ]

    # Alternativa B — criterio de betweenness: unir los nodos
    # de mayor betweenness que no estén ya conectados entre sí
    alt_b = [
        ("ROUTER-CAMPUS-HUAYNA-CAPAC", "DATCC-2A-C3",  1_000),
        ("ROUTER-CAMPUS-HUAYNA-CAPAC", "DATCC-2A-C2",  1_000),
        ("ROUTER-CAMPUS-YANUNCAY",     "DATCC-2A-C3",  1_000),
        ("CPAR-C10",                   "DATCC-2A-C2",  1_000),
        ("DT-0A-C13",                  "INTERNET-MPLS",1_000),
    ]

    # Construir los cuatro grafos
    G_prop = aplicar_enlaces(G, [(u,v,c) for u,v,c,_ in enlaces_propuesta])
    G_alta = aplicar_enlaces(G, alt_a)
    G_altb = aplicar_enlaces(G, alt_b)

    # ----------------------------------------------------------
    # Ítem 2: métricas estructurales antes / después
    # ----------------------------------------------------------
    print("[Ítem 2] Calculando métricas estructurales...")
    variantes = {
        "Original"      : G,
        "Propuesta ICC" : G_prop,
        "Alt. A (grado)": G_alta,
        "Alt. B (btw)"  : G_altb,
    }
    filas_met = []
    for nombre, Gv in variantes.items():
        print(f"  → {nombre}...")
        m = metricas_estructurales(Gv)
        m["variante"] = nombre
        filas_met.append(m)

    df_met = pd.DataFrame(filas_met).set_index("variante")
    df_met.to_csv(os.path.join(DIR_TAB, "p11_metricas_comparacion.csv"))

    # Tabla antes/después/variación (solo original vs propuesta)
    orig  = df_met.loc["Original"]
    prop  = df_met.loc["Propuesta ICC"]
    print("\n--- Tabla antes / después / variación ---")
    print(f"{'Métrica':<25} {'Antes':>10} {'Después':>10} {'Δ':>10} {'%':>8}")
    print("-" * 68)
    for col in df_met.columns:
        antes  = orig[col]
        despues = prop[col]
        delta  = despues - antes
        pct    = (delta / antes * 100) if antes != 0 else 0
        print(f"{col:<25} {antes:>10.4f} {despues:>10.4f} {delta:>+10.4f} {pct:>+7.1f}%")

    # ----------------------------------------------------------
    # Flujo máximo por campus
    # ----------------------------------------------------------
    print("\n[Flujo] Calculando flujo máximo por campus...")
    datos_flujo = {}
    for nombre, Gv in variantes.items():
        datos_flujo[nombre] = flujo_por_campus(Gv)
        print(f"  {nombre}: {datos_flujo[nombre]}")

    df_flujo = pd.DataFrame(datos_flujo).T
    df_flujo.to_csv(os.path.join(DIR_TAB, "p11_flujo_comparacion.csv"))

    # ----------------------------------------------------------
    # Percolación bajo ataque dirigido por grado
    # ----------------------------------------------------------
    print("\n[Percolación] Calculando curvas de percolación (ataque por grado)...")
    dfs_perc = {}
    for nombre, Gv in variantes.items():
        print(f"  → {nombre}...")
        dfs_perc[nombre] = percolacion_ataque_grado(Gv, pasos=25)

    # ----------------------------------------------------------
    # Visualizaciones
    # ----------------------------------------------------------
    print("\n[VIZ] Generando gráficos...")
    graficar_percolacion(dfs_perc)
    graficar_flujo(datos_flujo)

    # ----------------------------------------------------------
    # Resumen final
    # ----------------------------------------------------------
    print("\n" + "=" * 65)
    print("RESUMEN COMPARATIVO")
    print("=" * 65)
    print(df_met.to_string())
    print("\nFlujo máximo por campus (Mbps):")
    print(df_flujo.to_string())

    # fc: fracción donde E cae al 50% de E0 (ataque por grado)
    print("\nUmbral fc (E cae al 50% de E0) bajo ataque por grado:")
    for nombre, df in dfs_perc.items():
        col = "eficiencia_global"
        e0  = df[col].iloc[0]
        sub = df[df[col] <= 0.5 * e0]
        fc  = sub["fraccion"].iloc[0] if not sub.empty else ">max"
        print(f"  {nombre}: E0={e0:.5f}  fc={fc}")

    # Guardar también percolación
    for nombre, df in dfs_perc.items():
        key = nombre.replace(" ", "_").replace(".", "").replace("(", "").replace(")", "")
        df.to_csv(os.path.join(DIR_TAB, f"p11_perc_{key}.csv"), index=False)

    print("\n=== P11 completado ===\n")
