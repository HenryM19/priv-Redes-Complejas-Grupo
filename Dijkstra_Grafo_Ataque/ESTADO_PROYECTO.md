# Estado del Proyecto — Dijkstra en Grafos de Ataque (SolarWinds / MITRE ATT&CK)

> **Última actualización:** 2026-06-30 (post-merge con Henry Maldonado — `6c01246`)
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

**Modelo de pesos vigente:** `w = max(0.05, n_mitigaciones / max_mitigaciones)`.
Más mitigaciones documentadas = más resistencia defensiva = mayor costo para el atacante.
100 % derivado del bundle STIX. **No se usan pesos por CVE/CVSS.**

---

## 3. Estructura del proyecto

```
Dijkstra_Grafo_Ataque/
├── src/
│   ├── dataset_real.py            # Descarga STIX, extrae campaña, construye grafo + pesos
│   ├── analisis_real.py           # Dijkstra propio + Floyd-Warshall + FW-betweenness
│   ├── analisis_cientifico.py     # Validación: BFS/BF/NX, sensibilidad, métricas de red
│   ├── comparacion_campanas.py    # Generalización a 3 campañas ATT&CK
│   ├── recomendaciones_defensivas.py  # Simulación de bloqueo por nodo → Δcosto
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
python -X utf8 src/analisis_real.py            # ruta crítica + betweenness
python -X utf8 src/analisis_cientifico.py      # validación + sensibilidad + métricas
python -X utf8 src/comparacion_campanas.py     # multi-campaña
python -X utf8 src/recomendaciones_defensivas.py  # priorización defensiva
python -X utf8 src/gen_interactive_graph.py    # regenerar grafo HTML
```

> El flag `-X utf8` es necesario en Windows (cp1252) por caracteres Unicode en `print()`.
> El bundle MITRE (~35 MB) se cachea en `data/mitre_attack.json` (gitignored, se descarga solo).

---

## 5. Estado por componente

| Componente | Estado | Nota |
| --- | --- | --- |
| Pipeline core (Dijkstra/FW) | ✅ Completo | Validado vs NetworkX |
| Validación científica | ✅ Completo | BFS/BF/NX, sensibilidad, métricas de red |
| Multi-campaña | ✅ Completo | 3 campañas, discriminación confirmada |
| Recomendaciones defensivas | ✅ Completo | Bloqueo por nodo + Δcosto |
| Slides (13) | ✅ Completo | Sincronizadas con datos vigentes |
| Guía dataset + figuras + grafo interactivo | ✅ Completo | Sincronizados |
| Borrador paper IEEE (Markdown) | ✅ Completo | Listo para conversión a LaTeX |

---

## 6. Trabajo pendiente para publicación

**P1 — antes de submission**
- [ ] Convertir `paper_borrador.md` → LaTeX con template IEEE (Pandoc o manual).
- [ ] Exportar las 4 figuras Canvas a PNG/PDF de alta resolución para el paper.
- [ ] Verificar las 10 referencias (existencia + contenido) — actualmente sin validar.
- [ ] Revisión ciega por 2 compañeros sobre el borrador corregido.

**P2 — mejoras de rigor (trabajo futuro documentado en L1–L6)**
- [ ] Reemplazar aristas inferidas (cartesiano) por datos de co-ocurrencia/secuencia reales.
- [ ] Escalar generalización a 10+ campañas de distintos sectores/actores.
- [ ] Pesos de resistencia más finos (cobertura de fuentes de detección) para reducir empates.
- [ ] Simulación Monte-Carlo de atacante no racional.

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
