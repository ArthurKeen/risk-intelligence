# Sentries: Risk Management Knowledge Graph

Sentries is an advanced graph intelligence platform for advanced demonstration of Arango AI that leverages the OFAC SDN dataset to identify and propagate transitive risk through complex ownership, leadership, and familial networks.

## Features
- **RDF-to-Property Graph**: Automatic schema mapping from OWL ontology to ArangoDB collections.
- **Dynamic Risk Vetting**: AQL path-based engine that calculates real-time threat exposure based on transitive relationships.
- **Visual Intelligence**: Custom ArangoDB Visualizer themes for structural exploration and risk heatmaps.
- **Expert Analytics**: Built-in library of saved queries for threat discovery and portfolio risk concentration.

## Architecture
1. **Ontology Layer**: Formal OWL definition of the risk domain.
2. **Ingestion Pipeline**: Memory-efficient XML parsing and batch loading API.
3. **Analytic Engine**: Native AQL traversals for high-fidelity risk calculation.

## Quick Start

### 1. Prerequisites
- python 3.8+
- ArangoDB 3.10+ (with Visualizer enabled)

### 2. Setup
```bash
git clone https://github.com/ArthurKeen/risk-management.git
cd risk-management
pip install -r requirements.txt
```

### 3. Configuration
Copy `template.env` to `.env` and provide your ArangoDB credentials:
```bash
cp template.env .env
# Edit .env with your endpoint and password
```

### 4. Run Pipeline
```bash
# 1. Flatten the OFAC XML
python3 scripts/flatten_ofac.py

# 2. Load ontology and data
python3 scripts/load_data.py

# 3. Install themes and dashboard
python3 scripts/install_theme.py
python3 scripts/install_dashboard.py

# 4. Calculate direct risk
python3 scripts/calculate_direct_risk.py

# 5. Run Vetting Demonstration (Optional)
python3 scripts/generate_test_data.py
python3 scripts/calculate_inferred_risk.py
```

## Usage
Open the ArangoDB UI and navigate to **Graphs** -> **KnowledgeGraph**. Select the **sentries_risk_heatmap** theme to visualize threats. Use the **Saved Queries** tab to run the dynamic vetting tools.

### Vetting Demonstration
To see how association with sanctioned entities affects risk scores for "clean" entities, run the Vetting Demonstration scripts (Step 5 above). Synthetic entities will appear with a purple color or vial icon, and their relationships will be dashed lines. See [docs/vetting_demo.md](docs/vetting_demo.md) for full scenario details.

## License
MIT
