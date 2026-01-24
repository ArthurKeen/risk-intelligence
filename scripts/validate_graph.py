import os
from dotenv import load_dotenv
from arango import ArangoClient

load_dotenv()

def check_missing_targets():
    client = ArangoClient(hosts=os.getenv('ARANGO_ENDPOINT'))
    db = client.db(os.getenv('ARANGO_DATABASE'), username=os.getenv('ARANGO_USERNAME'), password=os.getenv('ARANGO_PASSWORD'))
    
    edge_cols = ['type', 'domain', 'range', 'subClassOf']
    for col in edge_cols:
        if not db.has_collection(col):
            continue
            
        print(f"\nChecking targets in edge collection: {col}")
        
        # Find edges where the target vertex doesn't exist
        aql = """
        FOR d IN @@col
            LET target = DOCUMENT(d._to)
            FILTER target == null
            LIMIT 5
            RETURN d._to
        """
        missing = list(db.aql.execute(aql, bind_vars={'@col': col}))
        if missing:
            print(f"  [FAIL] Found edges pointing to non-existent vertices: {missing}")
        else:
            print(f"  [PASS] All edges in {col} have valid targets.")
            
        # Find edges where the source vertex doesn't exist
        aql_src = """
        FOR d IN @@col
            LET src = DOCUMENT(d._from)
            FILTER src == null
            LIMIT 5
            RETURN d._from
        """
        missing_src = list(db.aql.execute(aql_src, bind_vars={'@col': col}))
        if missing_src:
            print(f"  [FAIL] Found edges originating from non-existent vertices: {missing_src}")
        else:
            print(f"  [PASS] All edges in {col} have valid sources.")

if __name__ == "__main__":
    check_missing_targets()
