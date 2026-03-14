# 🔬 Lab 2: Query Performance Tuning

**Duration:** 15–20 minutes | **Level:** L200 | **Hands-On Lab**

---

## 🎯 Lab Objective

In this lab, you will take slow, unoptimized queries and improve them step by step using projections, better filters, and aggregation pipeline optimization. You will measure the improvement at each step using `.explain()`.

---

## Prerequisites

- ✅ Completed [Step 0: Setup & Sample Data](00_Setup_and_Sample_Data.md)
- ✅ Read [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)
- ✅ Read [L200: Advanced Optimization & Cost Strategies](L200_Cost_Optimization.md)
- ✅ VSCode with DocumentDB extension connected to your cluster

---

## Lab Setup

Open a MongoDB Scrapbook in VSCode and reset indexes:

> 💡 **Note:** Select the `ecommerce` database from the VSCode DocumentDB extension's connection panel before running any commands. The `use()` command is not supported in the DocumentDB extension scrapbook.

```javascript
// Clean slate — drop all non-default indexes
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

---

## Exercise 1: Optimize a Slow Product Search

**Scenario:** Your e-commerce site has a product search page. Users can filter by category and sort by rating. The current query is slow.

### Step 1: Run the unoptimized query

```javascript
// Unoptimized: No index, no projection, fetches all fields
db.products.find(
  { category: "Electronics" }
).sort({ rating: -1 }).explain("executionStats");
```

📝 **Record the baseline:**
- Stage: __________
- totalDocsExamined: __________
- executionTimeMillis: __________
- Is there a SORT stage? __________

### Step 2: Add a compound index (ESR rule)

```javascript
// Equality (category) → Sort (rating descending)
db.products.createIndex({ category: 1, rating: -1 });
```

### Step 3: Run the query again with explain

```javascript
db.products.find(
  { category: "Electronics" }
).sort({ rating: -1 }).explain("executionStats");
```

📝 **Record improvements:**
- Stage: __________
- totalDocsExamined: __________
- Is the SORT stage gone? __________

### Step 4: Add a projection to reduce data transfer

```javascript
// Only return what the search results page needs
db.products.find(
  { category: "Electronics" },
  { _id: 1, name: 1, price: 1, rating: 1 }
).sort({ rating: -1 });
```

Run it and see the results — notice how much smaller the response is compared to the full document.

### Step 5: Add a limit for pagination

```javascript
// Real search pages show 10 results at a time
db.products.find(
  { category: "Electronics" },
  { _id: 1, name: 1, price: 1, rating: 1 }
).sort({ rating: -1 }).limit(10);
```

<details>
<summary>✅ Expected Optimization Summary</summary>

| Step | Change | Impact |
|------|--------|--------|
| Baseline | No index, full docs | COLLSCAN, in-memory sort |
| + Index | `{ category: 1, rating: -1 }` | IXSCAN, no SORT stage |
| + Projection | Only 4 fields | Less data transferred |
| + Limit | `.limit(10)` | Only 10 docs processed/returned |

Each step progressively improves performance.

</details>

---

## Exercise 2: Optimize an Order Lookup Query

**Scenario:** Customer support agents look up orders by customer ID and need recent orders first.

### Step 1: Run the unoptimized query

```javascript
// Agent searches for a customer's orders
db.orders.find(
  { customerId: "CUST005" }
).sort({ orderDate: -1 }).explain("executionStats");
```

📝 **Record:** Stage: __________ | DocsExamined: __________

### Step 2: Create an optimal index

```javascript
// ESR: Equality (customerId) → Sort (orderDate descending)
db.orders.createIndex({ customerId: 1, orderDate: -1 });
```

### Step 3: Re-run with explain

```javascript
db.orders.find(
  { customerId: "CUST005" }
).sort({ orderDate: -1 }).explain("executionStats");
```

### Step 4: Optimize with projection for the UI

```javascript
// Support agent only needs: order date, status, total, and items summary
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
<summary>✅ Expected Results</summary>

With the `{ customerId: 1, orderDate: -1 }` index:
- `totalDocsExamined` drops from 80 to ~4 (only CUST005's orders)
- No in-memory SORT stage (the index provides the sort)
- Projection reduces response size for the UI

</details>

---

## Exercise 3: Optimize an Aggregation Pipeline

**Scenario:** The analytics dashboard needs to show revenue by region for delivered orders, sorted by revenue.

### Step 1: Run an unoptimized pipeline

```javascript
// ❌ Unoptimized: No early filter, no index
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

This processes ALL 80 orders (including non-delivered ones).

### Step 2: Add an early `$match` stage

```javascript
// ✅ Filter to delivered orders FIRST
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

The first `$match` stage can use an index, so adding `{ status: 1 }` makes the pipeline more efficient.

</details>

---

## Exercise 4: Range Query Optimization

**Scenario:** The finance team needs to find high-value orders (total > $500) from the last 30 days.

### Step 1: Run without an index

```javascript
db.orders.find({
  total: { $gt: 500 },
  orderDate: { $gte: ISODate("2025-05-01") }
}).sort({ total: -1 }).explain("executionStats");
```

### Step 2: Create an optimized index

For range queries with sort, consider the ESR rule:
- No equality fields in this query
- Sort on `total` (descending)
- Range on `total` and `orderDate`

```javascript
// Since we sort by total and filter by total + orderDate:
db.orders.createIndex({ total: -1, orderDate: 1 });
```

### Step 3: Re-run and compare

```javascript
db.orders.find({
  total: { $gt: 500 },
  orderDate: { $gte: ISODate("2025-05-01") }
}).sort({ total: -1 }).explain("executionStats");
```

### Step 4: Add projection for the finance report

```javascript
db.orders.find(
  {
    total: { $gt: 500 },
    orderDate: { $gte: ISODate("2025-05-01") }
  },
  { _id: 1, customerId: 1, total: 1, orderDate: 1, status: 1 }
).sort({ total: -1 });
```

<details>
<summary>✅ Expected Results</summary>

High-value recent orders sorted by total:
```json
[
  { "_id": "ORD060", "customerId": "CUST018", "total": 4799.84, "orderDate": "2025-05-13", "status": "delivered" },
  { "_id": "ORD066", "customerId": "CUST025", "total": 3479.88, "orderDate": "2025-05-19", "status": "delivered" },
  { "_id": "ORD047", "customerId": "CUST025", "total": 1719.92, "orderDate": "2025-04-30", "status": "delivered" },
  ...
]
```

The index eliminates COLLSCAN and in-memory sort for this range query pattern.

</details>

---

## Lab Summary

| Exercise | Technique | Key Takeaway |
|----------|-----------|-------------|
| 1 | Index + Projection + Limit | Layer optimizations progressively |
| 2 | Customer lookup index | ESR rule for equality + sort queries |
| 3 | Aggregation `$match` early | Filter early, index the `$match` stage |
| 4 | Range query optimization | Index design for range + sort patterns |

---

## 🧹 Cleanup

```javascript
db.orders.dropIndexes();
db.products.dropIndexes();
db.customers.dropIndexes();
```

---

✅ **Lab 2 Complete!** You've practiced optimizing real-world query patterns. Proceed to [Lab 3: Scaling Strategy](Lab3_Scaling_Strategy.md).

---

[← Back to Module Overview](README.md) | [Next: Lab 3 — Scaling Strategy →](Lab3_Scaling_Strategy.md)
