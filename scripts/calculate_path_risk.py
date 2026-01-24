import os
from dotenv import load_dotenv
from arango import ArangoClient

# Load environment variables
load_dotenv()

ARANGO_ENDPOINT = os.getenv("ARANGO_ENDPOINT")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "risk-management")

def calculate_path_risk():
    client = ArangoClient(hosts=ARANGO_ENDPOINT)
    db = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    
    collections = ["Person", "Organization", "Vessel", "Aircraft"]
    
    # Path-based Risk Algorithm
    # For each node:
    # 1. Start at Node
    # 2. Traverse 1..3 hops
    # 3. Filter directions: 
    #    - owned_by: OUTBOUND (vetted -> owner)
    #    - leader_of: INBOUND (vetted -> leader)
    #    - family_member_of: ANY
    # 4. Calculate PRODUCT(edge.propagationWeight) * target.riskScore
    # 5. SUM all paths
    
    query = """
    LET baseScore = (doc.riskScore || 0)
    
    LET inheritedRisks = (
      FOR v, e, p IN 1..3 ANY doc._id owned_by, leader_of, family_member_of
        // Directional validation:
        // ownership flows from TO (parent) to FROM (child). Vetting child -> parent is OUTBOUND.
        // leadership flows from FROM (leader) to TO (org). Vetting org -> leader is INBOUND.
        FILTER (IS_SAME_COLLECTION('owned_by', e) ? e._from == doc._id : true)
        FILTER (IS_SAME_COLLECTION('leader_of', e) ? e._to == doc._id : true)
        
        LET pathMultiplier = PRODUCT(p.edges[*].propagationWeight)
        RETURN pathMultiplier * (v.riskScore || 0)
    )
    
    RETURN { 
        _key: doc._key, 
        inferredRisk: baseScore + SUM(inheritedRisks) 
    }
    """
    
    total_updated = 0
    for coll in collections:
        if not db.has_collection(coll): continue
        print(f"Calculating path-based risk for {coll}...")
        
        # We can run this in one AQL update if query complexity allowed, 
        # but for safety let's fetch in batches and update.
        cursor = db.aql.execute(f"FOR doc IN {coll} " + query)
        updates = []
        for result in cursor:
            updates.append(result)
            if len(updates) >= 1000:
                db.collection(coll).update_many(updates)
                total_updated += len(updates)
                updates = []
        
        if updates:
            db.collection(coll).update_many(updates)
            total_updated += len(updates)
            
    print(f"Successfully updated {total_updated} entities with path-based inferred risk.")

if __name__ == "__main__":
    calculate_path_risk()
