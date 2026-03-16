# Step 0: Setup & Sample Data

**Duration:** 10 minutes | **Required — Do this first!**

> ⚠️ **Important:** Complete this setup before starting any module, lab, or exercise. The sample data created here is used throughout the entire training.

---

## 🎯 Goal

Create the `ecommerce` database with three collections (`products`, `customers`, `orders`) and populate them with sample data that will be used across all Performance & Cost Optimization modules.

---

## 🛠️ Prerequisites

- VSCode with the **DocumentDB extension** installed
- A running Azure DocumentDB cluster (connected in the extension)

---

## Step 1: Open the Sample Data Script

1. In VSCode, open the file: `5-Performance-and-Cost-Optimization/sample-data/ecommerce_data.vscode-documentdb-scrapbook`
2. This is a **DocumentDB Scrapbook** file that the VSCode DocumentDB extension can execute directly

> 💡 **Tip:** The `.vscode-documentdb-scrapbook` file extension is recognized by the VSCode DocumentDB extension as a scrapbook. You can run the entire file or individual sections by selecting text and clicking **Run Selected**. Before running, make sure to select your target database from the extension's connection panel in the sidebar.

---

## Step 2: Run the Script

1. Make sure your DocumentDB connection is active in the extension sidebar
2. Open `sample-data/ecommerce_data.vscode-documentdb-scrapbook`
3. In the extension's connection panel, select the **`ecommerce`** database (it will be created if it doesn't exist)
4. Click **Run All** (▶️) at the top of the scrapbook, or press `Ctrl+Alt+Enter`
5. The script will:
   - Drop any existing collections (for a clean setup)
   - Insert **50 products**, **30 customers**, and **80 orders**

---

## Step 3: Verify the Data

After the script completes, run these verification queries in a new scrapbook:

> 💡 **Note:** Select the `ecommerce` database from the VSCode DocumentDB extension's connection panel before running any commands. The `use()` command is not supported in the DocumentDB extension scrapbook.

```javascript
// Check document counts
db.products.countDocuments();    // Expected: 50
db.customers.countDocuments();   // Expected: 30
db.orders.countDocuments();      // Expected: 80
```

You should see:
```
50
30
80
```

---

## Step 4: Quick Data Exploration

Run these queries to familiarize yourself with the data:

```javascript
// View a sample product
db.products.findOne({ _id: "PROD001" });
```

Expected output:
```json
{
  "_id": "PROD001",
  "name": "Wireless Bluetooth Headphones",
  "category": "Electronics",
  "subcategory": "Audio",
  "price": 79.99,
  "stock": 250,
  "rating": 4.5,
  "tags": ["wireless", "bluetooth", "audio"],
  "vendor": "AudioTech",
  "warehouse": "eastus",
  "createdAt": "2025-01-15T00:00:00.000Z"
}
```

```javascript
// View a sample customer
db.customers.findOne({ _id: "CUST001" });
```

Expected output:
```json
{
  "_id": "CUST001",
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "region": "eastus",
  "tier": "premium",
  "totalSpent": 2450.00,
  "orderCount": 12,
  "joinedAt": "2024-06-15T00:00:00.000Z",
  "preferences": {
    "categories": ["Electronics", "Furniture"],
    "notifications": true
  }
}
```

```javascript
// View a sample order
db.orders.findOne({ _id: "ORD001" });
```

Expected output:
```json
{
  "_id": "ORD001",
  "customerId": "CUST001",
  "items": [
    { "productId": "PROD001", "name": "Wireless Bluetooth Headphones", "quantity": 1, "price": 79.99 },
    { "productId": "PROD004", "name": "Mechanical Keyboard RGB", "quantity": 1, "price": 129.99 }
  ],
  "total": 209.98,
  "status": "delivered",
  "region": "eastus",
  "paymentMethod": "credit_card",
  "orderDate": "2025-03-15T00:00:00.000Z",
  "deliveredAt": "2025-03-19T00:00:00.000Z"
}
```

---

## 📊 Data Schema Summary

| Collection | Documents | Key Fields |
|-----------|-----------|------------|
| **products** | 50 | `_id`, `name`, `category`, `subcategory`, `price`, `stock`, `rating`, `tags`, `vendor`, `warehouse`, `createdAt` |
| **customers** | 30 | `_id`, `name`, `email`, `region`, `tier`, `totalSpent`, `orderCount`, `joinedAt`, `preferences` |
| **orders** | 80 | `_id`, `customerId`, `items[]`, `total`, `status`, `region`, `paymentMethod`, `orderDate`, `deliveredAt` |

### Data Distribution

- **Product categories:** Electronics (30), Furniture (20)
- **Customer regions:** eastus (12), westus (10), centralus (8)
- **Customer tiers:** standard (15), premium (10), enterprise (5)
- **Order statuses:** delivered (60), shipped (10), pending (10)
- **Order regions:** eastus (30), westus (25), centralus (25)

---

✅ **Checkpoint:** You should now have the `ecommerce` database with 50 products, 30 customers, and 80 orders. You're ready to proceed to [L100: Performance Fundamentals](L100_Performance_Fundamentals.md)!

---

[← Back to Module Overview](README.md) | [Next: L100 Performance Fundamentals →](L100_Performance_Fundamentals.md)
