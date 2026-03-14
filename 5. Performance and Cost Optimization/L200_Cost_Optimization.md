# L200: Advanced Optimization & Cost Strategies

**Duration:** 20–30 minutes | **Level:** L200 | **Goal:** Master advanced query optimization techniques and cost management strategies

---

## What You'll Learn

- 🔧 Compound index design using the ESR rule
- 🎯 Projections and their impact on performance
- 📊 Aggregation pipeline optimization techniques
- 💰 Compute tier selection and right-sizing strategies
- 📈 Monitoring and alerting for production workloads

---

## Prerequisites

- ✅ Completed [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ Understand `.explain()` output and COLLSCAN vs IXSCAN
- ✅ VSCode with DocumentDB extension connected to your cluster

---

## Part 1: Compound Index Design

### 1.1 Why Compound Indexes?

Single-field indexes work well for simple queries, but real applications often filter, sort, and range-query on multiple fields. Compound indexes support these complex patterns efficiently.

```javascript
// This query filters on TWO fields — a single-field index on "category"
// won't fully optimize it:
db.products.find({
  category: "Electronics",
  price: { $lt: 50 }
}).sort({ rating: -1 });
```

### 1.2 The ESR Rule

The **ESR rule** is the guiding principle for ordering fields in a compound index:

| Position | Type | Description | Example |
|----------|------|-------------|---------|
| 1st | **E**quality | Fields matched with `$eq` | `category: "Electronics"` |
| 2nd | **S**ort | Fields used in `.sort()` | `rating: -1` |
| 3rd | **R**ange | Fields matched with `$gt`, `$lt`, `$in` | `price: { $lt: 50 }` |

For the query above, the optimal compound index is:

```javascript
// ESR: Equality (category) → Sort (rating) → Range (price)
db.products.createIndex({ category: 1, rating: -1, price: 1 });
```

**Why this order?**
- **Equality first** narrows the search to a specific subset (e.g., only "Electronics")
- **Sort next** means the results come back already sorted — no in-memory sort needed
- **Range last** further filters within the sorted subset

### 1.3 Compound Index Example

```javascript
// Query: Find Electronics under $50, sorted by rating (highest first)
db.products.find(
  { category: "Electronics", price: { $lt: 50 } }
).sort({ rating: -1 }).explain("executionStats");
```

With the compound index `{ category: 1, rating: -1, price: 1 }`, the explain output will show:
- Stage: `IXSCAN` (no COLLSCAN)
- No in-memory `SORT` stage (the index provides the sort order)
- `totalDocsExamined` close to `nReturned`

> 💡 **Tip:** If you see a `SORT` stage in your explain output that is NOT backed by an index, it means DocumentDB is sorting in memory. For large result sets, this is expensive.

---

## Part 2: Projection Optimization

### 2.1 Why Projections Matter

By default, `find()` returns all fields in matching documents. Projections let you return only the fields you need, which:

- **Reduces network transfer** — less data sent to the client
- **Reduces memory usage** — smaller documents in the query pipeline
- **Enables covered queries** — if all projected fields are in the index

### 2.2 Projection Best Practices

```javascript
// ❌ BAD: Returns all fields (including the full items array)
db.orders.find({ status: "delivered" });

// ✅ GOOD: Returns only the fields needed
db.orders.find(
  { status: "delivered" },
  { _id: 1, customerId: 1, total: 1, orderDate: 1 }
);
```

### 2.3 Measuring the Impact

```javascript
// Compare: Full document vs projected fields
// Full document query
db.orders.find({ region: "eastus" }).explain("executionStats");

// Projected query — same filter, fewer fields returned
db.orders.find(
  { region: "eastus" },
  { _id: 1, total: 1, status: 1 }
).explain("executionStats");
```

While `totalDocsExamined` remains the same, the network and memory overhead is significantly reduced with projections.

---

## Part 3: Aggregation Pipeline Optimization

### 3.1 Pipeline Stage Ordering

The order of stages in an aggregation pipeline has a major impact on performance. The golden rule:

> **Filter early, transform late.** Place `$match` and `$limit` as early as possible to reduce the number of documents flowing through the pipeline.

```javascript
// ❌ BAD: Processes all 80 orders through $lookup before filtering
db.orders.aggregate([
  { $unwind: "$items" },
  { $group: { _id: "$customerId", totalSpent: { $sum: "$total" } } },
  { $match: { totalSpent: { $gt: 500 } } }
]);

// ✅ GOOD: Filters first, reducing documents before grouping
db.orders.aggregate([
  { $match: { status: "delivered" } },
  { $group: { _id: "$customerId", totalSpent: { $sum: "$total" } } },
  { $match: { totalSpent: { $gt: 500 } } }
]);
```

### 3.2 Optimizable Pipeline Patterns

| Pattern | Optimization | Benefit |
|---------|-------------|---------|
| `$match` at the start | Can use indexes | Reduces initial document count |
| `$match` + `$sort` at start | Can use compound index | Index-backed filter + sort |
| `$project` early | Drops unneeded fields | Less memory per document |
| `$limit` after `$sort` | Limits results | Avoids sorting the entire collection |

### 3.3 Example: Optimized Aggregation Pipeline

```javascript
// Find top 5 customers by total order value (delivered orders only)
db.orders.aggregate([
  // Stage 1: Filter early — uses index on status if available
  { $match: { status: "delivered" } },

  // Stage 2: Group by customer
  { $group: {
    _id: "$customerId",
    orderCount: { $sum: 1 },
    totalSpent: { $sum: "$total" }
  }},

  // Stage 3: Sort by total spent (descending)
  { $sort: { totalSpent: -1 } },

  // Stage 4: Limit to top 5
  { $limit: 5 },

  // Stage 5: Project final shape
  { $project: {
    customerId: "$_id",
    _id: 0,
    orderCount: 1,
    totalSpent: { $round: ["$totalSpent", 2] }
  }}
]);
```

Expected output:
```json
[
  { "customerId": "CUST018", "orderCount": 4, "totalSpent": 9399.54 },
  { "customerId": "CUST025", "orderCount": 3, "totalSpent": 5519.82 },
  { "customerId": "CUST011", "orderCount": 3, "totalSpent": 3389.66 },
  { "customerId": "CUST005", "orderCount": 4, "totalSpent": 2599.88 },
  { "customerId": "CUST009", "orderCount": 3, "totalSpent": 1639.91 }
]
```

---

## Part 4: Cost Optimization Strategies

### 4.1 Understanding DocumentDB Pricing

Azure DocumentDB pricing has two primary components:

| Component | What It Is | How It Scales |
|-----------|-----------|---------------|
| **Compute (vCores)** | CPU and memory for query processing | Vertical scaling (tier changes) |
| **Storage** | Disk space for data and indexes | Pay per GB used |

> 💡 **Key Insight:** Compute and storage are **decoupled** in DocumentDB. You can scale one without affecting the other, and scaling operations are **zero downtime**.

### 4.2 Right-Sizing Compute

Common over-provisioning mistake: scaling up compute to fix slow queries when the real issue is missing indexes.

**Before scaling up, check:**

1. **Are queries using indexes?** Run `.explain()` on your top queries
2. **Is CPU consistently > 80%?** If not, compute is not the bottleneck
3. **Are there slow queries in the logs?** Identify and optimize them first

```
Decision Flow:
                    ┌──────────────────────┐
                    │ Queries are slow?     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Run .explain()        │
                    │ on slow queries       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
    │ COLLSCAN?      │ │ High docs   │ │ IXSCAN with  │
    │ → Add index    │ │ examined?   │ │ low time?    │
    │                │ │ → Better    │ │ → Check CPU  │
    │                │ │   index     │ │ → Maybe scale│
    └────────────────┘ └─────────────┘ └──────────────┘
```

### 4.3 Index Cost Considerations

Indexes improve read performance but have costs:

| Cost | Impact |
|------|--------|
| **Storage** | Each index consumes additional disk space |
| **Write overhead** | Every insert/update/delete must update all affected indexes |
| **Memory** | Active indexes are loaded into working memory |

**Best practices:**
- Create indexes for queries that are **frequently run** or **latency-sensitive**
- Remove unused indexes (use the `$indexStats` aggregation stage)
- Prefer compound indexes over multiple single-field indexes

```javascript
// Check index usage statistics
// 💡 Note: $indexStats support in Azure DocumentDB may vary. If this command returns an error, you can check index usage through the Azure Portal metrics instead.
db.orders.aggregate([{ $indexStats: {} }]);
```

### 4.4 Storage Optimization

Reduce storage costs by:

1. **Right-size your documents** — avoid storing unused or redundant data
2. **Use short field names** for high-volume collections (e.g., `qty` vs `quantity`)
3. **Archive old data** — move historical data to cheaper storage
4. **Use TTL indexes** for data that expires

```javascript
// Example: TTL index to auto-delete pending orders after 30 days
// (Demonstration only — do NOT run this on the training data)
// db.orders.createIndex(
//   { orderDate: 1 },
//   { expireAfterSeconds: 2592000 }  // 30 days
// );
```

---

## Part 5: Monitoring and Alerting

### 5.1 Key Metrics to Monitor

| Metric | What to Watch | Action |
|--------|---------------|--------|
| **CPU utilization** | Sustained > 80% | Consider scaling compute |
| **Storage usage** | Approaching tier limit | Scale storage or archive data |
| **Slow query log** | Queries > 100ms | Analyze with `.explain()` and optimize |
| **Index hit ratio** | Low ratio | Review and optimize indexes |
| **Connection count** | Near pool limit | Optimize connection pooling |

### 5.2 Proactive Optimization Checklist

Use this checklist for production workloads:

- [ ] Run `.explain()` on the top 10 most frequent queries
- [ ] Verify all frequent queries use `IXSCAN` (not `COLLSCAN`)
- [ ] Check for unused indexes with `$indexStats`
- [ ] Review compute tier vs actual CPU utilization
- [ ] Set up alerts for CPU > 80% sustained
- [ ] Set up alerts for slow queries > 100ms
- [ ] Review and optimize aggregation pipeline ordering
- [ ] Use projections to limit data transfer on high-throughput queries

---

## Part 6: Key Takeaways

1. **Use the ESR rule** for compound index design: Equality → Sort → Range
2. **Project only needed fields** to reduce network and memory overhead
3. **Filter early in aggregation pipelines** — `$match` should be the first stage
4. **Right-size before scaling up** — most slow queries are index or query problems, not compute problems
5. **Monitor proactively** — set up alerts for CPU, storage, and slow queries
6. **Remove unused indexes** — they cost storage and write throughput with zero benefit

---

## 📋 Quick Reference: Optimization Cheat Sheet

```
Slow query?
├── Run .explain("executionStats")
├── COLLSCAN? → Create an index
├── IXSCAN but high docsExamined? → Better compound index (ESR rule)
├── SORT stage without index? → Add sort field to index
├── Large documents returned? → Add projection
└── Still slow with good indexes? → Check CPU utilization → Consider scaling
```

---

## 🧹 Cleanup (Optional)

Drop indexes created during this module:

```javascript
db.products.dropIndex("category_1_rating_-1_price_1");
```

---

✅ **Checkpoint:** You now understand advanced indexing strategies, aggregation optimization, and cost management. You're ready for the [Hands-On Lab: Performance Optimization](Lab_Hands_On.md)!

---

[← Back to Module Overview](README.md) | [Next: Hands-On Lab →](Lab_Hands_On.md)
