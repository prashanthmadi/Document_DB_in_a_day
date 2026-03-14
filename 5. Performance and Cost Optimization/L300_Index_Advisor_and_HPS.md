# L300: Index Advisor & High Performance Storage

**Duration:** 20–30 minutes | **Level:** L300 | **Goal:** Leverage AI-powered index recommendations and understand the High Performance Storage tier

---

## What You'll Learn

- 🤖 How the Index Advisor analyzes your queries and recommends optimal indexes
- 🖱️ How to apply index recommendations with one click from VSCode
- ⚡ What High Performance Storage (HPS) is and when to use it
- 📊 Performance tier comparison across cluster sizes

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ Read [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ Read [L200: Advanced Optimization & Cost Strategies](L200_Cost_Optimization.md)
- ✅ Azure subscription with an active DocumentDB cluster
- ✅ VSCode with the **DocumentDB extension** installed and connected
- ✅ *(Optional)* GitHub Copilot extension for enhanced AI explanations

---

## Part 1: Index Advisor (Preview)

### 1.1 What Is the Index Advisor?

The **Index Advisor** is an AI-powered feature built directly into the VSCode DocumentDB extension. It analyzes:

- Query execution plans from your workload history
- Collection statistics (document counts, field cardinality, data distribution)
- Index usage patterns (which indexes are used, which are redundant)

Based on this analysis, it recommends **missing indexes** or **more efficient index configurations** — and lets you apply them with a single click.

> 💡 **Why this matters:** Manually identifying missing indexes requires expertise in reading `.explain()` output and understanding the ESR rule. The Index Advisor automates this analysis and surfaces recommendations in plain English, even for teams new to DocumentDB performance tuning.

---

### 1.2 Step-by-Step Walkthrough

#### Step 1: Connect to Your Cluster in VSCode

1. Open VSCode and click the **DocumentDB** icon in the Activity Bar (left sidebar).
2. Expand your cluster connection and select the **`ecommerce`** database.

#### Step 2: Open a MongoDB Scrapbook and Run a Slow Query

Open a new Scrapbook and run a query that is not yet indexed:

```javascript
// Slow query: find orders for a specific customer, most recent first
db.orders.find({ customerId: "CUST005" }).sort({ orderDate: -1 })
```

The Index Advisor monitors queries executed through the extension. Running this query registers it as a workload pattern that the advisor will analyze.

You can also check the current execution plan:

```javascript
db.orders.find({ customerId: "CUST005" }).sort({ orderDate: -1 }).explain("executionStats")
```

Without an index, you will see:

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "SORT",
      "inputStage": {
        "stage": "COLLSCAN",
        "filter": { "customerId": { "$eq": "CUST005" } }
      }
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 4,
    "executionTimeMillis": 15,
    "totalKeysExamined": 0,
    "totalDocsExamined": 80
  }
}
```

> ❌ **Problem:** COLLSCAN + in-memory SORT. The query examines all 80 documents to return 4, and sorts them in memory.

#### Step 3: Open the Index Advisor Panel / Query Insights Tab

1. In the VSCode DocumentDB extension sidebar, right-click on your **`ecommerce`** database (or the **`orders`** collection).
2. Select **"Open Index Advisor"** or navigate to the **Query Insights** tab in the extension panel.
3. The advisor displays a list of analyzed queries, ranked by impact.

#### Step 4: Review the Recommendation

The Index Advisor will surface a recommendation similar to:

```
📋 Recommendation for: db.orders.find({ customerId: ... }).sort({ orderDate: -1 })

Suggested Index:  { customerId: 1, orderDate: -1 }

Expected Benefit: This compound index aligns with the ESR rule — equality on
                  customerId narrows the scan to only that customer's orders,
                  and the descending orderDate sort is served directly from the
                  index without an in-memory sort stage.

Estimated Impact: Reduce docsExamined from 80 → ~4 | Eliminate SORT stage
```

The recommendation follows the **ESR rule** automatically:
- **E**quality: `customerId` (exact match)
- **S**ort: `orderDate` (descending)
- No Range fields in this query

#### Step 5: Apply the Index Recommendation

Click **"Apply"** in the Index Advisor panel. The extension executes:

```javascript
db.orders.createIndex({ customerId: 1, orderDate: -1 })
```

You will see a confirmation that the index was created successfully.

#### Step 6: Re-Run the Query and Compare

```javascript
// Re-run the same query after applying the recommendation
db.orders.find({ customerId: "CUST005" }).sort({ orderDate: -1 }).explain("executionStats")
```

**After applying the recommended index:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",
      "inputStage": {
        "stage": "IXSCAN",
        "keyPattern": { "customerId": 1, "orderDate": -1 },
        "indexName": "customerId_1_orderDate_-1",
        "direction": "forward",
        "indexBounds": {
          "customerId": ["[\"CUST005\", \"CUST005\"]"],
          "orderDate": ["[MaxKey, MinKey]"]
        }
      }
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 4,
    "executionTimeMillis": 1,
    "totalKeysExamined": 4,
    "totalDocsExamined": 4
  }
}
```

| Metric | Before (COLLSCAN + SORT) | After (IXSCAN, index-backed sort) |
|--------|--------------------------|-----------------------------------|
| Stage | SORT → COLLSCAN | FETCH → IXSCAN |
| totalDocsExamined | 80 | 4 |
| executionTimeMillis | 15ms | 1ms |
| In-memory SORT | ❌ Yes | ✅ Eliminated |
| Efficiency ratio | 0.05 (5%) | 1.0 (100%) |

---

### 1.3 Index Advisor Benefits Summary

| Benefit | Description |
|---------|-------------|
| 🤖 **Automatic detection** | Continuously analyzes your query workload — no manual `.explain()` required |
| 🖱️ **One-click apply** | Apply recommended indexes directly from VSCode without writing DDL commands |
| 📊 **Before/after validation** | Instantly compare execution stats before and after applying an index |
| 🚫 **Avoids redundant indexes** | Considers your existing indexes and only recommends what is missing |
| 🎯 **Prioritised by impact** | Recommendations are ranked by the queries they will improve most |

---

### 1.4 Best Practices for Using the Index Advisor

- **Review before applying in production:** The advisor's recommendations are based on sampled query patterns. Review each suggestion and validate it matches your actual production workload before applying.
- **Consider write overhead:** Each new index adds write overhead (every insert, update, and delete must update all indexes). Evaluate the read/write ratio of your workload.
- **Consider storage cost:** Indexes consume storage. For large collections, a poorly designed compound index can add significant storage.
- **Pair with `$indexStats`:** After applying an index, use `$indexStats` to confirm it is being used in production.

  ```javascript
  // Check that the new index is being used
  db.orders.aggregate([{ $indexStats: {} }])
  ```

  > 💡 **Note:** `$indexStats` support in Azure DocumentDB may vary. If this command returns an error, check index usage through the Azure Portal metrics instead.

- **Re-run the Index Advisor periodically:** As your application evolves and new query patterns emerge, run the Index Advisor again to catch new opportunities.

🔗 **Official documentation:** [Azure DocumentDB Index Advisor](https://learn.microsoft.com/en-us/azure/documentdb/index-advisor)

---

## Part 2: High Performance Storage (Preview)

### 2.1 What Is High Performance Storage?

**High Performance Storage (HPS)** is a premium storage tier for Azure DocumentDB built on **Premium SSD v2**. It is designed for workloads that demand the highest levels of IOPS, throughput, and storage capacity.

| Specification | Value |
|---------------|-------|
| **Max IOPS** | Up to **80,000 IOPS** per physical shard |
| **Max Throughput** | Up to **1,200 MB/s** per physical shard |
| **Max Storage** | Up to **64 TiB** per physical shard |
| **Underlying technology** | Azure Premium SSD v2 |

> 💡 **What is a "shard"?** A shard is a physical node in your DocumentDB cluster. In a sharded cluster, each shard independently handles a subset of your data. HPS specs apply per shard, so adding shards multiplies your total capacity.

---

### 2.2 Key Benefits of HPS

| Benefit | Description |
|---------|-------------|
| ⚡ **Industry-leading IOPS** | 80,000 IOPS per shard — suited for the most demanding transactional workloads |
| 🚀 **High throughput** | 1,200 MB/s per shard supports large sequential reads (analytics, vector search) |
| 📉 **Consistent low latency** | Premium SSD v2 delivers predictable, low-latency I/O — no performance variance |
| 🔧 **Independent scaling** | Scale compute (vCores) and storage independently — pay only for what you need |
| 📈 **Scales with both axes** | Performance scales with both vCore count and storage size |
| 🤖 **Built for modern workloads** | AI/ML vector search, gaming leaderboards, IoT telemetry, real-time analytics |

---

### 2.3 Performance Tier Table (HPS)

The following table shows the maximum IOPS, throughput, and storage available per physical shard at each cluster tier with High Performance Storage enabled:

| Cluster Tier | Max IOPS per Shard | Max Throughput MB/s per Shard | Max Storage per Shard |
|-------------|-------------------|------------------------------|----------------------|
| **M30** | 3,200 | 125 MB/s | 4 TiB |
| **M40** | 6,400 | 250 MB/s | 8 TiB |
| **M50** | 12,800 | 500 MB/s | 16 TiB |
| **M60** | 25,600 | 600 MB/s | 32 TiB |
| **M80** | 51,200 | 900 MB/s | 48 TiB |
| **M200** | 80,000 | 1,200 MB/s | 64 TiB |

> 💡 **Scaling with shards:** In a multi-shard cluster, IOPS and throughput multiply per shard. A 3-shard M80 cluster with HPS provides up to 153,600 IOPS and 2,700 MB/s total throughput.

---

### 2.4 When to Use HPS vs Standard Storage

| Scenario | Recommended Storage |
|----------|-------------------|
| Development and testing environments | Standard Storage |
| Low-volume transactional workloads (< 5,000 IOPS) | Standard Storage |
| High-volume transactional workloads (> 10,000 IOPS) | **High Performance Storage** |
| AI/ML vector search at scale | **High Performance Storage** |
| Real-time gaming leaderboards and session state | **High Performance Storage** |
| IoT data ingestion (high write throughput) | **High Performance Storage** |
| Large-scale analytics over DocumentDB | **High Performance Storage** |
| Multi-tenant SaaS applications with unpredictable spikes | **High Performance Storage** |
| Workloads where query latency must be consistently < 5ms | **High Performance Storage** |

---

### 2.5 HPS and the Optimization-First Principle

> ⚠️ **Important:** High Performance Storage increases the ceiling for what your cluster can handle — but it does not fix inefficient queries. Before enabling HPS:
>
> 1. Use the **Index Advisor** to ensure all critical queries are indexed
> 2. Verify query efficiency with `.explain("executionStats")`
> 3. Confirm CPU is consistently > 70% (a sign that compute, not query design, is the bottleneck)
>
> Only then consider HPS or compute scaling. A COLLSCAN query will still be slow regardless of storage tier.

🔗 **Official documentation:** [Azure DocumentDB High Performance Storage](https://learn.microsoft.com/en-us/azure/documentdb/high-performance-storage)

---

## Part 3: Key Takeaways

1. **Index Advisor automates index discovery** — use it proactively before performance issues are reported by users.
2. **One-click apply removes friction** — no more manually writing `createIndex()` commands from `.explain()` analysis.
3. **Always validate recommendations** before applying in production — consider write overhead and storage cost.
4. **HPS delivers up to 80,000 IOPS and 1,200 MB/s per shard** — ideal for AI/ML, gaming, IoT, and analytics at scale.
5. **Scale compute and storage independently with HPS** — right-size each dimension without paying for more than you need.
6. **Optimize first, then consider HPS** — storage tier upgrades complement but do not replace good index design.

---

[← Back to Module Overview](README.md) | [Next: L300 Sharding & Scaling →](L300_Sharding_and_Scaling.md)
