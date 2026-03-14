# L300: Sharding & Scaling Strategies

**Duration:** 25–35 minutes | **Level:** L300 | **Goal:** Understand sharding concepts, choose the right shard key, and make informed vertical vs horizontal scaling decisions

---

## What You'll Learn

- 🔀 What sharding is and how DocumentDB implements it
- 🗝️ How to choose a shard key using the ecommerce data as examples
- ⬆️ When to use vertical scaling (scale up)
- ➕ When to use horizontal scaling (scale out)
- 🧭 A decision framework for scaling vs. optimizing

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ Read [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ Read [L200: Advanced Optimization & Cost Strategies](L200_Cost_Optimization.md)
- ✅ Azure subscription with an active DocumentDB cluster
- ✅ VSCode with the **DocumentDB extension** installed and connected

---

## Part 1: Sharding Concepts

### 1.1 What Is Sharding?

**Sharding** is the practice of distributing data across multiple physical nodes (called **shards**) based on a value derived from each document — the **shard key**.

Instead of storing all data on a single node, sharding splits the collection across multiple nodes:

```
Without sharding (single node):
┌─────────────────────────────────────────┐
│  Node 1: ALL 10,000,000 orders          │
│  - Customers A–Z                        │
│  - All regions                          │
│  - All time ranges                      │
└─────────────────────────────────────────┘

With sharding (3 shards by customerId hash):
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  Shard 1:         │  │  Shard 2:         │  │  Shard 3:         │
│  CUST001–CUST333  │  │  CUST334–CUST666  │  │  CUST667–CUST999  │
│  ~3.3M orders     │  │  ~3.3M orders     │  │  ~3.3M orders     │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

Sharding allows DocumentDB to:
- **Scale beyond a single node's limits** — storage, compute, and memory
- **Distribute read and write load** across multiple nodes
- **Increase total IOPS and throughput** (each shard adds its own capacity)

---

### 1.2 How DocumentDB Implements Sharding

DocumentDB uses a two-level sharding architecture:

```
Documents
    │
    ▼
Logical Shards (many — based on shard key hash ranges)
    │
    ▼
Physical Shards (fewer — each hosts multiple logical shards)
    │
    ▼
Automatic rebalancing when physical shards are added
```

| Concept | Description |
|---------|-------------|
| **Shard key** | A field (or combination of fields) in each document that determines which shard it belongs to |
| **Logical shard** | A hash range bucket — DocumentDB creates many of these internally |
| **Physical shard** | An actual compute node that hosts one or more logical shards |
| **Router** | DocumentDB automatically routes queries to the correct shard(s) |
| **Rebalancing** | When you add physical shards, DocumentDB automatically moves logical shards to balance data |

> 💡 **You don't manage routing manually.** DocumentDB's query router transparently sends queries to the correct shard. For queries that include the shard key in the filter, only the relevant shard is queried (a **targeted query**). For queries without the shard key, all shards are queried in parallel (a **scatter-gather query**).

---

### 1.3 Choosing a Shard Key

The shard key is one of the most important design decisions in a sharded DocumentDB cluster. A poor choice leads to **hot shards** (uneven load distribution), while a good choice delivers **even distribution** and **query efficiency**.

#### Key Criteria for a Good Shard Key

| Criterion | Why It Matters | Example |
|-----------|---------------|---------|
| **High cardinality** | More unique values = better distribution across logical shards | `customerId` (30 unique) vs `_id` (80 unique) |
| **Even distribution** | Prevents hot shards where one node gets all the load | Avoid fields like `status` (only 3 values) |
| **Query alignment** | Queries that include the shard key hit only one shard (targeted) | If most queries filter on `customerId`, shard by `customerId` |
| **Immutability** | DocumentDB does not allow shard key values to change after insertion | Avoid fields that get updated (e.g., `status`, `region`) |

---

### 1.4 Shard Key Examples Using the Ecommerce Data

Let's evaluate the candidate shard keys from the `orders` collection:

#### Option A: `customerId`

```javascript
// Distribution in our sample: 30 customers, ~2-4 orders each
// At production scale: millions of customers, orders spread evenly
db.orders.aggregate([
  { $group: { _id: "$customerId", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

| Criterion | Assessment |
|-----------|-----------|
| Cardinality | ✅ High at production scale (millions of customers) |
| Distribution | ✅ Even — each customer has roughly similar order counts |
| Query alignment | ✅ Most order queries filter by `customerId` |
| Immutability | ✅ Customer IDs don't change |
| **Verdict** | ✅ **Excellent shard key** |

#### Option B: `region`

```javascript
// Distribution in our sample: 3 regions
db.orders.aggregate([
  { $group: { _id: "$region", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

Sample output:
```json
[
  { "_id": "eastus", "count": 30 },
  { "_id": "centralus", "count": 21 },
  { "_id": "westus", "count": 29 }
]
```

| Criterion | Assessment |
|-----------|-----------|
| Cardinality | ❌ Low — only 3 values. At 100 shards, most shards would be empty |
| Distribution | ⚠️ Somewhat even here, but could be skewed in production |
| Query alignment | ⚠️ Only useful if most queries filter by region |
| Immutability | ✅ Regions don't change |
| **Verdict** | ❌ **Poor shard key** — low cardinality creates hot shards |

#### Option C: `_id` (ObjectId)

```javascript
// Distribution: every document has a unique _id
// At production scale: billions of unique values
```

| Criterion | Assessment |
|-----------|-----------|
| Cardinality | ✅ Perfect — every document has a unique value |
| Distribution | ✅ Hash of `_id` distributes perfectly evenly |
| Query alignment | ❌ Very few application queries filter by `_id` — leads to scatter-gather |
| Immutability | ✅ `_id` never changes |
| **Verdict** | ⚠️ **Acceptable for write-heavy workloads** but leads to scatter-gather reads |

#### Shard Key Selection Decision Table

| Scenario | Recommended Shard Key | Reason |
|----------|----------------------|--------|
| Multi-tenant SaaS | `tenantId` or `customerId` | Isolates tenant data; queries are tenant-scoped |
| IoT / telemetry | `deviceId` | High cardinality; queries filter by device |
| E-commerce orders | `customerId` | Most queries look up by customer; good cardinality |
| Time-series data | `{ deviceId: 1, timestamp: 1 }` | Compound key prevents time-based hot shards |
| Global app with regional data | `{ region: 1, userId: 1 }` | Compound key avoids low-cardinality problem |
| General purpose (when unsure) | `_id` | Even distribution, though queries are scatter-gather |

---

## Part 2: Vertical Scaling (Scale Up)

### 2.1 What Is Vertical Scaling?

**Vertical scaling** means increasing the resources of your existing nodes by moving to a higher cluster tier:

```
M30 (2 vCores, 8 GB RAM)
    ↓
M40 (4 vCores, 16 GB RAM)
    ↓
M50 (8 vCores, 32 GB RAM)
    ↓
M60 (16 vCores, 64 GB RAM)
    ↓
M80 (32 vCores, 128 GB RAM)
    ↓
M200 (64 vCores, 256 GB RAM)
```

The same nodes get more powerful — you don't add more nodes.

---

### 2.2 How to Scale Vertically in Azure DocumentDB

Vertical scaling in Azure DocumentDB is a **configuration change** performed through the Azure Portal or Azure CLI. The operation is designed to minimize disruption:

1. Navigate to your DocumentDB cluster in the Azure Portal.
2. Select **"Compute + Storage"** settings.
3. Choose a higher tier from the dropdown.
4. Review the cost impact and click **"Save"**.

> ✅ **Zero-downtime scaling:** Azure DocumentDB performs tier changes as a rolling update — replicas are upgraded one at a time so the cluster remains available throughout.

---

### 2.3 When to Use Vertical Scaling

| Use Case | Description |
|----------|-------------|
| **Steady, predictable growth** | Your data and query volume grows gradually and linearly |
| **Single-tenant applications** | One database serving one tenant — horizontal sharding adds complexity without benefit |
| **Operational simplicity** | No shard key design, no rebalancing, no scatter-gather queries to worry about |
| **CPU is the bottleneck** | Consistently > 70–80% CPU with optimized queries |
| **Memory pressure** | Working set exceeds available RAM causing excessive disk I/O |

---

### 2.4 Limitations of Vertical Scaling

| Limitation | Description |
|------------|-------------|
| **Physical ceiling** | M200 is the top tier. You cannot scale beyond it on a single node |
| **Cost non-linearity** | Higher tiers are disproportionately more expensive per vCore |
| **Not unlimited** | At some scale, even the largest tier becomes a bottleneck |
| **Single point of contention** | All writes go to the same nodes — no write distribution |

> 💡 **Rule of thumb:** Vertical scaling is the right first step. When you approach the top tier **or** when your workload is internet-scale (millions of users, billions of documents), it's time to consider horizontal scaling.

---

## Part 3: Horizontal Scaling (Scale Out)

### 3.1 What Is Horizontal Scaling?

**Horizontal scaling** means adding more physical shards (nodes), each with their own independent compute and storage:

```
Before (1 shard):                After (3 shards):
┌─────────────────────┐          ┌──────────────┐
│  Shard 1            │          │  Shard 1     │
│  M80: 32 vCores     │    →     │  M80: 32 vC  │
│  128 GB RAM         │          └──────────────┘
│  10 TB storage      │          ┌──────────────┐
│  51,200 IOPS        │          │  Shard 2     │
│  All data           │          │  M80: 32 vC  │
└─────────────────────┘          └──────────────┘
                                 ┌──────────────┐
                                 │  Shard 3     │
                                 │  M80: 32 vC  │
                                 └──────────────┘
                                 Total: 96 vCores
                                 Total: 30 TB storage
                                 Total: 153,600 IOPS
```

---

### 3.2 When to Use Horizontal Scaling

| Use Case | Description |
|----------|-------------|
| **Internet-scale workloads** | Hundreds of millions of users or billions of documents |
| **Multi-tenant SaaS applications** | Each new customer adds unpredictable load — you need elastic capacity |
| **Globally distributed systems** | Data must be distributed across regions or zones for low latency |
| **Single-node limit reached** | You have already scaled to M200 and still need more capacity |
| **Extremely high write throughput** | Millions of writes/second exceeds what a single node can handle |
| **Workloads with bursty traffic** | Adding shards allows linear capacity expansion during peak events |

---

### 3.3 Benefits of Horizontal Scaling

| Benefit | Description |
|---------|-------------|
| 🔓 **Near-unlimited scaling** | Add shards to approach theoretically infinite capacity |
| ⚖️ **Automatic rebalancing** | DocumentDB redistributes data when shards are added — no manual migration |
| ⚡ **Additive performance** | Each shard adds its own IOPS, throughput, and memory |
| 💰 **Granular cost control** | Add exactly as many shards as needed — scale incrementally |
| 🛡️ **Fault isolation** | A problem on one shard does not affect others |

---

## Part 4: Decision Framework — Vertical vs Horizontal

### 4.1 Comparison Table

| Dimension | Vertical Scaling (Scale Up) | Horizontal Scaling (Scale Out) |
|-----------|----------------------------|-------------------------------|
| **How** | Increase tier (M30 → M40 → ... → M200) | Add more physical shards |
| **Limits** | Physical ceiling at M200 | Near-unlimited (add more shards) |
| **Disruption** | Zero-downtime rolling update | Requires shard key design upfront |
| **Best for** | Steady growth, single-tenant, simpler apps | Internet scale, multi-tenant SaaS, global apps |
| **Complexity** | Low — no schema design changes needed | High — shard key must be chosen carefully |
| **App changes needed** | None | May need to include shard key in queries for targeted routing |
| **Cost model** | Pay more per node | Pay for more nodes at any tier |
| **Query behavior** | All queries hit the same nodes | Queries with shard key are targeted; without are scatter-gather |

---

### 4.2 Decision Flow

```
START: "My database is slow or capacity is running low"
          │
          ▼
┌─────────────────────────────────────────┐
│  Step 1: Are all critical queries       │
│  using IXSCAN (not COLLSCAN)?           │
└─────────────┬──────────────────────────┘
              │
         No ──┴──► Fix your indexes first (L100/L200)
              │    Use Index Advisor (L300)
              │ Yes
              ▼
┌─────────────────────────────────────────┐
│  Step 2: Is CPU utilization             │
│  consistently > 70–80%?                 │
└─────────────┬──────────────────────────┘
              │
         No ──┴──► Investigate network, connection count,
              │    query patterns. May not need scaling yet.
              │ Yes
              ▼
┌─────────────────────────────────────────┐
│  Step 3: Are you at or near the M200    │
│  tier? OR is your workload internet-    │
│  scale (multi-tenant, global, 100M+     │
│  documents)?                            │
└─────────────┬──────────────────────────┘
              │
         No ──┴──► Scale Vertically (increase tier)
              │
              │ Yes
              ▼
┌─────────────────────────────────────────┐
│  Scale Horizontally (add shards)        │
│  - Design your shard key carefully      │
│  - Choose high-cardinality, even-dist.  │
│  - Align with your most common queries  │
└─────────────────────────────────────────┘
```

---

### 4.3 The "Optimize First, Scale Second" Principle

> 📌 **The single most important performance lesson:** In the majority of real-world DocumentDB performance problems, the root cause is a missing or inefficient index — not insufficient compute or storage.
>
> Before approving any scaling operation:
>
> 1. Run `.explain("executionStats")` on your slowest queries
> 2. Check for COLLSCAN stages (`totalDocsExamined` >> `nReturned`)
> 3. Use the **Index Advisor** to identify missing indexes automatically
> 4. Create the recommended indexes
> 5. **Re-measure latency and CPU** after optimization
>
> In most cases, adding the right indexes resolves the performance issue without any scaling costs. This is the philosophy behind the [L200: Advanced Optimization](L200_Cost_Optimization.md) module — and it applies even more critically before committing to horizontal scaling, which requires upfront shard key design and cannot be easily undone.

---

## Part 5: Key Takeaways

1. **Sharding distributes data across physical nodes** based on a shard key — choose a key with high cardinality, even distribution, and alignment with your query patterns.
2. **Avoid low-cardinality shard keys** (like `region` with 3 values) — they create hot shards that negate the benefit of sharding.
3. **Vertical scaling is simpler** — increase the cluster tier with zero downtime and no application changes.
4. **Horizontal scaling is near-unlimited** — add shards to linearly scale IOPS, throughput, memory, and storage.
5. **Optimize first** — always verify query plans and apply missing indexes before scaling.
6. **Decision flow:** Check indexes → Verify CPU → Evaluate tier ceiling → Choose vertical or horizontal.

---

## 🔗 Additional Resources

- [Azure DocumentDB Scalability Overview](https://learn.microsoft.com/en-us/azure/documentdb/scalability-overview)
- [Azure DocumentDB Partitioning Guide](https://learn.microsoft.com/en-us/azure/documentdb/partitioning)
- [Azure DocumentDB Compute and Storage](https://learn.microsoft.com/en-us/azure/documentdb/compute-storage)

---

[← Back to Module Overview](README.md) | [Next: Knowledge Check Exercises →](Exercises.md)
