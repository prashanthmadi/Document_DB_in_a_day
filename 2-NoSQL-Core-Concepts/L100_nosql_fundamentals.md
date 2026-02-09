# Module 2.1: NoSQL Fundamentals (L100)

**Duration:** 60-90 minutes | **Level:** Beginner | **Goal:** Understand NoSQL basics and perform essential queries with DocumentDB

## What You'll Learn

- 🎯 Why NoSQL? Understanding the fundamentals
- 📊 DocumentDB vs Relational Databases
- 🔍 Basic querying with `find()`
- 📈 Aggregation pipelines
- 💡 When to use NoSQL

## Prerequisites

- Completed Module 1: Introduction (DocumentDB & AI Foundry Setup)
- Active DocumentDB cluster with VS Code connection
- Basic understanding of JSON

---

## Part 1: Why NoSQL? (15 minutes)

### 1.1 The Traditional Database World

**Relational Databases (SQL):**
```
Orders Table          Customers Table
┌─────┬──────┬───┐    ┌─────┬────────┬───────┐
│ ID  │CustID│Amt│    │ ID  │  Name  │ Email │
├─────┼──────┼───┤    ├─────┼────────┼───────┤
│ 101 │  1   │500│    │  1  │  John  │ j@... │
│ 102 │  1   │300│    │  2  │  Jane  │ ja... │
│ 103 │  2   │750│    │  3  │  Bob   │ b@... │
└─────┴──────┴───┘    └─────┴────────┴───────┘
```

**Challenges:**
- ❌ **Rigid Schema** - Must define structure upfront
- ❌ **JOINs Required** - Fetch data from multiple tables
- ❌ **Vertical Scaling** - Expensive hardware upgrades
- ❌ **Fixed Schema Changes** - Migrations break applications
- ❌ **Not Cloud-Native** - Difficult to distribute globally

### 1.2 Enter NoSQL (DocumentDB)

**Document Model:**
```json
{
  "_id": "101",
  "customer": {
    "name": "John Doe",
    "email": "john@example.com",
    "memberId": "GOLD-1234"
  },
  "items": [
    { "product": "Laptop", "price": 1299, "qty": 1 },
    { "product": "Mouse", "price": 25, "qty": 2 }
  ],
  "total": 1349,
  "status": "shipped",
  "orderDate": "2026-02-01"
}
```

**Advantages:**
- ✅ **Flexible Schema** - Add fields as needed
- ✅ **No JOINs** - Data stored together (embedded)
- ✅ **Horizontal Scaling** - Add more servers easily
- ✅ **Cloud-Native** - Distributed by design
- ✅ **Developer-Friendly** - JSON matches application objects

### 1.3 When to Use NoSQL?

| Use NoSQL When... | Use SQL When... |
|---|---|
| Rapid prototyping & agile development | Strict transactional requirements |
| Hierarchical/nested data structures | Complex reporting across many tables |
| High read/write throughput needed | ACID guarantees are critical |
| Schema evolves frequently | Schema is stable and well-defined |
| Global distribution required | Single-region deployment |
| Working with semi-structured data | Highly structured, tabular data |

**Real-World NoSQL Use Cases:**
- 🛒 **E-commerce:** Product catalogs with varying attributes
- 👤 **User Profiles:** Social media, gaming profiles
- 📱 **Mobile Apps:** Offline-first applications
- 📊 **IoT:** Sensor data with diverse structures
- 🤖 **AI/ML:** Embeddings, vectors, unstructured data

---

## Part 2: Basic Querying with DocumentDB (30 minutes)

### 2.1 Load Sample Data

Open DocumentDB Scrapbook (right-click `trainingdb` → **DocumentDB Scrapbook**):

```javascript
// Create products collection with sample data
db.products.insertMany([
  {
    name: "Wireless Mouse",
    category: "Electronics",
    brand: "TechCo",
    price: 29.99,
    inStock: true,
    quantity: 150,
    tags: ["wireless", "bluetooth", "ergonomic"],
    rating: 4.5,
    reviews: 342
  },
  {
    name: "USB-C Cable",
    category: "Electronics",
    brand: "CableMax",
    price: 12.99,
    inStock: true,
    quantity: 500,
    tags: ["usbc", "charging", "data-transfer"],
    rating: 4.8,
    reviews: 1205
  },
  {
    name: "Laptop Stand",
    category: "Accessories",
    brand: "ErgoDesk",
    price: 45.00,
    inStock: false,
    quantity: 0,
    tags: ["ergonomic", "adjustable", "aluminum"],
    rating: 4.7,
    reviews: 89
  },
  {
    name: "Mechanical Keyboard",
    category: "Electronics",
    brand: "TypeMaster",
    price: 89.99,
    inStock: true,
    quantity: 75,
    tags: ["mechanical", "rgb", "gaming"],
    rating: 4.6,
    reviews: 523
  },
  {
    name: "Monitor Stand",
    category: "Accessories",
    brand: "ErgoDesk",
    price: 35.00,
    inStock: true,
    quantity: 120,
    tags: ["ergonomic", "adjustable", "wooden"],
    rating: 4.3,
    reviews: 67
  },
  {
    name: "Webcam HD",
    category: "Electronics",
    brand: "VisionTech",
    price: 69.99,
    inStock: true,
    quantity: 200,
    tags: ["1080p", "webcam", "streaming"],
    rating: 4.4,
    reviews: 412
  }
])
```

Click **Run Command** above the query block to insert the data.

### 2.2 CRUD Operations

CRUD stands for **Create, Read, Update, Delete** - the four basic operations for any database.

---

#### CREATE Operations

**insertOne() - Insert Single Document**
```javascript
// Insert one product
db.products.insertOne({
  name: "Wireless Keyboard",
  category: "Electronics",
  brand: "TypeMaster",
  price: 79.99,
  inStock: true,
  quantity: 85,
  tags: ["wireless", "keyboard", "compact"],
  rating: 4.6,
  reviews: 234
})

// Returns: { acknowledged: true, insertedId: ObjectId("...") }
```

**insertMany() - Insert Multiple Documents**
```javascript
// Insert multiple products at once
db.products.insertMany([
  {
    name: "HDMI Cable",
    category: "Electronics",
    price: 14.99,
    inStock: true,
    quantity: 350
  },
  {
    name: "Desk Lamp",
    category: "Accessories",
    price: 42.50,
    inStock: true,
    quantity: 90
  }
])

// Returns: 
// {
//   acknowledged: true,
//   insertedIds: {
//     '0': ObjectId("..."),
//     '1': ObjectId("...")
//   }
// }
```

**Key Differences:**
- `insertOne()` - Single document, fails if error occurs
- `insertMany()` - Multiple documents, can use `ordered: false` to continue on errors

---

#### READ Operations

**findOne() - Return Single Document**
```javascript
// Find first product matching criteria
db.products.findOne({ name: "Wireless Mouse" })

// Find first Electronics product
db.products.findOne({ category: "Electronics" })

// Returns single document or null if not found
```

**find() - Return Multiple Documents (Cursor)**
```javascript
// Find all products (returns cursor)
db.products.find({})

// Find all Electronics
db.products.find({ category: "Electronics" })

// Find with multiple conditions
db.products.find({
  category: "Electronics",
  inStock: true,
  price: { $lt: 50 }
})

// Returns cursor - iterate to see all results
```

**find() with Projection**
```javascript
// Return only specific fields
db.products.find(
  { category: "Electronics" },
  { name: 1, price: 1, _id: 0 }  // 1 = include, 0 = exclude
)

// Returns only name and price fields
```

**find() with Sorting and Limiting**
```javascript
// Find and sort
db.products.find({}).sort({ price: -1 })  // -1 = descending

// Find with limit
db.products.find({}).limit(5)  // First 5 documents

// Combine sort and limit
db.products.find({})
  .sort({ rating: -1 })
  .limit(3)  // Top 3 highest rated
```

**Counting Documents**
```javascript
// Count all products
db.products.countDocuments({})

// Count with filter
db.products.countDocuments({ inStock: true })
db.products.countDocuments({ price: { $lt: 50 } })
```

**Key Differences:**
- `findOne()` - Returns first matching document (or null)
- `find()` - Returns cursor to all matching documents
- Use `findOne()` when you expect exactly one result
- Use `find()` when you expect multiple results

---

#### UPDATE Operations

**updateOne() - Update Single Document**
```javascript
// Update first matching document
db.products.updateOne(
  { name: "Wireless Mouse" },  // Filter
  { 
    $set: { 
      price: 24.99,
      inStock: false
    } 
  }
)

// Returns:
// {
//   acknowledged: true,
//   matchedCount: 1,
//   modifiedCount: 1
// }
```

**updateMany() - Update Multiple Documents**
```javascript
// Update all Electronics products
db.products.updateMany(
  { category: "Electronics" },
  { 
    $set: { 
      lastUpdated: new Date()
    } 
  }
)

// Increase price by 10% for all TechCo products
db.products.updateMany(
  { brand: "TechCo" },
  { 
    $mul: { price: 1.1 }  // Multiply price by 1.1
  }
)

// Returns:
// {
//   acknowledged: true,
//   matchedCount: 4,
//   modifiedCount: 4
// }
```

**Update Operators:**
```javascript
// $set - Set field value
db.products.updateOne(
  { name: "USB-C Cable" },
  { $set: { quantity: 600 } }
)

// $inc - Increment numeric value
db.products.updateOne(
  { name: "USB-C Cable" },
  { $inc: { quantity: 50 } }  // Add 50 to current quantity
)

// $mul - Multiply numeric value
db.products.updateOne(
  { name: "USB-C Cable" },
  { $mul: { price: 0.9 } }  // 10% discount
)

// $unset - Remove field
db.products.updateOne(
  { name: "USB-C Cable" },
  { $unset: { reviews: "" } }  // Remove reviews field
)

// $push - Add to array
db.products.updateOne(
  { name: "Wireless Mouse" },
  { $push: { tags: "office" } }  // Add "office" to tags array
)

// $pull - Remove from array
db.products.updateOne(
  { name: "Wireless Mouse" },
  { $pull: { tags: "bluetooth" } }  // Remove "bluetooth" from tags
)
```

**replaceOne() - Replace Entire Document**
```javascript
// Replace entire document (keeps _id)
db.products.replaceOne(
  { name: "Wireless Mouse" },
  {
    name: "Wireless Mouse V2",
    category: "Electronics",
    price: 34.99,
    inStock: true,
    quantity: 200
    // All other fields removed!
  }
)

// Returns:
// {
//   acknowledged: true,
//   matchedCount: 1,
//   modifiedCount: 1
// }
```

**Key Differences:**
- `updateOne()` - Updates first matching document
- `updateMany()` - Updates all matching documents
- `replaceOne()` - Replaces entire document (except _id)
- Use `$set` to modify specific fields
- Use `replaceOne()` to replace entire document

---

#### DELETE Operations

**deleteOne() - Delete Single Document**
```javascript
// Delete first matching document
db.products.deleteOne({ name: "Wireless Mouse" })

// Delete first out-of-stock product
db.products.deleteOne({ inStock: false })

// Returns:
// {
//   acknowledged: true,
//   deletedCount: 1
// }
```

**deleteMany() - Delete Multiple Documents**
```javascript
// Delete all out-of-stock products
db.products.deleteMany({ inStock: false })

// Delete all products under $20
db.products.deleteMany({ price: { $lt: 20 } })

// Delete all products from specific brand
db.products.deleteMany({ brand: "OldBrand" })

// ⚠️ DANGER: Delete ALL documents (no filter)
db.products.deleteMany({})  // Be careful!

// Returns:
// {
//   acknowledged: true,
//   deletedCount: 3
// }
```

**Key Differences:**
- `deleteOne()` - Deletes first matching document
- `deleteMany()` - Deletes all matching documents
- Both return count of deleted documents
- Always test with `find()` first to see what will be deleted!

---

#### CRUD Best Practices

**1. Always Test Filters First**
```javascript
// BAD: Delete without checking
db.products.deleteMany({ category: "Electronics" })

// GOOD: Check what will be deleted first
db.products.find({ category: "Electronics" })  // See results
db.products.countDocuments({ category: "Electronics" })  // Check count
db.products.deleteMany({ category: "Electronics" })  // Then delete
```

**2. Use Specific Filters**
```javascript
// BAD: Vague filter might match unexpected documents
db.products.updateOne({ name: "Mouse" }, { $set: { price: 20 } })

// GOOD: Specific filter
db.products.updateOne(
  { name: "Wireless Mouse", brand: "TechCo" },
  { $set: { price: 24.99 } }
)
```

**3. Check Return Values**
```javascript
const result = db.products.updateOne(
  { name: "NonExistent" },
  { $set: { price: 100 } }
)

// Check if document was found and updated
if (result.matchedCount === 0) {
  print("No document found!")
} else if (result.modifiedCount === 0) {
  print("Document found but not modified (same values)")
} else {
  print("Document updated successfully")
}
```

**4. Use findOne() vs find()**
```javascript
// When you need exactly one result
const product = db.products.findOne({ _id: ObjectId("...") })
if (product) {
  print(product.name)
}

// When you need multiple results
db.products.find({ category: "Electronics" }).forEach(product => {
  print(product.name)
})
```

---

### 2.4 Common Query Operators

```javascript
// Comparison Operators
db.products.find({ price: { $gte: 30, $lte: 70 } })  // Between 30 and 70
db.products.find({ category: { $in: ["Electronics", "Accessories"] } })  // In list
db.products.find({ quantity: { $ne: 0 } })  // Not equal to 0

// Logical Operators
db.products.find({
  $and: [
    { price: { $lt: 50 } },
    { rating: { $gte: 4.5 } }
  ]
})

// Array Operators
db.products.find({ tags: { $all: ["ergonomic", "adjustable"] } })  // Has all tags
db.products.find({ tags: { $size: 3 } })  // Array has exactly 3 elements

// Existence Check
db.products.find({ reviews: { $exists: true } })  // Has reviews field
```

---

## Part 3: Aggregation Pipelines (30 minutes)

### 3.1 Understanding Aggregation

**Aggregation = Multi-stage data transformation pipeline**

```
Documents → [$stage1] → [$stage2] → [$stage3] → Results
```

Common Stages:
- `$match` - Filter documents (like WHERE)
- `$group` - Group by field (like GROUP BY)
- `$sort` - Sort results (like ORDER BY)
- `$project` - Select/transform fields (like SELECT)
- `$limit` - Limit results
- `$count` - Count documents

### 3.2 Aggregation Examples

**Example 1: Count Products by Category**
```javascript
db.products.aggregate([
  {
    $group: {
      _id: "$category",
      count: { $sum: 1 }
    }
  }
])
```

**Example 2: Average Price by Category**
```javascript
db.products.aggregate([
  {
    $group: {
      _id: "$category",
      avgPrice: { $avg: "$price" },
      totalProducts: { $sum: 1 }
    }
  },
  {
    $sort: { avgPrice: -1 }
  }
])
```

**Example 3: In-Stock Inventory Value**
```javascript
db.products.aggregate([
  {
    $match: { inStock: true }
  },
  {
    $project: {
      name: 1,
      category: 1,
      inventoryValue: { $multiply: ["$price", "$quantity"] }
    }
  },
  {
    $sort: { inventoryValue: -1 }
  }
])
```

**Example 4: Statistics by Brand**
```javascript
db.products.aggregate([
  {
    $group: {
      _id: "$brand",
      totalProducts: { $sum: 1 },
      avgPrice: { $avg: "$price" },
      avgRating: { $avg: "$rating" },
      totalReviews: { $sum: "$reviews" }
    }
  },
  {
    $sort: { totalReviews: -1 }
  }
])
```

**Example 5: Filter Then Group**
```javascript
db.products.aggregate([
  {
    $match: { 
      inStock: true,
      price: { $lt: 100 }
    }
  },
  {
    $group: {
      _id: "$category",
      products: { $push: "$name" },
      minPrice: { $min: "$price" },
      maxPrice: { $max: "$price" },
      count: { $sum: 1 }
    }
  }
])
```

**Example 6: Top Products with Calculated Field**
```javascript
db.products.aggregate([
  {
    $project: {
      name: 1,
      category: 1,
      price: 1,
      rating: 1,
      // Calculate popularity score
      popularityScore: {
        $add: [
          { $multiply: ["$rating", 100] },
          { $multiply: ["$reviews", 0.5] }
        ]
      }
    }
  },
  {
    $sort: { popularityScore: -1 }
  },
  {
    $limit: 3
  }
])
```

### 3.3 Practical Lab Exercise

**Task: Inventory Analysis Report**

Create an aggregation that answers:
1. Total inventory value per category
2. Number of products per category
3. Average rating per category
4. Only include in-stock products
5. Sort by total value descending

**Your Turn - Try It:**
```javascript
db.products.aggregate([
  // Step 1: Filter in-stock products
  {
    $match: { inStock: true }
  },
  // Step 2: Calculate inventory value per product
  {
    $project: {
      category: 1,
      rating: 1,
      inventoryValue: { $multiply: ["$price", "$quantity"] }
    }
  },
  // Step 3: Group by category
  {
    $group: {
      _id: "$category",
      totalValue: { $sum: "$inventoryValue" },
      productCount: { $sum: 1 },
      avgRating: { $avg: "$rating" }
    }
  },
  // Step 4: Sort by total value
  {
    $sort: { totalValue: -1 }
  }
])
```

**Expected Output:**
```json
[
  {
    "_id": "Electronics",
    "totalValue": 62647.5,
    "productCount": 4,
    "avgRating": 4.575
  },
  {
    "_id": "Accessories",
    "totalValue": 4200,
    "productCount": 1,
    "avgRating": 4.3
  }
]
```

---

## Part 4: Hands-On Practice (15 minutes)

### Challenge Exercises

**Challenge 1: Product Search**
Find all products:
- Price between $20 and $50
- Rating above 4.0
- Currently in stock
- Return only: name, price, rating

<details>
<summary>Solution</summary>

```javascript
db.products.find(
  {
    price: { $gte: 20, $lte: 50 },
    rating: { $gt: 4.0 },
    inStock: true
  },
  {
    name: 1,
    price: 1,
    rating: 1,
    _id: 0
  }
)
```
</details>

**Challenge 2: Reorder Alert**
Find products with low inventory (quantity < 100) and aggregate by brand.

<details>
<summary>Solution</summary>

```javascript
db.products.aggregate([
  {
    $match: { quantity: { $lt: 100 } }
  },
  {
    $group: {
      _id: "$brand",
      products: { $push: "$name" },
      totalQuantity: { $sum: "$quantity" }
    }
  },
  {
    $sort: { totalQuantity: 1 }
  }
])
```
</details>

**Challenge 3: Brand Leaderboard**
Create a leaderboard showing brands ranked by average rating and total reviews.

<details>
<summary>Solution</summary>

```javascript
db.products.aggregate([
  {
    $group: {
      _id: "$brand",
      avgRating: { $avg: "$rating" },
      totalReviews: { $sum: "$reviews" },
      productCount: { $sum: 1 }
    }
  },
  {
    $sort: { avgRating: -1, totalReviews: -1 }
  }
])
```
</details>

---

## Key Takeaways

✅ **NoSQL is flexible** - Schema evolves with your application  
✅ **Documents are intuitive** - JSON matches how developers think  
✅ **Find queries are powerful** - Rich query operators for filtering  
✅ **Aggregations enable analytics** - Multi-stage pipelines for complex analysis  
✅ **No JOINs needed** - Embed related data together  

**What You've Learned:**
- Why NoSQL exists and when to use it
- Basic CRUD operations with `find()`
- Query operators ($lt, $gte, $in, $or, etc.)
- Aggregation pipeline stages ($match, $group, $sort, $project)
- Real-world query patterns

---

## Quick Reference

### Essential Query Operators
```javascript
// Comparison
{ field: { $eq: value } }      // Equal
{ field: { $ne: value } }      // Not equal
{ field: { $gt: value } }      // Greater than
{ field: { $gte: value } }     // Greater than or equal
{ field: { $lt: value } }      // Less than
{ field: { $lte: value } }     // Less than or equal
{ field: { $in: [v1, v2] } }   // In array

// Logical
{ $and: [{...}, {...}] }       // AND
{ $or: [{...}, {...}] }        // OR
{ $not: {...} }                // NOT

// Array
{ field: value }               // Contains value
{ field: { $all: [v1, v2] } }  // Contains all values
{ field: { $size: n } }        // Array length equals n

// Existence
{ field: { $exists: true } }   // Field exists
```

### Essential Aggregation Stages
```javascript
{ $match: { condition } }      // Filter documents
{ $group: { _id: "$field" } }  // Group by field
{ $sort: { field: 1 } }        // Sort ascending (1) or descending (-1)
{ $project: { field: 1 } }     // Select fields
{ $limit: n }                  // Limit results to n
{ $count: "fieldName" }        // Count documents
```

---

## Additional Resources

- MongoDB Query Operators documentation
- Aggregation Pipeline Reference documentation
- [DocumentDB Query Examples](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/query)

---

## Next Module

🎯 **Module 2.2: Schema Design Patterns (L200)**
- Common design patterns (Computed, Subset, Bucket, etc.)
- Anti-patterns to avoid
- When to embed vs reference
- Performance optimization

**Prerequisites:** Complete this L100 module with hands-on practice.

---

**🎉 Congratulations!** You now understand NoSQL fundamentals and can query DocumentDB effectively. Ready for schema design patterns!
