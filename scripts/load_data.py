import os
import csv
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
from arango import ArangoClient
from arango_rdf import ArangoRDF

# Load environment variables
load_dotenv()

def _ensure_endpoint_has_port(url: str, default_port: int = 8529) -> str:
    if not url:
        return url
    try:
        u = urlparse(url)
        if u.port is not None:
            return url
        host = u.hostname or u.netloc
        if not host:
            return url
        netloc = f"{host}:{default_port}"
        return urlunparse((u.scheme, netloc, u.path or "", u.params, u.query, u.fragment))
    except Exception:
        return url


ARANGO_ENDPOINT = _ensure_endpoint_has_port(os.getenv("ARANGO_ENDPOINT") or "")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "risk-intelligence")

# File paths
ONTOLOGY_PATH = "sentries_ontology.owl"
PARTIES_CSV = "data/parties.csv"
RELATIONSHIPS_CSV = "data/relationships.csv"
SYNTHETIC_PARTIES_CSV = "data/synthetic_parties.csv"
SYNTHETIC_RELATIONSHIPS_CSV = "data/synthetic_relationships.csv"

SYNTHETIC_ID_PREFIX = "SYN-"

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

    # The ontology is static — only load it when the graph doesn't yet exist.
    # arango_rdf always calls create_edge_definition unconditionally, which raises
    # ERR 1921 if the graph already has those edge definitions (i.e. on re-runs).
    if db.has_graph("OntologyGraph"):
        print(f"OntologyGraph already exists — skipping ontology load.")
    else:
        from rdflib import Graph as RDFGraph

        print(f"Loading ontology from {ONTOLOGY_PATH}...")
        rdf_g = RDFGraph()
        rdf_g.parse(ONTOLOGY_PATH, format="xml")
        adp.rdf_to_arangodb_by_pgt(name="OntologyGraph", rdf_graph=rdf_g)
        print("Ontology loaded.")

    # Delete the redundant SentriesRisk graph if it was created previously
    if db.has_graph("SentriesRisk"):
        db.delete_graph("SentriesRisk")
        print("Deleted redundant SentriesRisk graph.")

    print("Now importing CSV data...")
    
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

    def _ingest_parties_csv(path: str, batches: dict, party_to_col: dict, synthetic: bool = False):
        if not os.path.exists(path):
            print(f"  [SKIP] {path} not found")
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                party_id = str(row['party_id'])
                name = str(row['primary_name'])
                subtype = str(row['party_type'])
                col_name = collection_map.get(subtype, "Entity")

                doc = {
                    "_key": party_id,
                    "primaryName": name,
                    "label": name,
                    "party_id": party_id,
                }

                if synthetic:
                    doc["dataSource"] = "Synthetic"
                    doc["scenario"] = row.get("scenario", "")
                    risk_score = row.get("risk_score", "").strip()
                    if risk_score:
                        doc["riskScore"] = float(risk_score)

                if col_name not in batches:
                    batches[col_name] = []
                batches[col_name].append(doc)
                party_to_col[party_id] = col_name

    _ingest_parties_csv(PARTIES_CSV, batches, party_to_col, synthetic=False)
    print(f"  Loaded real parties from {PARTIES_CSV}")

    _ingest_parties_csv(SYNTHETIC_PARTIES_CSV, batches, party_to_col, synthetic=True)
    print(f"  Loaded synthetic parties from {SYNTHETIC_PARTIES_CSV}")

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

    def _ingest_relationships_csv(path: str, edge_batches: dict, party_to_col: dict, synthetic: bool = False):
        if not os.path.exists(path):
            print(f"  [SKIP] {path} not found")
            return
        skipped = 0
        with open(path, 'r', encoding='utf-8') as f:
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

                if not from_col or not to_col:
                    skipped += 1
                    continue

                doc = {
                    "_from": f"{from_col}/{from_p}",
                    "_to": f"{to_col}/{to_p}",
                    "rel_type_id": rel_type,
                    "label": edge_col,
                }
                if synthetic:
                    doc["dataSource"] = "Synthetic"

                if edge_col not in edge_batches:
                    edge_batches[edge_col] = []
                edge_batches[edge_col].append(doc)
        if skipped:
            print(f"  [WARN] {path}: skipped {skipped} relationships (unknown party IDs)")

    _ingest_relationships_csv(RELATIONSHIPS_CSV, edge_batches, party_to_col, synthetic=False)
    print(f"  Loaded real relationships from {RELATIONSHIPS_CSV}")

    _ingest_relationships_csv(SYNTHETIC_RELATIONSHIPS_CSV, edge_batches, party_to_col, synthetic=True)
    print(f"  Loaded synthetic relationships from {SYNTHETIC_RELATIONSHIPS_CSV}")

    # Mapping for propagation weights
    weight_map = {
        "owned_by": 1.0,
        "leader_of": 0.8,
        "family_member_of": 0.5,
        "operates": 0.9
    }

    for edge_col, docs in edge_batches.items():
        print(f"Loading {len(docs)} to {edge_col}...")
        weight = weight_map.get(edge_col, 0.1)
        for doc in docs:
            doc["propagationWeight"] = weight
        db.collection(edge_col).import_bulk(docs, overwrite=True)

    # Define 3 Graphs
    print("Defining graphs...")
    ont_vertices = ["Class", "Property", "ObjectProperty", "Ontology"]
    data_vertices = ["Person", "Organization", "Vessel", "Aircraft"]
    all_vertices = ont_vertices + data_vertices

    # OntologyGraph should be ontology-only (no instance vertex collections like Person/Aircraft/Vessel).
    # Keep instance->Class typing edges for KnowledgeGraph, not OntologyGraph.
    ontology_edges_ontology_graph = [
        {"edge_collection": "domain", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "range", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "subClassOf", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
    ]
    ontology_edges_knowledge_graph = [
        {"edge_collection": "domain", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "range", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "subClassOf", "from_vertex_collections": ont_vertices, "to_vertex_collections": ont_vertices},
        {"edge_collection": "type", "from_vertex_collections": all_vertices, "to_vertex_collections": ont_vertices},
    ]
    def _upsert_edge_def(g, edge_collection, from_vertex_collections, to_vertex_collections):
        """Replace edge definition if it exists, create it otherwise.

        Uses try/except rather than a pre-check because python-arango's
        edge_definitions() may return raw ArangoDB keys ('collection') instead
        of the normalised keys ('edge_collection') depending on version, causing
        the pre-check to silently return False and fall through to create —
        which then raises ERR 1921 when the definition already exists.
        """
        try:
            g.replace_edge_definition(edge_collection, from_vertex_collections, to_vertex_collections)
        except Exception:
            try:
                g.create_edge_definition(edge_collection, from_vertex_collections, to_vertex_collections)
            except Exception as e2:
                print(f"  [WARN] Could not upsert edge definition '{edge_collection}': {e2}")

    if not db.has_graph("OntologyGraph"):
        db.create_graph("OntologyGraph", edge_definitions=ontology_edges_ontology_graph)
    else:
        g = db.graph("OntologyGraph")
        for ed in ontology_edges_ontology_graph:
            _upsert_edge_def(g, ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])

        # Remove 'type' from OntologyGraph — it belongs only to KnowledgeGraph.
        try:
            g.delete_edge_definition("type", purge=False)
        except Exception:
            pass  # not present, nothing to do

        # Remove instance vertex collections from OntologyGraph (keep ontology-only).
        for vcol in data_vertices:
            try:
                g.delete_vertex_collection(vcol, purge=False)
            except Exception:
                pass
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
            _upsert_edge_def(g, ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
    print("Created/Updated DataGraph")

    knowledge_edges = ontology_edges_knowledge_graph + data_edges
    if not db.has_graph("KnowledgeGraph"):
        db.create_graph("KnowledgeGraph", edge_definitions=knowledge_edges)
    else:
        g = db.graph("KnowledgeGraph")
        for ed in knowledge_edges:
            _upsert_edge_def(g, ed['edge_collection'], ed['from_vertex_collections'], ed['to_vertex_collections'])
    print("Created/Updated KnowledgeGraph")
    print("Data loading and graph definitions completed.")

if __name__ == "__main__":
    load_data()
