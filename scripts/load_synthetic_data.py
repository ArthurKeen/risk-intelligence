"""
load_synthetic_data.py

Loads synthetic demo parties and relationships from:
  data/synthetic_parties.csv
  data/synthetic_relationships.csv

Runs after the real data is in place. Safe to re-run (idempotent via overwrite=True).
Does NOT reload the ontology or touch real data collections.

Run:
    python scripts/load_synthetic_data.py
    python scripts/calculate_inferred_risk.py   # re-propagate after loading
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import apply_config_to_env, get_arango_config, load_dotenv, sanitize_url

from arango import ArangoClient

SYNTHETIC_PARTIES_CSV = "data/synthetic_parties.csv"
SYNTHETIC_RELATIONSHIPS_CSV = "data/synthetic_relationships.csv"

COLLECTION_MAP = {"4": "Person", "3": "Organization", "1": "Vessel", "2": "Aircraft"}
EDGE_MAP = {
    "15003": "owned_by",
    "15004": "family_member_of",
    "91725": "leader_of",
    "92019": "operates",
}


def load_synthetic_data():
    load_dotenv()
    cfg = get_arango_config()
    apply_config_to_env(cfg)

    print(f"Connecting to ArangoDB ({cfg.mode}): {sanitize_url(cfg.url)}")
    print(f"Database: {cfg.database}\n")

    client = ArangoClient(hosts=cfg.url)
    db = client.db(cfg.database, username=cfg.username, password=cfg.password)

    # ------------------------------------------------------------------
    # 1. Load synthetic parties
    # ------------------------------------------------------------------
    print(f"Loading synthetic parties from {SYNTHETIC_PARTIES_CSV}...")
    batches: dict[str, list] = {}
    party_to_col: dict[str, str] = {}

    # First build party_to_col for ALL real parties (needed for cross-refs in relationships)
    for coll in COLLECTION_MAP.values():
        if db.has_collection(coll):
            cursor = db.aql.execute(f"FOR d IN {coll} RETURN d._key")
            for key in cursor:
                party_to_col[key] = coll

    with open(SYNTHETIC_PARTIES_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            party_id = str(row["party_id"])
            col_name = COLLECTION_MAP.get(str(row["party_type"]), "Entity")
            doc = {
                "_key": party_id,
                "primaryName": row["primary_name"],
                "label": row["primary_name"],
                "party_id": party_id,
                "dataSource": "Synthetic",
                "scenario": row.get("scenario", ""),
            }
            risk_score = row.get("risk_score", "").strip()
            if risk_score:
                doc["riskScore"] = float(risk_score)

            batches.setdefault(col_name, []).append(doc)
            party_to_col[party_id] = col_name

    for col_name, docs in batches.items():
        if db.has_collection(col_name):
            db.collection(col_name).import_bulk(docs, overwrite=True)
            print(f"  Upserted {len(docs)} synthetic {col_name} documents")

    # ------------------------------------------------------------------
    # 2. Load synthetic relationships
    # ------------------------------------------------------------------
    print(f"\nLoading synthetic relationships from {SYNTHETIC_RELATIONSHIPS_CSV}...")
    edge_batches: dict[str, list] = {}
    skipped = 0

    with open(SYNTHETIC_RELATIONSHIPS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            from_p = row["from_party"]
            to_p = row["to_party"]
            rel_type = row["rel_type"]
            edge_col = EDGE_MAP.get(rel_type)

            if not edge_col:
                continue

            from_col = party_to_col.get(from_p)
            to_col = party_to_col.get(to_p)

            if not from_col or not to_col:
                print(f"  [WARN] Unknown party in relationship: {from_p} → {to_p}")
                skipped += 1
                continue

            doc = {
                "_from": f"{from_col}/{from_p}",
                "_to": f"{to_col}/{to_p}",
                "rel_type_id": rel_type,
                "label": edge_col,
                "dataSource": "Synthetic",
            }
            edge_batches.setdefault(edge_col, []).append(doc)

    for edge_col, docs in edge_batches.items():
        if db.has_collection(edge_col):
            db.collection(edge_col).import_bulk(docs, overwrite=True)
            print(f"  Upserted {len(docs)} synthetic {edge_col} edges")

    if skipped:
        print(f"  Skipped {skipped} relationships with unresolved party IDs")

    # ------------------------------------------------------------------
    # 3. Initialise inferredRisk on synthetic parties (riskScore || 0)
    # ------------------------------------------------------------------
    print("\nInitialising inferredRisk on synthetic parties...")
    for col_name in COLLECTION_MAP.values():
        if db.has_collection(col_name):
            db.aql.execute(
                f"""
                FOR d IN {col_name}
                    FILTER d.dataSource == 'Synthetic'
                    UPDATE d WITH {{ inferredRisk: d.riskScore || 0 }} IN {col_name}
                """
            )

    print("\nDone. Now run: python scripts/calculate_inferred_risk.py")


if __name__ == "__main__":
    load_synthetic_data()
