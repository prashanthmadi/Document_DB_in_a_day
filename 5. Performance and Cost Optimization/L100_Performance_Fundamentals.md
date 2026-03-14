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

## Part 3: Reading `.explain()` Output — Walkthroughs

Let's run queries against our sample data and analyze their `.explain()` output in detail.

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

## Part 3.5: Compound Indexes for Multi-Field Queries

So far we have looked at queries that filter on a **single field**. Real-world application queries almost always filter on **multiple fields simultaneously** — and this is where compound indexes become essential.

### Why Compound Indexes Matter for Multi-Filter `find()` Queries

When a query filters on two or more fields, a **single-field index on just one of those fields** is not optimal. The index narrows the scan to documents matching the first field, but DocumentDB must then examine all of those documents individually to evaluate the second filter condition.

**Example:** If you have `{ region: 1 }` index and run `find({ region: "eastus", status: "delivered" })`:
- The index finds all ~30 documents where `region = "eastus"`
- DocumentDB then checks each of those 30 documents to see which ones also have `status = "delivered"`
- This is still far better than COLLSCAN, but a compound index on `{ region: 1, status: 1 }` would narrow the index scan directly to documents matching **both** conditions simultaneously

A compound index stores multiple fields together in a sorted B-tree, so the query engine can use a single index lookup to satisfy all filter conditions at once.

> 💡 **Brief ESR Rule introduction:** When building a compound index, field order matters. The **ESR rule** gives the optimal order:
> - **E**quality fields first (exact match filters like `{ status: "delivered" }`)
> - **S**ort fields next (fields used in `.sort()`)
> - **R**ange fields last (fields with `$gt`, `$lt`, `$gte`, `$lte`, `$in`)
>
> For the full ESR deep-dive with examples, see [L200: Advanced Optimization](L200_Cost_Optimization.md).

---

### Example 1 — Two Equality Filters

**Scenario:** Find all delivered orders in the eastus region.

```javascript
// Query: Find delivered orders in the eastus region
db.orders.find({ region: "eastus", status: "delivered" }).explain("executionStats");
```

**With only a single-field `{ region: 1 }` index:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",
      "filter": { "status": { "$eq": "delivered" } },
      "inputStage": {
        "stage": "IXSCAN",
        "keyPattern": { "region": 1 },
        "indexName": "region_1",
        "indexBounds": { "region": ["[\"eastus\", \"eastus\"]"] }
      }
    }
  },
  "executionStats": {
    "nReturned": 18,
    "executionTimeMillis": 4,
    "totalKeysExamined": 30,
    "totalDocsExamined": 30
  }
}
```

> ⚠️ **Problem:** The index on `region` finds 30 documents in "eastus", but DocumentDB must then fetch and check all 30 to filter out the non-delivered ones. `totalDocsExamined` (30) is significantly higher than `nReturned` (18).

Now create a compound index on both filter fields:

```javascript
// Create a compound index: both fields are equality matches
// Put the more selective field (region, ~30 unique per collection) first
db.orders.createIndex({ region: 1, status: 1 });
```

**Re-run the same query:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",
      "inputStage": {
        "stage": "IXSCAN",
        "keyPattern": { "region": 1, "status": 1 },
        "indexName": "region_1_status_1",
        "indexBounds": {
          "region": ["[\"eastus\", \"eastus\"]"],
          "status": ["[\"delivered\", \"delivered\"]"]
        }
      }
    }
  },
  "executionStats": {
    "nReturned": 18,
    "executionTimeMillis": 1,
    "totalKeysExamined": 18,
    "totalDocsExamined": 18
  }
}
```

| Metric | Single-field `{ region: 1 }` | Compound `{ region: 1, status: 1 }` |
|--------|------------------------------|-------------------------------------|
| totalDocsExamined | 30 | **18** |
| nReturned | 18 | 18 |
| Efficiency ratio | 0.60 | **1.0 (perfect)** |
| executionTimeMillis | 4ms | **1ms** |

> ✅ **Result:** The compound index eliminates all unnecessary document reads. `totalDocsExamined` now exactly equals `nReturned` — every document fetched was a match.

---

### Example 2 — Equality + Sort

**Scenario:** Find Electronics products sorted by rating (highest first).

```javascript
// Query: Find Electronics products sorted by rating (highest first)
db.products.find({ category: "Electronics" }).sort({ rating: -1 }).explain("executionStats");
```

**Without a compound index (using only `{ category: 1 }`):**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "SORT",
      "sortPattern": { "rating": -1 },
      "inputStage": {
        "stage": "FETCH",
        "inputStage": {
          "stage": "IXSCAN",
          "keyPattern": { "category": 1 },
          "indexName": "category_1"
        }
      }
    }
  },
  "executionStats": {
    "nReturned": 30,
    "executionTimeMillis": 8,
    "totalKeysExamined": 30,
    "totalDocsExamined": 30
  }
}
```

> ⚠️ **Problem:** The `SORT` stage appears in the winning plan. This means DocumentDB fetched all 30 Electronics documents and sorted them **in memory** after the IXSCAN. At production scale with thousands of documents, in-memory sorts are slow and memory-intensive.

Now apply the ESR rule — Equality (`category`) first, Sort (`rating`) next:

```javascript
// ESR Rule: Equality (category) → Sort (rating descending)
db.products.createIndex({ category: 1, rating: -1 });
```

**Re-run the same query:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",
      "inputStage": {
        "stage": "IXSCAN",
        "keyPattern": { "category": 1, "rating": -1 },
        "indexName": "category_1_rating_-1",
        "indexBounds": {
          "category": ["[\"Electronics\", \"Electronics\"]"],
          "rating": ["[MaxKey, MinKey]"]
        }
      }
    }
  },
  "executionStats": {
    "nReturned": 30,
    "executionTimeMillis": 2,
    "totalKeysExamined": 30,
    "totalDocsExamined": 30
  }
}
```

| Metric | Without compound index | With `{ category: 1, rating: -1 }` |
|--------|------------------------|-------------------------------------|
| SORT stage | ❌ Present (in-memory) | ✅ **Eliminated** |
| executionTimeMillis | 8ms | **2ms** |
| Index-backed sort | ❌ No | ✅ **Yes** |

> ✅ **Result:** The `SORT` stage is eliminated. The compound index stores documents pre-sorted by `rating` within each `category`, so DocumentDB delivers them in the correct order directly from the index scan — no in-memory sort required.

---

### Example 3 — Compound Index with Projection (Efficient Targeted Scan)

**Scenario:** Get only `status` and `total` for eastus orders, excluding all other fields.

```javascript
// Query: Get only status and total for eastus orders
db.orders.find(
  { region: "eastus" },
  { _id: 0, status: 1, total: 1 }
).explain("executionStats");
```

Create a compound index that includes the filter field **and** all projected fields:

```javascript
// Index includes: filter field (region) + projected fields (status, total)
db.orders.createIndex({ region: 1, status: 1, total: 1 });
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
          "keyPattern": { "region": 1, "status": 1, "total": 1 },
          "indexName": "region_1_status_1_total_1",
          "indexBounds": {
            "region": ["[\"eastus\", \"eastus\"]"],
            "status": ["[MinKey, MaxKey]"],
            "total": ["[MinKey, MaxKey]"]
          }
        }
      }
    }
  },
  "executionStats": {
    "nReturned": 30,
    "executionTimeMillis": 1,
    "totalKeysExamined": 30,
    "totalDocsExamined": 30
  }
}
```

> ⚠️ **Azure DocumentDB note:** Unlike native MongoDB, Azure DocumentDB does **not** currently support fully covered queries where `totalDocsExamined` is 0. Even when all projected fields are in the index, DocumentDB still fetches matching documents. The key benefit is that the IXSCAN narrows the scan to **only matching documents** (achieving a perfect 1.0 efficiency ratio), and the **projection reduces data transferred** to the client.

| Metric | Without compound+projection index | With `{ region: 1, status: 1, total: 1 }` |
|--------|------------------------------------|-------------------------------------------|
| totalDocsExamined | 80 (COLLSCAN) | **30** (only matching docs) |
| nReturned | 30 | 30 |
| Efficiency ratio | 0.375 | **1.0 (perfect)** |
| Data transferred | Full documents | **Only status + total fields** |

> ✅ **Result:** The compound index narrows the scan to only the 30 eastus documents (efficiency = 1.0), and the projection ensures only `status` and `total` are sent over the network — minimizing both server-side work and network overhead.

---

### Summary Table: Index Patterns for `find()` Queries

| Pattern | Index | Stage | docsExamined vs nReturned | Performance |
|---------|-------|-------|--------------------------|-------------|
| No index | — | `COLLSCAN` | All docs >> nReturned | ❌ Worst |
| Single field (one filter) | `{ region: 1 }` | `IXSCAN` → `FETCH` | Only matching (1 field) docs | ✅ Good |
| Compound (two equality filters) | `{ region: 1, status: 1 }` | `IXSCAN` → `FETCH` | Only exact matches | ✅ Better |
| Compound (equality + sort) | `{ category: 1, rating: -1 }` | `IXSCAN` → `FETCH` (no SORT) | Only matching, pre-sorted | ✅ Better |
| Compound + projection | `{ region: 1, status: 1, total: 1 }` | `IXSCAN` → `FETCH` → `PROJECTION` | Only matching docs, less data sent | ✅ Best |

---

### ⚠️ When NOT to Over-Index

Every index has a cost:
- **Storage:** Each index is a separate B-tree that consumes disk space
- **Write overhead:** Every `insert`, `update`, and `delete` must update all indexes on the collection
- **Maintenance:** More indexes = more complexity when troubleshooting performance

**Guidelines:**
- Create indexes for queries that are **frequent** and **critical** (high user-facing impact)
- Avoid creating an index for every possible field combination
- Use `$indexStats` to identify indexes that are rarely used and consider dropping them
- For low-frequency queries (e.g., monthly reports), a brief COLLSCAN may be acceptable

> 🔗 **Next step:** For advanced compound index design including the full ESR rule, range query optimization, and index intersection, see [L200: Advanced Optimization](L200_Cost_Optimization.md).

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

> 💡 **Note:** The Hands-On Lab will guide you through creating indexes from scratch, so dropping them here gives you a clean starting point.

---

✅ **Checkpoint:** You can now read `.explain()` output and identify the difference between collection scans, index scans, and compound index + projection queries. You're ready for [Hands-On Lab: Performance Optimization](Lab_Hands_On.md)!

---

[← Back to Module Overview](README.md) | [Next: Hands-On Lab →](Lab_Hands_On.md)
