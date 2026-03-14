# 🔬 Lab 1: Index Strategy Optimization

**Duration:** 15–20 minutes | **Level:** L100–L200 | **Hands-On Lab**

---

## 🎯 Lab Objective

In this lab, you will create indexes, compare query plans before and after indexing, and learn to select the right index strategy for different query patterns — all using the VSCode DocumentDB extension.

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ Read [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ VSCode with DocumentDB extension connected to your cluster

---

## Lab Setup

Open a new MongoDB Scrapbook in VSCode (or use an existing one). Make sure you are connected to your DocumentDB cluster.

> 💡 **Note:** Select the `ecommerce` database from the VSCode DocumentDB extension's connection panel before running any commands. The `use()` command is not supported in the DocumentDB extension scrapbook.

First, let's drop any indexes from previous exercises to start clean (this keeps the default `_id` index):

```javascript
// Reset indexes on all collections
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

---

## Exercise 1: Diagnose a Collection Scan

**Scenario:** Your application frequently queries orders by status. Let's see how this performs without an index.

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

## Exercise 2: Compound Index for Multi-Field Queries

**Scenario:** Your dashboard queries orders by region AND status simultaneously.

### Step 1: Test without a compound index

```javascript
db.orders.find({
  region: "eastus",
  status: "delivered"
}).explain("executionStats");
```

The `status` index from Exercise 1 may be used, but it's not optimal for this two-field query.

📝 **Note the `totalDocsExamined` value:** __________

### Step 2: Create a compound index

Following the **ESR rule** (Equality first):

```javascript
// Both fields are equality matches, so order by selectivity
// "status" has fewer unique values, "region" has more — put the more selective field first
db.orders.createIndex({ region: 1, status: 1 });
```

### Step 3: Re-run the query

```javascript
db.orders.find({
  region: "eastus",
  status: "delivered"
}).explain("executionStats");
```

### Step 4: Compare

📝 **Write down:**
- Is the compound index being used? __________
- How did `totalDocsExamined` change? __________

<details>
<summary>✅ Expected Results</summary>

The compound index `{ region: 1, status: 1 }` should now be used. `totalDocsExamined` should drop to approximately match `nReturned` (around 18–20 documents), since the index efficiently narrows to the intersection of both filters.

</details>

---

## Exercise 3: Compound Index with Projection

**Scenario:** Your reporting service only needs the order `total` and `status` — no other fields. Let's use a compound index and projection to optimize this.

> ⚠️ **Azure DocumentDB Note:** In Azure DocumentDB, `totalDocsExamined` will equal `nReturned` (not 0) even when all projected fields are in the index. The benefit is that the IXSCAN narrows the fetch to only matching documents (perfect 1.0 efficiency ratio), and the projection reduces data transferred to the client.

### Step 1: Create an index that covers the query

```javascript
// Index covers: filter field (region) + returned fields (status, total)
db.orders.createIndex({ region: 1, status: 1, total: 1 });
```

### Step 2: Run a query with projection

```javascript
// Projection must only include fields in the index + exclude _id
db.orders.find(
  { region: "eastus" },
  { _id: 0, status: 1, total: 1 }
).explain("executionStats");
```

### Step 3: Verify the results

📝 **Check these values:**
- `totalDocsExamined` → Should match `nReturned` (~30) — IXSCAN fetches only matching docs
- `totalKeysExamined` → Should match `nReturned`
- `winningPlan.stage` → Should include `IXSCAN` → `FETCH`

<details>
<summary>✅ Expected Results</summary>

```
totalDocsExamined: ~30  ← Only matching documents fetched (equals nReturned)
totalKeysExamined: ~30  ← Only index keys for matching docs were read
nReturned: ~30
stage: IXSCAN → FETCH
```

In Azure DocumentDB, the compound index + projection combination achieves a **perfect 1.0 efficiency ratio** — only matching documents are fetched. The projection also reduces data transferred to the client. While `totalDocsExamined` is not 0 (as would be in native MongoDB covered queries), this is still a highly efficient pattern.

</details>

---

## Exercise 4: Sort Optimization

**Scenario:** Your product listing page sorts Electronics by price (lowest first). Let's optimize the sort.

### Step 1: Test sort without index support

```javascript
db.products.find({ category: "Electronics" }).sort({ price: 1 }).explain("executionStats");
```

📝 **Look for:** Is there a `SORT` stage in the winning plan? This means in-memory sorting.

### Step 2: Create an index that supports the sort

```javascript
// ESR: Equality (category) → Sort (price)
db.products.createIndex({ category: 1, price: 1 });
```

### Step 3: Re-run the query

```javascript
db.products.find({ category: "Electronics" }).sort({ price: 1 }).explain("executionStats");
```

### Step 4: Verify the sort is index-backed

📝 **Check:** Is the `SORT` stage gone from the winning plan? The results should come back already sorted from the index scan.

<details>
<summary>✅ Expected Results</summary>

With the `{ category: 1, price: 1 }` compound index:
- The `SORT` stage should be eliminated from the winning plan
- The `IXSCAN` stage provides documents in the correct sort order
- This is especially important at scale — in-memory sorts have a memory limit that can impact performance on large result sets

</details>

---

## Lab Summary

| Exercise | Concept | Key Takeaway |
|----------|---------|-------------|
| 1 | Single-field index | Eliminates COLLSCAN, brings efficiency to ~1.0 |
| 2 | Compound index | Supports multi-field filters efficiently |
| 3 | Compound index + projection | Efficient IXSCAN + reduced data transfer |
| 4 | Sort optimization | Index-backed sort eliminates in-memory SORT stage |

---

## 🧹 Cleanup

Drop all indexes created in this lab:

```javascript
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

---

✅ **Lab 1 Complete!** You've learned how to diagnose query performance, create effective indexes, build covered queries, and optimize sort operations. Proceed to [L200: Advanced Optimization](L200_Cost_Optimization.md) or [Lab 2: Query Tuning](Lab2_Query_Tuning.md).

---

[← Back to Module Overview](README.md) | [Next: L200 Cost Optimization →](L200_Cost_Optimization.md)
