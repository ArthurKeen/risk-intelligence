# Risk Intelligence Domain Description

**Industry:** Risk Management / Sanctions Screening / PEP-AML  
**Focus:** Transitive Risk, Entity Resolution, Sanction Evasion Detection  
**Graph:** KnowledgeGraph (ArangoRDF)

---

## Domain Overview

### Industry & Business Context

The Risk Intelligence Knowledge Graph (Sentries) demonstrates identification and propagation of proportional risk from sanctioned/high-risk entities through complex ownership, control, and familial networks. Organizations need to identify indirect risk: a vendor may not be sanctioned, but their majority owner, controller, or close associate might be.

### Graph Structure Overview

**Core Vertex Collections:**
- **Person** – Individuals, beneficial owners, related parties
- **Organization** – Corporate entities including suspected shells
- **Vessel** – Maritime assets (OFAC)
- **Aircraft** – Aviation assets (OFAC)

**Edge Collections:**
- **owned_by** – Ownership with percentage
- **family_member_of** – Familial relationships
- **leader_of** – Leadership/control
- **operates** – Operation links

### Risk Analytics Focus

- **Centrality:** Key influencers, shadow owners who control many entities
- **Community Detection:** Sanction-evasion cells, high-risk clusters
- **Path Analysis:** Transitive exposure from clean to sanctioned
- **Proportional Risk:** Inherited risk based on ownership weight and path depth

---

## Objectives (analytics questions the graph should answer)

- **Sanction-evasion detection**: “Which entities form a tightly connected cell around a sanctioned seed?”
- **Ownership chain analysis**: “Who are the ultimate beneficial owners (UBOs) of company X?”
- **Explainable exposure**: “Why is entity X risky?” (return concrete paths and evidence, not just a score)
- **Shadow owner discovery**: “Who has outsized control/influence despite limited explicit ownership links?”
- **Cross-asset linkages**: “Which vessels/aircraft are operated/owned/controlled by entities linked to sanctions?”

## Use cases (canonical graph analytics tasks)

### 1) 3-hop exposure trace (vendor / counterparty screening)
- **Goal**: Find evidence of indirect exposure within a limited hop budget.
- **Typical pattern**: `Organization -> owned_by/leader_of/operates -> ... -> (Sanctioned/PEP)`
- **Return**: Top paths (ranked), hop count, relationship types, ownership %, and any sanction/PEP flags encountered.

### 2) Ownership chain & UBO roll-up
- **Goal**: Identify controlling persons and entities through layered ownership.
- **Typical pattern**: repeated `owned_by` edges; compute cumulative ownership across a path.
- **Return**: UBO candidates with cumulative ownership and supporting ownership-chain paths.

### 3) Shadow owners via centrality
- **Goal**: Surface controllers who sit on many paths (bridges) across ownership/control networks.
- **Typical pattern**: centrality on a subgraph (ownership + control + leadership).
- **Return**: ranked controllers plus “why” (high betweenness bridges, high PageRank hubs, etc.).

### 4) Sanction-evasion cells via community detection
- **Goal**: Detect clusters around sanctioned entities and their intermediaries.
- **Typical pattern**: community detection on neighborhoods; look for motifs (cycles, hubs, repeated intermediaries).
- **Return**: communities with risk density, shared intermediaries, and notable suspicious motifs.

---

## Domain terminology (glossary)

- **OFAC**: U.S. Treasury Office of Foreign Assets Control.
- **SDN**: Specially Designated Nationals and Blocked Persons List.
- **Sanctions list / watchlist**: Lists of restricted/high-risk entities (OFAC SDN, etc.) with aliases and identifiers.
- **PEP**: Politically Exposed Person.
- **AML / KYC**: Anti-Money Laundering / Know Your Customer.
- **UBO / beneficial owner**: Natural person(s) who ultimately own/control an entity.
- **Nominee director / straw owner**: Person/entity used to obscure true control.
- **Shell company**: Entity with limited operations used for concealment or structuring.
- **Entity resolution**: Matching/linking records that refer to the same real-world entity (names, aliases, identifiers).
- **Transitive exposure**: Risk inherited via indirect relationships (ownership/control/family).

## Sanction-evasion patterns (graph signals)

- **Layering**: long ownership chains through multiple intermediaries.
- **Circular ownership**: cycles in `owned_by` relationships.
- **Shared intermediaries**: the same person/org appears across many “clean” entities as officer/operator/owner.
- **Role-based control without equity**: `leader_of`/`operates` paths to sanctioned entities even when ownership is absent.
