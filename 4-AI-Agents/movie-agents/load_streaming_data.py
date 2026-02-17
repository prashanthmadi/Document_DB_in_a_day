"""
Load streaming platform data into Azure DocumentDB.

This script loads the pre-generated streaming_platforms.json into the
'streaming_platforms' collection in your DocumentDB database.

Usage:
    python load_streaming_data.py

Prerequisites:
    - Root .env file configured with DOCUMENTDB_CONNECTION_STRING and DOCUMENTDB_DATABASE
    - DocumentDB cluster running (Module 1)
    - Movies already loaded in 'movies' collection (Module 3)
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from project root .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def main():
    # Connect to DocumentDB
    connection_string = os.getenv("DOCUMENTDB_CONNECTION_STRING")
    database_name = os.getenv("DOCUMENTDB_DATABASE", "trainingdb")

    if not connection_string:
        print("❌ Error: DOCUMENTDB_CONNECTION_STRING not set in .env")
        print("   Copy .env.template to .env in the project root and fill in your connection string.")
        return

    print(f"Connecting to DocumentDB...")
    client = MongoClient(connection_string)
    db = client[database_name]

    # Load streaming data from JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(script_dir, "streaming_platforms.json")

    print(f"Reading streaming data from {data_file}...")
    with open(data_file, "r", encoding="utf-8") as f:
        streaming_data = json.load(f)

    print(f"Loaded {len(streaming_data)} movie streaming records")

    # Drop existing collection if it exists (for re-runs)
    collection_name = "streaming_platforms"
    if collection_name in db.list_collection_names():
        print(f"Dropping existing '{collection_name}' collection...")
        db[collection_name].drop()

    # Insert data
    print(f"Inserting into '{collection_name}' collection...")
    collection = db[collection_name]
    result = collection.insert_many(streaming_data)

    print(f"\n✅ Successfully loaded {len(result.inserted_ids)} streaming records")
    print(f"   Database: {database_name}")
    print(f"   Collection: {collection_name}")

    # Create index on title for fast lookups
    print("Creating index on 'title' field...")
    collection.create_index("title", unique=True)

    # Create index on streaming platform for platform searches
    print("Creating index on 'streaming.platform' field...")
    collection.create_index("streaming.platform")

    print("\n✅ Indexes created successfully")

    # Verify
    count = collection.count_documents({})
    sample = collection.find_one({"title": "Inception"})
    print(f"\nVerification:")
    print(f"  Total documents: {count}")
    print(f"  Sample (Inception): {json.dumps(sample, indent=2, default=str)}")

    client.close()


if __name__ == "__main__":
    main()
