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

```javascript
use("ecommerce");
```

First, let's drop any indexes from previous exercises to start clean (this keeps the default `_id` index):

```javascript
use("ecommerce");

// Reset indexes on all collections
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();

print("✅ All non-default indexes dropped");
```

---

## Exercise 1: Diagnose a Collection Scan

**Scenario:** Your application frequently queries orders by status. Let's see how this performs without an index.

### Step 1: Run the query with `.explain()`

```javascript
use("ecommerce");

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
use("ecommerce");

db.orders.createIndex({ status: 1 });
print("✅ Created index on 'status'");
```

### Step 4: Re-run the query

```javascript
use("ecommerce");

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
use("ecommerce");

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
use("ecommerce");

// Both fields are equality matches, so order by selectivity
// "status" has fewer unique values, "region" has more — put the more selective field first
db.orders.createIndex({ region: 1, status: 1 });
print("✅ Created compound index on { region: 1, status: 1 }");
```

### Step 3: Re-run the query

```javascript
use("ecommerce");

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

## Exercise 3: Covered Query

**Scenario:** Your reporting service only needs the order `total` and `status` — no other fields. Can we make this a covered query?

### Step 1: Create an index that covers the query

```javascript
use("ecommerce");

// Index covers: filter field (region) + returned fields (status, total)
db.orders.createIndex({ region: 1, status: 1, total: 1 });
print("✅ Created covering index on { region: 1, status: 1, total: 1 }");
```

### Step 2: Run a covered query

```javascript
use("ecommerce");

// Projection must only include fields in the index + exclude _id
db.orders.find(
  { region: "eastus" },
  { _id: 0, status: 1, total: 1 }
).explain("executionStats");
```

### Step 3: Verify it's covered

📝 **Check these values:**
- `totalDocsExamined` → Should be **0** (covered query!)
- `totalKeysExamined` → Should match `nReturned`
- `winningPlan.stage` → Should include `PROJECTION_COVERED`

<details>
<summary>✅ Expected Results</summary>

```
totalDocsExamined: 0    ← No documents fetched from storage!
totalKeysExamined: ~30  ← Only index keys were read
nReturned: ~30
stage: PROJECTION_COVERED
```

This is the most efficient query pattern possible. All data came from the index.

</details>

---

## Exercise 4: Sort Optimization

**Scenario:** Your product listing page sorts Electronics by price (lowest first). Let's optimize the sort.

### Step 1: Test sort without index support

```javascript
use("ecommerce");

db.products.find({ category: "Electronics" }).sort({ price: 1 }).explain("executionStats");
```

📝 **Look for:** Is there a `SORT` stage in the winning plan? This means in-memory sorting.

### Step 2: Create an index that supports the sort

```javascript
use("ecommerce");

// ESR: Equality (category) → Sort (price)
db.products.createIndex({ category: 1, price: 1 });
print("✅ Created index on { category: 1, price: 1 }");
```

### Step 3: Re-run the query

```javascript
use("ecommerce");

db.products.find({ category: "Electronics" }).sort({ price: 1 }).explain("executionStats");
```

### Step 4: Verify the sort is index-backed

📝 **Check:** Is the `SORT` stage gone from the winning plan? The results should come back already sorted from the index scan.

<details>
<summary>✅ Expected Results</summary>

With the `{ category: 1, price: 1 }` compound index:
- The `SORT` stage should be eliminated from the winning plan
- The `IXSCAN` stage provides documents in the correct sort order
- This is especially important at scale — in-memory sorts have a 100MB memory limit

</details>

---

## Lab Summary

| Exercise | Concept | Key Takeaway |
|----------|---------|-------------|
| 1 | Single-field index | Eliminates COLLSCAN, brings efficiency to ~1.0 |
| 2 | Compound index | Supports multi-field filters efficiently |
| 3 | Covered query | `totalDocsExamined: 0` — fastest possible query |
| 4 | Sort optimization | Index-backed sort eliminates in-memory SORT stage |

---

## 🧹 Cleanup

Drop all indexes created in this lab:

```javascript
use("ecommerce");

db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();

print("✅ Lab 1 cleanup complete");
```

---

✅ **Lab 1 Complete!** You've learned how to diagnose query performance, create effective indexes, build covered queries, and optimize sort operations. Proceed to [L200: Advanced Optimization](L200_Cost_Optimization.md) or [Lab 2: Query Tuning](Lab2_Query_Tuning.md).

---

[← Back to Module Overview](README.md) | [Next: L200 Cost Optimization →](L200_Cost_Optimization.md)
