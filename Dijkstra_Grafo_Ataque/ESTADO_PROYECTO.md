# Estado del Proyecto — Dijkstra en Grafos de Ataque (SolarWinds / MITRE ATT&CK)

> **Última actualización:** 2026-07-01 (rigor P2: co-ocurrencia real, 10 campañas, pesos combinados, Monte-Carlo)
> **Autores:** Jean Carlo Aucapina · Henry Maldonado — DEET, Universidad de Cuenca
> **Repositorio:** `priv-Redes-Complejas-Grupo/Dijkstra_Grafo_Ataque`

---

## 1. Resumen ejecutivo

Modelado de la campaña **SolarWinds Compromise (APT29, 2019–2020)** como grafo dirigido
ponderado a partir de datos reales de **MITRE ATT&CK Enterprise STIX 2.1**. Se aplican
Dijkstra (ruta de menor resistencia) y Floyd-Warshall (betweenness / cuellos de botella)
con implementaciones propias validadas contra NetworkX.

**Estado actual:** pipeline funcional y reproducible, presentación HTML completa (13 slides
+ guía + figuras + grafo interactivo), borrador de paper IEEE. Tras revisión por pares
interna se corrigió el modelo de pesos (eliminación de pesos CVE erróneos) y se re-generó
todo el material.

---

## 2. Resultados principales (datos vigentes)

| Métrica | Valor |
|---|---|
| Nodos / Aristas | 73 / 653 |
| **Ruta crítica (costo)** | **1.535** |
| Ruta crítica (técnicas) | T1078.003 → T1606.001 → T1016.001 → T1550.004 → T1074.002 → T1665 → T1048.002 |
| **Top betweenness** | **T1606.001 (Web Cookies, 1044 rutas)** |
| Validación | Dijkstra = Bellman-Ford = NetworkX = 1.535 ✓ |
| BFS sin pesos | 2.925 (+90.6 % sobre óptimo) |
| Spearman ρ (FW vs NetworkX) | 0.973 |
| Sensibilidad ±20 % | Jaccard = 1.0 (ruta idéntica) |
| Sensibilidad binaria | ruta cambia (límite de robustez reportado) |
| Bloqueo defensivo total | T1048.002 (único punto de falla del atacante) |
| Top controles defensivos | T1550.004 (+16.3 %), T1606.001 (+8.1 %) |
| Multi-campaña (Jaccard) | 0.0–0.1 entre SolarWinds / Wocao / Dream Job |
| Táctica común a las 3 campañas | **stealth** |

**Modelo de pesos vigente (canónico, sin cambios):** `w = max(0.05, n_mitigaciones / max_mitigaciones)`.
Más mitigaciones documentadas = más resistencia defensiva = mayor costo para el atacante.
100 % derivado del bundle STIX. **No se usan pesos por CVE/CVSS.**

### 2.1 Resultados nuevos — rigor P2 (2026-07-01, no reemplazan la tabla anterior)

Estos resultados se generaron con los nuevos modos `edge_mode`/`weight_mode`
(ver Sección 8). Los números de la Sección 2 siguen siendo los canónicos
citados en slides/paper hasta una revisión conjunta con Henry.

| Métrica | Valor |
| --- | --- |
| Cobertura co-ocurrencia real vs cartesiano (SolarWinds) | 69.0 % de los pares (472/653 aristas) |
| Alcanzabilidad ATTACKER→IMPACT en modo co-ocurrencia | SolarWinds: **NO** alcanzable (29 técnicas aisladas); 1/3 campañas legacy sí alcanzable |
| Empates de peso: solo-mitigaciones vs combinado | 70/71 → 63/71 técnicas empatadas (−10 % empates, 9→24 valores únicos) |
| Ruta crítica combinada vs solo-mitigaciones | Distinta (Jaccard 0.556); costo 1.535 → 2.91 |
| Top betweenness combinado | T1003.006 (DCSync) — cambia desde T1606.001 |
| Escalado a 10 campañas (auto-selección, min 10 técnicas) | 5/10 alcanzables; Jaccard medio 0.037 (min 0, max 0.133) |
| Monte-Carlo (atacante no racional, 10 000 trials/nivel) | ratio costo medio/óptimo: 3.30× (aleatorio) → 1.17× (bias_power=10); ningún nivel evaluado alcanza 95 % de trials dentro de +10 % del óptimo |

**Hallazgo clave:** la cobertura de co-ocurrencia real (66-69 %) confirma que
el modelo cartesiano SÍ sobreestima el espacio de ataque — pero también que
el bundle STIX no tiene granularidad suficiente para reconstruir una secuencia
100 % observada sin perder conectividad. Ambos modos quedan documentados y
disponibles para comparación honesta (`comparacion_modos_aristas.json`).

---

## 3. Estructura del proyecto

```
Dijkstra_Grafo_Ataque/
├── src/
│   ├── dataset_real.py            # Descarga STIX, extrae campaña, construye grafo + pesos
│   ├── analisis_real.py           # Dijkstra propio + Floyd-Warshall + FW-betweenness
│   ├── analisis_cientifico.py     # Validación: BFS/BF/NX, sensibilidad, métricas de red
│   ├── comparacion_campanas.py    # Generalización: --legacy3 (3 campañas) o --n (auto-seleccionadas)
│   ├── recomendaciones_defensivas.py  # Simulación de bloqueo por nodo → Δcosto
│   ├── dataset_edges_comparacion.py   # Comparación honesta cartesiano vs co-ocurrencia real
│   ├── analisis_pesos_finos.py    # Comparación pesos solo-mitigaciones vs combinado (mit+deteccion)
│   ├── monte_carlo_atacante.py    # Simulación de atacante no racional (random walk ponderado)
│   ├── gen_interactive_graph.py   # Genera diapositivas/grafo-interactivo.html (D3.js)
│   ├── nvd_fetch.py / attack_graph.py / dijkstra.py / run_pipeline.py  # Análisis sintético (1ra parte)
│   └── animate.py / gen_graph_img.py / gen_full_graph.py  # Figuras/animaciones
├── results/real/                  # JSON de resultados (regenerables con el pipeline)
├── diapositivas/
│   ├── index.html                 # Deck principal (13 slides)
│   ├── slides/01..13-*.html        # Slides individuales
│   ├── guia-dataset.html          # Guía didáctica del dataset + limitaciones
│   ├── figuras-cientificas.html   # 4 figuras Canvas para publicación
│   └── grafo-interactivo.html     # Grafo navegable (generado)
├── paper_borrador.md              # Borrador paper IEEE (Abstract → Conclusión → Referencias)
├── EXPLICACION.md / RESULTADOS.md / README.md  # Documentación
└── data/                          # Cache STIX ~35 MB (gitignored)
```

---

## 4. Cómo reproducir

```bash
# venv ya configurado en la raíz JULIA (.venv)
python -X utf8 src/analisis_real.py            # ruta crítica + betweenness (cartesiano/mitigaciones)
python -X utf8 src/analisis_cientifico.py      # validación + sensibilidad + métricas
python -X utf8 src/comparacion_campanas.py --legacy3   # 3 campañas legacy (numeros canonicos)
python -X utf8 src/comparacion_campanas.py --n 10      # 10 campañas auto-seleccionadas
python -X utf8 src/recomendaciones_defensivas.py  # priorización defensiva
python -X utf8 src/gen_interactive_graph.py    # regenerar grafo HTML

# Rigor P2 (nuevos, opt-in — no alteran los resultados canonicos de arriba)
python -X utf8 src/dataset_edges_comparacion.py   # cartesiano vs co-ocurrencia real
python -X utf8 src/analisis_pesos_finos.py        # solo-mitigaciones vs combinado (mit+deteccion)
python -X utf8 src/monte_carlo_atacante.py        # atacante no racional (Monte-Carlo)
# --edge-mode {cartesian,cooccurrence} y --weight-mode {mitigations,combined}
# disponibles en analisis_real.py, comparacion_campanas.py (via build_attack_graph),
# recomendaciones_defensivas.py, analisis_cientifico.py y monte_carlo_atacante.py.
```

> El flag `-X utf8` es necesario en Windows (cp1252) por caracteres Unicode en `print()`.
> El bundle MITRE (~35 MB) se cachea en `data/mitre_attack.json` (gitignored, se descarga solo).

---

## 5. Estado por componente

| Componente | Estado | Nota |
| --- | --- | --- |
| Pipeline core (Dijkstra/FW) | ✅ Completo | Validado vs NetworkX |
| Validación científica | ✅ Completo | BFS/BF/NX, sensibilidad, métricas de red |
| Multi-campaña | ✅ Completo | 3 campañas legacy + 10 auto-seleccionadas (`--legacy3` / `--n`) |
| Recomendaciones defensivas | ✅ Completo | Bloqueo por nodo + Δcosto |
| Aristas de co-ocurrencia real | ✅ Completo | `edge_mode="cooccurrence"`, comparación honesta vs cartesiano |
| Pesos combinados (mitigación+detección) | ✅ Completo | `weight_mode="combined"`, reduce empates 70→63/71 |
| Monte-Carlo atacante no racional | ✅ Completo | `monte_carlo_atacante.py`, sweep de bias_power |
| Slides (13) | ✅ Completo (numeros legacy) | Aun no reflejan resultados P2 — pendiente decision conjunta |
| Guía dataset + figuras + grafo interactivo | ✅ Completo (numeros legacy) | Aun no reflejan resultados P2 |
| Borrador paper IEEE (Markdown) | ✅ Completo (numeros legacy) | Listo para conversión a LaTeX; aun no reflejan resultados P2 |

---

## 6. Trabajo pendiente para publicación

**P1 — antes de submission**
- [ ] Convertir `paper_borrador.md` → LaTeX con template IEEE (Pandoc o manual).
- [ ] Exportar las 4 figuras Canvas a PNG/PDF de alta resolución para el paper.
- [ ] Verificar las 10 referencias (existencia + contenido) — actualmente sin validar.
- [ ] Revisión ciega por 2 compañeros sobre el borrador corregido.

**P2 — mejoras de rigor (implementadas 2026-07-01, ver Sección 2.1 y 8)**
- [x] Reemplazar aristas inferidas (cartesiano) por datos de co-ocurrencia/secuencia reales.
      → `dataset_real.py` (`build_cooccurrence_edges`, `edge_mode="cooccurrence"`),
      `dataset_edges_comparacion.py`. Resuelve L1 parcialmente: co-ocurrencia real
      disponible, pero deja campañas desconectadas por huecos del bundle STIX —
      documentado como hallazgo, no oculto.
- [x] Escalar generalización a 10+ campañas de distintos sectores/actores.
      → `dataset_real.py` (`list_eligible_campaigns`), `comparacion_campanas.py`
      (`select_campaigns`, `--n`/`--min-techniques`, `--legacy3` para reproducir
      las 3 originales). Resuelve L5.
- [x] Pesos de resistencia más finos (cobertura de fuentes de detección) para reducir empates.
      → `dataset_real.py` (`build_detection_index`, `compute_weight_v2`,
      `weight_mode="combined"`), `analisis_pesos_finos.py`. Reduce empates 70→63/71
      técnicas. Resuelve L4.
- [x] Simulación Monte-Carlo de atacante no racional.
      → `monte_carlo_atacante.py` (`weighted_random_walk`, `sweep_bias_power`).
      Cuantifica L2: ratio costo medio/óptimo va de 3.30× (atacante aleatorio) a
      1.17× (atacante casi-racional), sin alcanzar el umbral de robustez 95%/+10%
      en ningún nivel evaluado.

Todos los scripts anteriores mantienen su comportamiento original por defecto
(`edge_mode="cartesian"`, `weight_mode="mitigations"`); los nuevos modos son
opt-in vía flags `--edge-mode`/`--weight-mode`, verificado sin regresión
(costos de ruta crítica idénticos con flags por defecto).

**P3 — pendiente, no implementado en este pase**
- [ ] Integración CAPEC (severidad STIX-nativa como 3ra señal de peso) — requiere
      pipeline de descarga/cache propio, solo 36 refs directos en el bundle Enterprise.
- [ ] Test de permutación (p-value) sobre la sensibilidad ±20%.
- [ ] Intervalos de confianza bootstrap sobre el ranking de FW-betweenness.
- [ ] Validación cruzada leave-one-campaign-out de alpha/beta del modelo combinado.
- [ ] Decisión conjunta (Jean/Henry) sobre qué números pasan a ser canónicos en
      slides/paper/grafo interactivo — actualmente sin tocar, ver Sección 2.1.

**Venue objetivo:** IEEE Access (más accesible) o Computers & Security (Elsevier, mayor impacto).

---

## 7. Historial de correcciones (revisión por pares interna)

| Commit | Autor | Cambio |
| --- | --- | --- |
| `aba4cb5` | Jean Carlo | Eliminación de pesos CVE/CVSS (mapeos incorrectos); inversión semántica `w = n_mit/max_mit`; re-run pipeline completo → nuevos JSON |
| `fe5e12c` | Jean Carlo | Borrador paper IEEE completo con números corregidos |
| `35053e5` | Jean Carlo | Slides 4–13, grafo interactivo y figuras sincronizados con datos del pipeline |
| `6c01246` | **Henry Maldonado** | Corrección independiente de figuras-cientificas y guia-dataset (1.635→1.535, betweenness, sensibilidad binaria); corrección títulos gen_graph_img/gen_full_graph |
| `161ab7a` | Jean Carlo | Merge de ambas correcciones vía rebase; EXPLICACION.md + ESTADO_PROYECTO.md; conflicto resuelto a favor de `+90.6%` BFS (verificado con JSON: BFS=2.925, óptimo=1.535) |

**Nota de conflicto resuelto:** Henry calculó `+149%` BFS (basado en costo 3.875 de versión anterior). El JSON del pipeline corregido registra BFS=2.925 → sobrecoste=90.55 %. Se conservó el valor verificado.

---

## 8. Decisiones de diseño importantes (registro)

1. **Eliminación de pesos CVE/CVSS** (revisión por pares): el mapeo CVE↔técnica era
   no reproducible y técnicamente incorrecto (p.ej. CVE-2020-10148 = auth-bypass del API
   de Orion → T1190/T1195.002, no PowerShell/C2). Pesos ahora 100 % de mitigaciones STIX.
2. **Semántica de peso invertida** a `w = n_mit/max_mit`: más mitigaciones = más caro
   (antes, contraintuitivamente, más mitigaciones daba camino más barato).
3. **Grafo cartesiano entre tácticas** mantenido como modelo *worst-case* ("espacio de
   ataque posible"), documentado abiertamente como limitación L1.
4. **Sensibilidad honesta:** se reporta que la ruta es invariante a escalado ±20 % pero
   sensible a un esquema de peso binario grueso — límite de robustez explícito.
5. **Co-ocurrencia real como modo alternativo, no reemplazo** (2026-07-01): en vez de
   sustituir el grafo cartesiano, se añadió `edge_mode="cooccurrence"` como opción
   explícita. Motivo: verificado que solo 47/71 (66 %) de las técnicas de SolarWinds
   tienen algún actor (malware/tool/intrusion-set) real que las conecte con la técnica
   siguiente documentada en el bundle STIX — sustituir habría dejado el grafo
   desconectado en la mayoría de campañas evaluadas (solo 1/3 legacy y 5/10 del set
   de 10 campañas quedan alcanzables ATTACKER→IMPACT en este modo). Se prefirió reportar
   la desconexión como hallazgo (`comparacion_modos_aristas.json`) en vez de rellenar
   silenciosamente con aristas cartesianas, para no repetir el problema de dato no
   trazable que motivó eliminar los pesos CVE (ver decisión 1).
6. **Selección de campañas por umbral único, no lista curada**: `list_eligible_campaigns`
   usa solo `min_techniques` (parametrizable) como criterio. Ningún nombre de campaña
   se eligió a mano para el set de 10 — mismo principio que llevó a eliminar el mapeo
   CVE manual.
7. **Peso combinado pondera mitigación 60 % / detección 40 %** (`compute_weight_v2`):
   mitigar es una barrera ex-ante más fuerte que solo detectar (que requiere respuesta
   humana/SOC posterior), pero ambas son señales STIX reales (`mitigates` y `detects`)
   y se combinan en vez de descartar una. Los pesos alpha/beta quedan expuestos como
   parámetros explícitos, no constantes ocultas, para facilitar auditoría/ajuste futuro.
8. **Monte-Carlo no reemplaza Dijkstra, lo contextualiza**: la simulación de atacante
   no racional usa los mismos pesos ya presentes en el grafo (ninguna fuente de datos
   nueva) y responde una pregunta distinta ("¿qué tan frágil es la ventaja del atacante
   óptimo?") sin alterar la ruta crítica reportada como resultado principal.
