# Risk Intelligence - Business Requirements for Graph Analytics

**Project:** Risk Intelligence Knowledge Graph (Sentries)  
**Domain:** Sanctions Screening, PEP/AML, Transitive Risk  
**Date:** February 2026  
**Priority:** High

---

## Domain Description

### Industry & Business Context

Organizations in DoD (Vendor Vetting) and Financial Services (PEP/AML) sectors struggle to identify "indirect" risk. A vendor may not be on a sanctions list, but their majority owner might be. This project builds a Knowledge Graph that maps hidden relationships, calculates risk scores transitively, and identifies sanction-evasion patterns.

### Graph Structure Overview

The risk intelligence graph maps sanctioned entities, ownership, control, and familial networks.

**Vertex Collections (Nodes):**
- **Person**: Individuals, beneficial owners, sanctioned persons
- **Organization**: Corporate entities, shell companies
- **Vessel**: Maritime assets
- **Aircraft**: Aviation assets
- **SanctionedEntity**: OFAC and other sanctions list entities

**Edge Collections (Relationships):**
- **owned_by**: Ownership links with ownership percentage
- **family_member_of**: Familial relationships
- **leader_of**: Leadership/control links
- **operates**: Operation/control relationships

**Named Graph:** KnowledgeGraph (ArangoRDF OntologyGraph)

---

## Business Objectives

### Objectives (what the system must enable)

1. **Sanction-evasion detection** – Identify relationship patterns consistent with hiding control (e.g., layered ownership, nominee directors, circular ownership, shared intermediaries).
2. **Ownership chain analysis** – Trace control/beneficial ownership (UBO) through multi-hop corporate structures with weights (ownership percent) and roles (director/officer/operator).
3. **Transitive risk assessment** – Propagate risk from sanctioned/high-risk entities to indirectly connected entities using path depth and relationship weights.
4. **Shadow owner discovery** – Surface high-impact controllers who rarely appear explicitly as owners (centrality over control/leadership networks).
5. **Investigation acceleration** – Provide explainable outputs (paths, evidence, subgraphs) that analysts can act on and auditors can review.

### Use cases (agentic workflow targets)

1. **3-hop risk path for vendor onboarding**
   - **Input**: Candidate vendor `Organization/<id>` (or name to resolve) and max depth (default 3)
   - **Output**: Top \(N\) risk paths to sanctioned/PEP nodes with path evidence (edges, ownership %, roles), and an aggregate exposure score
2. **UBO identification through layered ownership**
   - **Input**: Target company, traversal rules (ownership-only vs ownership+control), depth cap (e.g., 5)
   - **Output**: Ranked list of ultimate beneficial owners (persons/orgs) with cumulative ownership and supporting ownership-chain paths
3. **Shadow owner / controller centrality**
   - **Input**: Subgraph scope (industry, geography, or all) and relationship types (leader_of, operates, owned_by)
   - **Output**: Top controllers by centrality (e.g., PageRank/Betweenness) with “why” explanations (key bridges, controlled entities)
4. **Sanction-evasion cell detection**
   - **Input**: Seed sanctioned entity (or risk threshold) and neighborhood radius (e.g., 2–3)
   - **Output**: Communities/clusters with high-risk density; shared intermediaries; suspicious motifs (cycles, hubs, repeated addresses)
5. **Ongoing monitoring / change impact**
   - **Input**: New/updated entity or relationship (e.g., new owner, new director)
   - **Output**: Delta in exposure score; newly introduced risk paths; entities newly within the risk neighborhood

### Domain terminology (minimum shared vocabulary)

- **OFAC**: U.S. Treasury Office of Foreign Assets Control; publishes sanctions programs and lists.
- **Sanctions list / watchlist**: A curated list of restricted entities (e.g., OFAC SDN); may include aliases and identifiers.
- **SDN**: Specially Designated Nationals and Blocked Persons List.
- **PEP**: Politically Exposed Person; higher AML risk due to political influence and corruption exposure.
- **AML / KYC**: Anti-Money Laundering / Know Your Customer controls and processes.
- **UBO / Beneficial Owner**: Natural person(s) who ultimately own/control an entity, directly or indirectly.
- **Ownership chain**: Directed path of `owned_by` edges from an entity to its owners (often multi-hop).
- **Control / influence**: Non-equity mechanisms (directors, officers, operators) captured via edges like `leader_of` and `operates`.
- **Entity resolution**: Deduping/linking records that refer to the same real-world entity (names, aliases, identifiers).
- **Transitive exposure**: Indirect risk due to connections to risky entities through ownership/control/family networks.

---

## Success Criteria

- **Explainable 3-hop tracing**: Trace a path from a clean company to a sanctioned entity through 3+ hops with human-readable evidence.
- **Ownership + control analytics**: Produce UBO candidates and controller centrality rankings on representative data volumes.
- **Sanction-evasion detection**: Identify high-risk clusters and repeated intermediaries (cells) around sanctioned seeds.
- **Agent-ready outputs**: Every analytic returns structured results suitable for downstream actions (save query, generate report, open subgraph).
