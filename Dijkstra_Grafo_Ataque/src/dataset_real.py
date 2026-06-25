"""
dataset_real.py — Caso de estudio: SolarWinds Compromise (ATT&CK Campaign G0118)

Pregunta de investigacion:
  En la campana SolarWinds Compromise (2019-2020), documentada por MITRE ATT&CK,
  ¿cual es la secuencia de tecnicas de menor resistencia desde el acceso inicial
  hasta el impacto, segun Dijkstra?
  ¿Y que tecnicas son cuellos de botella universales segun Floyd-Warshall?

Dataset:
  MITRE ATT&CK Enterprise STIX 2.1 (enterprise-attack.json)
  URL: https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json

Modelo de grafo (100% datos reales):
  NODOS  = tecnicas ATT&CK usadas en SolarWinds Compromise
           (relaciones "campaign uses attack-pattern" del bundle STIX)

  ARISTAS = conexiones entre tecnicas de tacticas consecutivas
            DENTRO de la misma campana (no toda ATT&CK).
            Solo existen aristas entre tecnicas que SolarWinds realmente uso.

  PESO   = costo (resistencia defensiva) calculado desde datos ATT&CK:
           w = max(0.05, n_mitigaciones / max_mitigaciones_campana)
           donde n_mitigaciones = numero de mitigaciones documentadas en ATT&CK
           para esa tecnica (relaciones 'mitigates' en bundle STIX).
           - Mas mitigaciones documentadas = mas controles de defensa disponibles
             = tecnica mas costosa de ejecutar para el atacante = w ALTO.
           - 0 mitigaciones = sin contramedidas documentadas = camino barato
             = w=0.05 (minimo, tecnica de baja resistencia).

           Interpretacion: el peso es la resistencia defensiva de la tecnica.
           Dijkstra encuentra la ruta de MENOR resistencia: la secuencia de
           tecnicas con menos controles documentados, es decir, el camino que
           un atacante racional preferiria por enfrentar menos defensas.

           Pesos derivados 100% del bundle STIX 2.1. No se usan CVE/CVSS:
           la asociacion CVE<->tecnica para una campana no esta en ATT&CK y
           requiere juicio manual no reproducible (ver Limitacion L6).

Kill chain (orden tactico ATT&CK):
  reconnaissance -> resource-development -> initial-access -> execution ->
  persistence -> privilege-escalation -> defense-impairment -> stealth ->
  credential-access -> discovery -> lateral-movement -> collection ->
  command-and-control -> exfiltration -> impact
"""

import json
import urllib.request
from pathlib import Path

MITRE_URL = (
    "https://raw.githubusercontent.com/mitre/cti/master/"
    "enterprise-attack/enterprise-attack.json"
)
CACHE_PATH = Path("data/mitre_attack.json")

# Campana objetivo: SolarWinds Compromise
TARGET_CAMPAIGN_NAME = "SolarWinds Compromise"

TACTIC_ORDER = [
    "reconnaissance",
    "resource-development",
    "initial-access",
    "execution",
    "persistence",
    "privilege-escalation",
    "defense-impairment",
    "stealth",
    "credential-access",
    "discovery",
    "lateral-movement",
    "collection",
    "command-and-control",
    "exfiltration",
    "impact",
]

ENTRY_NODE = "ATTACKER"
TARGET_NODE = "IMPACT"

# NOTA: el modelo NO usa pesos basados en CVE/CVSS. La version previa mapeaba
# CVEs a tecnicas manualmente, pero ese mapeo (a) no es reproducible desde el
# bundle STIX y (b) contenia asociaciones CVE<->tecnica incorrectas
# (p.ej. CVE-2020-10148 es un auth-bypass del API de Orion -> T1190/T1195.002,
# no PowerShell ni C2). Todos los pesos derivan ahora solo de mitigaciones
# documentadas en ATT&CK (relaciones 'mitigates'). Ver Limitacion L6.


# ── Descarga ─────────────────────────────────────────────────────────────────

def download_mitre(force: bool = False) -> dict:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists() and not force:
        size_kb = CACHE_PATH.stat().st_size // 1024
        print(f"  [MITRE] Cache local: {CACHE_PATH} ({size_kb} KB)")
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)

    print(f"  [MITRE] Descargando ATT&CK Enterprise desde GitHub (~40 MB)...")
    req = urllib.request.Request(MITRE_URL, headers={"User-Agent": "AttackGraphDijkstra/2.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"  [MITRE] Guardado en {CACHE_PATH}")
    return data


# ── Extraccion de campana ─────────────────────────────────────────────────────

def extract_campaign(bundle: dict, campaign_name: str) -> tuple[dict, list]:
    """
    Extrae la campana y lista de tecnicas que uso.
    Retorna (campaign_obj, lista_de_attack_patterns).
    """
    objects = bundle["objects"]
    id_map = {o["id"]: o for o in objects}

    # Encontrar la campana
    campaign = next(
        (o for o in objects
         if o.get("type") == "campaign"
         and o.get("name", "").lower() == campaign_name.lower()),
        None,
    )
    if campaign is None:
        available = [o.get("name") for o in objects if o.get("type") == "campaign"]
        raise ValueError(f"Campana '{campaign_name}' no encontrada. Disponibles: {available}")

    print(f"  [CAMPAIGN] Encontrada: {campaign['name']}")
    print(f"             ID STIX: {campaign['id']}")
    created = campaign.get("created", "?")[:10]
    modified = campaign.get("modified", "?")[:10]
    print(f"             Periodo documentado: {created} -> {modified}")

    # Todas las relaciones "campaign uses attack-pattern"
    tech_ids = set()
    for o in objects:
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "uses"
                and o.get("source_ref") == campaign["id"]
                and o.get("target_ref", "").startswith("attack-pattern--")):
            tech_ids.add(o["target_ref"])

    # Resolver tecnicas, excluir revocadas/deprecadas
    techniques = []
    for tid in tech_ids:
        t = id_map.get(tid)
        if t and not t.get("revoked") and not t.get("x_mitre_deprecated"):
            techniques.append(t)

    print(f"  [CAMPAIGN] Tecnicas documentadas: {len(techniques)}")
    return campaign, techniques


# ── Indice de mitigaciones (precalculado del bundle) ─────────────────────────

def build_mitigation_index(bundle: dict) -> dict:
    """
    Cuenta mitigaciones por tecnica (relaciones 'mitigates' en ATT&CK).
    Retorna dict: stix_id -> n_mitigaciones (dato 100% real del bundle STIX).
    """
    from collections import defaultdict
    count = defaultdict(int)
    for o in bundle.get("objects", []):
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "mitigates"
                and o.get("target_ref", "").startswith("attack-pattern--")):
            count[o["target_ref"]] += 1
    return dict(count)


# ── Calculo de peso REAL ─────────────────────────────────────────────────────

def compute_weight(technique: dict, n_mitigations: int, max_mitigations: int) -> tuple[float, str]:
    """
    Peso de arista = resistencia defensiva de la tecnica de destino.

    Formula (datos ATT&CK reales, derivados 100% del bundle STIX):
      w = max(0.05, n_mitigaciones / max_mitigaciones_en_campana)
      - Mas mitigaciones documentadas = mas controles de defensa = w ALTO
        = tecnica mas costosa/dificil para el atacante.
      - 0 mitigaciones = sin contramedidas = w=0.05 (camino de minima resistencia).

    Dijkstra sobre estos pesos encuentra la ruta de MENOR resistencia
    defensiva: las tecnicas que un atacante racional preferiria por enfrentar
    menos controles documentados.

    El minimo 0.05 evita aristas de peso 0 (que romperian la nocion de costo
    y permitirian rutas degeneradas de longitud arbitraria sin penalizacion).
    """
    if max_mitigations > 0:
        w = round(max(0.05, n_mitigations / max_mitigations), 3)
    else:
        w = 0.05
    source = f"mitigaciones={n_mitigations}/{max_mitigations}"
    return w, source


# ── Construccion del grafo ────────────────────────────────────────────────────

def _get_attack_id(technique: dict) -> str | None:
    for r in technique.get("external_references", []):
        if r.get("source_name") == "mitre-attack":
            return r["external_id"]
    return None


def _get_tactics(technique: dict) -> list[str]:
    return [
        p["phase_name"]
        for p in technique.get("kill_chain_phases", [])
        if p.get("kill_chain_name") == "mitre-attack"
    ]


def build_attack_graph(bundle: dict, campaign_techniques: list) -> object:
    """
    Construye DiGraph de la campana.

    Aristas REALES (no sinteticas):
      - Dentro de la misma campana, conecta tecnicas de tactica[i] -> tactica[i+1]
        cuando AMBAS tecnicas fueron usadas en la campana.
        Esto representa la progresion real del atacante: primero usaron
        reconnaissance, luego initial-access, etc.
      - Solo se crean aristas entre tacticas consecutivas, no entre cualquier par.

    Nodos ATTACKER/IMPACT son necesarios como frontera del modelo
    (el atacante externo y el objetivo final) y se justifican metodologicamente.

    Pesos: 100% derivados del bundle STIX (mitigaciones documentadas).
    """
    import networkx as nx

    # Indice de mitigaciones reales del bundle
    mitig_index = build_mitigation_index(bundle)
    # Maximo de mitigaciones en las tecnicas de ESTA campana
    max_mit = max(
        (mitig_index.get(t["id"], 0) for t in campaign_techniques),
        default=1
    )
    print(f"  [PESOS] Mitigaciones: max={max_mit}, basado en {len(campaign_techniques)} tecnicas")

    G = nx.DiGraph()

    # Construir nodos con datos reales
    tech_by_id = {}  # attack_id -> (technique_obj, weight, weight_source)
    for t in campaign_techniques:
        atk_id = _get_attack_id(t)
        if not atk_id:
            continue
        tactics = _get_tactics(t)
        if not tactics:
            continue
        n_mit = mitig_index.get(t["id"], 0)
        w, w_src = compute_weight(t, n_mit, max_mit)
        tech_by_id[atk_id] = (t, w, w_src)
        G.add_node(
            atk_id,
            name=t.get("name", ""),
            tactics=tactics,
            weight=w,
            weight_source=w_src,
            data_sources=t.get("x_mitre_data_sources", []),
            platforms=t.get("x_mitre_platforms", []),
            is_subtechnique=t.get("x_mitre_is_subtechnique", False),
            description=t.get("description", "")[:200],
        )

    # Nodos frontera (conceptuales, metodologicamente necesarios)
    G.add_node(ENTRY_NODE, name="Atacante externo", tactics=["entry"], weight=0.0)
    G.add_node(TARGET_NODE, name="Impacto logrado", tactics=["target"], weight=0.0)

    # Indice por tactica (solo tecnicas de esta campana)
    by_tactic: dict[str, list[str]] = {t: [] for t in TACTIC_ORDER}
    for atk_id, (t_obj, w, _) in tech_by_id.items():
        for tac in G.nodes[atk_id]["tactics"]:
            if tac in by_tactic:
                by_tactic[tac].append(atk_id)

    # Aristas: ATTACKER -> tecnicas de primera tactica presente
    first_tactics = ["reconnaissance", "resource-development", "initial-access"]
    for tac in first_tactics:
        for atk_id in by_tactic.get(tac, []):
            w = G.nodes[atk_id]["weight"]
            G.add_edge(ENTRY_NODE, atk_id, weight=w, rel_type="entry",
                       description=f"Inicio de campana via {tac}")

    # Aristas: tecnicas de ultima tactica -> IMPACT
    last_tactics = ["impact", "exfiltration"]
    for tac in last_tactics:
        for atk_id in by_tactic.get(tac, []):
            G.add_edge(atk_id, TARGET_NODE, weight=0.01, rel_type="exit",
                       description="Objetivo de campana alcanzado")

    # Aristas REALES: tactica[i] -> tactica[i+1], AMBAS tecnicas en la campana
    for i in range(len(TACTIC_ORDER) - 1):
        src_tac = TACTIC_ORDER[i]
        dst_tac = TACTIC_ORDER[i + 1]
        src_nodes = by_tactic.get(src_tac, [])
        dst_nodes = by_tactic.get(dst_tac, [])

        if not src_nodes or not dst_nodes:
            continue

        # Conectar cada dst desde cada src (todas las combinaciones dentro de campana)
        # Justificacion: el atacante podia usar cualquier tecnica de tactica i
        # para habilitar cualquier tecnica de tactica i+1, ambas documentadas en campana.
        for src_id in src_nodes:
            for dst_id in dst_nodes:
                if not G.has_edge(src_id, dst_id):
                    w = G.nodes[dst_id]["weight"]
                    G.add_edge(src_id, dst_id, weight=w,
                               rel_type="tactical-progression",
                               description=f"{src_tac} -> {dst_tac} (SolarWinds)")

    return G, tech_by_id, by_tactic


def graph_summary(G, campaign_name: str = "") -> dict:
    import networkx as nx
    return {
        "campaign": campaign_name,
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "n_techniques": G.number_of_nodes() - 2,  # excluir ATTACKER/IMPACT
        "entry": ENTRY_NODE,
        "target": TARGET_NODE,
        "is_dag": nx.is_directed_acyclic_graph(G),
        "density": round(nx.density(G), 6),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import networkx as nx

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-descargar ATT&CK")
    parser.add_argument("--campaign", default=TARGET_CAMPAIGN_NAME)
    args = parser.parse_args()

    bundle = download_mitre(force=args.force)
    campaign_obj, techniques = extract_campaign(bundle, args.campaign)
    G, tech_by_id, by_tactic = build_attack_graph(bundle, techniques)
    s = graph_summary(G, args.campaign)

    print(f"\n{'='*60}")
    print(f"  Caso de estudio: {s['campaign']}")
    print(f"  Tecnicas reales:  {s['n_techniques']}")
    print(f"  Nodos total:      {s['n_nodes']} (+ ATTACKER + IMPACT)")
    print(f"  Aristas:          {s['n_edges']}")
    print(f"  Es DAG:           {s['is_dag']}")
    print(f"  Densidad:         {s['density']}")
    print(f"{'='*60}")

    print(f"\nTecnicas por tactica:")
    for tac in TACTIC_ORDER:
        nodes = by_tactic.get(tac, [])
        if nodes:
            print(f"  {tac:<25} {len(nodes):2} tecnicas")

    print(f"\nEjemplo pesos reales (primeras 10 tecnicas):")
    print(f"  {'ATT&CK ID':<14} {'Peso':>6}  {'Fuente del peso':<35} Nombre")
    print(f"  {'-'*90}")
    for atk_id, (t_obj, w, w_src) in list(tech_by_id.items())[:10]:
        name = t_obj.get("name", "")[:40]
        print(f"  {atk_id:<14} {w:>6.3f}  {w_src:<35} {name}")

    # Verificar conectividad
    try:
        path = nx.shortest_path(G, ENTRY_NODE, TARGET_NODE, weight="weight")
        cost = nx.shortest_path_length(G, ENTRY_NODE, TARGET_NODE, weight="weight")
        print(f"\nRuta mas corta ATTACKER->IMPACT: {len(path)} pasos, costo={cost:.4f}")
        print("  " + " -> ".join(path))
    except nx.NetworkXNoPath:
        reachable = nx.descendants(G, ENTRY_NODE)
        print(f"\n[WARN] Sin ruta directa. Reachable desde ATTACKER: {len(reachable)}")
        impact_pred = list(G.predecessors(TARGET_NODE))
        print(f"       Predecessors de IMPACT: {impact_pred[:5]}")
        for p in impact_pred[:3]:
            print(f"       {p} reachable: {p in reachable}")
