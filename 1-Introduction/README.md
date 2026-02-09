# Introduction: Azure DocumentDB & AI Foundry Setup

**Duration:** 60-90 minutes | **Goal:** Set up Azure DocumentDB cluster, connect via VS Code, and create AI Foundry project with deployed models.

## What You'll Learn

- 🗄️ Provisioning Azure DocumentDB (vCore) cluster
- 🔌 Connecting to DocumentDB via VS Code extension
- 🎯 Creating Azure AI Foundry project
- 🤖 Deploying embedding and chat models
- ✅ Testing connections and basic operations

## What You'll Build

- Azure DocumentDB cluster configured and accessible
- VS Code workspace connected to DocumentDB
- AI Foundry project with models ready for development

---

## Prerequisites

- Azure subscription with contributor access
- [VS Code](https://code.visualstudio.com/) installed
- Web browser for Azure Portal

---

## Part 1: Create Azure DocumentDB Cluster (20 minutes)

### 1.1 Navigate to Azure Portal
1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your Azure credentials

### 1.2 Create DocumentDB Cluster
1. Click **+ Create a resource**
2. Search for **Azure Cosmos DB**
3. Click **Create** → Select **Azure Cosmos DB for MongoDB (vCore)**
4. Fill in details:
   - **Subscription:** Select your subscription
   - **Resource group:** Create new `rg-documentdb-training` or use existing
   - **Cluster name:** `docdb-training-cluster` (must be globally unique)
   - **Location:** Choose region (e.g., East US, West Europe)
   - **MongoDB version:** Select latest (7.0 or higher)
   - **Cluster tier:** Select **M25** or **M30** (for vector search support)
   - **Storage:** 128 GB (default)
   - **Compute:** 2 vCores (default for M25)
5. Click **Review + create**
6. Review settings and click **Create**

⏱️ **Wait 10-15 minutes** for deployment to complete

### 1.3 Configure Firewall
1. Once deployed, go to your DocumentDB resource
2. In left menu, select **Networking** under Security
3. Select **Public access (allowed IP addresses)**
4. Click **+ Add current client IP address** (adds your IP)
5. Optional: Click **Add 0.0.0.0 - 255.255.255.255** for testing (⚠️ Remove in production!)
6. Click **Save**

### 1.4 Get Connection String
1. In left menu, select **Connection strings** under Settings
2. Copy the **Primary Connection String**
3. Note: It will look like:
   ```
   mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true
   ```
4. **Save this connection string** - you'll need it for VS Code

✅ **Checkpoint:** DocumentDB cluster is running and connection string is saved

---

## Part 2: Connect DocumentDB via VS Code (15 minutes)

### 2.1 Install DocumentDB Extension for VS Code

**Method 1: Extensions Panel**
1. Open **VS Code**
2. Click **Extensions** icon (Ctrl+Shift+X or Cmd+Shift+X on Mac)
3. Search for **"DocumentDB for VS Code"**
4. Click **Install**
5. Reload VS Code if prompted

**Method 2: Quick Install (Alternative)**
1. Open VS Code Command Palette (Ctrl+P or Cmd+P on Mac)
2. Paste: `ext install ms-azuretools.vscode-documentdb`
3. Press Enter

💡 **Extension Features:**
- Universal support for DocumentDB and MongoDB databases
- Multiple data views: Table, Tree, and JSON layouts
- Query editor with syntax highlighting and auto-completion
- Document management (create, edit, delete)
- Data import/export (JSON, CSV)
- Index management and performance monitoring

### 2.2 Add Connection to Your DocumentDB Cluster
1. Open VS Code and click the **DocumentDB** icon in the left sidebar
2. Click **"Add New Connection"** button
3. Select **"Connection String"**
4. Paste your connection string from Part 1.4:
   ```
   mongodb+srv://<username>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256
   ```
5. Press **Enter**
6. Your cluster connection appears in the DocumentDB panel

👉 **Connection String Format:**
- Replace `<username>` with your DocumentDB admin username
- Replace `<password>` with your admin password
- Replace `<cluster>` with your cluster name
- Keep `?tls=true&authMechanism=SCRAM-SHA-256` parameters

### 2.3 Create Your First Database
1. In **DocumentDB** panel, right-click on your cluster connection
2. Select **"Create Database..."**
3. Enter database name: `trainingdb`
4. Press **Enter**
5. Right-click the cluster again → Select **"Refresh"** to see your new database

✅ **Checkpoint:** You now have a database called "trainingdb"

### 2.4 Open DocumentDB Scrapbook
1. Expand your cluster → You should see **trainingdb**
2. Right-click on **trainingdb** → Select **"DocumentDB Scrapbook"** (or **"New DocumentDB Scrapbook"**)
3. A new scrapbook file opens in the editor
4. In the scrapbook, type:
   ```javascript
   // Test connection to DocumentDB
   db.runCommand({ ping: 1 })
   ```
5. Click **Run Command** button above the query block
6. Results appear in the output panel

**Expected output:**
```json
{
  "ok": 1
}
```

✅ **Checkpoint:** DocumentDB Scrapbook is working and connected to trainingdb

### 2.5 Create Test Collection with Data
In the DocumentDB Scrapbook that's still open, create your first collection:

```javascript
// Create a collection with sample documents
db.customers.insertMany([
  {
    name: "John Doe",
    email: "john@example.com",
    age: 30,
    status: "active",
    createdAt: new Date()
  },
  {
    name: "Jane Smith",
    email: "jane@example.com",
    age: 28,
    status: "active",
    createdAt: new Date()
  }
])

// Query all customers
db.customers.find({})

// Count documents
db.customers.countDocuments()
```

**Expected results:**
```javascript
// Insert result
{
  acknowledged: true,
  insertedIds: {
    '0': ObjectId('...'),
    '1': ObjectId('...')
  }
}

// All customers
[
  { _id: ObjectId('...'), name: 'John Doe', email: 'john@example.com', ... },
  { _id: ObjectId('...'), name: 'Jane Smith', email: 'jane@example.com', ... }
]

// Count
2
```

Click **Run Command** above each query block to execute it (or **Run All** at the top to run all commands).

### 2.6 Explore DocumentDB Extension Features

**Browse and View Data:**
1. In **DocumentDB** panel, right-click your connection → Click **Refresh**
2. Expand your connection → **trainingdb** → **customers**
3. Click on **customers** collection to open it
4. Choose your preferred view:
   - **Table View** - Spreadsheet-like grid with sortable columns
   - **Tree View** - Hierarchical display of document structure
   - **JSON View** - Raw JSON with syntax highlighting
5. Use the pagination controls to browse through documents

💡 **Tip:** If you don't see your new database or collection, right-click the connection and select **Refresh**

**Working with DocumentDB Scrapbook:**
Create more scrapbooks for different queries (right-click database → **New DocumentDB Scrapbook**):
```javascript
// Find with filters
db.customers.find({ status: "active" })

// Create indexes
db.customers.createIndex({ email: 1 }, { unique: true })

// View indexes
db.customers.getIndexes()

// Aggregation pipeline
db.customers.aggregate([
  { $match: { age: { $gte: 25 } } },
  { $group: { _id: "$status", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

**Manage Databases and Collections:**
Right-click options available:
- **On Cluster:** Create Database, Refresh
- **On Database:** DocumentDB Scrapbook, Create Collection, Delete Database, Refresh
- **On Collection:** Create Document, Export, Drop Collection, Refresh

**Import/Export Data:**
- Right-click collection → **Export** to save as JSON or CSV
- Right-click database → **Import** to load JSON files

**Using DocumentDB Scrapbook**
To run queries:
- Right-click on your cluster → **DocumentDB Scrapbook**
- Copy and paste MongoDB commands
- Click **Run Command** above each query block (or **Run All** at the top)

✅ **Checkpoint:** Can browse databases, run queries via scrapbook, and manage documents in VS Code

---

## Part 3: Create AI Foundry Project (20 minutes)


### 3.1 Navigate to AI Foundry
1. Go to [https://ai.azure.com](https://ai.azure.com)
2. Sign in with your Azure credentials

### 3.2 Create New Project
1. Click **+ New project**
2. Fill in details:
   - **Project name:** `documentdb-ai-training`
   - **Subscription:** Select your Azure subscription
   - **Resource group:** Use `rg-documentdb-training` (same as DocumentDB) or create new
   - **Location:** Choose region (preferably same as DocumentDB)
3. Click **Create**

⏱️ **Wait 2-3 minutes** for project creation

### 3.3 Deploy Embedding Model
1. In AI Foundry portal, click **Start Building** dropdown → Select **Browse Models**
2. Search for **text-embedding-3-small**
3. Click on the model card
4. Click **Deploy**
5. Accept default settings:
   - **Deployment name:** `text-embedding-3-small`
   - **Model version:** Latest
6. Click **Deploy**

⏱️ **Wait 1-2 minutes** for deployment

### 3.4 Deploy Chat Model
1. In **Models** page, search for **gpt-4o**
2. Click on the model card
3. Click **Deploy**
4. Accept default settings:
   - **Deployment name:** `gpt-4o`
   - **Model version:** Latest
   - **Tokens per minute rate limit:** Default (varies by quota)
5. Click **Deploy**

⏱️ **Wait 1-2 minutes** for deployment

### 3.5 Verify Deployments
1. Go to **Deployments** page (left navigation)
2. You should see both deployments:
   - ✅ `text-embedding-3-small` - Status: Succeeded
   - ✅ `gpt-4o` - Status: Succeeded
3. Note the **Deployment names** - you'll use these in your code

✅ **Checkpoint:** AI Foundry project created with embedding and chat models deployed

---

## Part 4: Understanding Your Setup

**What You Now Have:**

```
┌─────────────────────────────────────────────────┐
│                 Azure Cloud                      │
│                                                  │
│  ┌──────────────────────┐  ┌─────────────────┐ │
│  │  DocumentDB Cluster   │  │  AI Foundry     │ │
│  │  (MongoDB vCore)      │  │  Project        │ │
│  │                       │  │                 │ │
│  │  • Stores data        │  │  • Embeddings   │ │
│  │  • MongoDB queries    │  │  • Chat models  │ │
│  │  • Vector search      │  │  • AI tools     │ │
│  └──────────────────────┘  └─────────────────┘ │
│           ↓                          ↓           │
└───────────│──────────────────────────│───────────┘
            │                          │
            ↓                          ↓
   ┌────────────────────────────────────────┐
   │        Your VS Code Workspace           │
   │                                         │
   │  • DocumentDB extension                 │
   │  • Scrapbooks for queries               │
   │  • Python/Node.js code                  │
   │  • Integration with both services       │
   └────────────────────────────────────────┘
```

**Components:**

1. **Azure DocumentDB Cluster**
   - MongoDB-compatible database (vCore model)
   - Stores your application data
   - Supports vector search for AI applications
   - Connected via DocumentDB extension

2. **AI Foundry Project**
   - Hosts your AI models (embeddings + chat)
   - Provides API endpoints for your code
   - Manages deployment and scaling
   - Used for building AI agents

3. **VS Code Workspace**
   - DocumentDB extension for database management
   - Scrapbooks for running queries
   - Code editor for Python/Node.js applications
   - Single place to manage everything

**Next Steps in Training:**
- Module 2: Data modeling patterns with DocumentDB
- Module 3: Vector search for AI applications
- Module 4: Building AI agents with DocumentDB + Foundry
- Module 5: Industry use cases and patterns

---

## Quick Reference

### DocumentDB Connection String Format
```
mongodb+srv://<username>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256
```

### Basic MongoDB Commands
```javascript
// Show databases
show dbs

// Switch database
use <dbname>

// Show collections
show collections

// Insert document
db.<collection>.insertOne({...})

// Find documents
db.<collection>.find({})

// Create index
db.<collection>.createIndex({field: 1})
```

### AI Foundry Endpoints
- **Portal:** https://ai.azure.com
- **Endpoint format:** `https://<resource>.openai.azure.com/`
- **API version:** Latest (check docs)

---

## Expected Outcomes

After completing this setup, you should have:

✅ **Azure DocumentDB cluster** provisioned and running  
✅ **VS Code connected** to DocumentDB with working queries  
✅ **AI Foundry project** created with models deployed  
✅ **Test database** with sample data in DocumentDB  
✅ **Connection details** saved for both services  
✅ **Understanding** of the infrastructure for AI+Database applications

**Skills gained:**
- Provisioning Azure DocumentDB (vCore) clusters
- Configuring networking and firewall rules
- Using DocumentDB for VS Code extension
- Running MongoDB queries in playgrounds
- Deploying Azure OpenAI models
- Setting up AI Foundry projects

---

## Additional Resources

### Azure DocumentDB (vCore)
- [Official Documentation](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/)
- [MongoDB Compatibility](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/compatibility)
- [Pricing Calculator](https://azure.microsoft.com/pricing/details/cosmos-db/)
- [Best Practices](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/best-practices)

### VS Code Extensions
- [DocumentDB for VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-documentdb) - **Recommended**
- [Official Extension Guide](https://documentdb.io/docs/getting-started/vscode-extension-guide) - Complete documentation
- [VS Code Quick Start](https://documentdb.io/docs/getting-started/vscode-quickstart) - Quick setup guide
- [Extension Announcement Blog](https://devblogs.microsoft.com/cosmosdb/meet-the-documentdb-extension-for-vs-code-and-documentdb-local-a-fast-friendly-way-to-work-with-documentdb-locally-and-beyond/)

### AI Foundry
- [AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Model Catalog](https://learn.microsoft.com/azure/ai-studio/how-to/model-catalog-overview)
- [Deployment Guide](https://learn.microsoft.com/azure/ai-services/openai/how-to/create-resource)

### MongoDB Resources
- MongoDB Query Language documentation
- Aggregation Framework documentation
- Online MongoDB courses available

---

## Next Module

🎯 **Module 2: Core Concepts & Data Modeling**
- NoSQL data modeling patterns
- Schema design for MongoDB
- Embedding vs referencing
- Indexing strategies
- Query optimization

**Prerequisites:** Complete this introduction module with working DocumentDB and AI Foundry setup.

---

**🎉 Setup Complete!** You now have a fully configured environment for building AI-powered applications with Azure DocumentDB and AI Foundry. Ready to dive into data modeling!
