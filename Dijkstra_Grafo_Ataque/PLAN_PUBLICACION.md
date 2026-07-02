# Plan de acción — publicación del trabajo

> Objetivo: llevar el proyecto "Dijkstra & Floyd-Warshall en grafos de ataque
> (SolarWinds / MITRE ATT&CK)" de estado *proyecto docente reproducible* a
> *artículo publicable*.
> Última actualización: 2026-07-01.

---

## 0. Diagnóstico de factibilidad

| Aspecto | Estado |
| --- | --- |
| Reproducibilidad (datos STIX públicos, código propio validado) | ✅ Fortaleza |
| Validación cruzada (Dijkstra = Bellman-Ford = NetworkX; Spearman ρ=0.973) | ✅ Fortaleza |
| Honestidad metodológica (pesos CVE eliminados, desconexión co-ocurrencia reportada) | ✅ Fortaleza |
| Contribución científica clara / novedad | ❌ Bloqueante |
| Revisión de literatura y posicionamiento | ❌ Bloqueante |
| Validación del modelo de peso vs ground-truth externo | ⚠️ Debilidad principal |
| Rigor estadístico (p-values, CI, bootstrap) | ⚠️ Parcial (P3 pendiente) |
| Generalización más allá de 1 caso | ⚠️ Parcial (10 campañas ya calculadas, no destacadas) |

**Veredicto:** publicable con trabajo enfocado. No en su forma actual.

### Metas por nivel

- **Realista (corto plazo, ~2-3 semanas):** conferencia IEEE regional (ANDESCON,
  CLEI, LatinCloud) o revista latinoamericana indexada en Scopus.
- **Ambiciosa (~2-3 meses):** revista Q2-Q3 de seguridad aplicada. Requiere además
  validar el modelo de peso contra fuente externa (lo más incierto).

---

## Fase 1 — Bloqueantes (sin esto no pasa revisión)

### 1.1 Revisión de literatura y posicionamiento
- [ ] Buscar y leer trabajo previo en:
  - [ ] Attack graph generation (MulVAL, TVA, Bayesian attack graphs)
  - [ ] ATT&CK-based risk scoring / threat modeling con grafos
  - [ ] Shortest-path / centralidad aplicados a seguridad de redes
- [ ] Redactar sección `Related Work` (mínimo 15-20 referencias relevantes)
- [ ] Escribir explícitamente **"nuestra contribución vs la de ellos"** — 1 párrafo
- [ ] Elegir el diferenciador central (candidatos):
  - Modelo de peso 100 % derivado de mitigaciones STIX (reproducible, sin CVSS subjetivo)
  - Análisis Monte-Carlo del atacante no-racional
  - Comparación cartesiano vs co-ocurrencia real como hallazgo sobre granularidad de STIX

### 1.2 Reencuadrar la contribución
- [ ] Reescribir abstract + introducción alrededor del diferenciador elegido
- [ ] Mover el análisis multi-campaña (10 campañas) al **cuerpo** del paper,
      no como apéndice — es más novel que el caso SolarWinds solo
- [ ] Enmarcar la tensión cartesiano/co-ocurrencia (69 % cobertura) como **resultado**,
      no como limitación

---

## Fase 2 — Rigor estadístico (P3, ya identificado en ESTADO_PROYECTO)

### 2.1 Significancia estadística
- [ ] Test de permutación / p-value sobre el análisis de sensibilidad ±20 %
- [ ] Bootstrap con intervalos de confianza sobre los rankings de FW-betweenness
- [ ] Reportar estabilidad del ranking (¿el top-5 sobrevive al resampleo?)

### 2.2 Consolidar el Monte-Carlo
- [ ] Desarrollar el análisis del atacante no-racional como sección propia
- [ ] Interpretar el hallazgo "ningún nivel de bias alcanza 95 % dentro de +10 %"
- [ ] Curva robustez-vs-racionalidad como figura principal

### 2.3 Reproducibilidad formal
- [ ] Fijar semillas y documentar la no-determinación de desempates (ya conocida)
- [ ] `requirements.txt` con versiones exactas
- [ ] README de reproducción paso a paso (1 comando → todos los resultados)
- [ ] Considerar liberar el repo con DOI (Zenodo) al momento de enviar

---

## Fase 3 — Validación del modelo (debilidad principal, meta ambiciosa)

### 3.1 Justificar el modelo de peso
- [ ] Argumentar teóricamente por qué "más mitigaciones documentadas = más resistencia"
- [ ] Anticipar y responder la crítica de circularidad
      (MITRE documenta más mitigaciones para técnicas más estudiadas)
- [ ] **O** validar contra ground-truth externo:
  - [ ] ¿Las técnicas de la ruta crítica coinciden con las que informes de
        incidentes reales marcan como difíciles de detectar/mitigar?
  - [ ] Comparar con al menos una fuente independiente (reportes de vendors,
        datasets de detección)

### 3.2 Análisis de sensibilidad al modelo de peso
- [ ] Probar modelos de peso alternativos (mitigaciones vs combinado ya existe)
- [ ] Reportar cuánto cambian las conclusiones según el modelo elegido

---

## Fase 4 — Preparación del manuscrito

- [ ] Convertir borrador Markdown → LaTeX (plantilla del venue elegido)
- [ ] Regenerar todas las figuras a calidad de publicación (vectorial, 300+ dpi)
- [ ] **Decidir números canónicos** (legacy vs P2) con Henry — pendiente registrado
      en ESTADO_PROYECTO §5
- [ ] Redacción en inglés (o español según el venue) revisada
- [ ] Declaración de disponibilidad de datos y código
- [ ] Revisión por pares interna final (checklist del venue)

---

## Orden recomendado de ejecución

1. **Fase 1** primero — sin posicionamiento no importa cuán bueno sea lo demás.
2. **Fase 2** en paralelo — es código, ROI alto, ya está el andamiaje.
3. **Fase 3** solo si se apunta a revista Q2-Q3; para conferencia regional es opcional.
4. **Fase 4** al final.

## Ruta rápida (si el objetivo es conferencia regional en 2-3 semanas)

Fase 1 (1.1 + 1.2) + Fase 2 (2.1 + 2.2) + Fase 4. Saltar Fase 3.

---

## Tareas de mayor ROI que se pueden empezar ya

- [ ] Implementar estadística P3 (permutación + bootstrap CI) — código concreto
- [ ] Reencuadrar el borrador para que las 10 campañas sean el resultado central
- [ ] Escribir `Related Work` con las líneas a citar y el diferenciador

---

*Fuente del diagnóstico: análisis de factibilidad sobre ESTADO_PROYECTO.md §2, §6 (P2/P3).*
