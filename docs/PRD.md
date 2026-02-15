This Product Requirements Document (PRD) outlines the framework for building a **Risk Management Knowledge Graph** (Project "Sentries"). It leverages the OFAC dataset to demonstrate transitive risk, entity resolution, and semantic reasoning within ArangoDB.

---

# PRD: ArangoDB Risk Management Knowledge Graph

**Project Version:** 1.0

**Status:** Phase 1 (Bootstrap)

**Primary Objective:** To demonstrate the identification and propagation of proportional risk from sanctioned entities through complex ownership, control, and familial networks using a multi-model approach (Graph, RDF, Document).

---

## 1. Executive Summary

Organizations in the DoD (Vendor Vetting) and Financial Services (PEP/AML) sectors struggle to identify "indirect" risk. A vendor may not be on a sanctions list, but their majority owner might be. This project builds a Knowledge Graph that maps these hidden relationships, calculates risk scores transitively, and provides multiple query interfaces (AQL, SPARQL, Cypher, Natural Language).

## 2. Data Strategy & Ingestion

### 2.1 Source Data

* **Initial Source:** OFAC Advanced XML (Sanctions list).
* **Expansion Sources:** Structured corporate registries (ETL) and unstructured news/reports (GraphRAG).

### 2.2 Data Transformation (Flattening)

* **Requirement:** Develop a pre-processing pipeline to convert OFAC XML into flattened CSV.
* **Naming Convention:** Use "dot notation" for nested structures to ensure compatibility with `arangoimport`.
* *Example:* `DistinctParty.Profile.Identity.Alias.Name` -> `alias.name`.
* *Example:* `DistinctParty.Address.ZipCode` -> `address.zip`.



### 2.3 Entity Resolution (ER)

* **Library:** Integration of `arango-entity-resolution`.
* **Function:** Resolve identities where names are transliterated differently or where high-integrity identifiers (Passport numbers, EINs) overlap.
* **Objective:** Create "Golden Records" for entities appearing across multiple data sources.

---

## 3. Ontology & Schema Mapping

### 3.1 The Risk Ontology (OWL)

* **Core Classes:** `Person`, `Organization`, `SanctionedEntity`, `IdentityDocument`, `Location`.
* **Object Properties (Edges):** `ownedBy`, `controls`, `childOf`, `spouseOf`, `directorOf`.
* **Data Properties:** `riskScore`, `sanctionDate`, `ownershipPercentage`.

### 3.2 Physical Schema Implementation

Using **ArangoRDF**, the OWL ontology will define the physical Property Graph:

* **OWL Classes**  **ArangoDB Vertex Collections.**
* **Object Properties**  **ArangoDB Edge Collections.**
* **Type Properties**  **JSON fields** within documents.

---

## 4. Risk Analytics & Logic

### 4.1 Proportional Risk Propagation

* **Logic:** Risk is not binary; it is inherited. If Entity A is 100% sanctioned, and Entity A owns 50% of Entity B, Entity B inherits a specific proportional risk weight.
* **Implementation:** AQL Graph Traversal (shortest path and K-shortest paths) calculating an aggregate `risk_exposure` score based on the path depth and ownership weight.

### 4.2 Graph Algorithms

Integration with the `agentic-graph-analytics` to perform:

* **Centrality:** Identifying "Key Influencers" or "Shadow Owners" who control many entities but appear in fewer documents.
* **Community Detection:** Identifying "Sanction-Evasion Cells" or clusters of highly interconnected high-risk entities.

---

## 5. Multi-Model Query Interfaces

To demonstrate the flexibility of ArangoDB, the system must support:

* **AQL:** For native graph traversals and proportional risk calculations.
* **SPARQL (via ArangoSPARQL):** For semantic queries against the imported OWL ontology logic.
* **Cypher (via ArangoCypher):** To support users migrating from Neo4j or those preferring the pattern-matching syntax.
* **Natural Language (via Arango AQLizer):** A user-facing chat interface that converts "Show me all companies owned by sanctioned Russians in the UK" into an AQL query.

---

## 6. Visualization & UX

### 6.1 Visualization Themes

The system will support the enhanced Arango Visualizer with two distinct themes:

#### Theme A: Knowledge Graph (Structural)

* **Icons:** Specific icons for People (👤), Companies (🏢), and Vessels (🚢).
* **Colors:** Based on entity type.

#### Theme B: Risk Heatmap (Functional)

* **Node/Edge Coloring:** * **Red:** Directly Sanctioned / 90-100% Risk Score.
* **Orange/Yellow:** Indirectly linked / 40-89% Risk Score (Transitive Risk).
* **Green:** Vetted / Low Risk (<10% score).


* **Edge Thickness:** Proportional to `ownershipPercentage` or `controlStrength`.

---

## 7. Phase 1 Roadmap: "The Bootstrap"

1. **Week 1:** Finalize OWL Ontology for OFAC/Risk domain.
2. **Week 2:** Develop Python script to flatten OFAC XML to CSV using dot notation.
3. **Week 3:** Use **ArangoRDF** to initialize the physical collections and load CSV data via `arangoimport`.
4. **Week 4:** Implement a standard "Risk Propagation" AQL function.
5. **Week 5:** Configure Visualizer "Risk Theme" and demo AQLizer NL-to-AQL interface.

---

## 8. Success Criteria

* Successfully trace a path from a "Clean" company to a "Sanctioned" entity through at least 3 hops.
* Automated creation of 10+ collections (Vertices/Edges) via ArangoRDF from the OWL source.
* Demonstrate a SPARQL query and an AQL query returning the same result set on the same data.