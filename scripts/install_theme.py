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

# File paths
THEME_FILES = [
    "docs/sentries_standard.json",
    "docs/sentries_risk_heatmap.json"
]

def install_themes():
    # Initialize ArangoDB Client
    client = ArangoClient(hosts=ARANGO_ENDPOINT)
    db = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    
    # Ensure collection exists
    if not db.has_collection("_graphThemeStore"):
        db.create_collection("_graphThemeStore")
        print("Created collection: _graphThemeStore")
    
    theme_col = db.collection("_graphThemeStore")
    
    # Target Graphs
    target_graphs = ["OntologyGraph", "DataGraph", "KnowledgeGraph"]
    
    for theme_path in THEME_FILES:
        if not os.path.exists(theme_path):
            print(f"Error: Theme file not found: {theme_path}")
            continue

        with open(theme_path, 'r') as f:
            base_theme = json.load(f)
        
        for g_id in target_graphs:
            # 1. Install/Update the specific theme
            theme = base_theme.copy()
            theme["graphId"] = g_id
            
            # Add timestamps
            now = datetime.utcnow().isoformat() + "Z"
            theme["createdAt"] = now
            theme["updatedAt"] = now
            
            # Check if theme already exists
            existing = list(theme_col.find({
                "name": theme["name"],
                "graphId": g_id
            }))
            
            if existing:
                doc_key = existing[0]["_key"]
                theme_col.update({"_key": doc_key}, theme)
                print(f"Updated theme '{theme['name']}' for graph '{g_id}'")
            else:
                theme_col.insert(theme)
                print(f"Installed theme '{theme['name']}' for graph '{g_id}'")

    print("\nVisualizer Theme Setup Complete.")

if __name__ == "__main__":
    install_themes()
