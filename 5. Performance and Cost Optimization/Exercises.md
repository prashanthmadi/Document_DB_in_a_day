# 📝 Knowledge Check Exercises

**Duration:** 10 minutes | **Level:** L100–L200

Test your understanding of Performance & Cost Optimization concepts covered in this module. Try to answer each question before revealing the solution.

---

## Question 1: Reading `.explain()` Output

A team member runs the following query and shares the `.explain("executionStats")` output:

```javascript
db.orders.find({ region: "westus", status: "shipped" }).explain("executionStats");
```

**Output:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "COLLSCAN",
      "filter": {
        "$and": [
          { "region": { "$eq": "westus" } },
          { "status": { "$eq": "shipped" } }
        ]
      },
      "direction": "forward"
    }
  },
  "executionStats": {
    "executionSuccess": true,
    "nReturned": 5,
    "executionTimeMillis": 45,
    "totalKeysExamined": 0,
    "totalDocsExamined": 500000
  }
}
```

**Questions:**

**(a)** What is the primary performance problem with this query?

**(b)** What is the efficiency ratio (`nReturned / totalDocsExamined`)?

**(c)** Write the command to create an optimal index for this query.

**(d)** After adding the index, what would you expect `totalDocsExamined` to become?

<details>
<summary>✅ Solution</summary>

**(a)** The query is performing a **COLLSCAN** (full collection scan). It reads all 500,000 documents to return only 5 matches. There is no index on `region` or `status`.

**(b)** Efficiency ratio = 5 / 500,000 = **0.00001** (extremely poor — 0.001% efficiency).

**(c)** Create a compound index on both filter fields:

```javascript
db.orders.createIndex({ region: 1, status: 1 });
```

Both fields use equality matching, so the order is flexible. Placing the more selective field first (the one with more distinct values) is slightly better.

**(d)** After adding the index, `totalDocsExamined` should drop to approximately **5** — matching `nReturned`. The efficiency ratio becomes 1.0 (perfect).

**Key takeaway:** A COLLSCAN with `totalDocsExamined` >> `nReturned` is the most common performance problem in DocumentDB. The fix is almost always an index, not a compute scaling operation.

</details>

---

## Question 2: Index Design with the ESR Rule

You need to optimize the following query for a product listing page:

```javascript
db.products.find({
  category: "Electronics",
  price: { $gte: 20, $lte: 100 }
}).sort({ rating: -1 }).limit(20);
```

**Questions:**

**(a)** Classify each part of the query as **Equality**, **Sort**, or **Range**:
- `category: "Electronics"` → __________
- `rating: -1` (sort) → __________
- `price: { $gte: 20, $lte: 100 }` → __________

**(b)** Using the ESR rule, what is the optimal index for this query?

**(c)** Which of these alternative indexes would be LESS optimal, and why?
- Option A: `{ price: 1, category: 1, rating: -1 }`
- Option B: `{ category: 1, rating: -1, price: 1 }`
- Option C: `{ rating: -1, category: 1, price: 1 }`

**(d)** If you added a projection `{ _id: 0, name: 1, price: 1, rating: 1 }`, would this query become a covered query with your optimal index? Why or why not?

<details>
<summary>✅ Solution</summary>

**(a)** Classification:
- `category: "Electronics"` → **Equality** (exact match)
- `rating: -1` (sort) → **Sort**
- `price: { $gte: 20, $lte: 100 }` → **Range**

**(b)** Using ESR (Equality → Sort → Range), the optimal index is:

```javascript
db.products.createIndex({ category: 1, rating: -1, price: 1 });
```

This puts equality first (narrows to "Electronics"), sort next (provides ordered results without in-memory sort), and range last (filters within the sorted subset).

**(c)** Analysis of alternatives:

- **Option A:** `{ price: 1, category: 1, rating: -1 }` — ❌ **Worst.** Range field (`price`) is first. This means the index scan starts with a range, which is less efficient. The sort on `rating` will require an in-memory sort since it's after a range field.

- **Option B:** `{ category: 1, rating: -1, price: 1 }` — ✅ **This IS the optimal index** (same as the answer). Equality → Sort → Range.

- **Option C:** `{ rating: -1, category: 1, price: 1 }` — ❌ **Suboptimal.** Sort field is first, but the equality field (`category`) is not in the leftmost position. The index can't efficiently narrow to "Electronics" first.

**(d)** **No**, this would NOT be a covered query. The projection includes `name`, but `name` is not in the index `{ category: 1, rating: -1, price: 1 }`. For a covered query, **all projected fields must exist in the index**. The server would still need to fetch documents to retrieve the `name` field.

To make it covered, you would need to either:
- Add `name` to the index: `{ category: 1, rating: -1, price: 1, name: 1 }`
- Or remove `name` from the projection

</details>

---

## Question 3: Scaling vs. Optimizing Decision

Your team is running an Azure DocumentDB cluster and experiencing the following symptoms:

- **Average query latency:** 200ms (target: < 50ms)
- **CPU utilization:** 25% average, 40% peak
- **Storage usage:** 50 GB out of 128 GB
- **Top query `.explain()` output:**

```json
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "COLLSCAN",
      "filter": { "customerId": { "$eq": "CUST12345" } },
      "direction": "forward"
    }
  },
  "executionStats": {
    "nReturned": 8,
    "executionTimeMillis": 180,
    "totalKeysExamined": 0,
    "totalDocsExamined": 2000000
  }
}
```

A colleague suggests scaling from **4 vCores to 16 vCores** to fix the latency issue. The upgrade would increase the monthly compute cost by 4x.

**Questions:**

**(a)** Is scaling to 16 vCores the right solution? Why or why not?

**(b)** What would you do instead? List the specific steps.

**(c)** After your fix, estimate the expected `totalDocsExamined` and `executionTimeMillis`.

**(d)** In what scenario WOULD scaling compute be the correct action?

<details>
<summary>✅ Solution</summary>

**(a)** **No**, scaling to 16 vCores is NOT the right solution. The evidence is clear:

- **CPU utilization is only 25% average / 40% peak** — compute is NOT the bottleneck
- The slow query uses **COLLSCAN** — it scans 2,000,000 documents to return 8
- The problem is a **missing index**, not insufficient compute
- Scaling from 4 to 16 vCores would 4x the cost while likely reducing latency by only a small fraction (the bottleneck is I/O from scanning 2M documents, not CPU)

**(b)** Steps to fix:

1. **Create an index on `customerId`:**
   ```javascript
   db.orders.createIndex({ customerId: 1 });
   ```

2. **Re-run the query with `.explain("executionStats")`** to verify it uses `IXSCAN`

3. **Check other top queries** for COLLSCAN patterns and add indexes as needed

4. **Review index efficiency** — if queries also sort or range-filter, create compound indexes using the ESR rule

5. **Monitor CPU after optimization** — if CPU drops further, you may even be able to **downscale** to save more money

**(c)** Expected results after adding the index:
- `totalDocsExamined`: **~8** (only matching documents, down from 2,000,000)
- `executionTimeMillis`: **~1-2ms** (down from 180ms)
- Improvement: **~100x faster** at zero additional cost

**(d)** Scaling compute IS the correct action when:
- All frequent queries already use **IXSCAN** (no COLLSCAN)
- CPU utilization is consistently **> 80%**
- Query latency is high despite efficient query plans
- The workload involves compute-heavy operations (complex aggregations, `$lookup` joins across large collections, text search)
- Connection count is approaching the tier limit

**Key takeaway:** Always check `.explain()` output and CPU metrics before approving a scale-up. In this case, a free index creation saves $X,XXX/month in unnecessary compute costs while delivering 100x better performance.

</details>

---

## 🎉 Congratulations!

You've completed the **Performance & Cost Optimization (L100–L200)** training module! Here's what you've learned:

- ✅ How to use `.explain("executionStats")` to diagnose query performance
- ✅ The difference between COLLSCAN, IXSCAN, and covered queries
- ✅ The ESR rule for compound index design
- ✅ Aggregation pipeline optimization techniques
- ✅ When to optimize vs. when to scale
- ✅ How to identify and remove unused indexes
- ✅ A systematic approach to performance troubleshooting

---

## 🔗 Continue Learning

- [Azure DocumentDB Documentation](https://learn.microsoft.com/en-us/azure/documentdb)
- [Module 2: NoSQL Core Concepts](../2-NoSQL-Core-Concepts/README.md) — Review schema design patterns
- [Module 3: AI Vector Search](../3-AI-Vector-Search/README.md) — Explore vector search performance

---

[← Back to Module Overview](README.md) | [← Back to Workshop Home](../README.md)
