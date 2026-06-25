# Attack Graph Analysis of the SolarWinds Compromise Using Dijkstra's Algorithm and Floyd-Warshall Betweenness on MITRE ATT&CK STIX 2.1 Data

**Jean Carlo Aucapina · Henry Maldonado**  
Department of Electrical, Electronic and Telecommunications Engineering (DEET)  
Universidad de Cuenca — Cuenca, Ecuador  
{jean.aucapina, henry.maldonado}@ucuenca.edu.ec

---

## Abstract

We model the SolarWinds Compromise (APT29, 2019–2020) as a weighted directed graph and apply shortest-path and centrality algorithms to identify the path of least resistance and universal bottleneck techniques. Nodes represent the 71 ATT&CK techniques documented for the campaign; edge weights encode defensive resistance as a function of the number of documented mitigations and known CVE severity (CVSS). Dijkstra's algorithm finds a critical path of cost 1.635 through seven techniques spanning initial-access, credential-access, discovery, lateral-movement, collection, command-and-control, and exfiltration tactics. Floyd-Warshall betweenness identifies T1078 (Valid Accounts) as the universal bottleneck, present in 1,218 optimal routes. Our implementations are validated against NetworkX (Spearman ρ = 0.9997 for betweenness; identical cost and path for Dijkstra). A four-scenario weight sensitivity analysis shows Jaccard similarity ≥ 0.75 across all perturbations. A defensive impact simulation reveals that blocking T1048.002 eliminates all ATTACKER→IMPACT routes, while blocking T1071.001 increases attacker cost by 42.8%. The method generalizes across three ATT&CK campaigns (SolarWinds, Operation Wocao, Operation Dream Job), producing Jaccard similarities of 0.07–0.22 between critical paths, confirming correct discrimination between distinct threat actors. All code, data, and results are fully reproducible from the public MITRE ATT&CK STIX 2.1 bundle.

**Keywords:** attack graph, shortest path, Dijkstra, Floyd-Warshall, MITRE ATT&CK, STIX 2.1, SolarWinds, threat modeling, betweenness centrality, defensive prioritization.

---

## 1. Introduction

Advanced Persistent Threat (APT) campaigns are characterized by multi-stage attack sequences that progressively compromise target organizations. Modeling these sequences as graphs enables rigorous quantitative analysis: which techniques are structurally critical, what is the minimum-cost path from initial access to impact, and which controls have the highest defensive leverage.

The SolarWinds Compromise is an ideal case study: it is one of the most extensively documented attacks in history, with MITRE ATT&CK encoding 71 techniques and their associated mitigations in a publicly accessible STIX 2.1 knowledge base. This work addresses two research questions:

**RQ1.** What is the sequence of ATT&CK techniques representing the path of least resistance from initial access to impact in the SolarWinds Compromise, as determined by Dijkstra's algorithm on a MITRE ATT&CK-derived weighted graph?

**RQ2.** Which techniques are universal bottlenecks—appearing in the maximum number of optimal routes—as determined by Floyd-Warshall betweenness?

Beyond answering these questions for a single campaign, we evaluate the robustness of results through sensitivity analysis, validate our implementations against reference algorithms, and demonstrate generalization across two additional ATT&CK campaigns. We also compute, for each candidate technique, the defensive impact of blocking it: the resulting increase in attacker cost or total path elimination.

### 1.1 Contributions

1. **Graph model** with attack-lifecycle-informed edge weights derived entirely from MITRE ATT&CK STIX 2.1 real data (mitigation counts and CVE/CVSS scores).
2. **Own implementations** of Dijkstra (binary heap) and Bellman-Ford, validated against NetworkX.
3. **FW-betweenness** metric computed over the full 73-node graph (O(n³) = 389K ops), validated against NetworkX Brandes (ρ = 0.9997).
4. **Four-scenario sensitivity analysis** of weight perturbations (±20%, CVE-free).
5. **Defensive impact simulation**: per-technique cost delta upon node removal.
6. **Multi-campaign generalization** across three ATT&CK campaigns with three distinct threat actors.

---

## 2. Related Work

Attack graphs have been studied for over two decades as tools for network vulnerability analysis [Sheyner et al. 2002, Phillips & Swiler 1998]. Classical work focuses on network topology with CVE-based edge weights and probabilistic reachability. More recent approaches integrate threat intelligence frameworks.

**MITRE ATT&CK-based graphs.** Milajerdi et al. [2019] use ATT&CK techniques as nodes in provenance graphs for APT detection. Peng et al. [2020] construct ATT&CK-based attack graphs for risk assessment in ICS environments. Our work differs in using campaign-specific subgraphs filtered from the full ATT&CK knowledge base, with weights derived from mitigation coverage rather than CVSS alone.

**Shortest path in attack modeling.** Idika & Bhargava [2012] survey shortest-path approaches to attack graph analysis. Most prior work uses uniform or probabilistic weights; we use a compound weight function combining mitigation count and CVE severity, operationalized as defensive resistance rather than attack probability.

**Floyd-Warshall betweenness.** Standard betweenness centrality (Brandes [2001]) has been applied to attack graphs to identify critical nodes [Noel & Jajodia 2008]. We define a variant (FW-betweenness) using the Floyd-Warshall all-pairs shortest path matrix to count exact path memberships on the full campaign graph.

Our work is distinguished by: (a) 100% real STIX 2.1 data with no synthetic topology; (b) explicit validation of own implementations; (c) sensitivity analysis; (d) defensive impact simulation; (e) multi-campaign generalization.

---

## 3. Methodology

### 3.1 Dataset

We use the MITRE ATT&CK Enterprise STIX 2.1 bundle (version downloaded from the official MITRE GitHub repository, `enterprise-attack.json`, ~35 MB). The SolarWinds Compromise is represented as campaign object `campaign--808d6b30-df4e-4341-8248-724da4bac650` with 71 non-revoked, non-deprecated attack-pattern objects linked via `uses` relationships.

### 3.2 Graph Construction

We define a directed graph G = (V, E, w) where:

- **V** = {T₁, …, T₇₁} ∪ {ATTACKER, IMPACT}, where Tᵢ are ATT&CK technique IDs.
- **E**: an edge (Tᵢ → Tⱼ) exists if Tᵢ belongs to tactic k and Tⱼ belongs to tactic k+1 in the ATT&CK kill chain order, and both techniques are documented for the campaign. Additional edges connect ATTACKER to first-tactic techniques and last-tactic techniques to IMPACT.
- **w(Tⱼ)**: the weight assigned to the destination node of each incoming edge, representing the defensive resistance of technique Tⱼ.

The edge set construction reflects the tactical progression model: the attacker executes techniques in kill-chain order, and any technique from tactic k can enable any technique from tactic k+1 within the same campaign. This yields |E| = 653 edges.

### 3.3 Weight Function

Edge weights encode how easy it is for the attacker to exploit the destination technique, from the defender's perspective:

```
w_mit(T) = max(0.05, 1 − n_mit(T) / max_mit)
```

where `n_mit(T)` is the number of mitigation objects linked to T in the STIX bundle and `max_mit` = 8 (maximum mitigations for any technique in this campaign). More mitigations → higher cost for attacker.

For techniques with a known CVE directly associated with SolarWinds (sourced from NVD and public incident reports):

```
w_cve(T) = max(0.05, (10 − CVSS) / 10)
w(T) = min(w_mit(T), w_cve(T))
```

We take the minimum (most conservative for the attacker) when a CVE is available. This produces 11 techniques with CVE-adjusted weights (see Table 1).

**Table 1. CVE-adjusted technique weights (selected).**

| Technique | Name | CVE | CVSS | w |
|---|---|---|---|---|
| T1195.002 | Supply Chain Compromise | CVE-2020-10148 | 9.8 | 0.050 |
| T1078 | Valid Accounts | CVE-2021-21985 | 9.8 | 0.050 |
| T1021.001 | Remote Desktop Protocol | CVE-2021-26855 | 9.8 | 0.050 |
| T1071.001 | Web Protocols (C2) | CVE-2020-10148 | 9.8 | 0.050 |
| T1558.003 | Kerberoasting | CVE-2014-6324 | 9.0 | 0.100 |
| T1003.001 | LSASS Memory | CVE-2017-0144 | 8.1 | 0.190 |

### 3.4 Algorithms

**Dijkstra (own implementation).** Binary min-heap, O((V + E) log V). Handles non-negative weights ≥ 0.05. Source: ATTACKER.

**Bellman-Ford (own implementation).** O(V · E) relaxation with negative-cycle detection. Used for cross-validation only.

**Floyd-Warshall.** O(V³) = O(73³) ≈ 389K operations. Produces all-pairs shortest distance matrix D ∈ ℝ^{73×73}.

**FW-Betweenness.** For each node k:

```
FW_betw(k) = |{(i,j) : D[i][k] + D[k][j] = D[i][j], i≠k, j≠k, D[i][j] < ∞}|
```

Counts pairs (i,j) for which k lies on at least one shortest path.

### 3.5 Sensitivity Analysis

Four weight scenarios: (1) original weights, (2) all weights × 0.8, (3) all weights × 1.2, (4) mitigation-only (CVE weights removed). For each, Dijkstra is re-run and the Jaccard similarity of critical-path node sets is computed against the original.

### 3.6 Defensive Impact Simulation

For each candidate technique T (union of critical-path nodes and top-10 FW-betweenness nodes): remove T from G, re-run Dijkstra, compute Δcost = new_cost − original_cost. If no path exists after removal, mark as total block.

### 3.7 Multi-Campaign Generalization

The identical pipeline (§3.1–3.4) is applied to two additional campaigns from the same STIX bundle: Operation Wocao (APT20, n=70 techniques) and Operation Dream Job (Lazarus, n=55 techniques). Jaccard similarity of critical paths is computed pairwise.

---

## 4. Results

### 4.1 Graph Properties

| Property | Value |
|---|---|
| Nodes | 73 (71 techniques + ATTACKER + IMPACT) |
| Edges | 653 |
| Density | 0.124 |
| Is DAG | No (54 SCCs due to multi-tactic nodes) |
| Diameter (WCC) | 9 |
| Average path length | 2.85 |
| Average clustering | 0.203 (Erdős-Rényi equiv.: 0.213) |
| Degree assortativity | +0.308 |
| In-degree power-law R² | 0.006 |

The low power-law R² confirms the degree distribution does not follow a power law: the graph has an imposed layered structure (kill chain order) rather than emerging scale-free topology. Positive assortativity indicates hub-to-hub connectivity, consistent with multi-tactic techniques (e.g., T1078 participates in 4 tactics).

### 4.2 Critical Path (RQ1)

Dijkstra finds the following critical path with total cost 1.635:

```
ATTACKER → T1078 (w=0.05) → T1558.003 (w=0.10) → T1087 (w=0.75)
         → T1021.001 (w=0.05) → T1213 (w=0.125) → T1071.001 (w=0.05)
         → T1048.002 (w=0.50) → IMPACT
```

**Table 2. Critical path — technique details.**

| Step | ID | Name | Tactic | w | Source |
|---|---|---|---|---|---|
| 1 | T1078 | Valid Accounts | initial-access/persistence/... | 0.050 | CVE-2021-21985 (9.8) |
| 2 | T1558.003 | Kerberoasting | credential-access | 0.100 | CVE-2014-6324 (9.0) |
| 3 | T1087 | Account Discovery | discovery | 0.750 | 2/8 mitigations |
| 4 | T1021.001 | Remote Desktop Protocol | lateral-movement | 0.050 | CVE-2021-26855 (9.8) |
| 5 | T1213 | Data from Info Repositories | collection | 0.125 | 7/8 mitigations |
| 6 | T1071.001 | Web Protocols | command-and-control | 0.050 | CVE-2020-10148 (9.8) |
| 7 | T1048.002 | Exfil. Asym. Encrypted | exfiltration | 0.500 | 4/8 mitigations |

The path reveals a pattern consistent with the documented SolarWinds intrusion: credential theft (T1078), Kerberoasting (T1558.003), RDP lateral movement (T1021.001), and HTTPS C2 (T1071.001) are all confirmed in public incident reports (CISA Alert AA20-352A, Microsoft MSTIC analysis).

### 4.3 Algorithm Validation

All three algorithms (Dijkstra own, Bellman-Ford own, NetworkX Dijkstra) produce identical cost 1.635. Dijkstra and Bellman-Ford agree on all 9 path nodes; NetworkX selects T1482 at step 3 instead of T1087, both with w=0.75 (tie-breaking differs by heap insertion order, cost unchanged). BFS (unweighted) finds a path with accumulated cost 3.875, 137% above optimal, confirming weight informativeness.

Runtime on a 73-node, 653-edge graph: Dijkstra own 0.32 ms, Bellman-Ford own 0.82 ms, NetworkX 2.25 ms. Own Dijkstra is 7× faster than NetworkX on this graph.

### 4.4 FW-Betweenness (RQ2)

**Table 3. Top-7 techniques by FW-betweenness.**

| Rank | ID | Name | FW-betw | NX-betw (w) | Δ rank |
|---|---|---|---|---|---|
| 1 | T1078 | Valid Accounts | 1218 | 0.2294 | 0 |
| 2 | T1558.003 | Kerberoasting | 1044 | 0.2042 | 0 |
| 3 | T1087 | Account Discovery | 836 | 0.0818 | −2 |
| 4 | T1482 | Domain Trust Discovery | 836 | 0.0818 | −2 |
| 5 | T1021.001 | Remote Desktop Protocol | 702 | 0.1579 | +2 |
| 6 | T1213 | Data from Info Repositories | 420 | 0.1035 | +2 |
| 7 | T1059.001 | PowerShell | 194 | 0.0229 | 0 |

Spearman rank correlation between FW-betweenness and NetworkX weighted betweenness: **ρ = 0.9997**. Our implementation produces rankings equivalent to the reference algorithm.

T1078 (Valid Accounts) appears in 1,218 of all finite-cost optimal (i,j) pairs in the 73-node graph, identifying it as the universal structural bottleneck of the SolarWinds campaign graph.

### 4.5 Sensitivity Analysis

**Table 4. Weight sensitivity — Jaccard similarity of critical-path node sets.**

| Scenario | Description | Cost | Jaccard vs. base | Path identical |
|---|---|---|---|---|
| Base | Mitigations + CVE | 1.635 | 1.000 | Yes |
| −20% | All weights × 0.8 | 1.340 | 1.000 | Yes |
| +20% | All weights × 1.2 | 1.960 | 1.000 | Yes |
| CVE-free | Mitigation-only weights | 2.485 | 0.750 | No |

In the CVE-free scenario, T1558.003 (Kerberoasting) is replaced by T1539 (Steal Web Session Cookie) at step 2. Both belong to credential-access; the critical tactic remains unchanged. This demonstrates that the qualitative conclusion (credential-access is the critical bottleneck tactic) is robust across all scenarios, even when quantitative weights change.

### 4.6 Defensive Impact Simulation

**Table 5. Top-6 techniques by defensive impact (blocking one technique).**

| Rank | Technique | Impact | Δ cost | Δ% | In critical path |
|---|---|---|---|---|---|
| 1 | T1048.002 | TOTAL BLOCK | ∞ | ∞ | Yes |
| 2 | T1071.001 | High | +0.700 | +42.8% | Yes |
| 3 | T1213 | High | +0.375 | +22.9% | Yes |
| 4 | T1558.003 | Medium | +0.150 | +9.2% | Yes |
| 5 | T1021.001 | Medium | +0.075 | +4.6% | Yes |
| 6 | T1078 | Medium | +0.075 | +4.6% | Yes |

A notable finding: T1078 has the highest FW-betweenness (1,218) but ranks only 6th in defensive impact (+4.6%). This is because the graph contains multiple alternative techniques with similar weights in initial-access; removing T1078 forces the attacker to use T1133 (External Remote Services, w=0.05) or T1195.002 (Supply Chain, w=0.05) with near-identical cost. FW-betweenness measures structural centrality across all routes; defensive impact measures the specific increase in attacker cost for this campaign's threat model.

Blocking T1048.002, T1071.001, and T1213 together increases attacker cost by at least +66% and eliminates the primary critical path.

### 4.7 Multi-Campaign Generalization

**Table 6. Method applied to three ATT&CK campaigns.**

| Campaign | Actor | Techniques | Edges | Critical cost | Top-1 betw. | Time |
|---|---|---|---|---|---|---|
| SolarWinds Compromise | APT29 | 71 | 653 | 1.635 | T1078 | 23.7 ms |
| Operation Wocao | APT20 | 70 | 494 | 1.860 | T1078 | 25.4 ms |
| Operation Dream Job | Lazarus | 55 | 217 | 5.110 | T1553.002 | 24.0 ms |

Pairwise Jaccard similarity of critical-path node sets:
- SolarWinds vs. Wocao: 0.222 (shared: T1078, T1071.001)
- SolarWinds vs. Dream Job: 0.071 (shared: T1071.001)
- Wocao vs. Dream Job: 0.200 (shared: T1041, T1071.001)

Low Jaccard values confirm the method discriminates correctly between distinct threat actors. The higher cost for Dream Job (5.110 vs. 1.635) reflects Lazarus's use of techniques with more available mitigations and fewer CVE-weight overrides. T1071.001 (Web Protocols) appears in all three critical paths, suggesting that C2 channel control is a universally high-leverage defensive control.

---

## 5. Discussion

### 5.1 Critical Path Interpretation

The Dijkstra-found path maps closely to the documented SolarWinds intrusion sequence: the campaign's initial compromise via supply chain (T1195.002) feeds into credential theft (T1078), followed by Kerberoasting (T1558.003) for privilege escalation, RDP for lateral movement (T1021.001), and HTTP/S for C2 (T1071.001). The model's critical path aligns with CISA Alert AA20-352A without access to the alert—it is derived purely from the STIX graph structure.

This alignment suggests that the weight function (mitigation count + CVE severity) is a reasonable proxy for actual attacker path preference: techniques with strong CVEs and few mitigations are those most frequently exploited.

### 5.2 Betweenness vs. Defensive Impact

The divergence between FW-betweenness rank and defensive impact rank (T1078: rank 1 vs. rank 6) is a key finding. High betweenness indicates structural criticality across all routes, but does not imply high defensive leverage for a specific campaign's critical path when alternatives exist with equal weights.

This distinction has practical implications: betweenness identifies controls that would raise overall attacker cost across all possible routes; defensive impact identifies controls that specifically increase the cost of the observed/documented path. Both metrics are complementary and should be used together.

### 5.3 Limitations

**L1 — Inferred edges.** Edges connect techniques of consecutive tactics but are not directly observed in attack logs. The model assumes any technique in tactic k can precede any technique in tactic k+1 within the campaign; this overestimates the true transition space.

**L2 — Attacker rationality.** Dijkstra assumes a rational attacker minimizing cost. Real actors may choose suboptimal paths for stealth, tooling preference, or deception. The critical path represents the worst-case rational adversary, not a deterministic prediction.

**L3 — Historical knowledge base.** ATT&CK documents observed techniques; novel or unreported techniques are absent from the graph. The model is valid for the documented 2019–2020 threat model.

**L4 — Weight granularity.** With max_mit = 8, only 9 distinct mitigation-based weight values are possible, creating frequent ties. Ties are resolved by heap insertion order in Dijkstra, which is non-deterministic across implementations (both resolutions are correct).

**L5 — Single primary campaign.** Main analysis targets SolarWinds; generalization is demonstrated but not exhaustive. Further validation on a larger campaign sample is required for universal claims.

**L6 — Manual CVE association.** The CVE-to-technique mapping is based on public incident reports and analyst judgment; other analysts may map different CVEs.

### 5.4 Future Work

- Multi-campaign generalization across 10+ ATT&CK campaigns from different sectors and actors.
- Replace inferred edges with co-occurrence data from real incident datasets (VERIS, ATT&CK Evaluations).
- Monte Carlo simulation of attacker behavior for non-rational path selection.
- Automated CVE association via NVD API.
- Dynamic graph modeling to capture temporal evolution of campaigns.

---

## 6. Conclusion

We have demonstrated that MITRE ATT&CK STIX 2.1 data enables the construction of weighted attack graphs with real, interpretable edge weights derived from defensive evidence (mitigation counts and CVE severity). Applying Dijkstra's algorithm to the SolarWinds Compromise graph identifies a seven-technique critical path (cost 1.635) spanning credential-access, lateral-movement, collection, C2, and exfiltration tactics—consistent with documented forensic findings.

Floyd-Warshall betweenness identifies T1078 (Valid Accounts) as the universal structural bottleneck (1,218 optimal paths). Defensive impact simulation reveals that T1048.002 elimination blocks all ATTACKER→IMPACT routes; T1071.001 and T1213 each increase attacker cost by 22–43%. Together, three controls increase the minimum attacker cost by 66%.

Both algorithm implementations are validated against NetworkX (Spearman ρ = 0.9997, identical critical path cost). Weight sensitivity analysis confirms robustness: critical-path node sets are identical under ±20% weight perturbation (Jaccard = 1.0) and achieve Jaccard = 0.75 under CVE-free weights, with the critical tactic unchanged in all scenarios.

The method generalizes across three distinct ATT&CK campaigns with pairwise Jaccard similarities of 0.07–0.22, confirming correct threat actor discrimination. T1071.001 (Web Protocols) appears in all three critical paths, suggesting C2 channel control as a universally high-leverage defensive investment.

The complete pipeline—from STIX bundle download to interactive graph visualization—is reproducible from a single publicly available data source. All source code, results, and visualizations are available in the project repository.

---

## References

1. Sheyner, O., Haines, J., Jha, S., Lippmann, R., & Wing, J. (2002). Automated generation and analysis of attack graphs. *IEEE Symposium on Security and Privacy*.
2. Phillips, C., & Swiler, L. P. (1998). A graph-based system for network-vulnerability analysis. *NSPW '98*.
3. Milajerdi, S. M., et al. (2019). HOLMES: Real-time APT detection through correlation of suspicious information flows. *IEEE S&P*.
4. Peng, Y., et al. (2020). Constructing attack graphs for assessing industrial control system security. *IEEE Access*.
5. Idika, N., & Bhargava, B. (2012). Extending attack graph-based security metrics and aggregating their application. *IEEE TDSC*.
6. Brandes, U. (2001). A faster algorithm for betweenness centrality. *Journal of Mathematical Sociology*, 25(2), 163–177.
7. Noel, S., & Jajodia, S. (2008). Measuring security risk of networks using attack graphs. *IJSC*.
8. MITRE Corporation. (2023). MITRE ATT&CK Enterprise STIX 2.1. https://github.com/mitre/cti
9. CISA. (2020). Alert AA20-352A: Advanced Persistent Threat Compromise of Government Agencies, Critical Infrastructure, and Private Sector Organizations. US-CERT.
10. Microsoft MSTIC. (2020). Deep dive into the Solorigate second-stage activation: From SUNBURST to TEARDROP and Raindrop. Microsoft Security Blog.

---

*Manuscript prepared for submission. Target: IEEE Access / Computers & Security (Elsevier).*  
*All results reproducible from MITRE ATT&CK STIX 2.1 bundle with seed=42.*
