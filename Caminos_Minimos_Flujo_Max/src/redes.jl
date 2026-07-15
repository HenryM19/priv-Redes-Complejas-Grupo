# ============================================================
# redes.jl — Definición de las redes usadas en la actividad
# ============================================================
#
# Tres redes:
#   1. red_clrs()   — red clásica de Cormen et al. (flujo máximo 23)
#   2. red_zigzag(M) — red trampa: arco u→v de capacidad 1 entre dos
#                      rutas de capacidad M (Parte 2 de la guía)
#   3. red_propia()  — red original de la pareja (Parte 3)
#
# Todas devuelven (red, s, t) para usar con ford_fulkerson/edmonds_karp.

"""
    red_clrs() -> (RedFlujo, s, t)

Red clásica de CLRS (Introduction to Algorithms, fig. 26.1).
6 nodos, 9 arcos, flujo máximo conocido = 23.
"""
function red_clrs()
    nombres = ["s", "v₁", "v₂", "v₃", "v₄", "t"]
    pos = [(0.0, 1.0), (1.0, 2.0), (1.0, 0.0),
           (2.2, 2.0), (2.2, 0.0), (3.2, 1.0)]
    C = zeros(Int, 6, 6)
    C[1, 2] = 16   # s  → v₁
    C[1, 3] = 13   # s  → v₂
    C[2, 4] = 12   # v₁ → v₃
    C[3, 2] = 4    # v₂ → v₁
    C[3, 5] = 14   # v₂ → v₄
    C[4, 3] = 9    # v₃ → v₂
    C[4, 6] = 20   # v₃ → t
    C[5, 4] = 7    # v₄ → v₃
    C[5, 6] = 4    # v₄ → t
    return RedFlujo(C, nombres, pos), 1, 6
end

"""
    red_zigzag(M) -> (RedFlujo, s, t)

Red trampa de la Parte 2. Dos rutas de capacidad `M` (s→u→t y s→v→t)
unidas por un arco u→v de capacidad 1.

El flujo máximo es 2M, pero un Ford-Fulkerson que insistiera en pasar
por el arco trampa avanzaría de 1 en 1 (2M iteraciones).
"""
function red_zigzag(M::Int)
    Cz = zeros(Int, 4, 4)
    Cz[1, 2] = M; Cz[1, 3] = M   # s→u, s→v
    Cz[2, 3] = 1                 # u→v  (arco trampa)
    Cz[2, 4] = M; Cz[3, 4] = M   # u→t, v→t
    red = RedFlujo(Cz, ["s", "u", "v", "t"],
                   [(0.0, 1.0), (1.2, 2.0), (1.2, 0.0), (2.4, 1.0)])
    return red, 1, 4
end

"""
    red_propia() -> (RedFlujo, s, t)

Red original de la pareja (Parte 3). Modela el backbone de un proveedor
de Internet: `s` es el punto de peering donde entra el tráfico, `t` el
data center que lo consume, y los nodos intermedios son enrutadores.
Las capacidades están en Gb/s.

Diseño: la topología (qué arcos existen) se fijó a mano pensando dónde
queremos el cuello de botella; las capacidades se ajustaron mediante una
búsqueda dirigida (`src/busqueda_red.jl`) sobre el espacio 2..15 hasta
encontrar una combinación que cumpliera *simultáneamente* los cuatro
requisitos de la guía. El proceso, con los intentos fallidos, está
documentado en `results/parte3_diseno.md`.

Requisitos de la guía que cumple (verificado en la Parte 3):
  * 9 nodos y 16 arcos (la guía pide ≥ 8 y ≥ 12).
  * Par antiparalelo: c ⇄ d — C[4,5] = 5 (c→d) y C[5,4] = 7 (d→c).
  * Arcos de retroceso usados por AMBAS ejecuciones: BFS los usa en su
    iteración 5 (f→b) y DFS en su iteración 8 (d→b).
  * Iteraciones distintas: BFS necesita 5, DFS necesita 8.

Además, y esto es lo pedagógicamente valioso:
  * El corte mínimo NO es trivial: S = {s, a, c, e}, es decir, el corte
    atraviesa el interior de la red (s→b, c→d, c→f, e→t = 24).
  * Las longitudes de BFS son no decrecientes (3,3,3,5,7) mientras que
    las de DFS oscilan (3,4,3,4,3,4,5,6), lo que exhibe el lema de
    Edmonds-Karp y su violación por la variante DFS en la misma red.

Índices: 1=s, 2=a, 3=b, 4=c, 5=d, 6=e, 7=f, 8=g, 9=t
"""
function red_propia()
    nombres = ["s", "a", "b", "c", "d", "e", "f", "g", "t"]
    pos = [(0.0, 1.5),    # s — peering
           (1.3, 3.0),    # a — enrutador norte
           (1.3, 0.0),    # b — enrutador sur
           (2.6, 2.4),    # c — núcleo norte
           (2.6, 0.6),    # d — núcleo sur
           (3.9, 3.2),    # e — agregador norte
           (3.9, 1.5),    # f — agregador central
           (3.9, 0.0),    # g — agregador sur
           (5.2, 1.5)]    # t — data center
    C = zeros(Int, 9, 9)
    # --- capa 1: salida de la fuente ---
    C[1, 2] = 13   # s → a
    C[1, 3] = 8    # s → b
    C[1, 4] = 6    # s → c   (atajo directo al núcleo)
    # --- capa 2: reparto interno ---
    C[2, 4] = 8    # a → c
    C[2, 6] = 15   # a → e   (ancho de sobra: e→t es el verdadero límite)
    C[3, 5] = 6    # b → d
    C[3, 7] = 13   # b → f
    # --- par antiparalelo c ⇄ d (enlace bidireccional del núcleo) ---
    C[4, 5] = 5    # c → d
    C[5, 4] = 7    # d → c   (antiparalelo)
    # --- capa 3: hacia los agregadores ---
    C[4, 6] = 6    # c → e
    C[4, 7] = 8    # c → f
    C[5, 7] = 3    # d → f
    C[5, 8] = 10   # d → g
    # --- capa 4: entrada al sumidero ---
    C[6, 9] = 3    # e → t   (enlace estrecho: crea el cuello de botella)
    C[7, 9] = 14   # f → t
    C[8, 9] = 7    # g → t
    return RedFlujo(C, nombres, pos), 1, 9
end
