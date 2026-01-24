import os
from dotenv import load_dotenv
from arango import ArangoClient

load_dotenv()

def verify_risk():
    client = ArangoClient(hosts=os.getenv('ARANGO_ENDPOINT'))
    db = client.db(os.getenv('ARANGO_DATABASE'), username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))
    
    collections = ['Person', 'Organization', 'Vessel', 'Aircraft']
    print("Risk Score Distribution Verification:")
    
    for coll in collections:
        if not db.has_collection(coll):
            continue
            
        count = len(list(db.aql.execute(f"FOR d IN {coll} FILTER d.riskScore > 0 RETURN 1")))
        
        avg_q = f"FOR d IN {coll} FILTER d.riskScore > 0 COLLECT AGGREGATE a = AVERAGE(d.riskScore) RETURN a"
        avg_res = list(db.aql.execute(avg_q))
        avg = avg_res[0] if avg_res and avg_res[0] is not None else 0
        
        print(f"  {coll}: {count} nodes with riskScore. Average risk: {avg:.2f}")

if __name__ == "__main__":
    verify_risk()
