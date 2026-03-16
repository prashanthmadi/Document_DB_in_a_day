# Module 5: Performance & Cost Optimization (L100–L300)

**Duration:** 90–120 minutes | **Level:** L100–L300

This hands-on, follow-along training covers **performance tuning and cost optimization** for **Azure DocumentDB**. You will learn how to analyze query execution plans, design efficient indexes, tune queries for maximum throughput, and apply cost-saving scaling strategies — all using the **VSCode DocumentDB extension**.

---

## 🎯 Learning Objectives

By the end of this module, you will be able to:

- ✅ Read and interpret `.explain()` output to diagnose slow queries
- ✅ Design index strategies that eliminate collection scans
- ✅ Optimize query patterns using projections, compound indexes, and aggregation pipelines
- ✅ Apply compute and storage scaling strategies to reduce cost
- ✅ Use the Index Advisor to automatically discover missing indexes
- ✅ Understand High Performance Storage (HPS) and when to use it
- ✅ Choose a shard key and decide between vertical and horizontal scaling
- ✅ Troubleshoot real-world performance bottlenecks

---

## 👥 Audience

- Cloud engineers and support engineers
- Architects evaluating or onboarding to Azure DocumentDB
- Developers building applications on DocumentDB

---

## 🛠️ Prerequisites

- Completed [Module 1: Introduction](../1-Introduction/README.md) (environment setup)
- VSCode with the **DocumentDB extension** installed and connected to a cluster
- Basic familiarity with MongoDB query syntax (covered in [Module 2](../2-NoSQL-Core-Concepts/README.md))

---

## 📚 Module Structure

### 📦 [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
**Duration:** 10 minutes | **Required — Do this first!**

One-time database, collection, and sample data setup used across all modules, labs, and exercises.
- Create the `ecommerce` database and collections
- Ingest 50 products, 30 customers, and 80 orders
- Verify the data is loaded correctly

---

### 📘 [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
**Duration:** 25–35 minutes | **Level:** L100

Core performance concepts for Azure DocumentDB.
- How DocumentDB processes queries (collection scans vs. index scans)
- Reading and interpreting `.explain("executionStats")` output
- Understanding key metrics: `docsExamined`, `nReturned`, `executionTimeMillis`
- 3 detailed `.explain()` output walkthroughs
- **Compound indexes for multi-field queries** (Part 3.5): two equality filters, equality + sort, projection patterns

---

### 📗 [L200: Advanced Optimization & Cost Strategies](L200_Performance_and_Cost_Optimization.md)
**Duration:** 20–30 minutes | **Level:** L200

Advanced query optimization and cost management.
- Compound indexes and the full ESR rule
- Aggregation pipeline optimization
- Compute tier selection and scaling strategies
- Monitoring and alerting best practices

---

### 📙 [L300: Index Advisor & High Performance Storage](L300_Index_Advisor_and_HPS.md)
**Duration:** 20–30 minutes | **Level:** L300

AI-powered index recommendations and premium storage tier.
- Index Advisor: automatic query analysis and one-click index apply
- Step-by-step walkthrough: slow query → recommendation → apply → compare
- High Performance Storage (HPS): up to 80,000 IOPS and 1,200 MB/s per shard
- Performance tier table (M30–M200) and when to use HPS vs standard storage

---

### 📙 [L300: Sharding & Scaling Strategies](L300_Sharding_and_Scaling.md)
**Duration:** 25–35 minutes | **Level:** L300

Distributed data and scaling decision framework.
- Sharding concepts: logical and physical shards, automatic balancing
- Choosing a shard key: high cardinality, even distribution, query alignment
- Vertical scaling (scale up): cluster tier changes, zero-downtime, when to use
- Horizontal scaling (scale out): add shards, near-unlimited capacity
- Decision framework: optimize → scale vertical → scale horizontal

---

### 🧪 Hands-On Lab

| Lab | Title | Duration | Focus |
|-----|-------|----------|-------|
| 🔬 [Hands-On Lab](Lab_Hands_On.md) | Performance Optimization | 30–40 min | Diagnose scans, compound indexes, query tuning, aggregation, workload analysis & scaling decision |

---

### 📝 [Knowledge Check Exercises](Exercises.md)
**Duration:** 10 minutes

3 questions to test your understanding of performance and cost optimization concepts.

---

## 🗺️ Recommended Learning Path

```
┌──────────────────────────────────┐
│  Step 0: Setup & Sample Data     │  ← Start here (one-time setup)
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  L100: Performance Fundamentals  │  ← Core concepts & .explain()
│  (incl. compound index patterns) │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  L200: Performance & Cost Optimization         │  ← Advanced strategies & ESR rule
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Hands-On Lab                    │  ← Practice all concepts in one lab
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  L300: Index Advisor & HPS       │  ← AI-powered recommendations
│  L300: Sharding & Scaling        │  ← Distributed scaling strategies
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Knowledge Check Exercises       │  ← Test your understanding
└──────────────────────────────────┘
```

---

## 📂 File Structure

```
5-Performance-and-Cost-Optimization/
├── README.md                          ← You are here
├── 00_Setup_and_Sample_Data.md        ← One-time data setup
├── L100_Performance_Fundamentals.md   ← L100 concepts module (incl. compound index patterns)
├── L200_Performance_and_Cost_Optimization.md          ← L200 concepts module
├── L300_Index_Advisor_and_HPS.md      ← L300: Index Advisor & High Performance Storage
├── L300_Sharding_and_Scaling.md       ← L300: Sharding & Scaling Strategies
├── Lab_Hands_On.md                    ← Consolidated hands-on lab (all exercises)
├── Exercises.md                       ← Knowledge check (3 questions)
└── sample-data/
    └── ecommerce_data.vscode-documentdb-scrapbook  ← Sample data script
```

---

## 🔗 Additional Resources

- [Azure DocumentDB Documentation](https://learn.microsoft.com/en-us/azure/documentdb)
- [DocumentDB Indexing Best Practices](https://learn.microsoft.com/en-us/azure/documentdb)
- [VSCode DocumentDB Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-documentdb)

---

[← Back to Workshop Home](../README.md)
