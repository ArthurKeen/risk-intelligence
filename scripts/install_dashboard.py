import os
import json
from datetime import datetime
from dotenv import load_dotenv
from arango import ArangoClient

# Load environment variables
load_dotenv()

ARANGO_ENDPOINT = os.getenv("ARANGO_ENDPOINT")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "risk-management")

# Expert Queries Definitions
QUERIES = [
    {
        "name": "Sentries - Dynamic Risk Vetting",
        "value": """/* Dynamic Risk Vetting Query */
FOR v, e, p IN 1..3 ANY @entityID owned_by, leader_of, family_member_of
    // Validate path direction for risk flow
    FILTER (IS_SAME_COLLECTION('owned_by', e) ? e._from == @entityID : true)
    FILTER (IS_SAME_COLLECTION('leader_of', e) ? e._to == @entityID : true)
    
    // Compute path multiplier from edge weights
    LET pathMultiplier = PRODUCT(p.edges[*].propagationWeight)
    
    // Aggregate risk from sanctioned targets
    COLLECT entity = @entityID AGGREGATE 
        inheritedRisk = SUM(pathMultiplier * (v.riskScore || 0))
    
    LET baseScore = DOCUMENT(@entityID).riskScore || 0
    RETURN {
        label: DOCUMENT(@entityID).label,
        directRisk: baseScore,
        inferredRisk: inheritedRisk,
        totalExposure: baseScore + inheritedRisk
    }"""
    },
    {
        "name": "Sentries - Top 20 Threat Organizations",
        "value": """/* List the top 20 High-Risk Organizations based on total exposure */
FOR d IN Organization
  SORT (d.inferredRisk || d.riskScore || 0) DESC
  LIMIT 20
  RETURN { 
    label: d.label, 
    totalRisk: d.inferredRisk || d.riskScore || 0, 
    id: d._id 
  }"""
    },
    {
        "name": "Sentries - Risk Concentration (Portfolio)",
        "value": """/* Detect entities with the most high-risk subsidiaries/assets */
FOR owner IN Organization, Person
  LET portfolio = (FOR e IN owned_by FILTER e._to == owner._id RETURN e._from)
  FILTER LENGTH(portfolio) > 0
  LET maxRisk = MAX(FOR p IN portfolio RETURN DOCUMENT(p).inferredRisk || 0)
  SORT maxRisk DESC
  LIMIT 10
  RETURN { 
    owner: owner.label, 
    maxPortfolioThreat: maxRisk, 
    portfolioSize: LENGTH(portfolio) 
  }"""
    }
]

def install_dashboard():
    client = ArangoClient(hosts=ARANGO_ENDPOINT)
    db = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    
    if not db.has_collection("_editor_saved_queries"):
        db.create_collection("_editor_saved_queries", system=True)
        
    query_col = db.collection("_editor_saved_queries")
    
    print("Registering Sentries Expert Queries...")
    
    for q in QUERIES:
        # Check if query already exists by name
        existing = list(query_col.find({"name": q["name"]}))
        
        doc = {
            "name": q["name"],
            "value": q["value"],
            "updatedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        if existing:
            query_col.update_match({"name": q["name"]}, doc)
            print(f"Updated: {q['name']}")
        else:
            query_col.insert(doc)
            print(f"Installed: {q['name']}")

if __name__ == "__main__":
    install_dashboard()
