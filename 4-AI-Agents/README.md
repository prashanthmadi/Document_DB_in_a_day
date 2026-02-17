# Module 4: AI Agents with DocumentDB

**Duration:** 1.5 hours | **Goal:** Build AI agents that use DocumentDB as their data backbone, powered by the Microsoft Agent Framework and DevUI.

## What You'll Learn

- 🤖 Creating AI agents with the Microsoft Agent Framework
- 🔧 Building function tools that query Azure DocumentDB
- 🔍 Combining vector search (DiskANN) with traditional queries in agent tools
- 🖥️ Using DevUI to interactively test and debug agents in a browser
- 🎯 Agent composition: each agent has a focused responsibility and toolset

## What You'll Build

Two AI agents served via a web-based DevUI interface:

| Agent | Purpose | DocumentDB Tools |
|-------|---------|-----------------|
| **MovieRecommendation** | Finds movies by mood, theme, genre, or title | Vector search (DiskANN), genre query, title lookup |
| **WhereToWatch** | Shows where to stream or rent movies | Platform lookup, browse-by-service |

```
┌──────────────────────────────────────────────────────────┐
│                    DevUI (Browser)                        │
│   http://localhost:8080                                   │
│                                                          │
│   ┌─────────────────┐    ┌──────────────────┐           │
│   │ MovieRecommend  │    │  WhereToWatch    │           │
│   │     Agent       │    │     Agent        │           │
│   └────────┬────────┘    └────────┬─────────┘           │
│            │                      │                      │
│   ┌────────▼────────┐    ┌───────▼──────────┐           │
│   │ Tools:          │    │ Tools:           │           │
│   │ • Vector search │    │ • Find where to  │           │
│   │ • Genre search  │    │   watch          │           │
│   │ • Movie details │    │ • Search by      │           │
│   └────────┬────────┘    │   platform       │           │
│            │              └───────┬──────────┘           │
│            └──────────┬───────────┘                      │
│                       ▼                                  │
│              Azure DocumentDB                            │
│         ┌──────────┬───────────────┐                     │
│         │  movies  │  streaming_   │                     │
│         │ (vectors)│  platforms    │                     │
│         └──────────┴───────────────┘                     │
└──────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- ✅ Completed Module 1 (DocumentDB cluster + AI Foundry with models deployed)
- ✅ Completed Module 3 Part 3.1-3.2 (movies collection loaded with vector index created)
- ✅ Python virtual environment set up with dependencies installed

---

## Folder Structure

```
4-AI-Agents/
├── README.md                              # This file
└── movie-agents/
    ├── streaming_platforms.json           # Pre-generated streaming data for 50 movies
    ├── load_streaming_data.py             # Loads streaming data into DocumentDB
    ├── movie_tools.py                     # Function tools for DocumentDB operations
    └── app.py                             # Main app: creates agents + launches DevUI

.env.template                              # ← Root-level config (shared by Modules 3 & 4)
```

---

## Part 1: Setup (15 minutes)

### 1.1 Install Dependencies

From the **project root** directory, install all required packages:

```powershell
# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Install all dependencies (includes Agent Framework + DevUI)
pip install -r requirements.txt
```

**Key new packages:**
- `agent-framework[azure]` — Microsoft Agent Framework with Azure OpenAI support
- `agent-framework-devui` — Browser-based UI for testing agents
- `pydantic` — Type annotations for tool parameters

### 1.2 Configure Environment

If you haven't already, copy the root-level `.env.template` and fill in your values:

```powershell
# From the project root
copy .env.template .env
```

Open `.env` and fill in your values from Module 1:

| Variable | Where to Find |
|----------|--------------|
| `DOCUMENTDB_CONNECTION_STRING` | Azure Portal → DocumentDB → Connection strings |
| `AZURE_OPENAI_ENDPOINT` | AI Foundry → Project → Overview → Endpoint |
| `AZURE_OPENAI_API_KEY` | AI Foundry → Project → Overview → API Key |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | AI Foundry → Deployments → `gpt-4o` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | AI Foundry → Deployments → `text-embedding-3-small` |

### 1.3 Load Streaming Platform Data

Load the streaming availability data into DocumentDB:

```powershell
python load_streaming_data.py
```

**Expected output:**
```
Connecting to DocumentDB...
Reading streaming data from streaming_platforms.json...
Loaded 50 movie streaming records
Inserting into 'streaming_platforms' collection...

✅ Successfully loaded 50 streaming records
   Database: trainingdb
   Collection: streaming_platforms

Creating index on 'title' field...
Creating index on 'streaming.platform' field...

✅ Indexes created successfully

Verification:
  Total documents: 50
  Sample (Inception): { "title": "Inception", "streaming": [...] }
```

### 1.4 Verify Data Setup

Open a **DocumentDB Scrapbook** in VS Code and run:

```javascript
use trainingdb

// Verify movies collection (from Module 3)
db.movies.countDocuments()  // Should return: 50

// Verify streaming_platforms collection (just loaded)
db.streaming_platforms.countDocuments()  // Should return: 50

// Check sample streaming data
db.streaming_platforms.findOne({ title: "Inception" })

// Verify vector index exists (from Module 3)
db.movies.getIndexes()
```

✅ **Checkpoint:** Both collections exist with 50 documents each, and the vector index is active on the movies collection.

---

## Part 2: Understanding the Architecture (15 minutes)

### 2.1 Microsoft Agent Framework

The [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview) is the successor to both Semantic Kernel and AutoGen. It provides:

- **Agents** — LLM-powered entities that can call tools, hold conversations, and reason
- **Function Tools** — Regular Python functions that agents can invoke during conversations
- **DevUI** — A browser-based interface for testing agents interactively

**Key pattern:**

```python
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.devui import serve

# 1. Create a chat client (connects to Azure OpenAI)
chat_client = AzureOpenAIChatClient(
    azure_endpoint="...",
    api_key="...",
    azure_deployment="gpt-4o",
)

# 2. Define tools (regular Python functions)
def my_tool(query: str) -> str:
    """Tool description for the LLM."""
    return "result"

# 3. Create an agent with instructions and tools
agent = chat_client.as_agent(
    name="MyAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)

# 4. Serve via DevUI
serve(entities=[agent], auto_open=True)
```

### 2.2 How Function Tools Work

When you give an agent function tools:

1. The agent receives a user message ("find me sci-fi movies")
2. The LLM decides which tool to call based on the tool's description and parameters
3. The framework executes your Python function with the LLM's chosen arguments
4. The tool result is sent back to the LLM
5. The LLM formulates a natural language response using the tool's output

```
User: "Find me movies like Inception"
  ↓
LLM Decision: Call search_similar_movies(query="mind-bending sci-fi like Inception", k=5)
  ↓
Python Function: Generates embedding → Queries DocumentDB → Returns results
  ↓
LLM Response: "Here are 5 movies similar to Inception: 1. The Matrix..."
```

### 2.3 Code Walkthrough

**`movie-agents/movie_tools.py`** — Contains all DocumentDB interaction logic:

| Tool | Agent | What It Does |
|------|-------|-------------|
| `search_similar_movies(query, k)` | MovieRecommendation | Generates embedding → DiskANN vector search |
| `search_movies_by_genre(genre)` | MovieRecommendation | Filters by genre, sorted by rating |
| `get_movie_details(title)` | MovieRecommendation | Case-insensitive title lookup |
| `find_where_to_watch(title)` | WhereToWatch | Looks up streaming platforms for a movie |
| `search_by_platform(platform)` | WhereToWatch | Lists all movies on a given service |

**`movie-agents/app.py`** — Creates the agents and launches DevUI:
- Initializes `AzureOpenAIChatClient` with Azure credentials
- Creates two agents, each with their own instructions and tools
- Starts DevUI on `http://localhost:8080`

---

## Part 3: Run the Agents (30 minutes)

### 3.1 Launch DevUI

```powershell
cd 4-AI-Agents/movie-agents
python app.py
```

Your browser should open automatically to `http://localhost:8080`. You'll see both agents listed in the DevUI dashboard.

**Expected console output:**
```
============================================================
  Module 4: AI Agents with DocumentDB
  Launching DevUI...
============================================================

  Agents available:
    1. MovieRecommendation  — Vector search + movie queries
    2. WhereToWatch         — Streaming platform lookup

  Open http://localhost:8080 in your browser
  Press Ctrl+C to stop
============================================================
```

### 3.2 Test the Movie Recommendation Agent

Click **MovieRecommendation** in DevUI. Try these prompts:

**Semantic Vector Search:**
```
Find me mind-bending sci-fi thrillers with complex plots
```
→ Agent calls `search_similar_movies` → generates embedding → DiskANN vector search → returns Inception, The Matrix, Interstellar, etc.

**Genre Search:**
```
Show me all animation movies
```
→ Agent calls `search_movies_by_genre("Animation")` → returns Toy Story, Finding Nemo, The Lion King, etc.

**Specific Movie Lookup:**
```
Tell me about The Dark Knight
```
→ Agent calls `get_movie_details("The Dark Knight")` → returns full movie details

**Multi-Tool Interaction:**
```
I'm looking for something like a heartwarming story about family. 
Also, what's the highest-rated drama you have?
```
→ Agent may call multiple tools to answer both questions

### 3.3 Test the Where to Watch Agent

Click **WhereToWatch** in DevUI. Try these prompts:

**Find Streaming Options:**
```
Where can I watch Inception?
```
→ Agent calls `find_where_to_watch("Inception")` → returns Netflix, Max, Amazon Prime Video

**Browse by Platform:**
```
What movies are available on Disney+?
```
→ Agent calls `search_by_platform("Disney+")` → returns all Disney+ movies

**Subscription Filter:**
```
What can I watch for free on Netflix (just with my subscription, no rentals)?
```
→ Agent calls `search_by_platform("Netflix", subscription_only=True)` → returns subscription-only titles

**Compare Platforms:**
```
I want to watch The Godfather. Which platform offers it with a subscription?
```
→ Agent calls `find_where_to_watch("The Godfather")` → shows Paramount+ (subscription) vs. others (rental)

### 3.4 Observe Tool Calls in DevUI

DevUI shows you **exactly what's happening** behind the scenes:

1. 💬 **User message** — what you typed
2. 🔧 **Tool calls** — which function the LLM chose, with what arguments
3. 📊 **Tool results** — the data returned from DocumentDB
4. 🤖 **Agent response** — the LLM's formatted answer

This visibility is invaluable for understanding how agents reason about which tools to use and how they interpret the results.

---

## Part 4: How It Works (15 minutes)

### 4.1 Vector Search Tool Deep Dive

The `search_similar_movies` tool is where AI and DocumentDB come together:

```python
def search_similar_movies(query: str, k: int = 5) -> str:
    # Step 1: Convert natural language to a vector embedding
    query_vector = _generate_embedding(query)  # → Azure OpenAI API
    
    # Step 2: Use DiskANN vector search in DocumentDB
    results = db.movies.aggregate([
        {
            "$search": {
                "cosmosSearch": {
                    "vector": query_vector,       # The 256-dim embedding
                    "path": "contentVector",       # Field in documents
                    "k": k,                        # Number of results
                }
            }
        },
        { "$project": { "title": 1, "genre": 1, ... } }
    ])
    
    # Step 3: Format results for the LLM to present
    return formatted_string
```

**Flow:**
```
User: "something about time travel and space"
  → Azure OpenAI: text-embedding-3-small → [0.05, -0.12, 0.34, ...]  (256 dims)
  → DocumentDB: DiskANN cosine similarity search
  → Results: Interstellar (0.91), Inception (0.87), The Matrix (0.84)
  → LLM formats and presents the results
```

### 4.2 Tool Selection by the LLM

The LLM chooses tools based on:

1. **Function name** — `search_similar_movies` vs `search_movies_by_genre`
2. **Docstring** — describes when to use each tool
3. **Parameter descriptions** — `Annotated[str, Field(description="...")]`
4. **Agent instructions** — guidelines in the system prompt

This is why good tool descriptions matter! Compare:
```python
# ❌ Vague - LLM won't know when to use this
def search(q): ...

# ✅ Descriptive - LLM can make informed decisions
def search_similar_movies(
    query: Annotated[str, Field(description="Natural language description of the kind of movie...")],
) -> str:
    """Search for movies by semantic similarity using vector search on DocumentDB.
    Use this when the user describes a mood, theme, or vague preference..."""
```

---

## Part 5: Exercises (15 minutes)

### Exercise 1: Add a Top-Rated Tool

Add a new tool to the Movie Recommendation Agent that returns the top N movies by rating.

<details>
<summary>Hint</summary>

Add a function in `movie-agents/movie_tools.py`:
```python
def get_top_rated_movies(
    n: Annotated[int, Field(description="Number of top movies to return")] = 10,
) -> str:
    """Get the highest-rated movies from the database."""
    db = _get_mongo_db()
    results = list(
        db.movies.find({}, {"title": 1, "rating": 1, "year": 1, "genre": 1, "_id": 0})
        .sort("rating", -1)
        .limit(n)
    )
    # Format and return...
```

Then add it to the agent's `tools` list in `movie-agents/app.py`.
</details>

### Exercise 2: Cross-Agent Query

Try asking the Where to Watch agent about a movie you found through the Movie Recommendation agent. For example:

1. In MovieRecommendation: "Find me animated family movies"
2. Note the results (e.g., Toy Story, Finding Nemo)
3. In WhereToWatch: "Where can I watch Toy Story and Finding Nemo?"

**Question:** How could you combine both agents into a single experience?

<details>
<summary>Answer</summary>

The Agent Framework supports using agents as tools for other agents:

```python
# Create a "super agent" that can call both agents
combined_agent = chat_client.as_agent(
    name="MovieAssistant",
    instructions="You help users find and watch movies.",
    tools=[
        movie_recommendation_agent.as_tool(
            name="recommend", description="Find movie recommendations"
        ),
        where_to_watch_agent.as_tool(
            name="streaming", description="Find where to watch a movie" 
        ),
    ],
)
```
</details>

### Exercise 3: Filtered Vector Search Tool

Create a tool that combines vector search with a year filter (e.g., "find sci-fi movies from after 2010"):

<details>
<summary>Solution</summary>

```python
def search_recent_similar_movies(
    query: Annotated[str, Field(description="Movie description")],
    min_year: Annotated[int, Field(description="Minimum release year")] = 2000,
    k: Annotated[int, Field(description="Number of results")] = 5,
) -> str:
    """Vector search filtered by release year."""
    query_vector = _generate_embedding(query)
    db = _get_mongo_db()
    results = list(db.movies.aggregate([
        {
            "$search": {
                "cosmosSearch": {
                    "vector": query_vector,
                    "path": "contentVector",
                    "k": k,
                    "filter": {"year": {"$gte": min_year}},
                }
            }
        },
        {"$project": {"title": 1, "year": 1, "genre": 1, "rating": 1, "score": {"$meta": "searchScore"}, "_id": 0}},
    ]))
    # Format and return...
```
</details>

---

## Troubleshooting

### Common Issues

**"DOCUMENTDB_CONNECTION_STRING not set"**
- Ensure `.env` file exists in the project root folder
- Verify the file has the correct variable names (copy from `.env.template`)

**"Authentication failed" / Credential errors**
- Verify `AZURE_OPENAI_API_KEY` is correct in `.env`
- Ensure `AZURE_OPENAI_ENDPOINT` is the full URL (e.g., `https://<name>.openai.azure.com/`)

**"Collection 'movies' not found"**
- Go back to Module 3, Part 3.1 and import the movies data
- Verify with: `db.movies.countDocuments()` in a DocumentDB Scrapbook

**"No vector index found" / Vector search returns errors**
- Ensure the DiskANN index was created in Module 3, Part 3.2
- Re-run the index creation command from Module 3

**"Module 'agent_framework' not found"**
- Install dependencies: `pip install -r requirements.txt` from the project root
- Make sure virtual environment is activated: `.venv\Scripts\Activate.ps1`

**DevUI doesn't open in browser**
- Manually navigate to `http://localhost:8080`
- Check the terminal for error messages
- Try a different port: change `port=8080` in `movie-agents/app.py`

---

## Summary

- ✅ **Microsoft Agent Framework** provides a clean pattern for building AI agents with tools
- ✅ **Function Tools** connect agents to DocumentDB — vector search, queries, and lookups
- ✅ **DevUI** enables interactive testing with full visibility into tool calls and LLM reasoning
- ✅ **DiskANN vector search** powers semantic movie recommendations through agent tools
- ✅ **Multiple agents** can have different responsibilities and tool sets

**Key Takeaways:**
- Agents are only as useful as their tools — good tool design is critical
- Vector search + traditional queries complement each other in agent tools
- DevUI makes it easy to iterate on agent instructions and tool descriptions
- DocumentDB serves as both the vector store and the application database

---

## Resources

**Microsoft Agent Framework:**
- [Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview)
- [Your First Agent](https://learn.microsoft.com/en-us/agent-framework/get-started/your-first-agent)
- [Function Tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/function-tools)
- [DevUI Documentation](https://learn.microsoft.com/en-us/agent-framework/devui/)
- [GitHub Repository](https://github.com/microsoft/agent-framework)

**Azure DocumentDB:**
- [Vector Search](https://learn.microsoft.com/en-us/azure/documentdb/vector-search)
- [DiskANN Algorithm](https://www.microsoft.com/en-us/research/publication/diskann-fast-accurate-billion-point-nearest-neighbor-search-on-a-single-node/)

**Patterns:**
- [RAG with DocumentDB](https://github.com/microsoft/AzureDataRetrievalAugmentedGenerationSamples/tree/main/Python/CosmosDB-MongoDB-vCore)
- [LangChain + DocumentDB](https://python.langchain.com/docs/integrations/vectorstores/azure_cosmos_db/)

---

## Next Steps

After completing this module:

- **Try with Healthcare data:** Apply the same agent pattern to the healthcare dataset from Module 3
- **Add more tools:** Create tools for aggregation pipelines, cross-collection joins
- **Build workflows:** Use the Agent Framework's workflow feature for multi-step orchestration
- **Deploy:** Package agents for production deployment with Azure Functions or Container Apps
