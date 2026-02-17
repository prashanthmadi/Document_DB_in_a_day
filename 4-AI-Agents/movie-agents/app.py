"""
Module 4: AI Agents with DocumentDB — DevUI Application

This script creates two AI agents powered by Azure DocumentDB and serves them
via the Microsoft Agent Framework DevUI for interactive browser-based testing.

Agents:
  1. Movie Recommendation Agent  — vector search + genre/title queries
  2. Where to Watch Agent        — streaming platform lookup

Usage:
    1. Copy .env.template to .env in the project root and fill in your credentials
    2. Run:  python app.py
    3. Open: http://localhost:8080 in your browser

The DevUI will show both agents in a web interface where you can chat with
them, see tool invocations, and observe how they use DocumentDB.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from project root .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from agent_framework.azure import AzureOpenAIChatClient  # noqa: E402
from agent_framework.devui import serve  # noqa: E402

from movie_tools import (  # noqa: E402
    find_where_to_watch,
    get_movie_details,
    search_by_platform,
    search_movies_by_genre,
    search_similar_movies,
)


# ---------------------------------------------------------------------------
# Create the Azure OpenAI Chat Client
# ---------------------------------------------------------------------------
# Uses API key authentication from .env file.
# ---------------------------------------------------------------------------

chat_client = AzureOpenAIChatClient(
    endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    deployment_name=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
)


# ---------------------------------------------------------------------------
# Agent 1: Movie Recommendation Agent
# ---------------------------------------------------------------------------
# This agent uses DocumentDB vector search (DiskANN) to find semantically
# similar movies, plus traditional queries for genre and title lookup.
# It leverages the same movie data loaded in Module 3.
# ---------------------------------------------------------------------------

movie_recommendation_agent = chat_client.as_agent(
    name="MovieRecommendation",
    instructions="""You are a movie recommendation assistant powered by a DocumentDB database 
containing 50 popular films with vector embeddings.

Your capabilities:
- **Semantic search**: Find movies by mood, theme, or description using vector search
  (e.g., "something mind-bending like Inception")
- **Genre search**: Find movies by genre category 
  (e.g., "show me all action movies")
- **Movie details**: Look up specific movies by title
  (e.g., "tell me about The Dark Knight")

Guidelines:
- When users describe a vague preference or mood, use search_similar_movies (vector search)
- When users ask for a specific genre, use search_movies_by_genre
- When users ask about a specific movie, use get_movie_details
- Always present results in a clear, formatted way
- Include ratings and brief descriptions to help users choose
- You can suggest related searches based on results
- If a search returns no results, suggest alternative approaches""",
    tools=[search_similar_movies, search_movies_by_genre, get_movie_details],
)


# ---------------------------------------------------------------------------
# Agent 2: Where to Watch Agent
# ---------------------------------------------------------------------------
# This agent helps users find where to stream or rent movies. It queries
# the streaming_platforms collection in DocumentDB.
# ---------------------------------------------------------------------------

where_to_watch_agent = chat_client.as_agent(
    name="WhereToWatch",
    instructions="""You are a streaming guide assistant that helps users find where to watch movies.
You have access to a DocumentDB database with streaming availability data for 50 popular films.

Your capabilities:
- **Find streaming options**: Look up which platforms offer a specific movie
  (e.g., "where can I watch Inception?")
- **Browse by platform**: See what movies are available on a specific service
  (e.g., "what can I watch on Netflix?")
- **Filter by subscription**: Show only movies included with a subscription
  (vs. rental/purchase)

Available platforms in the database: Netflix, Amazon Prime Video, Disney+, Max, 
Hulu, Paramount+, Apple TV, Peacock, Google Play.

Guidelines:
- When users ask where to watch a specific movie, use find_where_to_watch
- When users ask what's available on a platform, use search_by_platform
- Clearly distinguish between "included with subscription" and "available to rent"
- If a movie isn't found, suggest they check the specific platform's website
- You can compare platforms if the user asks which service has the most options
- Be helpful about pricing information when available

Note: Streaming availability is sample data for training purposes.""",
    tools=[find_where_to_watch, search_by_platform],
)


# ---------------------------------------------------------------------------
# Launch DevUI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Module 4: AI Agents with DocumentDB")
    print("  Launching DevUI...")
    print("=" * 60)
    print()
    print("  Agents available:")
    print("    1. MovieRecommendation  — Vector search + movie queries")
    print("    2. WhereToWatch         — Streaming platform lookup")
    print()
    print("  Open http://localhost:8080 in your browser")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    serve(
        entities=[movie_recommendation_agent, where_to_watch_agent],
        auto_open=True,
        port=8080,
    )
