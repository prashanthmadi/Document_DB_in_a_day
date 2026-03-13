# Module 5: Performance & Cost Optimization (L100–L200)

**Duration:** 60–90 minutes | **Level:** L100–L200

This hands-on, follow-along training covers **performance tuning and cost optimization** for **Azure DocumentDB**. You will learn how to analyze query execution plans, design efficient indexes, tune queries for maximum throughput, and apply cost-saving scaling strategies — all using the **VSCode DocumentDB extension**.

---

## 🎯 Learning Objectives

By the end of this module, you will be able to:

- ✅ Read and interpret `.explain()` output to diagnose slow queries
- ✅ Design index strategies that eliminate collection scans
- ✅ Optimize query patterns using projections, covered queries, and aggregation pipelines
- ✅ Apply compute and storage scaling strategies to reduce cost
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
**Duration:** 20–30 minutes | **Level:** L100

Core performance concepts for Azure DocumentDB.
- How DocumentDB processes queries (collection scans vs. index scans)
- Reading and interpreting `.explain("executionStats")` output
- Understanding key metrics: `docsExamined`, `nReturned`, `executionTimeMillis`
- 3 detailed `.explain()` output walkthroughs

---

### 📗 [L200: Advanced Optimization & Cost Strategies](L200_Cost_Optimization.md)
**Duration:** 20–30 minutes | **Level:** L200

Advanced query optimization and cost management.
- Compound indexes and index intersection
- Covered queries for maximum efficiency
- Aggregation pipeline optimization
- Compute tier selection and scaling strategies
- Monitoring and alerting best practices

---

### 🧪 Hands-On Labs

| Lab | Title | Duration | Focus |
|-----|-------|----------|-------|
| 🔬 [Lab 1](Lab1_Index_Optimization.md) | Index Strategy Optimization | 15–20 min | Create and compare indexes using `.explain()` |
| 🔬 [Lab 2](Lab2_Query_Tuning.md) | Query Performance Tuning | 15–20 min | Optimize slow queries with projections and pipelines |
| 🔬 [Lab 3](Lab3_Scaling_Strategy.md) | Scaling & Right-Sizing | 15–20 min | Analyze workloads and apply cost-saving strategies |

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
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Lab 1: Index Optimization       │  ← Hands-on practice
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  L200: Cost Optimization         │  ← Advanced strategies
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Lab 2: Query Tuning             │  ← Hands-on practice
│  Lab 3: Scaling Strategy         │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│  Knowledge Check Exercises       │  ← Test your understanding
└──────────────────────────────────┘
```

---

## 📂 File Structure

```
5. Performance and Cost Optimization/
├── README.md                          ← You are here
├── 00_Setup_and_Sample_Data.md        ← One-time data setup
├── L100_Performance_Fundamentals.md   ← L100 concepts module
├── L200_Cost_Optimization.md          ← L200 concepts module
├── Lab1_Index_Optimization.md         ← Hands-on lab 1
├── Lab2_Query_Tuning.md               ← Hands-on lab 2
├── Lab3_Scaling_Strategy.md           ← Hands-on lab 3
├── Exercises.md                       ← Knowledge check (3 questions)
└── sample-data/
    └── ecommerce_data.js              ← Sample data script
```

---

## 🔗 Additional Resources

- [Azure DocumentDB Documentation](https://learn.microsoft.com/en-us/azure/documentdb)
- [DocumentDB Indexing Best Practices](https://learn.microsoft.com/en-us/azure/documentdb)
- [VSCode DocumentDB Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-documentdb)

---

[← Back to Workshop Home](../README.md)
