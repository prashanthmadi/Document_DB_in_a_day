# Module 2.3: Modeling Data Relationships (L300)

**Duration:** 45-60 minutes | **Level:** Advanced | **Goal:** Master complex relationship modeling in NoSQL

## What You'll Learn

- 🔗 One-to-one relationships
- 📊 One-to-many relationships
- 🔄 Many-to-many relationships
- 🎯 Choosing the right approach
- 🏗️ Real-world relationship patterns

## Prerequisites

- Completed Module 2.1: NoSQL Fundamentals (L100)
- Completed Module 2.2: Schema Design Patterns (L200)
- Understanding of embed vs reference trade-offs

---

## Part 1: One-to-One Relationships (10 minutes)

### 1.1 When to Use One-to-One

**Scenarios:**
- User → User Profile
- Employee → Employee Details (salary, SSN, etc.)
- Product → Product Specifications
- Order → Shipping Address

### 1.2 Approach 1: Embedded (Preferred)

**Best for:** Data always accessed together

```json
{
  "_id": "user-123",
  "username": "johndoe",
  "email": "john@example.com",
  "profile": {
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1-555-0100",
    "address": {
      "street": "123 Main St",
      "city": "Seattle",
      "state": "WA",
      "zip": "98101"
    },
    "preferences": {
      "theme": "dark",
      "notifications": true
    }
  },
  "createdAt": "2025-06-15"
}
```

**Advantages:**
- ✅ Single query to get all data
- ✅ Atomic updates
- ✅ Simpler code

---

### 1.3 Approach 2: Separate Collections (For Large or Sensitive Data)

**Best for:** Privacy, security, or very large documents

```javascript
// Users collection (public info)
{
  "_id": "user-123",
  "username": "johndoe",
  "email": "john@example.com",
  "profileId": "profile-456",  // Reference
  "createdAt": "2025-06-15"
}

// Profiles collection (detailed/sensitive info)
{
  "_id": "profile-456",
  "userId": "user-123",  // Back-reference
  "ssn": "***-**-1234",  // Sensitive!
  "salary": 125000,      // Sensitive!
  "emergencyContact": {
    "name": "Jane Doe",
    "phone": "+1-555-0200"
  },
  "medicalInfo": {
    // Large medical history
  }
}
```

**Advantages:**
- ✅ Separate access control
- ✅ Keeps main document small
- ✅ Can lazy-load detailed info

---

## Part 2: One-to-Many Relationships (20 minutes)

### 2.1 Key Decision: Embed or Reference?

**Factors:**
- **Cardinality:** How many "many"? (Few vs. Thousands)
- **Size:** How big is each child document?
- **Growth:** Bounded or unbounded?
- **Access Pattern:** Read together or separate?

---

### 2.2 Approach 1: Embedded Array (One-to-Few)

**Best for:** < 100 items, bounded growth, accessed together

**Example: Order → Order Items**
```json
{
  "_id": "order-123",
  "customerId": "cust-456",
  "status": "shipped",
  "items": [
    {
      "productId": "prod-789",
      "name": "Laptop",
      "price": 1299.99,
      "quantity": 1
    },
    {
      "productId": "prod-101",
      "name": "Mouse",
      "price": 29.99,
      "quantity": 2
    }
  ],
  "subtotal": 1359.97,
  "tax": 108.80,
  "total": 1468.77,
  "orderDate": "2026-02-05"
}
```

**Query Example:**
```javascript
// Get order with all items in one query
db.orders.findOne({ _id: "order-123" })
```

**Advantages:**
- ✅ Single query for all data
- ✅ Atomic updates
- ✅ No JOINs needed

**When NOT to use:**
- ❌ Array can grow unbounded (user's orders)
- ❌ Items updated independently
- ❌ Items need separate queries

---

### 2.3 Approach 2: Child References Parent (One-to-Many)

**Best for:** Many items, independent access, unbounded growth

**Example: Blog → Blog Posts**
```javascript
// Blogs collection
{
  "_id": "blog-123",
  "title": "Tech Insights",
  "author": "John Doe",
  "stats": {
    "posts": 247,
    "subscribers": 5234
  }
}

// Posts collection (each references parent)
{
  "_id": "post-456",
  "blogId": "blog-123",  // Reference to parent
  "title": "Understanding NoSQL",
  "content": "Full content here...",
  "publishDate": "2026-02-05",
  "views": 1523
}
{
  "_id": "post-457",
  "blogId": "blog-123",  // Same blog
  "title": "MongoDB Patterns",
  "content": "...",
  "publishDate": "2026-02-06"
}
```

**Query Examples:**
```javascript
// Get blog
db.blogs.findOne({ _id: "blog-123" })

// Get all posts for blog (separate query)
db.posts.find({ blogId: "blog-123" })
  .sort({ publishDate: -1 })
  .limit(10)

// Index for performance
db.posts.createIndex({ blogId: 1, publishDate: -1 })
```

**Advantages:**
- ✅ Handles unlimited posts
- ✅ Posts queried independently
- ✅ Easy pagination
- ✅ No document size limits

---

### 2.4 Approach 3: Parent References Children (Rare)

**Best for:** Need to query "all children" from parent frequently, bounded list

**Example: Project → Team Members**
```json
{
  "_id": "project-123",
  "name": "Website Redesign",
  "memberIds": [
    "user-456",
    "user-789",
    "user-101"
  ],
  "status": "active",
  "deadline": "2026-03-01"
}
```

**Query Example:**
```javascript
// Get project with member details (requires $lookup or application-level join)
const project = db.projects.findOne({ _id: "project-123" });
const members = db.users.find({
  _id: { $in: project.memberIds }
});
```

**Use Sparingly:**
- ⚠️ Application must manage array updates
- ⚠️ Array can't be too large
- ⚠️ Better for bounded lists (team members, roles, etc.)

---

## Part 3: Many-to-Many Relationships (15 minutes)

### 3.1 Many-to-Many Scenarios

- Students ↔ Courses
- Users ↔ Groups
- Products ↔ Categories
- Actors ↔ Movies

### 3.2 Approach 1: Array of References (Simple)

**Best for:** Small lists, one direction is primary

**Example: Users ↔ Skills**
```json
{
  "_id": "user-123",
  "name": "John Doe",
  "skills": [
    "JavaScript",
    "Python",
    "Docker",
    "MongoDB"
  ]
}
```

**Query:**
```javascript
// Find users with Python skill
db.users.find({ skills: "Python" })

// Find users with both Python AND Docker
db.users.find({
  skills: { $all: ["Python", "Docker"] }
})
```

**Limitations:**
- ❌ Can't store additional data about relationship
- ❌ Hard to query "reverse" direction

---

### 3.3 Approach 2: Two-Way Embedding (Denormalization)

**Best for:** Need to query both directions efficiently

**Example: Students ↔ Courses**
```javascript
// Students collection
{
  "_id": "student-123",
  "name": "John Doe",
  "enrolledCourses": [
    {
      "courseId": "course-456",
      "courseName": "Data Science 101",  // Denormalized
      "enrolledDate": "2026-01-15",
      "grade": null
    },
    {
      "courseId": "course-789",
      "courseName": "Web Development",   // Denormalized
      "enrolledDate": "2026-01-20",
      "grade": null
    }
  ]
}

// Courses collection
{
  "_id": "course-456",
  "name": "Data Science 101",
  "instructor": "Dr. Smith",
  "students": [
    {
      "studentId": "student-123",
      "studentName": "John Doe",  // Denormalized
      "enrolledDate": "2026-01-15"
    },
    {
      "studentId": "student-456",
      "studentName": "Jane Smith",
      "enrolledDate": "2026-01-16"
    }
  ],
  "capacity": 30,
  "enrolled": 2
}
```

**Queries:**
```javascript
// Find all courses for a student
db.students.findOne({ _id: "student-123" })

// Find all students in a course
db.courses.findOne({ _id: "course-456" })
```

**Trade-offs:**
- ✅ Fast queries in both directions
- ✅ Can store relationship metadata (enrollment date, grade)
- ❌ Data duplication
- ❌ Must update both documents when relationship changes

---

### 3.4 Approach 3: Join Collection (Most Flexible)

**Best for:** Complex relationships with metadata, frequent relationship updates

**Example: Users ↔ Projects**
```javascript
// Users collection
{
  "_id": "user-123",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "Developer"
}

// Projects collection
{
  "_id": "project-456",
  "name": "Website Redesign",
  "status": "active",
  "budget": 50000
}

// UserProjects collection (join collection)
{
  "_id": "userproj-789",
  "userId": "user-123",
  "projectId": "project-456",
  "role": "Lead Developer",
  "hoursPerWeek": 20,
  "startDate": "2026-01-15",
  "endDate": null,
  "active": true
}
```

**Queries:**
```javascript
// Get all projects for a user
db.userProjects.find({ userId: "user-123" })

// Get all users on a project
db.userProjects.find({ projectId: "project-456" })

// Get active lead developers on any project
db.userProjects.find({
  role: "Lead Developer",
  active: true
})

// Indexes
db.userProjects.createIndex({ userId: 1, active: 1 })
db.userProjects.createIndex({ projectId: 1, active: 1 })
```

**Advantages:**
- ✅ Most flexible approach
- ✅ Rich relationship metadata
- ✅ Easy to add/remove relationships
- ✅ No document size limits
- ✅ Query relationships independently

**Use for:**
- Social network (users ↔ users / followers)
- E-commerce (products ↔ categories with promotions)
- Project management (users ↔ projects with roles)

---

## Part 4: Real-World Scenarios (15 minutes)

### Scenario 1: E-commerce Platform

**Entities:** Users, Products, Orders, Reviews, Categories

```javascript
// Users
{
  "_id": "user-123",
  "name": "John Doe",
  "email": "john@example.com",
  "addresses": [  // One-to-few embedded
    {
      "type": "home",
      "street": "123 Main St",
      "city": "Seattle",
      "default": true
    }
  ],
  "stats": {
    "orders": 42,
    "reviews": 15
  }
}

// Products
{
  "_id": "product-456",
  "name": "Laptop Pro",
  "price": 1299.99,
  "categories": ["Electronics", "Computers"],  // Many-to-many
  "specs": {  // One-to-one embedded
    "cpu": "Intel i7",
    "ram": "16GB",
    "storage": "512GB SSD"
  },
  "reviewStats": {  // Computed pattern
    "avgRating": 4.7,
    "totalReviews": 523
  },
  "recentReviews": [  // Subset pattern
    // Last 5 reviews
  ]
}

// Orders (one-to-many: user → orders)
{
  "_id": "order-789",
  "userId": "user-123",  // Reference
  "items": [  // One-to-few embedded
    { "productId": "product-456", "name": "Laptop Pro", "price": 1299.99, "qty": 1 }
  ],
  "total": 1299.99,
  "status": "shipped"
}

// Reviews (separate collection for pagination)
{
  "_id": "review-101",
  "productId": "product-456",  // Reference
  "userId": "user-123",        // Reference
  "userName": "John Doe",      // Denormalized
  "rating": 5,
  "comment": "Excellent!",
  "helpful": 23,
  "date": "2026-02-05"
}
```

---

### Scenario 2: Social Media Platform

**Entities:** Users, Posts, Comments, Followers

```javascript
// Users
{
  "_id": "user-123",
  "username": "johndoe",
  "profile": {  // One-to-one embedded
    "bio": "Developer",
    "avatar": "url"
  },
  "stats": {  // Computed
    "posts": 347,
    "followers": 5234,
    "following": 892
  }
}

// Posts (one-to-many: user → posts)
{
  "_id": "post-456",
  "userId": "user-123",
  "author": {  // Extended reference
    "username": "johndoe",
    "avatar": "url"
  },
  "content": "Post text...",
  "media": [  // One-to-few embedded
    { "type": "image", "url": "..." }
  ],
  "stats": {  // Computed
    "likes": 523,
    "comments": 47,
    "shares": 12
  },
  "recentComments": [  // Subset pattern
    // Last 3 comments
  ]
}

// Comments (separate for pagination)
{
  "_id": "comment-789",
  "postId": "post-456",
  "userId": "user-999",
  "username": "janedoe",  // Denormalized
  "text": "Great post!",
  "likes": 5
}

// Followers (many-to-many join collection)
{
  "_id": "follow-101",
  "followerId": "user-123",
  "followingId": "user-456",
  "createdAt": "2026-01-15"
}
```

---

## Key Takeaways

✅ **One-to-One:** Embed unless sensitive/large  
✅ **One-to-Few:** Embed array  
✅ **One-to-Many:** Child references parent  
✅ **Many-to-Many:** Join collection for flexibility  
✅ **Denormalize display data** for performance  

**Decision Tree:**
```
Is it one-to-one?
  → YES: Embed (unless sensitive)
  
Is it one-to-few (<100)?
  → YES: Embed array
  
Is it one-to-many (unbounded)?
  → YES: Child references parent
  
Is it many-to-many?
  → Simple: Array of IDs
  → Complex: Join collection
```

---

## Quick Reference

### Relationship Patterns

| Pattern | Example | Implementation |
|---|---|---|
| **One-to-One** | User → Profile | Embed in same document |
| **One-to-Few** | Order → Items | Embed array (< 100 items) |
| **One-to-Many** | Blog → Posts | Child references parent |
| **Many-to-Many** | Students ↔ Courses | Join collection |

### Indexing for Relationships

```javascript
// One-to-many: Child references parent
db.posts.createIndex({ blogId: 1, publishDate: -1 })

// Many-to-many: Join collection
db.userProjects.createIndex({ userId: 1 })
db.userProjects.createIndex({ projectId: 1 })

// Query with embedded array
db.users.createIndex({ "skills": 1 })
```

---

## Additional Resources

- MongoDB Relationship Modeling documentation
- [DocumentDB Schema Design](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/how-to-model-partition-example)
- MongoDB Schema Design best practices documentation

---

## Next Steps

🎯 **Continue to AI/Vector Search Modules** to learn:
- Vector embeddings
- Semantic search with DocumentDB
- Building AI agents with your data

**You're now ready to design complex, production-ready NoSQL schemas!**

---

**🎉 Excellent!** You've mastered NoSQL relationship modeling. You can now design schemas for any application!
