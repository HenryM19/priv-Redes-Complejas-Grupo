# Least-Resistance Path and Bottleneck Analysis of the SolarWinds Compromise Using Dijkstra's Algorithm and Floyd-Warshall Betweenness on MITRE ATT&CK STIX 2.1 Data

**Jean Carlo Aucapina · Henry Maldonado**
Department of Electrical, Electronic and Telecommunications Engineering (DEET)
Universidad de Cuenca — Cuenca, Ecuador
{jean.aucapina, henry.maldonado}@ucuenca.edu.ec

---

## Abstract

We model the SolarWinds Compromise (APT29, 2019–2020) as a weighted directed graph and apply shortest-path and centrality algorithms to identify the path of least defensive resistance and the universal bottleneck techniques. Nodes represent the 71 ATT&CK techniques documented for the campaign; edge weights encode **defensive resistance** as the proportion of documented mitigations a technique has, derived entirely and reproducibly from the MITRE ATT&CK STIX 2.1 bundle (`w = max(0.05, n_mit / max_mit)`). Dijkstra's algorithm finds a critical path of total cost 1.535 through seven techniques spanning stealth, credential-access, discovery, lateral-movement, collection, command-and-control, and exfiltration tactics. Floyd-Warshall betweenness identifies T1606.001 (Web Cookies) as the top structural bottleneck, lying on 1,044 optimal routes. Our own implementations of Dijkstra and Bellman-Ford are validated against NetworkX (identical cost and path for Dijkstra; Spearman ρ = 0.973 for betweenness ranking vs. NetworkX Brandes). A breadth-first (unweighted) baseline yields a path costing 2.925 (+90% over optimal), confirming that the weights are informative. A weight-perturbation sensitivity analysis shows the critical path is invariant under ±20% scaling (Jaccard = 1.0) but changes under a coarse binary weighting scheme, locating the limit of robustness. A defensive impact simulation reveals that blocking T1048.002 eliminates all ATTACKER→IMPACT routes, while blocking T1550.004 and T1606.001 raises attacker cost by +16.3% and +8.1% respectively. The method generalizes across three ATT&CK campaigns (SolarWinds/APT29, Operation Wocao/APT20, Operation Dream Job/Lazarus), producing critical-path Jaccard similarities of 0.0–0.1, confirming discrimination between distinct threat actors; the *stealth* tactic appears in all three critical paths. We are explicit about the model's limitations, chiefly that inter-tactic edges are inferred (worst-case layered model) rather than observed from execution traces.

**Keywords:** attack graph, shortest path, Dijkstra, Floyd-Warshall, MITRE ATT&CK, STIX 2.1, SolarWinds, threat modeling, betweenness centrality, defensive prioritization.

---

## 1. Introduction

Advanced Persistent Threat (APT) campaigns proceed through multi-stage attack sequences. Modeling these sequences as graphs enables quantitative questions: which techniques are structurally critical, what is the minimum-resistance path from initial access to impact, and which controls have the highest defensive leverage.

The SolarWinds Compromise is an ideal case study: one of the most extensively documented attacks in history, with MITRE ATT&CK encoding 71 techniques and their mitigations in a publicly accessible STIX 2.1 knowledge base. This work addresses two research questions:

**RQ1.** What is the sequence of ATT&CK techniques representing the path of least defensive resistance from initial access to impact in the SolarWinds Compromise, under a mitigation-derived weighting?

**RQ2.** Which techniques are universal bottlenecks—appearing on the maximum number of optimal routes—as determined by Floyd-Warshall betweenness over the campaign graph?

We additionally (a) validate our own algorithm implementations against a reference library, (b) test robustness via weight-perturbation sensitivity, (c) simulate the defensive impact of blocking each candidate technique, and (d) demonstrate generalization across two further campaigns with distinct threat actors.

### 1.1 Contributions

1. **Reproducible weight model** using only MITRE ATT&CK STIX 2.1 data (mitigation counts); no manual CVE mapping.
2. **Own implementations** of Dijkstra (binary heap) and Bellman-Ford, validated against NetworkX.
3. **Floyd-Warshall betweenness** over the full 73-node graph, validated against NetworkX Brandes (ρ = 0.973).
4. **Sensitivity analysis** including a robustness boundary (binary weighting).
5. **Defensive impact simulation**: per-technique attacker-cost delta on node removal.
6. **Multi-campaign generalization** across three campaigns / three threat actors.

---

## 2. Related Work

Attack graphs have been studied for over two decades for network vulnerability analysis [1, 2]. Classical work uses network topology with CVE-based edge weights and probabilistic reachability. More recent approaches integrate threat-intelligence frameworks.

**MITRE ATT&CK-based graphs.** Milajerdi et al. [3] use ATT&CK techniques as nodes in provenance graphs for APT detection. Peng et al. [4] construct ATT&CK-based attack graphs for risk assessment. Our work differs in using campaign-specific subgraphs filtered from the full ATT&CK knowledge base, with weights derived from mitigation coverage rather than CVSS alone.

**Shortest path in attack modeling.** Idika & Bhargava [5] survey shortest-path approaches to attack-graph analysis. Most prior work uses uniform or probabilistic weights; we use defensive resistance (mitigation coverage) as the cost.

**Betweenness centrality.** Brandes' algorithm [6] has been applied to attack graphs to identify critical nodes [7]. We define a variant using the Floyd-Warshall all-pairs shortest-path matrix to count exact path memberships, and we validate it against the weighted Brandes implementation.

Our work is distinguished by: (a) 100% real, reproducible STIX 2.1 data with no synthetic topology and no manual CVE mapping; (b) explicit validation of own implementations; (c) a sensitivity analysis that reports its own robustness limit; (d) defensive impact simulation; (e) multi-campaign generalization.

---

## 3. Methodology

### 3.1 Dataset

We use the MITRE ATT&CK Enterprise STIX 2.1 bundle (`enterprise-attack.json`, ~35 MB, from the official MITRE `cti` GitHub repository). The SolarWinds Compromise is represented as a `campaign` object; we extract the 71 non-revoked, non-deprecated `attack-pattern` objects linked via `uses` relationships.

### 3.2 Graph Construction

We define a directed graph G = (V, E, w):

- **V** = {T₁, …, T₇₁} ∪ {ATTACKER, IMPACT}, where Tᵢ are ATT&CK technique IDs.
- **E**: an edge (Tᵢ → Tⱼ) exists if Tᵢ belongs to tactic *k* and Tⱼ to tactic *k+1* in the ATT&CK kill-chain order, and both are documented for the campaign. ATTACKER connects to first-tactic techniques; last-tactic techniques connect to IMPACT.
- **w(Tⱼ)**: the defensive resistance of the destination technique.

This yields |V| = 73, |E| = 653. **The inter-tactic edge set is the full cartesian product between consecutive-tactic technique sets** — a deliberately conservative "layered worst-case" model: any technique in tactic *k* is assumed able to enable any technique in tactic *k+1*. This over-approximates the true transition space; we treat the resulting betweenness as *structural centrality over the space of possible attacks*, not as an estimate of empirical transition frequency (see §5.3, L1).

### 3.3 Weight Function (defensive resistance)

```
w(T) = max(0.05, n_mit(T) / max_mit)
```

where `n_mit(T)` is the number of `mitigates` relationships targeting T in the STIX bundle and `max_mit` = 8 (the per-campaign maximum). **More documented mitigations ⇒ more defensive controls ⇒ higher cost to the attacker.** Dijkstra therefore finds the path of *least defensive resistance*: the sequence of techniques facing the fewest documented controls. The 0.05 floor avoids zero-weight edges (which would permit degenerate paths). All weights are reproducible from the bundle; no CVE/CVSS mapping is used (see §5.3, L6).

### 3.4 Algorithms

- **Dijkstra (own, binary min-heap):** O((V+E) log V). Source: ATTACKER.
- **Bellman-Ford (own):** O(V·E), with negative-cycle check. Cross-validation only.
- **Floyd-Warshall:** O(V³) = O(73³) ≈ 389K ops. All-pairs distance matrix D.
- **FW-betweenness:** for each node *k*, `FW_betw(k) = |{(i,j) : i≠k, j≠k, D[i,k]+D[k,j] = D[i,j] < ∞}|`.

### 3.5 Sensitivity Analysis

Four scenarios: (1) base mitigation weights; (2) ×0.8; (3) ×1.2; (4) a coarse **binary** scheme (w=0.9 if `n_mit` above the median, else w=0.1). For each, Dijkstra is re-run and the Jaccard similarity of critical-path node sets is computed vs. base.

### 3.6 Defensive Impact Simulation

For each candidate (critical-path nodes ∪ top-10 FW-betweenness): remove the node, re-run Dijkstra, compute Δcost. No path ⇒ total block.

### 3.7 Multi-Campaign Generalization

The identical pipeline is applied to Operation Wocao (APT20) and Operation Dream Job (Lazarus). Pairwise critical-path Jaccard similarity is computed.

---

## 4. Results

### 4.1 Graph Properties

| Property | Value |
|---|---|
| Nodes | 73 (71 techniques + ATTACKER + IMPACT) |
| Edges | 653 |
| Density | 0.124 |
| Is DAG | No (54 SCCs; many techniques span multiple tactics) |
| Diameter (WCC) | 9 |
| Average path length | 2.85 |
| Average clustering | 0.203 (Erdős–Rényi equivalent: 0.213; ratio 0.953) |
| Degree assortativity | +0.308 |

The clustering ratio ≈ 1 and the imposed layered structure indicate the graph is close to a layered random graph rather than an emergent scale-free network. Cycles (54 SCCs) arise because several techniques (e.g. T1078.003) are tagged with multiple tactics; all weights are non-negative, so Dijkstra and Floyd-Warshall remain valid.

### 4.2 Critical Path (RQ1)

Dijkstra finds the following least-resistance path, total cost **1.535**:

```
ATTACKER → T1078.003 (w=0.500) → T1606.001 (w=0.250) → T1016.001 (w=0.050)
         → T1550.004 (w=0.125) → T1074.002 (w=0.050) → T1665 (w=0.050)
         → T1048.002 (w=0.500) → IMPACT
```

**Table 2. Critical path — technique details.**

| Step | ID | Name | Tactic (first) | n_mit | w |
|---|---|---|---|---|---|
| 1 | T1078.003 | Local Accounts | stealth/persistence/priv-esc/init-access | 4/8 | 0.500 |
| 2 | T1606.001 | Web Cookies | credential-access | 2/8 | 0.250 |
| 3 | T1016.001 | Internet Connection Discovery | discovery | 0/8 | 0.050 |
| 4 | T1550.004 | Web Session Cookie | lateral-movement | 1/8 | 0.125 |
| 5 | T1074.002 | Remote Data Staging | collection | 0/8 | 0.050 |
| 6 | T1665 | Hide Infrastructure | command-and-control | 0/8 | 0.050 |
| 7 | T1048.002 | Exfil. Over Asym. Encrypted Non-C2 | exfiltration | 4/8 | 0.500 |

The path's endpoints (T1078.003 valid-account use, T1048.002 encrypted exfiltration) carry the highest cost (4/8 mitigations each); the mid-path discovery, collection, and C2 techniques are the least-defended (0/8 mitigations), consistent with the documented difficulty of detecting discovery and staging activity in the SolarWinds intrusion.

### 4.3 Algorithm Validation

All three weighted algorithms produce identical cost **1.535**. Dijkstra (own) and NetworkX agree on all path nodes. Bellman-Ford selects T1057 (Process Discovery, w=0.05) at step 3 instead of T1016.001 (also w=0.05) — a tie broken by edge-iteration order, with identical cost. The unweighted BFS baseline yields a different path costing 2.925 when its edge weights are summed, **+90.6% above optimal**, confirming the weights carry information beyond hop count.

Measured runtimes on the 73-node, 653-edge graph: Dijkstra (own) 0.32 ms, Bellman-Ford (own) 0.82 ms, NetworkX 2.25 ms.

### 4.4 FW-Betweenness (RQ2)

**Table 3. Top FW-betweenness techniques (with NetworkX-weighted rank).**

| Rank FW | ID | Name | FW-betw | Rank NX | Δrank |
|---|---|---|---|---|---|
| 1 | T1606.001 | Web Cookies | 1044 | 1 | 0 |
| 2 | T1018 | Remote System Discovery | 836 | 13 | −11 |
| 3 | T1069.002 | Domain Groups | 836 | 14 | −11 |
| 4 | T1069 | Permission Groups Discovery | 836 | 15 | −11 |
| 5 | T1680 | Local Storage Discovery | 836 | 16 | −11 |
| 6 | T1083 | File and Directory Discovery | 836 | 17 | −11 |
| 7 | T1016.001 | Internet Connection Discovery | 836 | 18 | −11 |
| 8 | T1057 | Process Discovery | 836 | 19 | −11 |

Spearman rank correlation between FW-betweenness and NetworkX weighted betweenness: **ρ = 0.973**. The top technique, **T1606.001 (Web Cookies)**, lies on 1,044 optimal routes. The large rank gap for the discovery cluster (ranks 2–8) reflects that FW-betweenness counts membership across *all* optimal (i,j) pairs while NetworkX normalizes by source-target flow; the discovery techniques sit on the single mandatory discovery layer and share an identical betweenness of 836, so their FW rank is high while their normalized Brandes flow is diluted across the eight equivalent siblings.

### 4.5 Sensitivity Analysis

**Table 4. Weight sensitivity — Jaccard similarity of critical-path node sets.**

| Scenario | Description | Cost | Jaccard vs. base | Path identical |
|---|---|---|---|---|
| Base | Mitigation proportion | 1.535 | 1.000 | Yes |
| −20% | Weights × 0.8 | 1.260 | 1.000 | Yes |
| +20% | Weights × 1.2 | 1.840 | 1.000 | Yes |
| Binary | 0.9/0.1 by median | 1.910 | low | No |

The critical path is **invariant under proportional ±20% perturbation** (linear scaling preserves the ordering of path costs, so the argmin is unchanged). Under the coarse **binary** scheme the path changes entirely (a longer 11-technique route through T1195.002→T1059.003→…→T1071.001). This is an honest robustness boundary: the result is stable to magnitude scaling but sensitive to discretizing the weight resolution, because binary weights collapse the fine distinctions (0/8 vs 1/8 vs 2/8 mitigations) that the linear scheme uses to order techniques. We therefore report conclusions at the level of *tactic* rather than exact technique where appropriate.

### 4.6 Defensive Impact Simulation

**Table 5. Top techniques by defensive impact (blocking one technique).**

| Rank | Technique | Name | Impact | Δcost | Δ% |
|---|---|---|---|---|---|
| 1 | T1048.002 | Exfil. Asym. Encrypted | TOTAL BLOCK | ∞ | ∞ |
| 2 | T1550.004 | Web Session Cookie | High | +0.250 | +16.3% |
| 3 | T1606.001 | Web Cookies | Medium | +0.125 | +8.1% |
| 4 | T1078.003 | Local Accounts | Medium | +0.100 | +6.5% |
| 5 | T1074.002 | Remote Data Staging | Low | +0.075 | +4.9% |
| 6 | T1665 | Hide Infrastructure | Low | +0.075 | +4.9% |

T1048.002 is the sole **single point of failure for the attacker**: it is the only exfiltration technique in the campaign graph, so removing it disconnects ATTACKER from IMPACT. Notably, the top-betweenness technique T1606.001 is also the #3 defensive control (+8.1%) — under the mitigation weighting, structural centrality and defensive leverage are aligned for this campaign (in contrast to scenarios where many equal-cost alternatives dilute the leverage of a central node). The eight discovery techniques (ranks 7–15) each yield Δcost = 0: blocking any one forces a zero-cost reroute through a sibling, so the *discovery layer* must be addressed as a whole rather than per-technique.

### 4.7 Multi-Campaign Generalization

**Table 6. Method applied to three ATT&CK campaigns.**

| Campaign | Actor | Nodes | Edges | Critical cost | Top-1 betweenness | Time |
|---|---|---|---|---|---|---|
| SolarWinds Compromise | APT29 | 73 | 653 | 1.535 | T1606.001 (Web Cookies) | 16.8 ms |
| Operation Wocao | APT20 | 72 | 494 | 0.935 | T1056.001 (Keylogging) | 16.1 ms |
| Operation Dream Job | Lazarus | 57 | 217 | 1.496 | T1553.002 (Code Signing) | 14.4 ms |

Pairwise critical-path Jaccard similarity:
- SolarWinds vs. Wocao: 0.100 (shared: T1078.003)
- SolarWinds vs. Dream Job: 0.000
- Wocao vs. Dream Job: 0.000

The very low Jaccard values confirm the method discriminates sharply between distinct threat actors: each actor's least-resistance path traverses largely different techniques. The lower cost for Wocao (0.935) reflects a graph with more low-mitigation techniques on its critical layers. Across all three campaigns, the **stealth** tactic appears in every critical path, suggesting defense-evasion/stealth controls as a candidate universally high-leverage investment.

---

## 5. Discussion

### 5.1 Interpretation

Under a mitigation-derived weighting, the least-resistance path concentrates its cost at the entry (valid-account abuse, T1078.003) and exit (encrypted exfiltration, T1048.002) — the two best-mitigated stages — and threads through the least-defended middle stages (discovery, staging, C2 infrastructure hiding, all 0/8 mitigations). This matches the intuition that the hard-to-detect middle of an intrusion is where a campaign like SolarWinds operated with least friction.

### 5.2 Betweenness vs. Defensive Impact

For this campaign and weighting, the top-betweenness technique (T1606.001) is also a top-3 defensive control, so the two views agree. The instructive divergence is the **discovery cluster**: eight techniques tie at betweenness 836 yet each has zero individual defensive impact, because they are mutually substitutable. Betweenness identifies a *critical layer*; defensive impact reveals that the layer, not any single node, is the actionable unit. Both metrics are complementary.

### 5.3 Limitations

- **L1 — Inferred edges (worst-case layered model).** Inter-tactic edges are the full cartesian product between consecutive-tactic technique sets, not observed transitions. This inflates absolute betweenness counts and should be read as structural centrality over *possible* attacks, not empirical frequency.
- **L2 — Attacker rationality.** Dijkstra assumes a cost-minimizing attacker. Real actors may choose suboptimal paths for stealth or tooling reasons; the critical path is a worst-case rational adversary, not a prediction.
- **L3 — Historical knowledge base.** ATT&CK records observed techniques; the model is valid for the documented 2019–2020 threat picture.
- **L4 — Weight granularity.** With `max_mit` = 8 only nine distinct weight values exist, producing frequent ties (resolved by iteration order; both resolutions are correct and equal-cost). The binary-scheme sensitivity (§4.5) quantifies the effect.
- **L5 — Limited campaign sample.** Generalization is demonstrated on three campaigns, not exhaustively.
- **L6 — No CVE weighting.** An earlier version mapped CVEs to techniques manually; that mapping was neither reproducible from STIX nor technically correct (e.g. CVE-2020-10148 is an Orion API auth-bypass mapping to T1190/T1195.002, not to PowerShell/C2). We removed it; weights now derive solely from documented mitigations.

### 5.4 Future Work

- Replace inferred edges with co-occurrence/sequence data from incident datasets (e.g. ATT&CK Evaluations).
- Scale generalization to 10+ campaigns across sectors and actors.
- Monte-Carlo modeling of non-rational attacker behavior.
- Finer-grained resistance weights (e.g. detection-data-source coverage) to reduce ties.

---

## 6. Conclusion

We modeled the SolarWinds Compromise as a weighted attack graph with reproducible, mitigation-derived edge weights from MITRE ATT&CK STIX 2.1. Dijkstra identifies a seven-technique least-resistance path (cost 1.535) running through stealth, credential-access, discovery, lateral-movement, collection, C2, and exfiltration. Floyd-Warshall betweenness identifies T1606.001 (Web Cookies) as the top structural bottleneck (1,044 optimal routes).

Both own implementations are validated against NetworkX (identical critical path cost; Spearman ρ = 0.973 for betweenness). An unweighted BFS baseline costs +90.6% more, confirming weight informativeness. Sensitivity analysis shows the path is invariant under ±20% scaling (Jaccard = 1.0) and reports its own robustness limit under binary weighting. Defensive simulation finds T1048.002 a single point of failure (total block), with T1550.004 (+16.3%) and T1606.001 (+8.1%) the next-highest-leverage controls; the discovery layer must be defended collectively.

Applied unchanged to two further campaigns, the method yields critical-path Jaccard similarities of 0.0–0.1, confirming threat-actor discrimination, while the *stealth* tactic recurs in all three critical paths. The complete pipeline — STIX download to results — is reproducible from a single public data source, and we are explicit about the worst-case nature of the inferred edge model.

---

## References

1. Sheyner, O., Haines, J., Jha, S., Lippmann, R., & Wing, J. (2002). Automated generation and analysis of attack graphs. *IEEE Symposium on Security and Privacy*.
2. Phillips, C., & Swiler, L. P. (1998). A graph-based system for network-vulnerability analysis. *NSPW '98*.
3. Milajerdi, S. M., et al. (2019). HOLMES: Real-time APT detection through correlation of suspicious information flows. *IEEE S&P*.
4. Peng, Y., et al. (2020). Constructing attack graphs for assessing security risk in industrial environments. *IEEE Access*.
5. Idika, N., & Bhargava, B. (2012). Extending attack graph-based security metrics and aggregating their application. *IEEE TDSC*, 9(1).
6. Brandes, U. (2001). A faster algorithm for betweenness centrality. *Journal of Mathematical Sociology*, 25(2), 163–177.
7. Noel, S., & Jajodia, S. (2008). Measuring security risk of networks using attack graphs. *Int. J. Next-Gen. Computing*.
8. MITRE Corporation. (2023). MITRE ATT&CK Enterprise STIX 2.1. https://github.com/mitre/cti
9. CISA. (2020). Alert AA20-352A: Advanced Persistent Threat Compromise of Government Agencies, Critical Infrastructure, and Private Sector Organizations.
10. FireEye/Mandiant. (2020). Highly Evasive Attacker Leverages SolarWinds Supply Chain to Compromise Multiple Global Victims (SUNBURST).

---

*Manuscript prepared for submission. Target: IEEE Access / Computers & Security (Elsevier).*
*All results reproducible from the MITRE ATT&CK STIX 2.1 bundle via the project pipeline (`src/analisis_real.py`, `analisis_cientifico.py`, `comparacion_campanas.py`, `recomendaciones_defensivas.py`).*
