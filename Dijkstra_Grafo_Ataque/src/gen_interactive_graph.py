"""
gen_interactive_graph.py — Grafo interactivo navegable (D3.js) del ataque SolarWinds.

Genera diapositivas/grafo-interactivo.html con:
  - Zoom/pan con rueda y drag
  - Hover: muestra nombre, táctica, peso, FW-betweenness
  - Click: fija tooltip
  - Ruta crítica resaltada en rojo
  - Layout por columnas de táctica (kill chain)
  - Sin dependencias externas (D3 desde CDN)

Fuentes: results/real/fw_betweenness_solarwinds.json
         results/real/ruta_critica_solarwinds.json
"""

import json
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
REAL_DIR = ROOT / "results" / "real"
OUT_FILE = ROOT / "diapositivas" / "grafo-interactivo.html"

TACTIC_ORDER = [
    "reconnaissance", "resource-development", "initial-access",
    "execution", "persistence", "privilege-escalation",
    "defense-impairment", "stealth", "credential-access",
    "discovery", "lateral-movement", "collection",
    "command-and-control", "exfiltration",
]

TACTIC_COLORS = {
    "reconnaissance":      "#6366f1",
    "resource-development":"#8b5cf6",
    "initial-access":      "#ff8c42",
    "execution":           "#ffd23f",
    "persistence":         "#ff3b5c",
    "privilege-escalation":"#c084fc",
    "defense-impairment":  "#22d3ee",
    "stealth":             "#5ad1a0",
    "credential-access":   "#f472b6",
    "discovery":           "#3fb6ff",
    "lateral-movement":    "#fb923c",
    "collection":          "#a3e635",
    "command-and-control": "#e879f9",
    "exfiltration":        "#f87171",
    "_entry":              "#5ad1a0",
    "_exit":               "#ff3b5c",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_graph_data(nodes_data, ruta_data):
    critical_nodes = {nd["node"] for nd in ruta_data}
    critical_path  = [nd["node"] for nd in ruta_data]
    critical_edges = set()
    for i in range(len(critical_path) - 1):
        critical_edges.add((critical_path[i], critical_path[i + 1]))

    # Índice por táctica (primera táctica = columna principal)
    by_tactic = {t: [] for t in TACTIC_ORDER}
    for nd in nodes_data:
        for tac in nd.get("tactics", []):
            if tac in by_tactic:
                by_tactic[tac].append(nd["node"])
                break  # solo primera táctica para posición

    # Asignar posiciones x/y
    COL_W = 150  # px por columna
    ROW_H = 60   # px por fila
    pos = {}
    # ATTACKER
    pos["ATTACKER"] = {"x": 0, "y": 0, "col": -1}
    # Técnicas por táctica
    for ti, tac in enumerate(TACTIC_ORDER):
        nodes_in_col = by_tactic[tac]
        k = len(nodes_in_col)
        for j, nid in enumerate(nodes_in_col):
            y = (j - (k - 1) / 2.0) * ROW_H
            pos[nid] = {"x": (ti + 1) * COL_W, "y": y, "col": ti}
    # IMPACT
    pos["IMPACT"] = {"x": (len(TACTIC_ORDER) + 1) * COL_W, "y": 0, "col": len(TACTIC_ORDER)}

    # Nodos
    nodes = []
    # ATTACKER
    nodes.append({
        "id": "ATTACKER",
        "name": "Atacante externo",
        "label": "ATTACKER",
        "weight": 0.0,
        "weight_source": "",
        "tactics": ["entry"],
        "fw_betweenness": 0,
        "in_degree": 0,
        "out_degree": 0,
        "critical": True,
        "color": "#5ad1a0",
        "size": 22,
        "x": pos["ATTACKER"]["x"],
        "y": pos["ATTACKER"]["y"],
    })
    for nd in nodes_data:
        nid = nd["node"]
        tacs = nd.get("tactics", [])
        tac0 = tacs[0] if tacs else "unknown"
        color = TACTIC_COLORS.get(tac0, "#8a97ad")
        is_crit = nid in critical_nodes
        nodes.append({
            "id": nid,
            "name": nd.get("name", ""),
            "label": nid,
            "weight": nd.get("weight", 0.5),
            "weight_source": nd.get("weight_source", ""),
            "tactics": tacs,
            "fw_betweenness": nd.get("fw_betweenness", 0),
            "in_degree": nd.get("in_degree", 0),
            "out_degree": nd.get("out_degree", 0),
            "critical": is_crit,
            "color": "#ff3b5c" if is_crit else color,
            "size": 18 if is_crit else max(7, min(16, 7 + nd.get("fw_betweenness", 0) * 0.006)),
            "x": pos.get(nid, {}).get("x", 0),
            "y": pos.get(nid, {}).get("y", 0),
        })
    # IMPACT
    nodes.append({
        "id": "IMPACT",
        "name": "Impacto logrado",
        "label": "IMPACT",
        "weight": 0.0,
        "weight_source": "",
        "tactics": ["target"],
        "fw_betweenness": 0,
        "in_degree": 0,
        "out_degree": 0,
        "critical": True,
        "color": "#ff3b5c",
        "size": 22,
        "x": pos["IMPACT"]["x"],
        "y": pos["IMPACT"]["y"],
    })

    # Aristas — indice por TODAS las tacticas de cada nodo (no solo la primera),
    # igual que build_attack_graph() en dataset_real.py. Usar solo la primera
    # tactica aqui subrepresenta el grafo real: un nodo con tacticas
    # ["stealth", "persistence", "privilege-escalation", "initial-access"]
    # debe conectar en las 4 columnas, no solo en la primera de su lista.
    node_ids = {n["id"] for n in nodes}
    by_tactic_ids = {t: [] for t in TACTIC_ORDER}
    for nd in nodes_data:
        for tac in nd.get("tactics", []):
            if tac in by_tactic_ids:
                by_tactic_ids[tac].append(nd["node"])

    edges = []
    added = set()

    def add_edge(s, t):
        if s in node_ids and t in node_ids and (s, t) not in added:
            added.add((s, t))
            is_crit = (s, t) in critical_edges
            edges.append({
                "source": s,
                "target": t,
                "critical": is_crit,
                "color": "#ff3b5c" if is_crit else "#1e2a40",
                "width": 3 if is_crit else 0.8,
                "opacity": 0.95 if is_crit else 0.35,
            })

    # ATTACKER → primera táctica
    for tac in ["reconnaissance", "resource-development", "initial-access"]:
        for nid in by_tactic_ids.get(tac, []):
            add_edge("ATTACKER", nid)

    # Última táctica → IMPACT (impact + exfiltration, igual que dataset_real.py)
    for tac in ["impact", "exfiltration"]:
        for nid in by_tactic_ids.get(tac, []):
            add_edge(nid, "IMPACT")

    # Tácticas consecutivas
    for i in range(len(TACTIC_ORDER) - 1):
        for src in by_tactic_ids.get(TACTIC_ORDER[i], []):
            for dst in by_tactic_ids.get(TACTIC_ORDER[i + 1], []):
                add_edge(src, dst)

    return nodes, edges, critical_path


def generate_html(nodes, edges, critical_path, total_cost):
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    critical_json = json.dumps(critical_path, ensure_ascii=False)
    cost_str = f"{total_cost:.3f}"

    tactic_legend = []
    for tac in TACTIC_ORDER:
        color = TACTIC_COLORS.get(tac, "#8a97ad")
        short = tac.replace("-", " ").title()
        tactic_legend.append(f'<div class="leg-item"><span class="dot" style="background:{color}"></span>{short}</div>')
    legend_html = "\n".join(tactic_legend)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Grafo Interactivo — SolarWinds Compromise</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
  :root {{
    --bg:#0d1320; --panel:#121a2b; --panel2:#1a2438; --line:#1e2a40;
    --txt:#e8edf6; --muted:#8a97ad; --crit:#ff3b5c; --high:#ff8c42;
    --cyan:#3fb6ff; --green:#5ad1a0; --amber:#ffd23f; --purple:#c084fc;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; overflow:hidden; background:var(--bg); font-family:'Space Grotesk',sans-serif; color:var(--txt); }}

  /* ── Header ── */
  #header {{
    position:fixed; top:0; left:0; right:0; height:56px; z-index:200;
    background:var(--panel); border-bottom:1px solid var(--line);
    display:flex; align-items:center; padding:0 24px; gap:20px;
  }}
  #header h1 {{ font-size:18px; font-weight:700; letter-spacing:-.01em; }}
  #header h1 .accent {{ color:var(--cyan); }}
  #header .badge {{
    font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
    padding:3px 9px; border-radius:4px; border:1px solid;
  }}
  #header .badge.red {{ border-color:var(--crit); color:var(--crit); background:rgba(255,59,92,.1); }}
  #header .badge.cyan {{ border-color:var(--cyan); color:var(--cyan); background:rgba(63,182,255,.1); }}
  #header .badge.green {{ border-color:var(--green); color:var(--green); background:rgba(90,209,160,.1); }}
  #header .spacer {{ flex:1; }}
  #header .hint {{ font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--muted); }}

  /* ── Controls ── */
  #controls {{
    position:fixed; top:56px; left:0; right:0; height:40px; z-index:199;
    background:rgba(13,19,32,.92); border-bottom:1px solid var(--line);
    display:flex; align-items:center; padding:0 20px; gap:12px;
    backdrop-filter:blur(6px);
  }}
  #controls button {{
    font-family:'JetBrains Mono',monospace; font-size:12px;
    background:var(--panel2); border:1px solid var(--line);
    color:var(--muted); padding:4px 12px; border-radius:5px;
    cursor:pointer; transition:all .15s;
  }}
  #controls button:hover {{ background:var(--line); color:var(--txt); }}
  #controls button.active {{ border-color:var(--cyan); color:var(--cyan); background:rgba(63,182,255,.1); }}
  #controls .sep {{ width:1px; height:20px; background:var(--line); }}
  #controls label {{ font-size:12px; color:var(--muted); }}
  #controls input[type=range] {{ width:100px; accent-color:var(--cyan); cursor:pointer; }}

  /* ── SVG canvas ── */
  #canvas {{
    position:fixed; top:96px; left:0; right:320px; bottom:0;
    overflow:hidden; cursor:grab;
  }}
  #canvas:active {{ cursor:grabbing; }}
  #canvas svg {{ width:100%; height:100%; }}

  /* ── Sidebar ── */
  #sidebar {{
    position:fixed; top:56px; right:0; bottom:0; width:320px;
    background:var(--panel); border-left:1px solid var(--line);
    overflow-y:auto; padding:20px;
    display:flex; flex-direction:column; gap:16px;
  }}

  /* ── Info panel ── */
  #info {{ display:none; }}
  #info.visible {{ display:block; }}
  #info .info-id {{
    font-family:'JetBrains Mono',monospace; font-size:20px; font-weight:700;
    color:var(--cyan); margin-bottom:4px;
  }}
  #info .info-name {{ font-size:16px; font-weight:600; margin-bottom:12px; }}
  .info-row {{
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 0; border-bottom:1px solid var(--line); font-size:13px;
  }}
  .info-row:last-child {{ border-bottom:none; }}
  .info-row .k {{ color:var(--muted); }}
  .info-row .v {{ font-family:'JetBrains Mono',monospace; color:var(--txt); font-weight:600; }}
  .info-row .v.red {{ color:var(--crit); }}
  .info-row .v.green {{ color:var(--green); }}
  .info-row .v.amber {{ color:var(--amber); }}
  .tac-badge {{
    display:inline-block; font-size:11px; padding:2px 7px; border-radius:4px;
    background:rgba(63,182,255,.1); border:1px solid var(--line); color:var(--cyan);
    font-family:'JetBrains Mono',monospace; margin:2px;
  }}

  /* ── Path panel ── */
  #path-panel h3 {{
    font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--muted); margin-bottom:12px;
  }}
  .path-step {{
    display:flex; align-items:center; gap:8px; padding:6px 0;
    border-bottom:1px solid rgba(30,42,64,.6); font-size:13px;
  }}
  .path-step .ps-id {{ font-family:'JetBrains Mono',monospace; color:var(--crit); font-weight:700; min-width:80px; }}
  .path-step .ps-name {{ color:var(--muted); font-size:12px; flex:1; }}
  .path-step .ps-w {{ font-family:'JetBrains Mono',monospace; color:var(--amber); font-size:12px; }}

  /* ── Legend ── */
  #legend h3 {{
    font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--muted); margin-bottom:10px;
  }}
  .leg-item {{
    display:flex; align-items:center; gap:8px; font-size:12px;
    color:var(--muted); margin-bottom:6px;
  }}
  .dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}

  /* ── Tooltip ── */
  #tooltip {{
    position:fixed; z-index:500; pointer-events:none;
    background:var(--panel2); border:1px solid var(--line);
    border-radius:8px; padding:10px 14px;
    font-size:13px; max-width:240px;
    box-shadow:0 8px 32px rgba(0,0,0,.5);
    display:none;
  }}
  #tooltip .t-id {{ font-family:'JetBrains Mono',monospace; font-size:15px; font-weight:700; color:var(--cyan); }}
  #tooltip .t-name {{ color:var(--txt); font-size:13px; margin:3px 0 6px; }}
  #tooltip .t-row {{ display:flex; justify-content:space-between; gap:16px; font-size:12px; color:var(--muted); }}
  #tooltip .t-row span {{ font-family:'JetBrains Mono',monospace; color:var(--amber); }}

  /* ── Placeholder ── */
  #info-placeholder {{ color:var(--muted); font-size:14px; text-align:center; padding:20px 0; }}
</style>
</head>
<body>

<!-- HEADER -->
<div id="header">
  <h1>&#128202; Grafo <span class="accent">Interactivo</span> — SolarWinds Compromise</h1>
  <span class="badge red">71 técnicas reales</span>
  <span class="badge cyan">73 nodos</span>
  <span class="badge green">MITRE ATT&CK</span>
  <div class="spacer"></div>
  <span class="hint">&#128269; Rueda = zoom &nbsp;|&nbsp; Drag = mover &nbsp;|&nbsp; Click nodo = info</span>
</div>

<!-- CONTROLS -->
<div id="controls">
  <button id="btn-reset">&#8635; Reset zoom</button>
  <button id="btn-crit" class="active">Ruta crítica</button>
  <button id="btn-all">Todas aristas</button>
  <div class="sep"></div>
  <label>Opacidad aristas <input type="range" id="edge-opacity" min="5" max="100" value="35"></label>
  <div class="sep"></div>
  <label>Tamaño nodos <input type="range" id="node-size" min="50" max="200" value="100"></label>
</div>

<!-- CANVAS -->
<div id="canvas">
  <svg id="svg">
    <defs>
      <marker id="arrow-crit" markerWidth="8" markerHeight="8" refX="8" refY="3" orient="auto">
        <path d="M0,0 L0,6 L8,3 z" fill="#ff3b5c" opacity="0.9"/>
      </marker>
      <marker id="arrow-norm" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L6,3 z" fill="#1e2a40" opacity="0.6"/>
      </marker>
    </defs>
    <g id="graph-root">
      <g id="layer-edges"></g>
      <g id="layer-nodes"></g>
      <g id="layer-labels"></g>
      <g id="layer-tactic-labels"></g>
    </g>
  </svg>
</div>

<!-- SIDEBAR -->
<div id="sidebar">

  <!-- Info del nodo seleccionado -->
  <div id="info">
    <div class="info-id" id="info-id">—</div>
    <div class="info-name" id="info-name">—</div>
    <div class="info-row"><span class="k">Peso (w)</span><span class="v amber" id="info-weight">—</span></div>
    <div class="info-row"><span class="k">Fuente peso</span><span class="v" id="info-wsrc" style="font-size:11px;text-align:right;max-width:170px">—</span></div>
    <div class="info-row"><span class="k">FW-Betweenness</span><span class="v" id="info-bw">—</span></div>
    <div class="info-row"><span class="k">In-degree</span><span class="v" id="info-in">—</span></div>
    <div class="info-row"><span class="k">Out-degree</span><span class="v" id="info-out">—</span></div>
    <div class="info-row" style="flex-direction:column;align-items:flex-start;gap:6px">
      <span class="k">Tácticas</span>
      <div id="info-tacs"></div>
    </div>
  </div>
  <div id="info-placeholder">&#128199; Click en un nodo para ver detalles</div>

  <!-- Ruta crítica -->
  <div id="path-panel">
    <h3>&#128308; Ruta crítica — Dijkstra (costo={cost_str})</h3>
  </div>

  <!-- Leyenda -->
  <div id="legend">
    <h3>&#127912; Leyenda por táctica</h3>
    {legend_html}
    <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--line)">
      <div class="leg-item"><span style="width:28px;height:3px;background:#ff3b5c;border-radius:2px;display:inline-block"></span>&nbsp;Arista ruta crítica</div>
      <div class="leg-item"><span style="width:28px;height:1px;background:#1e2a40;border-radius:2px;display:inline-block"></span>&nbsp;Arista alternativa</div>
    </div>
  </div>

</div>

<!-- TOOLTIP -->
<div id="tooltip">
  <div class="t-id" id="tt-id"></div>
  <div class="t-name" id="tt-name"></div>
  <div class="t-row"><span>peso</span><span id="tt-w"></span></div>
  <div class="t-row"><span>FW-betw.</span><span id="tt-bw"></span></div>
</div>

<script>
const NODES = {nodes_json};
const EDGES = {edges_json};
const CRITICAL_PATH = {critical_json};

// ── Ruta crítica en sidebar ──────────────────────────────────────────────────
const pathPanel = document.getElementById('path-panel');
// Buscar datos de ruta de nodes
const nodeIndex = {{}};
NODES.forEach(n => nodeIndex[n.id] = n);

CRITICAL_PATH.forEach((nid, i) => {{
  const nd = nodeIndex[nid];
  if (!nd) return;
  const div = document.createElement('div');
  div.className = 'path-step';
  const distAcum = nd.id === 'ATTACKER' ? '0.000' :
                   nd.id === 'IMPACT'   ? '{cost_str}' : '';
  div.innerHTML = `
    <span class="ps-id">${{nd.label || nd.id}}</span>
    <span class="ps-name">${{nd.name}}</span>
    <span class="ps-w">w=${{nd.weight.toFixed(3)}}</span>
  `;
  pathPanel.appendChild(div);
}});

// ── D3 Setup ─────────────────────────────────────────────────────────────────
const svg    = d3.select('#svg');
const root   = d3.select('#graph-root');
const eLayer = d3.select('#layer-edges');
const nLayer = d3.select('#layer-nodes');
const lLayer = d3.select('#layer-labels');
const tLayer = d3.select('#layer-tactic-labels');

// Zoom
const zoom = d3.zoom()
  .scaleExtent([0.05, 6])
  .on('zoom', (e) => root.attr('transform', e.transform));
svg.call(zoom);

// ── Dibujar aristas ───────────────────────────────────────────────────────────
let showAllEdges = false;

function getEdges() {{
  return showAllEdges ? EDGES : EDGES.filter(e => e.critical);
}}

// Líneas
const line = eLayer.selectAll('line')
  .data(EDGES)
  .join('line')
  .attr('x1', e => nodeIndex[e.source]?.x ?? 0)
  .attr('y1', e => nodeIndex[e.source]?.y ?? 0)
  .attr('x2', d => {{
    const src = nodeIndex[d.source];
    const tgt = nodeIndex[d.target];
    if (!src || !tgt) return 0;
    const dx = tgt.x - src.x, dy = tgt.y - src.y;
    const len = Math.sqrt(dx*dx + dy*dy) || 1;
    const r = (tgt.size || 10) + 3;
    return tgt.x - dx/len*r;
  }})
  .attr('y2', d => {{
    const src = nodeIndex[d.source];
    const tgt = nodeIndex[d.target];
    if (!src || !tgt) return 0;
    const dx = tgt.x - src.x, dy = tgt.y - src.y;
    const len = Math.sqrt(dx*dx + dy*dy) || 1;
    const r = (tgt.size || 10) + 3;
    return tgt.y - dy/len*r;
  }})
  .attr('stroke', e => e.color)
  .attr('stroke-width', e => e.width)
  .attr('stroke-opacity', e => e.critical ? e.opacity : 0.35)
  .attr('marker-end', e => e.critical ? 'url(#arrow-crit)' : 'url(#arrow-norm)')
  .style('display', e => (showAllEdges || e.critical) ? null : 'none');

// ── Dibujar nodos ─────────────────────────────────────────────────────────────
let sizeMultiplier = 1.0;

const circle = nLayer.selectAll('circle')
  .data(NODES)
  .join('circle')
  .attr('cx', d => d.x)
  .attr('cy', d => d.y)
  .attr('r', d => d.size * sizeMultiplier)
  .attr('fill', d => d.color)
  .attr('fill-opacity', d => d.critical ? 0.95 : 0.7)
  .attr('stroke', d => d.critical ? '#ffffff' : 'none')
  .attr('stroke-width', d => d.critical ? 1.5 : 0)
  .style('cursor', 'pointer')
  .on('mouseover', showTooltip)
  .on('mousemove', moveTooltip)
  .on('mouseout', hideTooltip)
  .on('click', selectNode);

// ── Labels ────────────────────────────────────────────────────────────────────
const critSet = new Set(CRITICAL_PATH);

const label = lLayer.selectAll('text')
  .data(NODES.filter(n => critSet.has(n.id) || n.id === 'ATTACKER' || n.id === 'IMPACT'))
  .join('text')
  .attr('x', d => d.x)
  .attr('y', d => d.y - d.size * sizeMultiplier - 4)
  .attr('text-anchor', 'middle')
  .attr('font-family', 'JetBrains Mono, monospace')
  .attr('font-size', 11)
  .attr('font-weight', 'bold')
  .attr('fill', '#e8edf6')
  .text(d => d.label);

// ── Etiquetas de táctica (fila superior) ─────────────────────────────────────
const TACTIC_ORDER = {json.dumps(TACTIC_ORDER)};
const TACTIC_COLORS_JS = {json.dumps(TACTIC_COLORS)};
const COL_W = 150;

// Calcular y_min para posicionar labels arriba
const yVals = NODES.map(n => n.y);
const yMin = Math.min(...yVals) - 60;

TACTIC_ORDER.forEach((tac, i) => {{
  const x = (i + 1) * COL_W;
  const color = TACTIC_COLORS_JS[tac] || '#8a97ad';
  const short = tac.replace(/-/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());

  // Línea vertical de columna
  tLayer.append('line')
    .attr('x1', x - COL_W/2 + 8).attr('y1', yMin)
    .attr('x2', x - COL_W/2 + 8).attr('y2', -yMin)
    .attr('stroke', color).attr('stroke-width', 0.3)
    .attr('stroke-opacity', 0.3).attr('stroke-dasharray', '4,6');

  // Label táctica
  tLayer.append('text')
    .attr('x', x).attr('y', yMin)
    .attr('text-anchor', 'middle')
    .attr('font-family', 'JetBrains Mono, monospace')
    .attr('font-size', 10)
    .attr('fill', color)
    .text(short);
}});

// ── Fit inicial ───────────────────────────────────────────────────────────────
function fitGraph() {{
  const canvas = document.getElementById('canvas');
  const cw = canvas.clientWidth;
  const ch = canvas.clientHeight;

  const xs = NODES.map(n => n.x);
  const ys = NODES.map(n => n.y);
  const x0 = Math.min(...xs) - 60;
  const y0 = Math.min(...ys) - 80;
  const x1 = Math.max(...xs) + 60;
  const y1 = Math.max(...ys) + 60;
  const gw = x1 - x0, gh = y1 - y0;

  const scale = Math.min(cw / gw, ch / gh) * 0.92;
  const tx = (cw - gw * scale) / 2 - x0 * scale;
  const ty = (ch - gh * scale) / 2 - y0 * scale;

  svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
}}
fitGraph();

// ── Tooltip ───────────────────────────────────────────────────────────────────
const tooltip = document.getElementById('tooltip');

function showTooltip(event, d) {{
  document.getElementById('tt-id').textContent = d.label;
  document.getElementById('tt-name').textContent = d.name;
  document.getElementById('tt-w').textContent = d.weight.toFixed(3);
  document.getElementById('tt-bw').textContent = d.fw_betweenness;
  tooltip.style.display = 'block';
  moveTooltip(event);
}}
function moveTooltip(event) {{
  tooltip.style.left = (event.clientX + 16) + 'px';
  tooltip.style.top  = (event.clientY - 10) + 'px';
}}
function hideTooltip() {{
  tooltip.style.display = 'none';
}}

// ── Seleccionar nodo → sidebar ─────────────────────────────────────────────────
let selectedId = null;

function selectNode(event, d) {{
  event.stopPropagation();
  selectedId = d.id;

  // Highlight
  circle.attr('stroke', n => n.id === d.id ? '#ffffff' : (n.critical ? '#ffffff' : 'none'))
        .attr('stroke-width', n => n.id === d.id ? 2.5 : (n.critical ? 1.5 : 0))
        .attr('fill-opacity', n => n.id === d.id ? 1.0 : (n.critical ? 0.95 : 0.5));

  // Sidebar info
  document.getElementById('info').classList.add('visible');
  document.getElementById('info-placeholder').style.display = 'none';
  document.getElementById('info-id').textContent = d.label;
  document.getElementById('info-name').textContent = d.name;
  document.getElementById('info-weight').textContent = d.weight.toFixed(3);
  document.getElementById('info-wsrc').textContent = d.weight_source || '—';
  document.getElementById('info-bw').textContent = d.fw_betweenness;
  document.getElementById('info-in').textContent = d.in_degree;
  document.getElementById('info-out').textContent = d.out_degree;

  const tacsDiv = document.getElementById('info-tacs');
  tacsDiv.innerHTML = d.tactics.map(t =>
    `<span class="tac-badge">${{t}}</span>`
  ).join('');
}}

svg.on('click', () => {{
  selectedId = null;
  circle.attr('stroke', d => d.critical ? '#ffffff' : 'none')
        .attr('stroke-width', d => d.critical ? 1.5 : 0)
        .attr('fill-opacity', d => d.critical ? 0.95 : 0.7);
  document.getElementById('info').classList.remove('visible');
  document.getElementById('info-placeholder').style.display = 'block';
}});

// ── Controles ─────────────────────────────────────────────────────────────────
document.getElementById('btn-reset').addEventListener('click', () => fitGraph());

document.getElementById('btn-crit').addEventListener('click', function() {{
  showAllEdges = false;
  line.style('display', e => e.critical ? null : 'none');
  this.classList.add('active');
  document.getElementById('btn-all').classList.remove('active');
}});

document.getElementById('btn-all').addEventListener('click', function() {{
  showAllEdges = true;
  line.style('display', null);
  this.classList.add('active');
  document.getElementById('btn-crit').classList.remove('active');
}});

document.getElementById('edge-opacity').addEventListener('input', function() {{
  const val = this.value / 100;
  line.attr('stroke-opacity', e => e.critical ? Math.max(0.8, val) : val);
}});

document.getElementById('node-size').addEventListener('input', function() {{
  sizeMultiplier = this.value / 100;
  circle.attr('r', d => d.size * sizeMultiplier);
  label.attr('y', d => d.y - d.size * sizeMultiplier - 4);
}});

// Resize
window.addEventListener('resize', fitGraph);
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    print("Cargando datos...")
    nodes_data = load_json(REAL_DIR / "fw_betweenness_solarwinds.json")
    ruta_data  = load_json(REAL_DIR / "ruta_critica_solarwinds.json")

    print(f"  Técnicas: {len(nodes_data)}")
    print(f"  Pasos ruta crítica: {len(ruta_data)}")

    print("Construyendo datos del grafo...")
    nodes, edges, critical_path = build_graph_data(nodes_data, ruta_data)
    total_cost = round(sum(step.get("weight", 0) for step in ruta_data), 3)
    print(f"  Nodos: {len(nodes)}")
    print(f"  Aristas: {len(edges)}")
    print(f"  Aristas críticas: {sum(1 for e in edges if e['critical'])}")
    print(f"  Costo ruta crítica: {total_cost}")

    print("Generando HTML interactivo...")
    html = generate_html(nodes, edges, critical_path, total_cost)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  Guardado en: {OUT_FILE}")
    print("  Abrir en navegador para ver el grafo interactivo.")
