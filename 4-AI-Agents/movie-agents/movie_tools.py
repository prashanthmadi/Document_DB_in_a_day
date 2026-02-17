"""
Movie Tools - DocumentDB Function Tools for AI Agents

This module defines the function tools that agents use to interact with
Azure DocumentDB. Each tool is a regular Python function that the Microsoft
Agent Framework can expose to LLMs.

Tools:
  - search_similar_movies: Vector search using DiskANN (uses Module 3 data)
  - search_movies_by_genre: Filter movies by genre
  - get_movie_details: Lookup a specific movie by title
  - find_where_to_watch: Find streaming platforms for a movie
  - search_by_platform: Find all movies available on a platform
"""

import json
import os
from typing import Annotated

from agent_framework import tool
from openai import AzureOpenAI
from pydantic import Field
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Shared clients (initialized once, reused by all tool calls)
# ---------------------------------------------------------------------------

_mongo_client = None
_openai_client = None


def _get_mongo_db():
    """Get or create the MongoDB database connection."""
    global _mongo_client
    if _mongo_client is None:
        connection_string = os.environ["DOCUMENTDB_CONNECTION_STRING"]
        _mongo_client = MongoClient(connection_string)
    db_name = os.environ.get("DOCUMENTDB_DATABASE", "trainingdb")
    return _mongo_client[db_name]


def _get_openai_client():
    """Get or create the Azure OpenAI client (for embeddings)."""
    global _openai_client
    if _openai_client is None:
        _openai_client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )
    return _openai_client


def _generate_embedding(text: str) -> list[float]:
    """Generate a vector embedding for the given text using Azure OpenAI."""
    client = _get_openai_client()
    deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "256"))

    response = client.embeddings.create(
        model=deployment,
        input=text,
        dimensions=dimensions,
    )
    return response.data[0].embedding


# ===========================================================================
# Agent 1 Tools: Movie Recommendation
# ===========================================================================


@tool
def search_similar_movies(
    query: Annotated[str, Field(description="Natural language description of the kind of movie the user is looking for, e.g. 'mind-bending sci-fi thriller'")],
    k: Annotated[int, Field(description="Number of results to return (1-10)", ge=1, le=10)] = 5,
) -> str:
    """Search for movies by semantic similarity using vector search on DocumentDB.
    
    This performs a DiskANN vector search: it converts the user's query into an
    embedding, then finds the most semantically similar movies in the database.
    Use this when the user describes a mood, theme, or vague preference rather
    than asking for a specific title or genre.
    """
    # Generate embedding for the user's query
    query_vector = _generate_embedding(query)

    db = _get_mongo_db()
    results = list(
        db.movies.aggregate([
            {
                "$search": {
                    "cosmosSearch": {
                        "vector": query_vector,
                        "path": "contentVector",
                        "k": k,
                    }
                }
            },
            {
                "$project": {
                    "title": 1,
                    "genre": 1,
                    "description": 1,
                    "year": 1,
                    "rating": 1,
                    "director": 1,
                    "score": {"$meta": "searchScore"},
                    "_id": 0,
                }
            },
        ])
    )

    if not results:
        return "No movies found matching that description."

    # Format results for the LLM
    output_lines = [f"Found {len(results)} similar movies:\n"]
    for i, movie in enumerate(results, 1):
        score = movie.get("score", 0)
        output_lines.append(
            f"{i}. **{movie['title']}** ({movie['year']}) — {movie['genre']}\n"
            f"   Rating: {movie['rating']}/10 | Director: {movie['director']}\n"
            f"   {movie['description']}\n"
            f"   Similarity score: {score:.4f}\n"
        )
    return "\n".join(output_lines)


@tool
def search_movies_by_genre(
    genre: Annotated[str, Field(description="Movie genre to filter by, e.g. 'Sci-Fi', 'Drama', 'Action', 'Comedy', 'Animation', 'Crime', 'Thriller', 'Horror', 'War', 'Romance', 'Adventure', 'Fantasy', 'Biography'")],
) -> str:
    """Search for movies by genre in DocumentDB.
    
    Use this when the user asks for movies in a specific genre category.
    Returns all movies matching the genre, sorted by rating.
    """
    db = _get_mongo_db()
    results = list(
        db.movies.find(
            {"genre": {"$regex": f"^{genre}$", "$options": "i"}},
            {"title": 1, "genre": 1, "year": 1, "rating": 1, "director": 1, "description": 1, "_id": 0},
        ).sort("rating", -1)
    )

    if not results:
        return f"No movies found in genre '{genre}'. Available genres: Sci-Fi, Drama, Action, Comedy, Animation, Crime, Thriller, Horror, War, Romance, Adventure, Fantasy, Biography."

    output_lines = [f"Found {len(results)} {genre} movies (sorted by rating):\n"]
    for i, movie in enumerate(results, 1):
        output_lines.append(
            f"{i}. **{movie['title']}** ({movie['year']}) — Rating: {movie['rating']}/10\n"
            f"   Director: {movie['director']} | {movie['description']}\n"
        )
    return "\n".join(output_lines)


@tool
def get_movie_details(
    title: Annotated[str, Field(description="The title of the movie to look up")],
) -> str:
    """Get detailed information about a specific movie from DocumentDB.
    
    Use this when the user asks about a specific movie by name.
    Performs a case-insensitive search to find the movie.
    """
    db = _get_mongo_db()
    movie = db.movies.find_one(
        {"title": {"$regex": title, "$options": "i"}},
        {"title": 1, "genre": 1, "description": 1, "year": 1, "rating": 1, "director": 1, "_id": 0},
    )

    if not movie:
        return f"Movie '{title}' not found in the database. Try a different title or use search_similar_movies to find related movies."

    return (
        f"**{movie['title']}** ({movie['year']})\n"
        f"Genre: {movie['genre']}\n"
        f"Director: {movie['director']}\n"
        f"Rating: {movie['rating']}/10\n"
        f"Description: {movie['description']}"
    )


# ===========================================================================
# Agent 2 Tools: Where to Watch
# ===========================================================================


@tool
def find_where_to_watch(
    title: Annotated[str, Field(description="The title of the movie to find streaming options for")],
) -> str:
    """Find which streaming platforms offer a specific movie.
    
    Searches the streaming_platforms collection in DocumentDB to find where
    a movie is available to watch (Netflix, Amazon Prime, Disney+, etc.).
    Use this when the user wants to know where they can watch a specific movie.
    """
    db = _get_mongo_db()
    result = db.streaming_platforms.find_one(
        {"title": {"$regex": title, "$options": "i"}},
        {"_id": 0},
    )

    if not result:
        return f"Streaming information for '{title}' not found in our database."

    title = result["title"]
    streaming = result.get("streaming", [])

    if not streaming:
        return f"No streaming platforms found for '{title}'."

    output_lines = [f"Where to watch **{title}**:\n"]
    for platform_info in streaming:
        platform = platform_info["platform"]
        stream_type = platform_info["type"]
        price = platform_info.get("price", "")

        if stream_type == "subscription":
            output_lines.append(f"  • **{platform}** — Included with subscription")
        else:
            output_lines.append(f"  • **{platform}** — Available to {stream_type} ({price})")

    return "\n".join(output_lines)


@tool
def search_by_platform(
    platform: Annotated[str, Field(description="Streaming platform name, e.g. 'Netflix', 'Amazon Prime Video', 'Disney+', 'Max', 'Hulu', 'Paramount+', 'Apple TV', 'Peacock', 'Google Play'")],
    subscription_only: Annotated[bool, Field(description="If true, only return movies included with subscription (not rentals)")] = False,
) -> str:
    """Find all movies available on a specific streaming platform.
    
    Searches DocumentDB for all movies available on a particular platform.
    Can optionally filter to show only movies included with a subscription.
    Use this when the user wants to know what movies they can watch on a
    specific service.
    """
    db = _get_mongo_db()

    query = {"streaming.platform": {"$regex": platform, "$options": "i"}}
    results = list(
        db.streaming_platforms.find(query, {"_id": 0}).sort("title", 1)
    )

    if not results:
        return f"No movies found on '{platform}'. Available platforms: Netflix, Amazon Prime Video, Disney+, Max, Hulu, Paramount+, Apple TV, Peacock, Google Play."

    # Filter and format results
    output_movies = []
    for doc in results:
        for p in doc.get("streaming", []):
            if p["platform"].lower() == platform.lower() or platform.lower() in p["platform"].lower():
                if subscription_only and p["type"] != "subscription":
                    continue
                output_movies.append({
                    "title": doc["title"],
                    "type": p["type"],
                    "price": p.get("price", ""),
                })

    if not output_movies:
        return f"No movies found on '{platform}' with the selected filter."

    filter_label = " (subscription only)" if subscription_only else ""
    output_lines = [f"Movies on **{platform}**{filter_label}: ({len(output_movies)} found)\n"]

    for m in output_movies:
        if m["type"] == "subscription":
            output_lines.append(f"  • **{m['title']}** — Included with subscription")
        else:
            output_lines.append(f"  • **{m['title']}** — {m['type'].capitalize()} ({m['price']})")

    return "\n".join(output_lines)
