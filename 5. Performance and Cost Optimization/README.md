# Azure DocumentDB Performance & Cost Optimization Training (L100–L200)

This hands-on, follow-along training covers **performance tuning and cost optimization**
for **Azure DocumentDB (MongoDB compatibility)**.

**Audience**
- Cloud engineers
- Support engineers
- Architects new to Azure DocumentDB

**Goals**
- Understand how performance works in Azure DocumentDB
- Learn how query shape and indexing impact cost
- Apply scaling strategies to reduce overprovisioning
- Practice real-world troubleshooting patterns

---

## Module 1 – Performance Fundamentals

### Key Concepts
- Compute (vCores + memory) and storage are **decoupled**
- Performance depends on:
  - CPU & memory (compute tier)
  - Storage IOPS
  - Index efficiency
- Scaling operations are **zero downtime**

### Why This Matters
Blindly scaling compute increases cost without fixing root causes.
Most performance issues are query or index related.

---

### 🧪 Lab 1 – Establish a Baseline

**Goal:** Observe baseline query performance.

```js
db.orders.find({ region: "eastus" }).explain("executionStats")
