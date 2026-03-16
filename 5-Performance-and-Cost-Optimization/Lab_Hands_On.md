# 🔬 Hands-On Lab: Performance Optimization

**Duration:** 30–40 minutes | **Level:** L100–L200 | **Hands-On Lab**

---

## 🎯 Lab Objective

In this lab, you will apply the concepts from L100 and L200 in a single cohesive workflow:
- Diagnose collection scans with `.explain()`
- Build compound indexes for multi-field queries and projections
- Tune queries using projections, limits, and the ESR rule
- Optimize aggregation pipelines
- Analyze a real workload and make a scaling decision

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ Read [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ Read [L200: Advanced Optimization & Cost Strategies](L200_Performance_and_Cost_Optimization.md)
- ✅ VSCode with DocumentDB extension connected to your cluster

---

## Lab Setup

Open a new MongoDB Scrapbook in VSCode. Make sure you are connected to your DocumentDB cluster.

> 💡 **Note:** Select the `ecommerce` database from the VSCode DocumentDB extension's connection panel before running any commands. The `use()` command is not supported in the DocumentDB extension scrapbook.

Drop any existing indexes to start clean (preserves the default `_id` index):

```javascript
// Reset indexes on all collections — start with a clean slate
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

---

## Exercise 1: Diagnose Collection Scans

**Scenario:** Your application frequently queries orders by status. Let's see how this performs without an index and then fix it.

### Step 1: Run the query with `.explain()`

```javascript
db.orders.find({ status: "delivered" }).explain("executionStats");
```

### Step 2: Analyze the output

Look for these fields in the output:

- `winningPlan.stage` → Should be `COLLSCAN`
- `totalDocsExamined` → Should be `80` (all documents)
- `nReturned` → Should be approximately `60`
- `executionTimeMillis` → Note the value

📝 **Write down:**
- What stage is used? __________
- How many documents were examined? __________
- How many documents were returned? __________
- What is the efficiency ratio (nReturned / totalDocsExamined)? __________

### Step 3: Create a single-field index

```javascript
db.orders.createIndex({ status: 1 });
```

### Step 4: Re-run the query

```javascript
db.orders.find({ status: "delivered" }).explain("executionStats");
```

### Step 5: Compare the results

📝 **Write down the new values:**
- What stage is used now? __________
- How many documents were examined? __________
- How many documents were returned? __________
- What is the efficiency ratio? __________

<details>
<summary>✅ Expected Results</summary>

| Metric | Before (COLLSCAN) | After (IXSCAN) |
|--------|-------------------|-----------------|
| Stage | COLLSCAN | IXSCAN → FETCH |
| totalDocsExamined | 80 | ~60 |
| nReturned | ~60 | ~60 |
| Efficiency | ~0.75 | ~1.0 |

The index reduced `totalDocsExamined` to match `nReturned` — the server no longer reads documents that don't match.

</details>

---

## Exercise 2: Compound Indexes & Covered Queries

**Scenario:** Your dashboard queries orders by region AND status simultaneously, and your reporting service only needs specific fields.

### Part A — Compound Index for Multi-Field Filter

```javascript
// Step 1: Test the two-field query (status index from Ex 1 may be used, but not optimal)
db.orders.find({
  region: "eastus",
  status: "delivered"
}).explain("executionStats");
```

📝 **Note the `totalDocsExamined` value:** __________

```javascript
// Step 2: Create a compound index following the ESR rule
// Both fields are equality matches — put the more selective field first
db.orders.createIndex({ region: 1, status: 1 });
```

```javascript
// Step 3: Re-run the query
db.orders.find({
  region: "eastus",
  status: "delivered"
}).explain("executionStats");
```

📝 **Write down:**
- Is the compound index being used? __________
- What is `totalDocsExamined` now? __________
- What is `nReturned`? __________

<details>
<summary>✅ Expected Results (Part A)</summary>

The compound index `{ region: 1, status: 1 }` should now be used. `totalDocsExamined` should drop to approximately match `nReturned` (around 18–20 documents), since the index efficiently narrows to the intersection of both filters — achieving a perfect 1.0 efficiency ratio.

</details>

---

### Part B — Extend to a Projection Query

```javascript
// Step 4: Create a compound index that also includes the projected fields
db.orders.createIndex({ region: 1, status: 1, total: 1 });
```

```javascript
// Step 5: Run a projection query — only request fields covered by the index
db.orders.find(
  { region: "eastus" },
  { _id: 0, status: 1, total: 1 }
).explain("executionStats");
```

📝 **Check these values:**
- `totalDocsExamined` → Should match `nReturned` (~30) — IXSCAN fetches only matching docs
- `totalKeysExamined` → Should match `nReturned`
- `winningPlan.stage` → Should include `IXSCAN` → `FETCH`

> ⚠️ **Azure DocumentDB Note:** In Azure DocumentDB, `totalDocsExamined` will equal `nReturned` (not 0) even when all projected fields are in the index. The IXSCAN narrows the fetch to only matching documents (perfect 1.0 efficiency ratio), and the projection reduces data transferred to the client.

<details>
<summary>✅ Expected Results (Part B)</summary>

```
totalDocsExamined: ~30  ← Only matching documents fetched (equals nReturned)
totalKeysExamined: ~30  ← Only index keys for matching docs were read
nReturned: ~30
stage: IXSCAN → FETCH → PROJECTION_SIMPLE
```

The compound index + projection achieves a **perfect 1.0 efficiency ratio** — only matching documents are fetched. The projection also reduces data transferred to the client.

</details>

---

## Exercise 3: Query Tuning with Projections & Limits

### Part A — Product Search Optimization

**Scenario:** Your e-commerce site has a product search page. Users filter by category and sort by rating. The current query is slow.

```javascript
// Step 1: Run the unoptimized query — no index, no projection
db.products.find(
  { category: "Electronics" }
).sort({ rating: -1 }).explain("executionStats");
```

📝 **Record the baseline:**
- Stage: __________
- totalDocsExamined: __________
- Is there a SORT stage? __________

```javascript
// Step 2: Add a compound index using the ESR rule
// Equality (category) → Sort (rating descending)
db.products.createIndex({ category: 1, rating: -1 });
```

```javascript
// Step 3: Re-run with explain — note that SORT stage is eliminated
db.products.find(
  { category: "Electronics" }
).sort({ rating: -1 }).explain("executionStats");
```

📝 **Record improvements:**
- Stage: __________
- Is the SORT stage gone? __________

```javascript
// Step 4: Add projection to reduce data transfer
db.products.find(
  { category: "Electronics" },
  { _id: 1, name: 1, price: 1, rating: 1 }
).sort({ rating: -1 });
```

```javascript
// Step 5: Add a limit for pagination (real search pages show 10 results)
db.products.find(
  { category: "Electronics" },
  { _id: 1, name: 1, price: 1, rating: 1 }
).sort({ rating: -1 }).limit(10);
```

<details>
<summary>✅ Expected Optimization Summary (Part A)</summary>

| Step | Change | Impact |
|------|--------|--------|
| Baseline | No index, full docs | COLLSCAN, in-memory sort |
| + Index | `{ category: 1, rating: -1 }` | IXSCAN, no SORT stage |
| + Projection | Only 4 fields returned | Less data transferred |
| + Limit | `.limit(10)` | Only 10 docs processed/returned |

Each step progressively improves performance.

</details>

---

### Part B — Customer Order Lookup Optimization

**Scenario:** Customer support agents look up orders by customer ID and need recent orders first.

```javascript
// Step 1: Run the unoptimized query
db.orders.find(
  { customerId: "CUST005" }
).sort({ orderDate: -1 }).explain("executionStats");
```

📝 **Record:** Stage: __________ | DocsExamined: __________

```javascript
// Step 2: Create an optimal index using the ESR rule
// Equality (customerId) → Sort (orderDate descending)
db.orders.createIndex({ customerId: 1, orderDate: -1 });
```

```javascript
// Step 3: Re-run with explain
db.orders.find(
  { customerId: "CUST005" }
).sort({ orderDate: -1 }).explain("executionStats");
```

```javascript
// Step 4: Add a projection for the support agent UI
// Only the fields needed: order date, status, total, and items summary
db.orders.find(
  { customerId: "CUST005" },
  { _id: 1, orderDate: 1, status: 1, total: 1, "items.name": 1 }
).sort({ orderDate: -1 });
```

Expected output (most recent orders first):
```json
[
  { "_id": "ORD053", "orderDate": "2025-05-06", "status": "pending", "total": 389.97, "items": [{"name": "Drawing Tablet Pen"}, {"name": "Portable Monitor 15.6 inch"}] },
  { "_id": "ORD035", "orderDate": "2025-04-18", "status": "delivered", "total": 869.94, "items": [{"name": "Thunderbolt 4 Dock"}, {"name": "External SSD 1TB"}] },
  { "_id": "ORD018", "orderDate": "2025-04-01", "status": "delivered", "total": 1089.96, "items": [{"name": "Executive Desk Large"}, {"name": "Ergonomic Office Chair"}, {"name": "Monitor Arm Mount"}] },
  { "_id": "ORD005", "orderDate": "2025-03-19", "status": "delivered", "total": 339.97, "items": [{"name": "Noise Cancelling Earbuds"}, {"name": "Laptop Stand Aluminum"}] }
]
```

<details>
<summary>✅ Expected Results (Part B)</summary>

With the `{ customerId: 1, orderDate: -1 }` index:
- `totalDocsExamined` drops from 80 to ~4 (only CUST005's orders)
- No in-memory SORT stage (the index provides the sort)
- Projection reduces response size for the UI

</details>

---

## Exercise 4: Aggregation Pipeline Optimization

**Scenario:** The analytics dashboard needs to show revenue by region for delivered orders, sorted by revenue.

### Step 1: Run an unoptimized pipeline

```javascript
// ❌ Unoptimized: $group runs on ALL documents before any filtering
db.orders.aggregate([
  { $group: {
    _id: "$region",
    totalRevenue: { $sum: "$total" },
    orderCount: { $sum: 1 }
  }},
  { $match: { orderCount: { $gt: 0 } } },
  { $sort: { totalRevenue: -1 } }
]);
```

This processes ALL 80 orders (including non-delivered ones) in the `$group` stage.

### Step 2: Add an early `$match` stage

```javascript
// ✅ Optimized: Filter to delivered orders FIRST, then aggregate
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $group: {
    _id: "$region",
    totalRevenue: { $sum: "$total" },
    orderCount: { $sum: 1 }
  }},
  { $sort: { totalRevenue: -1 } },
  { $project: {
    region: "$_id",
    _id: 0,
    totalRevenue: { $round: ["$totalRevenue", 2] },
    orderCount: 1
  }}
]);
```

### Step 3: Add an index to support the `$match`

```javascript
db.orders.createIndex({ status: 1 });
```

### Step 4: Verify the pipeline uses the index

```javascript
db.orders.explain("executionStats").aggregate([
  { $match: { status: "delivered" } },
  { $group: {
    _id: "$region",
    totalRevenue: { $sum: "$total" },
    orderCount: { $sum: 1 }
  }},
  { $sort: { totalRevenue: -1 } }
]);
```

Expected analytics output:
```json
[
  { "region": "eastus", "totalRevenue": 15284.95, "orderCount": 24 },
  { "region": "centralus", "totalRevenue": 13193.09, "orderCount": 17 },
  { "region": "westus", "totalRevenue": 4855.70, "orderCount": 19 }
]
```

<details>
<summary>✅ Expected Results</summary>

| Optimization | Impact |
|-------------|--------|
| Early `$match` | Reduces documents flowing through pipeline (80 → ~60) |
| Index on `status` | `$match` uses IXSCAN instead of COLLSCAN |
| `$project` at end | Shapes output cleanly for the dashboard |

The first `$match` stage can use an index, so adding `{ status: 1 }` makes the pipeline more efficient. Always put `$match` (and `$limit`) as early as possible in aggregation pipelines.

</details>

---

## Exercise 5: Workload Analysis & Scaling Decision

**Scenario:** Your team is considering scaling up the DocumentDB cluster because "the database is slow." Before approving the cost increase, let's analyze the actual workload and apply the optimization-first principle.

### Step 1: Reset indexes and identify top query patterns

```javascript
// Start clean for this workload analysis
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

Run these 5 representative queries to simulate the workload:

```javascript
// Query Pattern 1: Order lookup by customer (customer support portal)
db.orders.find({ customerId: "CUST001" }).sort({ orderDate: -1 }).explain("executionStats");
```

```javascript
// Query Pattern 2: Product search by category + sort by rating (storefront)
db.products.find({ category: "Electronics" }).sort({ rating: -1 }).explain("executionStats");
```

```javascript
// Query Pattern 3: Order status filter (operations dashboard)
db.orders.find({ status: "pending" }).explain("executionStats");
```

```javascript
// Query Pattern 4: Customer lookup by region + tier (marketing)
db.customers.find({ region: "eastus", tier: "premium" }).explain("executionStats");
```

```javascript
// Query Pattern 5: Revenue analytics (finance dashboard)
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $group: { _id: "$region", revenue: { $sum: "$total" } } },
  { $sort: { revenue: -1 } }
]);
```

### Step 2: Record the findings

📝 **Fill in this analysis table:**

| Query Pattern | Stage | DocsExamined | nReturned | Ratio | Needs Index? |
|---------------|-------|-------------|-----------|-------|-------------|
| 1. Order by customer | | | | | |
| 2. Product search | | | | | |
| 3. Order by status | | | | | |
| 4. Customer lookup | | | | | |
| 5. Revenue analytics | | | | | |

<details>
<summary>✅ Expected Results (Before Indexes)</summary>

| Query Pattern | Stage | DocsExamined | nReturned | Ratio | Needs Index? |
|---------------|-------|-------------|-----------|-------|-------------|
| 1. Order by customer | COLLSCAN | 80 | ~4 | 0.05 | ✅ Yes |
| 2. Product search | COLLSCAN | 50 | ~30 | 0.60 | ✅ Yes (also needs sort) |
| 3. Order by status | COLLSCAN | 80 | ~10 | 0.13 | ✅ Yes |
| 4. Customer lookup | COLLSCAN | 30 | ~4 | 0.13 | ✅ Yes |
| 5. Revenue analytics | COLLSCAN | 80 | N/A | N/A | ✅ Yes ($match stage) |

**Conclusion:** All 5 queries use COLLSCAN. The fix is **indexing, not scaling**. Throwing more compute at this workload would be wasteful.

</details>

---

### Step 3: Design the minimum index set

Consider which queries can share indexes. A compound index `{ A: 1, B: 1 }` supports queries that filter on `A` alone or `A` and `B` together (but NOT `B` alone — leftmost prefix rule).

```javascript
// Index 1: Orders — supports customer lookup + sort (Pattern 1)
db.orders.createIndex({ customerId: 1, orderDate: -1 });

// Index 2: Orders — supports status filter (Pattern 3) AND aggregation $match (Pattern 5)
db.orders.createIndex({ status: 1 });

// Index 3: Products — supports category search + rating sort (Pattern 2)
db.products.createIndex({ category: 1, rating: -1 });

// Index 4: Customers — supports region + tier lookup (Pattern 4)
db.customers.createIndex({ region: 1, tier: 1 });
```

> 💡 **Notice:** We created only **4 indexes** to support **5 query patterns**. Index 2 (`status: 1`) supports both Pattern 3 (status filter) and Pattern 5 (aggregation `$match` on status). This is efficient index design.

> 💡 **Tip:** Use `$indexStats` to monitor which indexes are actually being used in production and identify unused ones to clean up. In Azure DocumentDB, `$indexStats` support may vary — check the Azure Portal metrics as an alternative.

---

### Step 4: Verify all queries now use indexes

Re-run all 5 queries with `.explain()` and confirm they all show `IXSCAN`:

```javascript
// Verify Pattern 1
db.orders.find({ customerId: "CUST001" }).sort({ orderDate: -1 }).explain("executionStats");
```

```javascript
// Verify Pattern 2
db.products.find({ category: "Electronics" }).sort({ rating: -1 }).explain("executionStats");
```

```javascript
// Verify Pattern 3
db.orders.find({ status: "pending" }).explain("executionStats");
```

```javascript
// Verify Pattern 4
db.customers.find({ region: "eastus", tier: "premium" }).explain("executionStats");
```

```javascript
// Verify Pattern 5
db.orders.explain("executionStats").aggregate([
  { $match: { status: "delivered" } },
  { $group: { _id: "$region", revenue: { $sum: "$total" } } }
]);
```

📝 **Verify:** All 5 queries should now show `IXSCAN` instead of `COLLSCAN`.

<details>
<summary>✅ Expected Results (After Indexes)</summary>

| Query Pattern | Stage | DocsExamined | Improvement |
|---------------|-------|-------------|-------------|
| 1. Order by customer | IXSCAN → FETCH | ~4 | 80 → 4 (20x fewer) |
| 2. Product search | IXSCAN → FETCH | ~30 | No SORT stage (index-backed) |
| 3. Order by status | IXSCAN → FETCH | ~10 | 80 → 10 (8x fewer) |
| 4. Customer lookup | IXSCAN → FETCH | ~4 | 30 → 4 (7.5x fewer) |
| 5. Revenue analytics | IXSCAN in $match | ~60 | $match uses index |

</details>

---

### Step 5: Apply the scaling decision framework

After optimizing indexes, answer these questions to decide whether scaling is needed:

📝 **Question 1:** Did optimization resolve the performance issue?
- Check CPU utilization after applying indexes: __________
- If CPU dropped to < 50%, the issue was missing indexes — no scaling needed.

📝 **Question 2:** If queries are still slow after full index optimization:
- Is CPU consistently > 70–80%? → Consider vertical scaling (increase tier)
- Are you near the M200 tier limit or running millions of users? → Consider horizontal scaling (add shards)
- See [L300: Sharding & Scaling](L300_Sharding_and_Scaling.md) for the full scaling decision framework.

<details>
<summary>✅ Cost Impact Summary</summary>

```
Before Optimization:
   - All queries: COLLSCAN
   - Potential "fix": Scale compute from 4 vCores → 8 vCores ($$$)
   - Actual impact of scaling: Marginal improvement (I/O bottleneck, not CPU)

After Optimization:
   - All queries: IXSCAN
   - Indexes added: 4 (minimal storage cost)
   - Performance improvement: 5–20x faster queries
   - Compute scaling needed: NO
   - Cost savings: Avoided unnecessary compute upgrade
```

**Key takeaway:** Optimize first, scale second. Most "slow database" complaints are resolved at the index level without any cost increase.

</details>

---

## Lab Summary

| Exercise | Concept | Key Takeaway |
|----------|---------|-------------|
| 1 | Single-field index | Eliminates COLLSCAN; brings efficiency to ~1.0 |
| 2 | Compound index + projection | Supports multi-field filters; reduces data transfer |
| 3 | Projection + limit + ESR | Layer optimizations progressively; eliminate in-memory SORT |
| 4 | Aggregation pipeline | Move `$match` early; index the `$match` stage |
| 5 | Workload analysis | Profile queries before scaling; 4 indexes can serve 5 patterns |

---

## 🧹 Cleanup

Drop all indexes created in this lab:

```javascript
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

---

✅ **Lab Complete!** You've practiced the full optimization workflow: diagnose collection scans, build compound indexes, tune queries progressively, optimize aggregation pipelines, and make informed scaling decisions.

Continue to the [Knowledge Check Exercises](Exercises.md) to test your understanding.

---

[← Back to Module Overview](README.md) | [Next: Knowledge Check →](Exercises.md)
