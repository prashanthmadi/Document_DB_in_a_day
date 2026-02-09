# Module 2.2: Schema Design Patterns (L200)

**Duration:** 60-90 minutes | **Level:** Intermediate | **Goal:** Master common NoSQL design patterns and anti-patterns

## What You'll Learn

- 🎨 Common schema design patterns
- ⚠️ Anti-patterns to avoid
- 🔄 When to embed vs reference
- ⚡ Performance optimization techniques
- 🛠️ Solving real-world problems with patterns

## Prerequisites

- Completed Module 2.1: NoSQL Fundamentals (L100)
- Understanding of basic NoSQL queries and aggregations
- DocumentDB cluster with VS Code connection

---

## Part 1: Embedding vs Referencing (15 minutes)

### 1.1 The Core Decision

Every NoSQL schema design starts with: **Should I embed or reference?**

**Embedding (Denormalization)**
```json
{
  "_id": "order-123",
  "customer": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "items": [
    { "product": "Laptop", "price": 1299 }
  ],
  "total": 1299
}
```

**Referencing (Normalization)**
```json
// Orders collection
{
  "_id": "order-123",
  "customerId": "cust-456",
  "itemIds": ["item-789"],
  "total": 1299
}

// Customers collection
{
  "_id": "cust-456",
  "name": "John Doe",
  "email": "john@example.com"
}
```

### 1.2 Decision Matrix

| Factor | Embed When... | Reference When... |
|---|---|---|
| **Relationship** | One-to-few | One-to-many / Many-to-many |
| **Data Size** | Small, bounded | Large, unbounded |
| **Update Frequency** | Related data updated together | Updated independently |
| **Read Pattern** | Always read together | Sometimes read separately |
| **Data Growth** | Size is predictable | Size grows unbounded |
| **Duplication** | Acceptable | Must avoid |

**Examples:**

✅ **Embed:** Order items, User addresses (2-3 max), Product reviews
❌ **Reference:** User's orders (hundreds), Product inventory across stores, Social media followers

---

## Part 2: Common Design Patterns (45 minutes)

### Pattern 1: Computed Pattern

**Problem:** Frequently calculated values slow down queries

**Solution:** Store pre-calculated values

**Example: E-commerce Order**

❌ **Bad - Calculate Every Time:**
```json
{
  "_id": "order-123",
  "items": [
    { "product": "Laptop", "price": 1299, "qty": 1 },
    { "product": "Mouse", "price": 25, "qty": 2 }
  ]
  // Total calculated on every read!
}
```

✅ **Good - Computed Pattern:**
```json
{
  "_id": "order-123",
  "items": [
    { "product": "Laptop", "price": 1299, "qty": 1 },
    { "product": "Mouse", "price": 25, "qty": 2 }
  ],
  "subtotal": 1349,
  "tax": 107.92,
  "shipping": 0,
  "total": 1456.92,
  "itemCount": 2
}
```

**When to Use:**
- Sum, average, count operations
- Complex calculations (tax, discounts)
- Statistics (ratings, reviews)
- Denormalized totals

---

### Pattern 2: Subset Pattern

**Problem:** Document has large arrays or fields rarely accessed

**Solution:** Store frequently accessed subset in main document, full data elsewhere

**Example: Product with Many Reviews**

❌ **Bad - All Reviews Embedded:**
```json
{
  "_id": "product-123",
  "name": "Laptop Pro",
  "price": 1299,
  "reviews": [
    // 10,000 reviews here - document becomes huge!
  ]
}
```

✅ **Good - Subset Pattern:**
```json
// Product document (frequently accessed)
{
  "_id": "product-123",
  "name": "Laptop Pro",
  "price": 1299,
  "reviewStats": {
    "avgRating": 4.7,
    "totalReviews": 10000
  },
  "recentReviews": [
    { "user": "John", "rating": 5, "date": "2026-02-05" },
    { "user": "Jane", "rating": 4, "date": "2026-02-04" }
    // Only 5-10 most recent
  ]
}

// Reviews collection (paginated access)
{
  "_id": "review-456",
  "productId": "product-123",
  "user": "John",
  "rating": 5,
  "comment": "Excellent laptop!",
  "date": "2026-02-05"
}
```

**When to Use:**
- Large arrays (reviews, comments, logs)
- Historical data with recent summary
- Media metadata (show 5 images, link to full gallery)

---

### Pattern 3: Extended Reference Pattern

**Problem:** Need some fields from referenced document on every read

**Solution:** Duplicate frequently accessed fields

**Example: Blog Posts with Author**

❌ **Bad - Separate Lookup:**
```json
// Posts
{
  "_id": "post-123",
  "title": "NoSQL Best Practices",
  "authorId": "user-456"  // Need separate query for author name!
}
```

✅ **Good - Extended Reference:**
```json
{
  "_id": "post-123",
  "title": "NoSQL Best Practices",
  "author": {
    "id": "user-456",
    "name": "John Doe",        // Duplicated for fast access
    "avatar": "url/to/img.jpg"  // Duplicated for fast access
  }
}
```

**When to Use:**
- Display lists (blog posts with author names)
- References where you need 2-3 fields consistently
- "Display-only" data that doesn't change often

**Trade-off:** Data duplication, but avoids expensive lookups

---

### Pattern 4: Bucket Pattern

**Problem:** Time-series or IoT data creates too many documents

**Solution:** Group data into buckets

**Example: IoT Sensor Data**

❌ **Bad - One Document Per Reading:**
```json
// 1 million readings = 1 million documents!
{ "sensorId": "temp-01", "value": 22.5, "time": "2026-02-07T10:00:00Z" }
{ "sensorId": "temp-01", "value": 22.7, "time": "2026-02-07T10:01:00Z" }
{ "sensorId": "temp-01", "value": 22.6, "time": "2026-02-07T10:02:00Z" }
```

✅ **Good - Bucket Pattern:**
```json
{
  "_id": "temp-01-2026-02-07-10",
  "sensorId": "temp-01",
  "date": "2026-02-07",
  "hour": 10,
  "readings": [
    { "minute": 0, "value": 22.5 },
    { "minute": 1, "value": 22.7 },
    { "minute": 2, "value": 22.6 }
    // 60 readings per document (1 hour bucket)
  ],
  "stats": {
    "min": 22.3,
    "max": 23.1,
    "avg": 22.7
  }
}
```

**When to Use:**
- Time-series data (IoT sensors, logs, metrics)
- Event streams
- Analytics data
- Any high-volume, time-ordered data

**Benefits:**
- Fewer documents (60x reduction in example)
- Better compression
- Pre-computed statistics

---

### Pattern 5: Outlier Pattern

**Problem:** Some documents have extreme values that don't fit normal pattern

**Solution:** Handle outliers separately

**Example: Social Media Posts**

✅ **Outlier Pattern:**
```json
// Regular post (< 100 comments)
{
  "_id": "post-123",
  "content": "Check out my photo",
  "comments": [
    { "user": "Alice", "text": "Nice!" },
    { "user": "Bob", "text": "Cool!" }
    // Embed up to 100 comments
  ],
  "hasOverflowComments": false
}

// Viral post (10,000+ comments)
{
  "_id": "post-viral",
  "content": "This went viral!",
  "commentsPreview": [
    { "user": "Alice", "text": "Amazing!" }
    // First 10 comments
  ],
  "commentCount": 10523,
  "hasOverflowComments": true,
  "commentsBucketId": "comments-post-viral"
}

// Overflow comments in separate collection
{
  "_id": "comments-post-viral-bucket-1",
  "postId": "post-viral",
  "comments": [
    // 100 comments per bucket
  ]
}
```

**When to Use:**
- 95% of documents fit normal pattern
- 5% are outliers (very popular posts, products, etc.)
- Want to optimize for common case

---

## Part 3: Anti-Patterns to Avoid (20 minutes)

### Anti-Pattern 1: Massive Arrays (Unbounded Growth)

❌ **BAD:**
```json
{
  "_id": "user-123",
  "name": "John",
  "orders": [
    // User has 10,000 orders over 10 years
    // Document size exceeds 16MB limit!
  ]
}
```

✅ **FIX:** Use references or subset pattern
```json
{
  "_id": "user-123",
  "name": "John",
  "recentOrders": [
    // Last 5 orders only
  ]
}

// Orders collection
{
  "_id": "order-456",
  "userId": "user-123",
  "items": [...]
}
```

---

### Anti-Pattern 2: One Collection Per Customer/Tenant

❌ **BAD:**
```javascript
// customer1_orders, customer2_orders, customer3_orders...
// Nightmare to maintain!
```

✅ **FIX:** Use single collection with tenant field
```json
{
  "_id": "order-123",
  "tenantId": "customer1",
  "items": [...]
}

// Index on tenantId for fast filtering
db.orders.createIndex({ tenantId: 1 })
```

---

### Anti-Pattern 3: Unnecessary Indexes

❌ **BAD:**
```javascript
// Index on every field "just in case"
db.products.createIndex({ name: 1 })
db.products.createIndex({ category: 1 })
db.products.createIndex({ brand: 1 })
db.products.createIndex({ price: 1 })
db.products.createIndex({ rating: 1 })
// Slows down writes, wastes storage
```

✅ **FIX:** Index only queried fields
```javascript
// Based on actual query patterns
db.products.createIndex({ category: 1, inStock: 1 })  // Compound index
db.products.createIndex({ rating: -1 })  // For sorting
```

---

### Anti-Pattern 4: Lack of Schema Validation

❌ **BAD:**
```json
// No consistency
{ "name": "Product 1", "price": 100 }
{ "productName": "Product 2", "cost": "50" }  // Different field names, wrong type!
{ "name": "Product 3" }  // Missing price!
```

✅ **FIX:** Use schema validation
```javascript
db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "price", "category"],
      properties: {
        name: { bsonType: "string" },
        price: { bsonType: "double", minimum: 0 },
        category: { bsonType: "string" }
      }
    }
  }
})
```

---

### Anti-Pattern 5: Case-Sensitive Fields

❌ **BAD:**
```json
{ "email": "JOHN@EXAMPLE.COM" }
{ "email": "john@example.com" }
// Same user, different emails due to case!
```

✅ **FIX:** Normalize to lowercase
```javascript
// Normalize before insert
const email = userInput.email.toLowerCase();
db.users.insertOne({ email: email });

// Case-insensitive index
db.users.createIndex(
  { email: 1 },
  { collation: { locale: "en", strength: 2 } }
)
```

---

## Part 4: Practical Lab (15 minutes)

### Lab Exercise: Design a Blog Platform

**Requirements:**
- Users can write posts
- Posts have many comments (potentially thousands)
- Show post with author name and avatar
- Show most recent 5 comments on main page
- Full comments on separate page
- Track post views and likes
- Users can follow other users

**Your Design:**

<details>
<summary>Suggested Solution</summary>

```javascript
// Users collection
{
  "_id": "user-123",
  "username": "johndoe",
  "email": "john@example.com",
  "avatar": "url/to/avatar.jpg",
  "bio": "Developer and writer",
  "stats": {
    "posts": 42,
    "followers": 1523,
    "following": 89
  },
  "followerIds": [],  // Reference, not embedded (unbounded)
  "createdAt": "2025-01-15"
}

// Posts collection (Extended Reference Pattern)
{
  "_id": "post-456",
  "title": "Getting Started with NoSQL",
  "content": "Full post content here...",
  "author": {
    "id": "user-123",
    "username": "johndoe",        // Duplicated
    "avatar": "url/to/avatar.jpg"  // Duplicated
  },
  "stats": {  // Computed Pattern
    "views": 5234,
    "likes": 312,
    "comments": 47
  },
  "recentComments": [  // Subset Pattern (last 5)
    {
      "user": "janedoe",
      "text": "Great post!",
      "date": "2026-02-05"
    }
  ],
  "tags": ["nosql", "database", "tutorial"],
  "createdAt": "2026-02-01",
  "updatedAt": "2026-02-05"
}

// Comments collection (separate for pagination)
{
  "_id": "comment-789",
  "postId": "post-456",
  "userId": "user-999",
  "username": "janedoe",  // Duplicated for display
  "text": "Great post!",
  "likes": 5,
  "createdAt": "2026-02-05"
}

// Followers collection (separate due to unbounded growth)
{
  "_id": "follow-111",
  "followerId": "user-123",
  "followingId": "user-456",
  "createdAt": "2026-01-20"
}

// Indexes
db.posts.createIndex({ "author.id": 1, createdAt: -1 })
db.comments.createIndex({ postId: 1, createdAt: -1 })
db.followers.createIndex({ followerId: 1 })
db.followers.createIndex({ followingId: 1 })
```

**Patterns Used:**
1. ✅ **Extended Reference** - Author info in posts
2. ✅ **Computed Pattern** - Stats (views, likes, comments)
3. ✅ **Subset Pattern** - Recent comments embedded
4. ✅ **Reference Pattern** - Full comments separate
5. ✅ **Avoid Massive Arrays** - Followers in separate collection

</details>

---

## Key Takeaways

✅ **Embed when data is read together** - One query is faster than multiple  
✅ **Reference when data is large or unbounded** - Avoid document size limits  
✅ **Use patterns to solve common problems** - Don't reinvent the wheel  
✅ **Avoid anti-patterns** - They cause performance and maintenance issues  
✅ **Design for your queries** - Schema follows access patterns  

**Pattern Summary:**
- **Computed:** Pre-calculate expensive operations
- **Subset:** Store frequently accessed subset + reference
- **Extended Reference:** Duplicate display fields to avoid lookups
- **Bucket:** Group time-series/high-volume data
- **Outlier:** Handle exceptions separately

---

## Quick Reference

### When to Embed vs Reference

```
EMBED if:
✓ One-to-few relationship
✓ Data accessed together
✓ Bounded growth
✓ Few updates

REFERENCE if:
✗ One-to-many / many-to-many
✗ Data accessed separately
✗ Unbounded growth
✗ Frequent independent updates
```

---

## Additional Resources

- MongoDB Schema Design Patterns documentation
- [DocumentDB Best Practices](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/best-practices-schema-design)
- Schema Anti-Patterns documentation

---

## Next Module

🎯 **Module 2.3: Data Relationships (L300)**
- Modeling one-to-one relationships
- Modeling one-to-many relationships
- Modeling many-to-many relationships
- Advanced relationship patterns
- Real-world scenarios

**Prerequisites:** Complete this L200 module and practice the patterns.

---

**🎉 Great work!** You now understand how to design effective NoSQL schemas using proven patterns!
