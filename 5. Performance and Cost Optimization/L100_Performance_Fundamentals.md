# L100: Performance Fundamentals

**Duration:** 20–30 minutes | **Level:** L100 | **Goal:** Understand how DocumentDB processes queries and learn to read `.explain()` output

---

## What You'll Learn

- 🔍 How DocumentDB executes queries (scan types)
- 📊 Using `.explain("executionStats")` to analyze query performance
- 📈 Key performance metrics and what they mean
- 💡 Identifying performance bottlenecks from explain output

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ VSCode with DocumentDB extension connected to your cluster

---

## Part 1: How DocumentDB Processes Queries

### 1.1 The Query Execution Pipeline

When you run a query in DocumentDB, the server follows this process:

```
Query → Query Planner → Execution Plan → Data Access → Results
```

The **Query Planner** decides the most efficient way to access data. The two primary strategies are:

| Strategy | Description | Performance |
|----------|-------------|-------------|
| **Collection Scan (COLLSCAN)** | Reads every document in the collection | ❌ Slow — scales linearly with data size |
| **Index Scan (IXSCAN)** | Uses an index to jump directly to matching documents | ✅ Fast — scales logarithmically |

### 1.2 Why This Matters

Consider a `products` collection with 50 documents vs. one with 5,000,000 documents:

- **COLLSCAN** on 50 docs: ~1ms (fine for development)
- **COLLSCAN** on 5M docs: ~5,000ms+ (unacceptable for production)
- **IXSCAN** on 5M docs: ~2ms (fast at any scale)

> 💡 **Key Insight:** Most performance issues in DocumentDB come from missing indexes — not from insufficient compute resources. Always check your query plans before scaling up.

### 1.3 What Is an Index?

An index is a data structure that stores a sorted subset of fields from your documents, enabling the database to locate matching documents without scanning the entire collection.

Think of it like a book's index: instead of reading every page to find a topic, you look up the page number in the index.

```javascript
// Without an index, this scans ALL 80 orders:
db.orders.find({ status: "delivered" });

// With an index on "status", the server jumps directly to matching documents:
db.orders.createIndex({ status: 1 });
db.orders.find({ status: "delivered" });
```
### 1.4 Index Can Be Slower on Small Collections

### What’s Happening
With a very small dataset (e.g., **80 documents**), adding an index can actually **degrade performance**. This is an expected behavior.

### Without Index — **COLLSCAN (Collection Scan)**
- DocumentDB scans all documents sequentially
- 80 documents fit entirely in RAM
- Single linear read from memory/cache
- **Minimal overhead and very fast**

### With Index — **IXSCAN (Index Scan)**
DocumentDB performs **two steps instead of one**:
1. Traverse the B-tree index to find matching entries (e.g., `region = "eastus"`)
2. Fetch each document by record ID using random lookups

For such a small dataset, below `.explain()` sample outputs are tweaked for learning purposes

---

## Part 2: The `.explain()` Method

### 2.1 What Is `.explain()`?

The `.explain()` method reveals how DocumentDB plans to execute (or has executed) a query. It's the most important tool for diagnosing performance issues.

Three verbosity levels:

| Level | What It Shows |
|-------|---------------|
| `"queryPlanner"` | The winning query plan (default) |
| `"executionStats"` | Plan + actual execution metrics |
| `"allPlansExecution"` | All candidate plans with execution stats |

For performance analysis, always use **`"executionStats"`**:

```javascript
db.orders.find({ region: "eastus" }).explain("executionStats");
```

### 2.2 Key Metrics to Watch

When reading `.explain()` output, focus on these critical fields:

| Metric | Location | What It Means |
|--------|----------|---------------|
| `winningPlan.stage` | `queryPlanner` | How the data is accessed (`COLLSCAN` vs `IXSCAN`) |
| `nReturned` | `executionStats` | Number of documents returned to the client |
| `totalDocsExamined` | `executionStats` | Number of documents the server had to read |
| `totalKeysExamined` | `executionStats` | Number of index entries scanned |
| `executionTimeMillis` | `executionStats` | Total time to execute the query |

### 2.3 The Efficiency Ratio

The most important thing to check is the **ratio** between documents examined and documents returned:

```
Efficiency = nReturned / totalDocsExamined
```

| Ratio | Meaning |
|-------|---------|
| **1.0** (nReturned == totalDocsExamined) | ✅ Perfect — every document examined was returned |
| **< 0.5** | ⚠️ Warning — more than half of examined documents were filtered out |
| **<< 0.01** | ❌ Critical — the query is scanning far more data than needed |

---

## Part 3: Reading `.explain()` Output — Three Walkthroughs

Let's run three queries against our sample data and analyze their `.explain()` output in detail.

### 3.1 Example 1: Collection Scan (COLLSCAN) — No Index

Run this query in your VSCode DocumentDB scrapbook:

```javascript
// Query: Find all orders in the "eastus" region
db.orders.find({ region: "eastus" }).explain("executionStats");
```

**Sample `.explain()` output:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "COLLSCAN",
      "filter": {
        "region": { "$eq": "eastus" }
      },
      "direction": "forward"
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 30,
    "executionTimeMillis": 12,
    "totalKeysExamined": 0,
    "totalDocsExamined": 80
  }
}
```

**📖 How to Read This:**

| Field | Value | Interpretation |
|-------|-------|----------------|
| `stage` | `COLLSCAN` | ❌ Full collection scan — no index was used |
| `nReturned` | `30` | 30 orders matched the filter `region: "eastus"` |
| `totalDocsExamined` | `80` | All 80 documents were read to find those 30 |
| `totalKeysExamined` | `0` | No index keys were used (confirms COLLSCAN) |
| `executionTimeMillis` | `12` | 12ms execution time |

**🔍 Analysis:** The server scanned **all 80 documents** to return **30 results**. The efficiency ratio is 30/80 = **0.375**. With 80 documents this is fast enough, but at production scale (millions of documents) this would be extremely slow.

> ❌ **Problem:** COLLSCAN means every query touches every document. Cost and time grow linearly with collection size.

---

### 3.2 Example 2: Index Scan (IXSCAN) — Single Field Index

First, create an index on the `region` field:

```javascript
// Create a single-field index on region
db.orders.createIndex({ region: 1 });
```

Now re-run the same query with `.explain()`:

```javascript
// Same query, but now an index exists
db.orders.find({ region: "eastus" }).explain("executionStats");
```

**Sample `.explain()` output:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",
      "inputStage": {
        "stage": "IXSCAN",
        "keyPattern": { "region": 1 },
        "indexName": "region_1",
        "direction": "forward",
        "indexBounds": {
          "region": ["[\"eastus\", \"eastus\"]"]
        }
      }
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 30,
    "executionTimeMillis": 2,
    "totalKeysExamined": 30,
    "totalDocsExamined": 30
  }
}
```

**📖 How to Read This:**

| Field | Value | Interpretation |
|-------|-------|----------------|
| `stage` | `FETCH` → `IXSCAN` | ✅ Used an index scan, then fetched matching documents |
| `indexName` | `region_1` | The `region` index was used |
| `nReturned` | `30` | 30 orders matched |
| `totalDocsExamined` | `30` | Only 30 documents were read (exactly the matching ones) |
| `totalKeysExamined` | `30` | 30 index keys were checked |
| `executionTimeMillis` | `2` | 2ms — 6x faster than the COLLSCAN |

**🔍 Analysis:** With the index, the efficiency ratio is 30/30 = **1.0 (perfect)**. The server only examined documents that matched the query. Execution time dropped from 12ms to 2ms.

> ✅ **Result:** Adding a single index reduced documents examined from 80 → 30 and execution time from 12ms → 2ms.

---

### 3.3 Example 3: Compound Index with Projection — Efficient Targeted Scan

A **compound index with a projection** is an important optimization pattern. By including all projected fields in a compound index, the query engine can narrow the index scan to only matching documents while also reducing the amount of data sent to the client.

For this pattern to work effectively:
1. All fields in the **filter** must be in the index
2. All fields in the **projection** should be in the index (reduces data transfer)
3. The `_id` field should be excluded from the projection (unless needed)

> ⚠️ **Azure DocumentDB Note:** Unlike native MongoDB, Azure DocumentDB does **not** currently support fully covered queries where `totalDocsExamined` equals 0. Even when all projected fields are in the index, DocumentDB still fetches the matching documents. The benefit is that the IXSCAN narrows the scan to only matching documents, and the projection reduces the data sent to the client.

```javascript
// Create a compound index that covers the query
db.orders.createIndex({ status: 1, total: 1 });
```

Now run the query with a projection:

```javascript
// Projection query: only request fields that exist in the index
db.orders.find(
  { status: "delivered" },
  { _id: 0, status: 1, total: 1 }
).explain("executionStats");
```

**Sample `.explain()` output:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "PROJECTION_SIMPLE",
      "inputStage": {
        "stage": "FETCH",
        "inputStage": {
          "stage": "IXSCAN",
          "keyPattern": { "status": 1, "total": 1 },
          "indexName": "status_1_total_1",
          "direction": "forward",
          "indexBounds": {
            "status": ["[\"delivered\", \"delivered\"]"],
            "total": ["[MinKey, MaxKey]"]
          }
        }
      }
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 60,
    "executionTimeMillis": 1,
    "totalKeysExamined": 60,
    "totalDocsExamined": 60
  }
}
```

**📖 How to Read This:**

| Field | Value | Interpretation |
|-------|-------|----------------|
| `stage` | `PROJECTION_SIMPLE` → `FETCH` → `IXSCAN` | ✅ Index scan, then fetches only matching documents |
| `nReturned` | `60` | 60 delivered orders found |
| `totalDocsExamined` | `60` | Only matching documents fetched (equals nReturned — perfect efficiency) |
| `totalKeysExamined` | `60` | 60 index entries scanned |
| `executionTimeMillis` | `1` | 1ms — very fast execution |

**🔍 Analysis:** The compound index + projection combination is highly efficient. `totalDocsExamined` equals `nReturned` (60/60 = 1.0 — perfect ratio), meaning the IXSCAN eliminated all non-matching documents. The projection further reduces data transferred to the client. This is the recommended pattern for Azure DocumentDB.

> ✅ **Best Practice:** Use projections with compound indexes to minimize both scan scope and data transfer. In Azure DocumentDB, the index narrows the fetch to only matching documents (achieving a 1.0 efficiency ratio), and the projection reduces network overhead.

---

## Part 4: Common Performance Patterns

### 4.1 Pattern Summary

| Pattern | Stage | Docs Examined | Performance |
|---------|-------|---------------|-------------|
| No index | `COLLSCAN` | All documents | ❌ Worst |
| Single-field index | `IXSCAN` → `FETCH` | Only matching docs | ✅ Good |
| Compound index | `IXSCAN` → `FETCH` | Only matching docs (narrower scan) | ✅ Better |
| Compound index + projection | `IXSCAN` → `FETCH` | Only matching docs | ✅ Best with projection |

### 4.2 Warning Signs in `.explain()` Output

Watch for these red flags:

- **`COLLSCAN`** — No index is being used
- **`totalDocsExamined` >> `nReturned`** — Index doesn't match the query well
- **`totalKeysExamined` >> `nReturned`** — Index is being scanned inefficiently
- **`SORT` stage without `IXSCAN`** — In-memory sort (slow for large results)

### 4.3 Index Types in DocumentDB

| Index Type | Use Case | Example |
|------------|----------|---------|
| **Single field** | Queries on one field | `{ region: 1 }` |
| **Compound** | Queries on multiple fields | `{ category: 1, price: -1 }` |
| **Wildcard** | Queries on dynamic/varied fields | `{ "$**": 1 }` |
| **Text** | Full-text search | `{ name: "text" }` |

> 💡 **Tip:** Compound indexes follow the **ESR rule** — put **E**quality fields first, **S**ort fields next, and **R**ange fields last for optimal performance.

---

## Part 5: Key Takeaways

1. **Always use `.explain("executionStats")`** to understand how your queries perform
2. **COLLSCAN = performance risk** — add an index for any query that hits production
3. **Check the efficiency ratio** — `nReturned` should be close to `totalDocsExamined`
4. **Use projections with compound indexes** — this minimizes both scan scope and data transfer; Azure DocumentDB still fetches matching documents but the IXSCAN ensures only relevant documents are read
5. **Indexes cost storage and write throughput** — don't create indexes you don't need

---

## 📋 Quick Reference: `.explain()` Cheat Sheet

```javascript
// Basic explain (query plan only)
db.collection.find({ field: value }).explain();

// Execution stats (recommended for analysis)
db.collection.find({ field: value }).explain("executionStats");

// All plans execution (compare candidate plans)
db.collection.find({ field: value }).explain("allPlansExecution");
```

**Key fields to check:**
```
queryPlanner.winningPlan.stage          → COLLSCAN or IXSCAN?
executionStats.nReturned                → How many docs returned?
executionStats.totalDocsExamined        → How many docs read?
executionStats.totalKeysExamined        → How many index keys scanned?
executionStats.executionTimeMillis      → How long did it take?
```

---

## 🧹 Cleanup (Optional)

If you want to reset indexes before the next module, drop the ones created in this lesson:

```javascript
db.orders.dropIndex("region_1");
db.orders.dropIndex("status_1_total_1");
```

> 💡 **Note:** Lab 1 will guide you through creating indexes from scratch, so dropping them here gives you a clean starting point.

---

✅ **Checkpoint:** You can now read `.explain()` output and identify the difference between collection scans, index scans, and compound index + projection queries. You're ready for [Lab 1: Index Optimization](Lab1_Index_Optimization.md)!

---

[← Back to Module Overview](README.md) | [Next: Lab 1 — Index Optimization →](Lab1_Index_Optimization.md)
