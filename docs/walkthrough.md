# Walkthrough: Git Project Initialization

I have successfully initialized the Git repository for the `risk-management` project.

## Phase 1: Bootstrap (Completed)

I have successfully bootstrapped the Risk Management Knowledge Graph with the following steps:

### 1. OWL Ontology
Created `sentries_ontology.owl` defining:
- **Classes:** `Person`, `Organization`, `Vessel`, `Aircraft`.
- **Properties:** `owned_by`, `family_member_of`, `leader_of`, `operates`.

### 2. Data Transformation & Loading
Implemented `scripts/flatten_ofac.py` and `scripts/load_data.py` to:
- Parse 121MB `SDN_ADVANCED.XML`.
- Reified triangulation of 18,535 records with and native naming properties (`label`).
- Synchronized all graphs with consistent icons and standardized labeling.

## Phase 2: Risk Analytics & Logic

### 1. Direct Risk Scoring
Developed `scripts/calculate_direct_risk.py` which assigns weight-based scores to all 18,535 entities using raw OFAC metadata (averaging 1.0 for SDN primary list).

### 2. Dynamic Risk Vetting (AQL Path-Based)
Implemented a high-fidelity risk exposure model based on BOM methodology. Instead of simple iteration, we now use native ArangoDB graph traversals to compute risk dynamically for any entity:
- **Calculation**: Computes all paths (1-3 hops) to sanctioned nodes.
- **Weights**: Multiplies `propagationWeight` (Ownership: 1.0, Leadership: 0.8, Family: 0.5) along each path.
- **Aggregation**: Sums the product of path weights and vertex risk scores to produce a final `inferredRisk` metric.

**Ontology Alignment**: Both `riskScore` and `inferredRisk` are formally defined as `DatatypeProperty` entities in `sentries_ontology.owl`.

## Phase 3: Analytics & Advanced Discovery

### 1. Expert Query Dashboard
Implemented `scripts/install_dashboard.py` which registers professional analytic tools directly in the ArangoDB UI:
- **`Sentries - Dynamic Risk Vetting`**: Performs real-time transitive risk calculation for any entity.
- **`Sentries - Top 20 Threat Organizations`**: Instant discovery of the highest-risk exposure entities.
- **`Sentries - Risk Concentration (Portfolio)`**: Identifies owners with significant indirect threat exposure across their assets.

## Verification Results

The Knowledge Graph is now a interactive intelligence platform. All analytics are live in the ArangoDB "Queries" dashboard, and all core data/scripts are committed to Git.

## Phase 4: Vetting Demonstration (Vetting Assessment)

I have implemented a specialized demonstration phase to assess the transitive risk of entities by association:
- **Synthetic Dataset**: Created `scripts/generate_test_data.py` to produce deterministic test cases.
- **Transitive Risk**: Demonstrated inheritance of risk through multi-hop ownership, leadership, and family ties.
- **Visual Distinction**: Configured visualizer rules to highlight synthetic nodes and edges (dashed lines).

For a detailed breakdown of the scenarios and results, see [Vetting Demonstration Results](docs/vetting_demo.md).
