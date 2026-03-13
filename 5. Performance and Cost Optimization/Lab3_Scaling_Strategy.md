# 🔬 Lab 3: Scaling & Right-Sizing Strategy

**Duration:** 15–20 minutes | **Level:** L200 | **Hands-On Lab**

---

## 🎯 Lab Objective

In this lab, you will analyze workload patterns, evaluate index efficiency, identify unused indexes, and practice the decision-making process for scaling vs. optimizing — using real queries against the sample data.

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ Read [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ Read [L200: Advanced Optimization & Cost Strategies](L200_Cost_Optimization.md)
- ✅ VSCode with DocumentDB extension connected to your cluster

---

## Lab Setup

```javascript
use("ecommerce");

// Clean slate
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();

print("✅ Ready for Lab 3");
```

---

## Exercise 1: Workload Analysis — Before You Scale, Understand Your Queries

**Scenario:** Your team is considering scaling up the DocumentDB cluster because "the database is slow." Before approving the cost increase, you need to analyze the actual workload.

### Step 1: Identify the top query patterns

In a real application, you would check the slow query log. For this lab, we'll simulate the most common queries from a typical e-commerce application:

```javascript
use("ecommerce");

// Query Pattern 1: Order lookup by customer (customer support portal)
db.orders.find({ customerId: "CUST001" }).sort({ orderDate: -1 }).explain("executionStats");
```

```javascript
use("ecommerce");

// Query Pattern 2: Product search by category + sort by rating (storefront)
db.products.find({ category: "Electronics" }).sort({ rating: -1 }).explain("executionStats");
```

```javascript
use("ecommerce");

// Query Pattern 3: Order status filter (operations dashboard)
db.orders.find({ status: "pending" }).explain("executionStats");
```

```javascript
use("ecommerce");

// Query Pattern 4: Customer lookup by region + tier (marketing)
db.customers.find({ region: "eastus", tier: "premium" }).explain("executionStats");
```

```javascript
use("ecommerce");

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

## Exercise 2: Design an Efficient Index Set

**Scenario:** Based on the workload analysis, create indexes for each query pattern. But remember — every index has a cost (storage + write overhead). Design the **minimum set** of indexes needed.

### Step 1: Think before you create

Consider which queries can share indexes. A compound index on `{ A: 1, B: 1 }` supports queries that filter on:
- `A` alone ✅
- `A` and `B` together ✅
- `B` alone ❌ (leftmost prefix rule)

### Step 2: Create the indexes

```javascript
use("ecommerce");

// Index 1: Orders — supports customer lookup + sort (Pattern 1)
db.orders.createIndex({ customerId: 1, orderDate: -1 });

// Index 2: Orders — supports status filter (Pattern 3) AND aggregation $match (Pattern 5)
db.orders.createIndex({ status: 1 });

// Index 3: Products — supports category search + rating sort (Pattern 2)
db.products.createIndex({ category: 1, rating: -1 });

// Index 4: Customers — supports region + tier lookup (Pattern 4)
db.customers.createIndex({ region: 1, tier: 1 });

print("✅ Created 4 indexes to support 5 query patterns");
```

> 💡 **Notice:** We created only **4 indexes** to support **5 query patterns**. Index 2 (`status: 1`) supports both Pattern 3 (status filter) and Pattern 5 (aggregation `$match` on status). This is efficient index design.

### Step 3: Verify all queries now use indexes

Re-run all 5 queries with `.explain()` and confirm they all show `IXSCAN`:

```javascript
use("ecommerce");

// Verify Pattern 1
db.orders.find({ customerId: "CUST001" }).sort({ orderDate: -1 }).explain("executionStats");
```

```javascript
use("ecommerce");

// Verify Pattern 2
db.products.find({ category: "Electronics" }).sort({ rating: -1 }).explain("executionStats");
```

```javascript
use("ecommerce");

// Verify Pattern 3
db.orders.find({ status: "pending" }).explain("executionStats");
```

```javascript
use("ecommerce");

// Verify Pattern 4
db.customers.find({ region: "eastus", tier: "premium" }).explain("executionStats");
```

```javascript
use("ecommerce");

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

## Exercise 3: Identify and Remove Unused Indexes

**Scenario:** Over time, application queries evolve but old indexes remain. Unused indexes waste storage and slow down writes. Let's practice identifying them.

### Step 1: Add a "legacy" index that nobody uses

```javascript
use("ecommerce");

// Simulate a leftover index from an old feature
db.orders.createIndex({ paymentMethod: 1, deliveredAt: 1 });
db.products.createIndex({ vendor: 1, warehouse: 1 });

print("✅ Added 2 'legacy' indexes");
```

### Step 2: Check index usage statistics

```javascript
use("ecommerce");

// Check which indexes have been used
db.orders.aggregate([{ $indexStats: {} }]);
```

```javascript
use("ecommerce");

db.products.aggregate([{ $indexStats: {} }]);
```

### Step 3: Analyze the results

The `$indexStats` output shows an `accesses.ops` field — the number of times each index has been used since the server started.

📝 **Identify:** Which indexes have `accesses.ops: 0`? These are candidates for removal.

### Step 4: Remove unused indexes

```javascript
use("ecommerce");

// Remove indexes that have zero or very low usage
db.orders.dropIndex("paymentMethod_1_deliveredAt_1");
db.products.dropIndex("vendor_1_warehouse_1");

print("✅ Removed 2 unused indexes");
```

### Step 5: Review the final index set

```javascript
use("ecommerce");

print("📊 Orders indexes:");
printjson(db.orders.getIndexes());

print("\n📊 Products indexes:");
printjson(db.products.getIndexes());

print("\n📊 Customers indexes:");
printjson(db.customers.getIndexes());
```

<details>
<summary>✅ Expected Final Index Set</summary>

**Orders collection (3 indexes):**
1. `{ _id: 1 }` — default
2. `{ customerId: 1, orderDate: -1 }` — customer lookup
3. `{ status: 1 }` — status filter + aggregation

**Products collection (2 indexes):**
1. `{ _id: 1 }` — default
2. `{ category: 1, rating: -1 }` — product search

**Customers collection (2 indexes):**
1. `{ _id: 1 }` — default
2. `{ region: 1, tier: 1 }` — customer lookup

**Total: 7 indexes** (including 3 default `_id` indexes) supporting 5 query patterns.

</details>

---

## Exercise 4: The Scaling Decision Framework

**Scenario:** After optimizing indexes, one query is still slower than acceptable. Walk through the decision framework.

### Step 1: Run a complex analytics query

```javascript
use("ecommerce");

// Complex query: Top spending customers with their order details
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $group: {
    _id: "$customerId",
    totalSpent: { $sum: "$total" },
    orderCount: { $sum: 1 },
    avgOrderValue: { $avg: "$total" },
    lastOrder: { $max: "$orderDate" }
  }},
  { $sort: { totalSpent: -1 } },
  { $limit: 10 },
  { $lookup: {
    from: "customers",
    localField: "_id",
    foreignField: "_id",
    as: "customerInfo"
  }},
  { $unwind: "$customerInfo" },
  { $project: {
    _id: 0,
    customerId: "$_id",
    customerName: "$customerInfo.name",
    tier: "$customerInfo.tier",
    totalSpent: { $round: ["$totalSpent", 2] },
    orderCount: 1,
    avgOrderValue: { $round: ["$avgOrderValue", 2] },
    lastOrder: 1
  }}
]);
```

### Step 2: Apply the decision framework

Answer these questions:

📝 **Question 1:** Does the `$match` stage use an index?
- Run with `.explain()` to check: __________

📝 **Question 2:** Can the query be further optimized?
- Is `$match` first? __________
- Is `$limit` used to cap results? __________
- Does `$project` come at the end? __________

📝 **Question 3:** If the query is already optimized with indexes, what's the next step?
- Check CPU utilization. If CPU is consistently > 80%, then scaling compute is justified.
- If CPU is low but the query is still slow, look for network latency or client-side issues.

<details>
<summary>✅ Decision Framework Answer</summary>

**This query is already well-optimized:**
1. ✅ `$match` is first and uses the `status` index
2. ✅ `$limit: 10` caps the `$lookup` to only 10 documents
3. ✅ `$project` is at the end

**If this query is still slow after optimization:**
- At production scale with millions of documents, the `$group` stage processes more data
- The `$lookup` performs a join (requires reading from the customers collection)
- **This is a valid case for scaling compute** — but only after confirming indexes are optimal

**Decision:** Optimize first, scale second. Most "slow database" complaints are resolved at the index level without any cost increase.

</details>

---

## Lab Summary

| Exercise | Concept | Key Takeaway |
|----------|---------|-------------|
| 1 | Workload analysis | Profile queries before scaling decisions |
| 2 | Minimum index set | 4 indexes can support 5 query patterns |
| 3 | Unused index cleanup | Remove unused indexes to save storage and writes |
| 4 | Scaling decision | Optimize first, scale only when compute is the bottleneck |

### Cost Impact Summary

```
Before Optimization:
  - All queries: COLLSCAN
  - Potential "fix": Scale compute from 4 vCores → 8 vCores ($$$)
  - Actual impact of scaling: Marginal improvement

After Optimization:
  - All queries: IXSCAN
  - Indexes added: 4 (minimal storage cost)
  - Performance improvement: 5-20x faster queries
  - Compute scaling needed: NO
  - Cost savings: Avoided unnecessary compute upgrade
```

---

## 🧹 Cleanup

```javascript
use("ecommerce");

db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();

print("✅ Lab 3 cleanup complete");
```

---

✅ **Lab 3 Complete!** You've practiced the full optimization workflow: analyze workloads, design efficient indexes, remove waste, and make informed scaling decisions. Proceed to the [Knowledge Check Exercises](Exercises.md).

---

[← Back to Module Overview](README.md) | [Next: Knowledge Check →](Exercises.md)
