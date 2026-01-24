import os
import csv
from dotenv import load_dotenv
from arango import ArangoClient
from arango_rdf import ArangoRDF

# Load environment variables
load_dotenv()

ARANGO_ENDPOINT = os.getenv("ARANGO_ENDPOINT")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "risk-management")

# File paths
ONTOLOGY_PATH = "sentries_ontology.owl"
PARTIES_CSV = "data/parties.csv"
RELATIONSHIPS_CSV = "data/relationships.csv"

def load_data():
    # Initialize ArangoDB Client
    client = ArangoClient(hosts=ARANGO_ENDPOINT)
    sys_db = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    
    # Create database if not exists
    if not sys_db.has_database(ARANGO_DATABASE):
        sys_db.create_database(ARANGO_DATABASE)
    
    db = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    
    # Initialize ArangoRDF
    adp = ArangoRDF(db)
    
    from rdflib import Graph
    
    print(f"Loading ontology from {ONTOLOGY_PATH}...")
    # Load ontology into a rdflib Graph
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="xml")
    
    # Load ontology into ArangoDB to set up collections
    adp.rdf_to_arangodb_by_pgt(
        name="OntologyGraph",
        rdf_graph=g
    )
    
    # Delete the redundant SentriesRisk graph if it was created previously
    if db.has_graph("SentriesRisk"):
        db.delete_graph("SentriesRisk")
        print("Deleted redundant SentriesRisk graph.")
    
    print("Ontology loaded. Now importing CSV data...")
    
    # Map CSV SubType IDs to ArangoDB collections
    collection_map = {
        "4": "Person",
        "3": "Organization",
        "1": "Vessel",
        "2": "Aircraft"
    }
    
    # Map CSV Relationship IDs to ArangoDB edge collections
    edge_map = {
        "15003": "owned_by",
        "15004": "family_member_of",
        "91725": "leader_of",
        "92019": "operates"
    }

    # Ensure collections exist
    for col in list(collection_map.values()) + list(edge_map.values()):
        if not db.has_collection(col):
            if col in edge_map.values():
                db.create_collection(col, edge=True)
            else:
                db.create_collection(col)

    # Batch Import Parties
    print("Importing parties in batches...")
    batches = {} 
    party_to_col = {} 
    
    with open(PARTIES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            party_id = str(row['party_id'])
            name = str(row['primary_name'])
            subtype = str(row['party_type'])
            col_name = collection_map.get(subtype, "Entity")
            
            doc = {
                "_key": party_id,
                "primaryName": name,
                "label": name, # Standardized property for visualizer
                "party_id": party_id
            }
            
            if col_name not in batches:
                batches[col_name] = []
            batches[col_name].append(doc)
            party_to_col[party_id] = col_name

    # Mapping for ontology classes
    class_map = {
        "Person": "Class/4254344209254636453",
        "Organization": "Class/2686369784577023745",
        "Vessel": "Class/18357045211339981443",
        "Aircraft": "Class/8751360868399758229"
    }

    all_type_edges = []
    for col_name, docs in batches.items():
        print(f"Loading {len(docs)} to {col_name}...")
        db.collection(col_name).import_bulk(docs, overwrite=True)
        
        target_class = class_map.get(col_name)
        if target_class:
            all_type_edges.extend([
                {"_from": f"{col_name}/{doc['_key']}", "_to": target_class, "label": "type", "_label": "type"}
                for doc in docs
            ])
            
    if all_type_edges:
        print(f"Loading {len(all_type_edges)} total type edges...")
        db.collection("type").import_bulk(all_type_edges, overwrite=True)

    # Sync Ontology Labels to 'label' attribute
    print("Syncing ontology labels...")
    ontology_colls = ["Class", "Property", "ObjectProperty", "Ontology", "domain", "range", "subClassOf", "type"]
    for oc in ontology_colls:
        if db.has_collection(oc):
            db.aql.execute(f"FOR d IN {oc} FILTER d._label != null AND d.label == null UPDATE d WITH {{ label: d._label }} IN {oc}")

    # Batch Import Relationships
    print("Importing relationships in batches...")
    edge_batches = {} 
    
    with open(RELATIONSHIPS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_p = row['from_party']
            to_p = row['to_party']
            rel_type = row['rel_type']
            edge_col = edge_map.get(rel_type)
            
            if not edge_col:
                continue
                
            from_col = party_to_col.get(from_p)
            to_col = party_to_col.get(to_p)
            
            if from_col and to_col:
                doc = {
                    "_from": f"{from_col}/{from_p}",
                    "_to": f"{to_col}/{to_p}",
                    "rel_type_id": rel_type,
                    "label": edge_col # Standard label
                }
                if edge_col not in edge_batches:
                    edge_batches[edge_col] = []
                edge_batches[edge_col].append(doc)

    for edge_col, docs in edge_batches.items():
        print(f"Loading {len(docs)} to {edge_col}...")
        db.collection(edge_col).import_bulk(docs, overwrite=True)

    # Define 3 Graphs
    print("Defining graphs...")
    ont_vertices = ["Class", "Property", "ObjectProperty", "Ontology"]
    data_vertices = ["Person", "Organization", "Vessel", "Aircraft"]
    all_vertices = ont_vertices + data_vertices

    ontology_edges = [
        {"edge_collection": "domain", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "range", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "subClassOf", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "type", "from_vertex_collections": all_vertices, "to_vertex_collections": ont_vertices}
    ]
    if not db.has_graph("OntologyGraph"):
        db.create_graph("OntologyGraph", edge_definitions=ontology_edges)
    else:
        g = db.graph("OntologyGraph")
        for ed in ontology_edges:
            if any(e['edge_collection'] == ed['edge_collection'] for e in g.edge_definitions()):
                g.replace_edge_definition(ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
            else:
                g.create_edge_definition(ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
    print("Created/Updated OntologyGraph")

    data_edges = [
        {"edge_collection": "owned_by", "from_vertex_collections": data_vertices, "to_vertex_collections": data_vertices},
        {"edge_collection": "family_member_of", "from_vertex_collections": data_vertices, "to_vertex_collections": data_vertices},
        {"edge_collection": "leader_of", "from_vertex_collections": data_vertices, "to_vertex_collections": data_vertices},
        {"edge_collection": "operates", "from_vertex_collections": data_vertices, "to_vertex_collections": data_vertices}
    ]
    if not db.has_graph("DataGraph"):
        db.create_graph("DataGraph", edge_definitions=data_edges)
    else:
        g = db.graph("DataGraph")
        for ed in data_edges:
            if any(e['edge_collection'] == ed['edge_collection'] for e in g.edge_definitions()):
                g.replace_edge_definition(ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
            else:
                g.create_edge_definition(ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
    print("Created/Updated DataGraph")

    knowledge_edges = ontology_edges + data_edges
    if not db.has_graph("KnowledgeGraph"):
        db.create_graph("KnowledgeGraph", edge_definitions=knowledge_edges)
    else:
        g = db.graph("KnowledgeGraph")
        for ed in knowledge_edges:
            if any(e['edge_collection'] == ed['edge_collection'] for e in g.edge_definitions()):
                g.replace_edge_definition(ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
            else:
                g.create_edge_definition(ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
    print("Created/Updated KnowledgeGraph")
    print("Data loading and graph definitions completed.")

if __name__ == "__main__":
    load_data()
