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


def list_eligible_campaigns(bundle: dict, min_techniques: int = 10) -> list[dict]:
    """
    Escanea TODAS las campanas del bundle (56 en total), cuenta sus tecnicas
    reales via la misma relacion 'uses' que extract_campaign(), y filtra por
    min_techniques. Unico criterio de seleccion: el umbral explicito
    (parametrizable), no una lista curada a mano.

    Retorna lista de {name, id, n_techniques}, ordenada desc por n_techniques.
    """
    objects = bundle["objects"]

    campaigns = [
        o for o in objects
        if o.get("type") == "campaign"
        and not o.get("revoked")
        and not o.get("x_mitre_deprecated")
    ]

    tech_count: dict[str, int] = {c["id"]: 0 for c in campaigns}
    for o in objects:
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "uses"
                and o.get("source_ref") in tech_count
                and o.get("target_ref", "").startswith("attack-pattern--")):
            tech_count[o["source_ref"]] += 1

    eligible = [
        {"name": c["name"], "id": c["id"], "n_techniques": tech_count[c["id"]]}
        for c in campaigns
        if tech_count[c["id"]] >= min_techniques
    ]
    eligible.sort(key=lambda x: -x["n_techniques"])
    return eligible


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


def build_detection_index(bundle: dict) -> dict:
    """
    Cuenta cobertura de deteccion por tecnica, desde dos relaciones STIX
    independientes de 'mitigates':
      - n_strategies: relaciones 'detects' (x-mitre-detection-strategy ->
        attack-pattern), 697 en el bundle. Amplitud de deteccion.
      - n_analytics: suma de len(x_mitre_analytic_refs) de cada estrategia
        que detecta la tecnica. Profundidad de deteccion (una estrategia con
        4 analiticas documentadas es una senal mas fuerte que una con 1).

    Retorna dict: stix_id -> {"n_strategies": int, "n_analytics": int}
    """
    from collections import defaultdict

    objects = bundle.get("objects", [])
    strategy_analytics = {
        o["id"]: len(o.get("x_mitre_analytic_refs", []))
        for o in objects
        if o.get("type") == "x-mitre-detection-strategy"
    }

    result: dict = defaultdict(lambda: {"n_strategies": 0, "n_analytics": 0})
    for o in objects:
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "detects"
                and o.get("target_ref", "").startswith("attack-pattern--")):
            tech_id = o["target_ref"]
            strategy_id = o.get("source_ref", "")
            result[tech_id]["n_strategies"] += 1
            result[tech_id]["n_analytics"] += strategy_analytics.get(strategy_id, 0)

    return dict(result)


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


def compute_weight_v2(
    n_mitigations: int, max_mitigations: int,
    n_detect_strategies: int, max_detect_strategies: int,
    n_analytics: int, max_analytics: int,
    alpha: float = 0.6, beta: float = 0.4,
) -> tuple[float, str]:
    """
    Peso combinado: resistencia defensiva = cobertura PREVENTIVA (mitigates)
    + cobertura DETECTIVA (detects + profundidad analitica). Ambos componentes
    100% derivados de relaciones STIX reales (ver build_mitigation_index y
    build_detection_index) -- ningun dato manual o externo.

      mit_score = n_mitigaciones / max_mitigaciones_campana       (barrera ex-ante)
      det_score = 0.5*(n_estrategias/max_estrategias)
                + 0.5*(n_analiticas/max_analiticas)                (barrera ex-post:
                  amplitud [n_estrategias] + profundidad [n_analiticas])
      w = max(0.05, alpha*mit_score + beta*det_score)

    alpha=0.6/beta=0.4: mitigar (prevenir) es una barrera mas fuerte para el
    atacante que solo detectar (requiere respuesta humana/SOC posterior);
    se pondera mas alto pero no exclusivamente. Parametros explicitos, no
    constantes magicas ocultas.

    Con 2 fuentes independientes en vez de 1 sola (mitigaciones), el espacio
    de valores posibles gana resolucion, reduciendo el problema de empates
    documentado en ESTADO_PROYECTO.md (Limitacion L4).
    """
    mit_score = n_mitigations / max_mitigations if max_mitigations > 0 else 0.0
    strat_score = n_detect_strategies / max_detect_strategies if max_detect_strategies > 0 else 0.0
    analytic_score = n_analytics / max_analytics if max_analytics > 0 else 0.0
    det_score = 0.5 * strat_score + 0.5 * analytic_score

    w = round(max(0.05, alpha * mit_score + beta * det_score), 3)
    source = (
        f"combinado(mit={n_mitigations}/{max_mitigations},"
        f"det_estr={n_detect_strategies}/{max_detect_strategies},"
        f"det_analit={n_analytics}/{max_analytics},a={alpha},b={beta})"
    )
    return w, source


# ── Co-ocurrencia real (actor comparte tecnicas) ──────────────────────────────

def build_actor_technique_index(bundle: dict, campaign: dict) -> dict:
    """
    Indexa, para cada actor (malware/tool usado por la campana, o intrusion-set
    atribuido a la campana via relacion 'attributed-to'), el conjunto de
    tecnicas (attack-pattern stix ids) que ese actor usa.

    100% relaciones STIX reales:
      - campaign --uses--> malware/tool
      - malware/tool --uses--> attack-pattern
      - campaign --attributed-to--> intrusion-set
      - intrusion-set --uses--> attack-pattern

    Retorna: actor_id -> set(attack_pattern_stix_id)
    """
    objects = bundle["objects"]

    actor_ids = set()
    for o in objects:
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "uses"
                and o.get("source_ref") == campaign["id"]
                and (o.get("target_ref", "").startswith("malware--")
                     or o.get("target_ref", "").startswith("tool--"))):
            actor_ids.add(o["target_ref"])
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "attributed-to"
                and o.get("source_ref") == campaign["id"]
                and o.get("target_ref", "").startswith("intrusion-set--")):
            actor_ids.add(o["target_ref"])

    actor_techniques: dict[str, set] = {aid: set() for aid in actor_ids}
    for o in objects:
        if (o.get("type") == "relationship"
                and o.get("relationship_type") == "uses"
                and o.get("source_ref") in actor_ids
                and o.get("target_ref", "").startswith("attack-pattern--")):
            actor_techniques[o["source_ref"]].add(o["target_ref"])

    return actor_techniques


def build_cooccurrence_edges(
    bundle: dict, campaign: dict, tech_by_id: dict, by_tactic: dict
) -> tuple[list[tuple[str, str, list[str]]], dict]:
    """
    Aristas de co-ocurrencia REAL: tecnica_A -> tecnica_B solo si existe al
    menos un actor (malware/tool/intrusion-set) que use AMBAS tecnicas en
    esta campana, y B esta en una tactica igual o posterior a A en
    TACTIC_ORDER (preserva la progresion sin ciclos).

    A diferencia del modo cartesiano (cross-product completo entre tacticas
    consecutivas), aqui solo se conecta lo que un actor real documentado
    efectivamente uso en ambas tecnicas -- es el "camino realmente observado"
    en vez del "espacio de ataque posible".

    Retorna (edges, stats):
      edges = lista de (src_atk_id, dst_atk_id, [nombres_actores_compartidos])
      stats = { n_pairs_connected, n_pairs_possible_cartesian, coverage_ratio,
                n_techniques_isolated, isolated_techniques }
    """
    objects = bundle["objects"]
    id_map = {o["id"]: o for o in objects}

    actor_techniques = build_actor_technique_index(bundle, campaign)

    # stix_id -> atk_id, para traducir tecnicas de un actor a nuestros nodos
    stix_to_atk = {t_obj["id"]: atk_id for atk_id, (t_obj, _, _) in tech_by_id.items()}

    tactic_rank = {tac: i for i, tac in enumerate(TACTIC_ORDER)}

    # actor_id -> nombres de tecnicas (atk_id) que usa, dentro de esta campana
    actor_atk_techs: dict[str, set] = {}
    for actor_id, stix_ids in actor_techniques.items():
        atk_ids = {stix_to_atk[sid] for sid in stix_ids if sid in stix_to_atk}
        if atk_ids:
            actor_atk_techs[actor_id] = atk_ids

    # Para cada par de tecnicas co-usadas por un mismo actor, registrar el actor
    pair_actors: dict[tuple[str, str], list[str]] = {}
    for actor_id, atk_ids in actor_atk_techs.items():
        actor_name = id_map.get(actor_id, {}).get("name", actor_id)
        atk_list = sorted(atk_ids)
        for i, a in enumerate(atk_list):
            for b in atk_list:
                if a == b:
                    continue
                pair_actors.setdefault((a, b), []).append(actor_name)

    n_pairs_possible_cartesian = 0
    for i in range(len(TACTIC_ORDER) - 1):
        src_nodes = by_tactic.get(TACTIC_ORDER[i], [])
        dst_nodes = by_tactic.get(TACTIC_ORDER[i + 1], [])
        n_pairs_possible_cartesian += len(src_nodes) * len(dst_nodes)

    edges = []
    connected_techniques = set()
    for (a, b), actors in pair_actors.items():
        if a not in tech_by_id or b not in tech_by_id:
            continue
        tacs_a = _get_tactics(tech_by_id[a][0])
        tacs_b = _get_tactics(tech_by_id[b][0])
        rank_a = min((tactic_rank[t] for t in tacs_a if t in tactic_rank), default=None)
        rank_b = min((tactic_rank[t] for t in tacs_b if t in tactic_rank), default=None)
        if rank_a is None or rank_b is None or rank_b < rank_a:
            continue  # solo progresion hacia adelante (o misma tactica, no hacia atras)
        if rank_a == rank_b:
            continue  # evita auto-ciclos entre tecnicas de la misma tactica
        edges.append((a, b, sorted(set(actors))))
        connected_techniques.add(a)
        connected_techniques.add(b)

    all_techniques = set(tech_by_id.keys())
    isolated = sorted(all_techniques - connected_techniques)

    stats = {
        "n_pairs_connected": len(edges),
        "n_pairs_possible_cartesian": n_pairs_possible_cartesian,
        "coverage_ratio": round(len(edges) / n_pairs_possible_cartesian, 4)
                           if n_pairs_possible_cartesian else 0.0,
        "n_techniques_isolated": len(isolated),
        "isolated_techniques": isolated,
    }
    return edges, stats


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


def build_attack_graph(
    bundle: dict, campaign_techniques: list, campaign: dict | None = None,
    edge_mode: str = "cartesian", weight_mode: str = "mitigations",
) -> object:
    """
    Construye DiGraph de la campana.

    edge_mode="cartesian" (default, comportamiento original sin cambios):
      - Dentro de la misma campana, conecta tecnicas de tactica[i] -> tactica[i+1]
        cuando AMBAS tecnicas fueron usadas en la campana (cross-product completo).
        Representa el "espacio de ataque posible" (worst-case), no una secuencia
        observada. Ver Limitacion L1.

    edge_mode="cooccurrence" (nuevo, ver build_cooccurrence_edges):
      - Conecta tecnica_A -> tecnica_B SOLO SI un actor real (malware/tool/
        intrusion-set) documentado en el bundle STIX uso AMBAS tecnicas.
        Representa la secuencia realmente observada, no el espacio posible.
        Requiere `campaign` (objeto STIX campaign, no solo la lista de tecnicas).
        Puede dejar tecnicas sin conexion si ningun actor comun las une
        (diagnostico incluido en graph_summary()['edge_construction_stats']).

    Nodos ATTACKER/IMPACT son necesarios como frontera del modelo
    (el atacante externo y el objetivo final) y se justifican metodologicamente.
    Las aristas ENTRY/EXIT (ATTACKER->primera tactica, ultima tactica->IMPACT)
    son identicas en ambos modos: son framing metodologico, no parte del
    problema cartesiano.

    Pesos: 100% derivados del bundle STIX. weight_mode="mitigations" (default,
    comportamiento original): solo mitigaciones documentadas. weight_mode=
    "combined" (nuevo, ver compute_weight_v2): mitigaciones + cobertura de
    deteccion (detects + analiticas).
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

    detect_index = {}
    max_strat = max_analytics = 1
    if weight_mode == "combined":
        detect_index = build_detection_index(bundle)
        max_strat = max(
            (detect_index.get(t["id"], {}).get("n_strategies", 0) for t in campaign_techniques),
            default=1
        ) or 1
        max_analytics = max(
            (detect_index.get(t["id"], {}).get("n_analytics", 0) for t in campaign_techniques),
            default=1
        ) or 1
        print(f"  [PESOS] Deteccion: max_estrategias={max_strat}, max_analiticas={max_analytics}")

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
        if weight_mode == "combined":
            det = detect_index.get(t["id"], {"n_strategies": 0, "n_analytics": 0})
            w, w_src = compute_weight_v2(
                n_mit, max_mit,
                det["n_strategies"], max_strat,
                det["n_analytics"], max_analytics,
            )
        else:
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

    edge_construction_stats = None
    if edge_mode == "cooccurrence":
        if campaign is None:
            raise ValueError("edge_mode='cooccurrence' requiere el objeto `campaign` (STIX).")
        cooc_edges, edge_construction_stats = build_cooccurrence_edges(
            bundle, campaign, tech_by_id, by_tactic
        )
        for src_id, dst_id, actors in cooc_edges:
            if not G.has_edge(src_id, dst_id):
                w = G.nodes[dst_id]["weight"]
                G.add_edge(src_id, dst_id, weight=w,
                           rel_type="cooccurrence-real",
                           description=f"Actor(es) compartido(s): {', '.join(actors)}")
    else:
        # Aristas cartesianas: tactica[i] -> tactica[i+1], AMBAS tecnicas en la campana
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

    G.graph["edge_mode"] = edge_mode
    G.graph["weight_mode"] = weight_mode
    if edge_construction_stats is not None:
        G.graph["edge_construction_stats"] = edge_construction_stats

    return G, tech_by_id, by_tactic


def graph_summary(G, campaign_name: str = "") -> dict:
    import networkx as nx
    s = {
        "campaign": campaign_name,
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "n_techniques": G.number_of_nodes() - 2,  # excluir ATTACKER/IMPACT
        "entry": ENTRY_NODE,
        "target": TARGET_NODE,
        "is_dag": nx.is_directed_acyclic_graph(G),
        "density": round(nx.density(G), 6),
        "edge_mode": G.graph.get("edge_mode", "cartesian"),
        "weight_mode": G.graph.get("weight_mode", "mitigations"),
    }
    if "edge_construction_stats" in G.graph:
        s["edge_construction_stats"] = G.graph["edge_construction_stats"]
    return s


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import networkx as nx

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-descargar ATT&CK")
    parser.add_argument("--campaign", default=TARGET_CAMPAIGN_NAME)
    parser.add_argument("--edge-mode", choices=["cartesian", "cooccurrence"], default="cartesian")
    parser.add_argument("--weight-mode", choices=["mitigations", "combined"], default="mitigations")
    args = parser.parse_args()

    bundle = download_mitre(force=args.force)
    campaign_obj, techniques = extract_campaign(bundle, args.campaign)
    G, tech_by_id, by_tactic = build_attack_graph(
        bundle, techniques, campaign=campaign_obj,
        edge_mode=args.edge_mode, weight_mode=args.weight_mode,
    )
    s = graph_summary(G, args.campaign)

    print(f"\n{'='*60}")
    print(f"  Caso de estudio: {s['campaign']}")
    print(f"  Modo de aristas:  {s['edge_mode']}")
    print(f"  Tecnicas reales:  {s['n_techniques']}")
    print(f"  Nodos total:      {s['n_nodes']} (+ ATTACKER + IMPACT)")
    print(f"  Aristas:          {s['n_edges']}")
    print(f"  Es DAG:           {s['is_dag']}")
    print(f"  Densidad:         {s['density']}")
    if "edge_construction_stats" in s:
        st = s["edge_construction_stats"]
        print(f"  Cobertura vs cartesiano: {st['coverage_ratio']*100:.1f}% "
              f"({st['n_pairs_connected']}/{st['n_pairs_possible_cartesian']} pares)")
        print(f"  Tecnicas aisladas (sin co-ocurrencia): {st['n_techniques_isolated']}")
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
