"""
Pre-generate query embeddings for common healthcare search scenarios
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
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small")
    response = client.embeddings.create(
        model=model,
        input=text,
        dimensions=dimensions
    )
    return response.data[0].embedding

# Query scenarios for healthcare search
queries = [
    {
        "query": "diabetes treatment and blood sugar management",
        "description": "Looking for research on diabetes management strategies",
        "collection": "ResearchPapers",
        "expected_matches": ["Diabetes research papers", "Blood glucose studies"]
    },
    {
        "query": "elderly patient with heart disease and hypertension",
        "description": "Find patients with cardiovascular conditions",
        "collection": "PatientRecords",
        "expected_matches": ["Patients with cardiac conditions", "Hypertension cases"]
    },
    {
        "query": "hypertension guidelines and blood pressure control",
        "description": "Medical knowledge about managing high blood pressure",
        "collection": "MedicalKnowledge",
        "expected_matches": ["Hypertension management articles", "Blood pressure guidelines"]
    }
]

print("Generating healthcare query embeddings...\n")

query_embeddings = []
for q in queries:
    embedding = generate_embedding(q["query"])
    query_embeddings.append({
        "query": q["query"],
        "description": q["description"],
        "collection": q["collection"],
        "expected_matches": q["expected_matches"],
        "embedding": embedding
    })
    print(f"✅ Generated: \"{q['query']}\"")

# Save to file
with open('healthcare_query_embeddings.json', 'w') as f:
    json.dump(query_embeddings, f, indent=2)

print(f"\n✅ Saved {len(query_embeddings)} query embeddings to healthcare_query_embeddings.json")
print(f"   Vector dimensions: {len(query_embeddings[0]['embedding'])}")
