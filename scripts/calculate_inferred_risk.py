import os
from dotenv import load_dotenv
from arango import ArangoClient

# Load environment variables
load_dotenv()

ARANGO_ENDPOINT = os.getenv("ARANGO_ENDPOINT")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "risk-management")

def calculate_inferred_risk():
    client = ArangoClient(hosts=ARANGO_ENDPOINT)
    db = client.db(ARANGO_DATABASE, username=os.getenv("ARANGO_USERNAME"), password=os.getenv("ARANGO_PASSWORD"))
    
    collections = ["Person", "Organization", "Vessel", "Aircraft"]
    
    print("Initializing inferredRisk from direct riskScore...")
    for coll in collections:
        if not db.has_collection(coll): continue
        db.aql.execute(f"""
            FOR d IN {coll}
                UPDATE d WITH {{ inferredRisk: d.riskScore || 0 }} IN {coll}
        """)

    # Propagation Rules:
    # 1. owned_by: from (owned) inherits from to (owner) * 1.0
    # 2. leader_of: to (entity) inherits from from (leader) * 0.8
    # 3. family_member_of: symmetrical * 0.5
    
    iterations = 3
    for i in range(1, iterations + 1):
        print(f"Iteration {i}/{iterations}: Propagating risk...")
        
        # We'll calculate potential increases and apply the max
        # Using a temporary structure or multiple AQL passes
        # Pass 1: Ownership (from inherits from to)
        db.aql.execute("""
            FOR edge IN owned_by
                LET owner = DOCUMENT(edge._to)
                LET owned = DOCUMENT(edge._from)
                FILTER owner.inferredRisk > 0
                LET newRisk = owner.inferredRisk * 1.0
                FILTER newRisk > (owned.inferredRisk || 0)
                UPDATE owned WITH { inferredRisk: newRisk } IN @@coll
        """, bind_vars={"@coll": "Person"}) # Need to do for all? 
        
        # Actually, let's write a more generic multi-collection update logic
        
        # Pass 1: Ownership (Propagate to any entity that is owned)
        for target_coll in collections:
            db.aql.execute(f"""
                FOR edge IN owned_by
                    FILTER IS_SAME_COLLECTION('{target_coll}', edge._from)
                    LET owner = DOCUMENT(edge._to)
                    LET owned = DOCUMENT(edge._from)
                    FILTER owner != null AND owner.inferredRisk > 0
                    LET newRisk = owner.inferredRisk * 1.0
                    FILTER newRisk > (owned.inferredRisk || 0)
                    UPDATE owned WITH {{ inferredRisk: newRisk }} IN {target_coll}
            """)

        # Pass 2: Leadership (Leader -> Org)
        db.aql.execute("""
            FOR edge IN leader_of
                LET leader = DOCUMENT(edge._from)
                LET entity = DOCUMENT(edge._to)
                FILTER leader != null AND leader.inferredRisk > 0
                LET newRisk = leader.inferredRisk * 0.8
                FILTER newRisk > (entity.inferredRisk || 0)
                UPDATE entity WITH { inferredRisk: newRisk } IN Organization
        """)

        # Pass 3: Family (Symmetrical)
        db.aql.execute("""
            FOR edge IN family_member_of
                LET p1 = DOCUMENT(edge._from)
                LET p2 = DOCUMENT(edge._to)
                
                // Risk from p1 to p2
                FILTER p1 != null AND p1.inferredRisk > 0
                LET riskToP2 = p1.inferredRisk * 0.5
                IF riskToP2 > (p2.inferredRisk || 0)
                    UPDATE p2 WITH { inferredRisk: riskToP2 } IN Person
                
                // Risk from p2 to p1
                FILTER p2 != null AND p2.inferredRisk > 0
                LET riskToP1 = p2.inferredRisk * 0.5
                IF riskToP1 > (p1.inferredRisk || 0)
                    UPDATE p1 WITH { inferredRisk: riskToP1 } IN Person
        """)
        # Note: The Family AQL needs fixing because IF is not allowed in standard AQL like that
        # Re-writing Family Logic...
        
    print("Inferred risk calculation complete.")

def run_propagation_iteration(db, colls):
    # Unified propagation query for efficiency
    # Pass 1: Ownership
    for c in colls:
        db.aql.execute(f"FOR e IN owned_by FILTER IS_SAME_COLLECTION('{c}', e._from) LET o = DOCUMENT(e._to) FILTER o != null AND o.inferredRisk > 0 LET nr = o.inferredRisk * 1.0 FILTER nr > (DOCUMENT(e._from).inferredRisk || 0) UPDATE DOCUMENT(e._from) WITH {{ inferredRisk: nr }} IN {c}")
    
    # Pass 2: Leadership
    db.aql.execute("FOR e IN leader_of LET l = DOCUMENT(e._from) FILTER l != null AND l.inferredRisk > 0 LET nr = l.inferredRisk * 0.8 LET ent = DOCUMENT(e._to) FILTER ent != null AND nr > (ent.inferredRisk || 0) UPDATE ent WITH { inferredRisk: nr } IN Organization")
    
    # Pass 3: Family (Two steps for symmetry)
    db.aql.execute("FOR e IN family_member_of LET p1 = DOCUMENT(e._from) LET p2 = DOCUMENT(e._to) FILTER p1 != null AND p1.inferredRisk > 0 LET nr = p1.inferredRisk * 0.5 FILTER p2 != null AND nr > (p2.inferredRisk || 0) UPDATE p2 WITH { inferredRisk: nr } IN Person")
    db.aql.execute("FOR e IN family_member_of LET p1 = DOCUMENT(e._from) LET p2 = DOCUMENT(e._to) FILTER p2 != null AND p2.inferredRisk > 0 LET nr = p2.inferredRisk * 0.5 FILTER p1 != null AND nr > (p1.inferredRisk || 0) UPDATE p1 WITH { inferredRisk: nr } IN Person")

if __name__ == "__main__":
    # Actually implementing the clean 3-iteration loop
    load_dotenv()
    client = ArangoClient(hosts=os.getenv("ARANGO_ENDPOINT"))
    db = client.db(os.getenv("ARANGO_DATABASE"), username=os.getenv("ARANGO_USERNAME"), password=os.getenv("ARANGO_PASSWORD"))
    
    colls = ["Person", "Organization", "Vessel", "Aircraft"]
    
    # Init
    for c in colls:
        if db.has_collection(c):
            db.aql.execute(f"FOR d IN {c} UPDATE d WITH {{ inferredRisk: d.riskScore || 0 }} IN {c}")
    
    for i in range(1, 4):
       print(f"Propagating iteration {i}...")
       run_propagation_iteration(db, colls)
    
    print("Done.")
