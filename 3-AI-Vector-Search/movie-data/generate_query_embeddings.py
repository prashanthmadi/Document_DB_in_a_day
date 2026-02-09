"""
Pre-generate query embeddings for common movie search scenarios
These will be used in the tutorial so users don't need Azure OpenAI access
"""

from openai import AzureOpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01"
)

def generate_embedding(text, dimensions=256):
    """Generate embedding with reduced dimensions for smaller file size"""
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small")
    response = client.embeddings.create(
        model=model,
        input=text,
        dimensions=dimensions  # Reduce from 1536 to 256 for smaller files
    )
    return response.data[0].embedding

# Query scenarios for the tutorial
queries = [
    {
        "query": "mind-bending sci-fi thriller with complex plot",
        "description": "Looking for movies like Inception or The Matrix",
        "expected_matches": ["Inception", "The Matrix", "Interstellar"]
    },
    {
        "query": "heartwarming animated family movie",
        "description": "Family-friendly animation with emotional story",
        "expected_matches": ["Toy Story", "Finding Nemo", "The Lion King"]
    },
    {
        "query": "intense crime drama with mob violence",
        "description": "Gritty crime films like Godfather or Goodfellas",
        "expected_matches": ["The Godfather", "Goodfellas", "The Departed"]
    },
    {
        "query": "epic fantasy adventure with battles",
        "description": "Large-scale fantasy with heroes and battles",
        "expected_matches": ["The Lord of the Rings", "Braveheart", "Gladiator"]
    },
    {
        "query": "psychological thriller with dark atmosphere",
        "description": "Dark, suspenseful films that mess with your mind",
        "expected_matches": ["Se7en", "The Silence of the Lambs", "Fight Club"]
    }
]

print("Generating query embeddings...\n")

query_embeddings = []
for q in queries:
    embedding = generate_embedding(q["query"])
    query_embeddings.append({
        "query": q["query"],
        "description": q["description"],
        "expected_matches": q["expected_matches"],
        "embedding": embedding
    })
    print(f"✅ Generated: \"{q['query']}\"")

# Save to file
with open('query_embeddings.json', 'w') as f:
    json.dump(query_embeddings, f, indent=2)

print(f"\n✅ Saved {len(query_embeddings)} query embeddings to query_embeddings.json")
