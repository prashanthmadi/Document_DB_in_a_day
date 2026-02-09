"""
Generate embeddings for movie dataset using Azure OpenAI
Reads: movies_input.ndjson (without embeddings)
Writes: movies_with_vectors.ndjson (with embeddings)
"""

from openai import AzureOpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01"
)

def generate_embedding(text, dimensions=256):
    """Generate embedding for given text with reduced dimensions"""
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "text-embedding-3-small")
    response = client.embeddings.create(
        model=model,
        input=text,
        dimensions=dimensions  # Reduce from 1536 to 256 for smaller files
    )
    return response.data[0].embedding

def main():
    input_file = "movies_input.ndjson"
    output_file = "movies_with_vectors.json"
    
    print(f"Reading movies from {input_file}...")
    movies = []
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            movie = json.loads(line.strip())
            movies.append(movie)
    
    print(f"Loaded {len(movies)} movies")
    print(f"\nGenerating embeddings using Azure OpenAI (text-embedding-3-small)...")
    
    # Generate embeddings
    for i, movie in enumerate(movies, 1):
        # Combine title, genre, and description for better embeddings
        text_to_embed = f"{movie['title']} {movie['genre']} {movie['description']}"
        
        try:
            embedding = generate_embedding(text_to_embed)
            movie['contentVector'] = embedding
            print(f"  [{i}/{len(movies)}] Generated embedding for '{movie['title']}'")
        except Exception as e:
            print(f"  Error generating embedding for '{movie['title']}': {e}")
            continue
    
    # Save output file as JSON array
    print(f"\nWriting results to {output_file}...")
    movies_with_vectors = [movie for movie in movies if 'contentVector' in movie]
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movies_with_vectors, f, indent=2)
    
    print(f"\n✅ Successfully generated embeddings for {len([m for m in movies if 'contentVector' in m])} movies")
    print(f"   Vector dimensions: {len(movies[0]['contentVector'])}")
    print(f"   Output file: {output_file}")

if __name__ == "__main__":
    main()
