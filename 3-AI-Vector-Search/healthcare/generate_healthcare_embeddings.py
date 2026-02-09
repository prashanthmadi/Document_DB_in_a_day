"""
Generate Healthcare Data with Embeddings

This script generates pre-embedded healthcare data files ready for import into DocumentDB.
Users don't need to run this - output files are already included in the repository.
This script is provided to show how embeddings were generated.

Outputs:
- ResearchPapers_with_vectors.json
- PatientRecords_with_vectors.json  
- MedicalKnowledge_with_vectors.json
"""

import os
import json
import random
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small")

# Data directory
DATA_DIR = "data"

def generate_embedding(text: str, openai_client, dimensions=256) -> list:
    """Generate embedding vector for text with reduced dimensions"""
    response = openai_client.embeddings.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        input=text,
        dimensions=dimensions  # Reduced from 1536 to 256 for smaller files
    )
    return response.data[0].embedding

def generate_research_papers(openai_client):
    """Generate research papers with embeddings"""
    
    print("\n📄 Generating ResearchPapers with embeddings...")
    
    # Load data
    with open(f"{DATA_DIR}/research_papers.json", 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    results = []
    for i, paper in enumerate(papers, 1):
        # Generate embedding from title + abstract
        embedding_text = f"{paper['title']}. {paper['abstract']}"
        embedding = generate_embedding(embedding_text, openai_client)
        
        # Create document
        document = {
            "_id": paper["pmid"],
            "pmid": paper["pmid"],
            "title": paper["title"],
            "abstract": paper["abstract"],
            "authors": paper["authors"],
            "publicationYear": paper["publicationYear"],
            "journal": paper.get("journal"),
            "keywords": paper.get("keywords", []),
            "citationCount": paper.get("citationCount", 0),
            "embedding": embedding
        }
        
        results.append(document)
        print(f"  [{i}/{len(papers)}] Generated embedding for: {paper['title'][:50]}...")
    
    # Save to file
    with open('ResearchPapers_with_vectors.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Saved {len(results)} research papers to ResearchPapers_with_vectors.json")
    print(f"   Vector dimensions: {len(results[0]['embedding'])}")

def generate_patient_records(openai_client):
    """Generate patient records with embeddings (combining multiple data sources)"""
    
    print("\n🏥 Generating PatientRecords with embeddings...")
    print("   (Combining patients, diagnoses, medications, clinical notes)")
    
    # Load all patient-related data
    with open(f"{DATA_DIR}/patients.json", 'r', encoding='utf-8') as f:
        patients = json.load(f)
    with open(f"{DATA_DIR}/diagnoses.json", 'r', encoding='utf-8') as f:
        all_diagnoses = json.load(f)
    with open(f"{DATA_DIR}/medications.json", 'r', encoding='utf-8') as f:
        all_medications = json.load(f)
    with open(f"{DATA_DIR}/clinical_notes.json", 'r', encoding='utf-8') as f:
        all_notes = json.load(f)
    
    results = []
    for i, patient in enumerate(patients, 1):
        patient_id = patient["patientId"]
        
        # Find related data from other JSON files
        diagnoses = [d for d in all_diagnoses if d["patientId"] == patient_id]
        medications = [m for m in all_medications if m["patientId"] == patient_id]
        notes = [n for n in all_notes if n["patientId"] == patient_id]
        
        # Calculate age
        dob = datetime.strptime(patient['dateOfBirth'], '%Y-%m-%d')
        age = (datetime.now() - dob).days // 365
        
        # Create summary for embedding
        summary_parts = [
            f"Patient: {age} year old {patient['gender']}",
            f"Conditions: {', '.join([d['conditionName'] for d in diagnoses])}",
            f"Medications: {', '.join([m['drugName'] for m in medications])}"
        ]
        summary_text = ". ".join(summary_parts)
        summary_embedding = generate_embedding(summary_text, openai_client)
        
        # Create embedded document with location (for geospatial demo)
        # Generate random location within US bounds
        longitude = random.uniform(-125, -65)
        latitude = random.uniform(25, 50)
        
        document = {
            "_id": patient_id,
            "patientId": patient_id,
            "demographics": {
                "firstName": patient["firstName"],
                "lastName": patient["lastName"],
                "dateOfBirth": patient["dateOfBirth"],
                "age": age,
                "gender": patient["gender"],
                "email": patient["email"],
                "phone": patient["phone"],
                "address": patient["address"],
                "insuranceProvider": patient["insuranceProvider"],
                "primaryPhysician": patient["primaryPhysician"]
            },
            "diagnoses": diagnoses,
            "medications": medications,
            "clinicalNotes": notes,
            "location": {"type": "Point", "coordinates": [longitude, latitude]},  # GeoJSON format
            "is_active": True,
            "summaryEmbedding": summary_embedding
        }
        
        results.append(document)
        print(f"  [{i}/{len(patients)}] Generated embedding for patient: {patient_id}")
    
    # Save to file
    with open('PatientRecords_with_vectors.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Saved {len(results)} patient records to PatientRecords_with_vectors.json")
    print(f"   Vector dimensions: {len(results[0]['summaryEmbedding'])}")

def generate_medical_knowledge(openai_client):
    """Generate medical knowledge articles with embeddings"""
    
    print("\n📚 Generating MedicalKnowledge with embeddings...")
    
    # Load data
    with open(f"{DATA_DIR}/medical_knowledge.json", 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    results = []
    for i, article in enumerate(articles, 1):
        # Create text for embedding
        embedding_text = f"{article['title']}. {article['content']}"
        embedding = generate_embedding(embedding_text, openai_client)
        
        # Create document
        document = {
            "_id": article["id"],
            "articleId": article["id"],
            "category": article["category"],
            "title": article["title"],
            "content": article["content"],
            "keywords": article.get("keywords", []),
            "relatedConditions": article.get("relatedConditions", []),
            "lastUpdated": article.get("lastUpdated"),
            "embedding": embedding
        }
        
        results.append(document)
        print(f"  [{i}/{len(articles)}] Generated embedding for: {article['title'][:50]}...")
    
    # Save to file
    with open('MedicalKnowledge_with_vectors.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Saved {len(results)} knowledge articles to MedicalKnowledge_with_vectors.json")
    print(f"   Vector dimensions: {len(results[0]['embedding'])}")

def main():
    print("=" * 70)
    print("🏥 Healthcare Data with Embeddings Generator")
    print("=" * 70)
    print("\nThis script generates pre-embedded healthcare data files.")
    print("Users can import these files directly without running this script.")
    print("=" * 70)
    
    # Validate environment variables
    if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY]):
        print("\n❌ ERROR: Missing required environment variables!")
        print("\nPlease create a .env file with:")
        print("- AZURE_OPENAI_ENDPOINT")
        print("- AZURE_OPENAI_API_KEY")
        print("- AZURE_OPENAI_DEPLOYMENT (optional, defaults to text-embedding-3-small)")
        print("\nCopy .env.template to .env and fill in your values.\n")
        return
    
    # Initialize OpenAI client
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-02-01"
    )
    
    # Generate all collections with embeddings
    generate_research_papers(openai_client)
    generate_patient_records(openai_client)
    generate_medical_knowledge(openai_client)
    
    print("\n" + "=" * 70)
    print("✅ All files generated successfully!")
    print("=" * 70)
    print("\nGenerated files (ready for DocumentDB import):")
    print("  • ResearchPapers_with_vectors.json")
    print("  • PatientRecords_with_vectors.json")
    print("  • MedicalKnowledge_with_vectors.json")
    print("\nThese files contain 256-dimensional embeddings and are ready to import")
    print("using the DocumentDB VS Code Extension.")
    print()

if __name__ == "__main__":
    main()
