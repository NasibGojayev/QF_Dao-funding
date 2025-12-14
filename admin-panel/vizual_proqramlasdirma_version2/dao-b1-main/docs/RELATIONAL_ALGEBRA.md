# Relational Algebra Review

This document demonstrates the relational algebra foundations of key database queries and explains join strategy decisions.

---

## Notation Reference

| Symbol | Operation | SQL Equivalent |
|:---:|:---|:---|
| σ | Selection | WHERE |
| π | Projection | SELECT columns |
| ⋈ | Natural Join | JOIN ON |
| ⋈θ | Theta Join | JOIN ON condition |
| × | Cartesian Product | CROSS JOIN |
| ∪ | Union | UNION |
| − | Difference | EXCEPT |
| ρ | Rename | AS |

---

## Query 1: Fetch Recent Transactions for User

### SQL
```sql
SELECT tx_hash, amount, created_at, p.title as project_title
FROM transactions t
JOIN projects p ON t.project_id = p.id
WHERE t.user_id = 123
ORDER BY t.created_at DESC
LIMIT 50;
```

### Relational Algebra

```
π tx_hash, amount, created_at, title (
    σ user_id = 123 (
        transactions ⋈ project_id = id projects
    )
)
```

**Step-by-step breakdown:**

1. **Join**: `transactions ⋈ project_id = id projects`
   - Theta join on foreign key relationship

2. **Selection**: `σ user_id = 123 (...)`
   - Filter to specific user

3. **Projection**: `π tx_hash, amount, created_at, title (...)`
   - Return only needed columns

### Query Optimization

**Push Selection Down:**
```
π tx_hash, amount, created_at, title (
    (σ user_id = 123 transactions) ⋈ project_id = id projects
)
```

By applying selection BEFORE the join, we reduce the number of rows participating in the join operation.

**Join Strategy:** 
- With index on `(user_id, created_at)`, the optimizer uses **Nested Loop Join with Index Lookup**
- Outer: Index scan on transactions for user_id = 123
- Inner: Index lookup on projects.id

---

## Query 2: Dashboard Summary by Tag

### SQL
```sql
SELECT tags.name, COUNT(*) as tx_count, SUM(amount) as total
FROM transactions t
LEFT JOIN tags ON t.tag_id = tags.id
GROUP BY tags.name;
```

### Relational Algebra

```
γ tag_name; COUNT(*), SUM(amount) (
    π tag_id, amount, name (
        transactions ⟕ tag_id = id tags
    )
)
```

Where:
- `⟕` = Left Outer Join
- `γ` = Grouping/Aggregation operator

### Materialized View Optimization

Instead of computing this at runtime, we precompute and store as `mv_tx_summary`:

```
mv_tx_summary = γ day, tag; COUNT(*), SUM(amount) (
    π DATE(created_at), tag_id, amount, name (
        transactions ⟕ tag_id = id tags
    )
)
```

**Join Strategy:**
- **Hash Join** preferred for full table aggregation
- Build hash table on smaller `tags` table (build phase)
- Probe with larger `transactions` table (probe phase)

---

## Query 3: Projects with Their Tags

### SQL
```sql
SELECT p.id, p.title, t.name as tag_name
FROM projects p
JOIN project_tags pt ON p.id = pt.project_id
JOIN tags t ON pt.tag_id = t.id
WHERE p.owner_id = 5;
```

### Relational Algebra

```
π id, title, name (
    σ owner_id = 5 (
        projects ⋈ id = project_id project_tags ⋈ tag_id = id tags
    )
)
```

**Optimized form (selection pushed down):**
```
π id, title, name (
    (σ owner_id = 5 projects) ⋈ id = project_id project_tags ⋈ tag_id = id tags
)
```

### Join Strategy Analysis

| Join | Left Table | Right Table | Strategy |
|:---|:---|:---|:---|
| projects ⋈ project_tags | Small (filtered) | Medium | Nested Loop + Index |
| result ⋈ tags | Small | Small | Nested Loop + Index |

---

## Query 4: User Transaction History with All Details

### SQL
```sql
SELECT u.wallet, t.tx_hash, t.amount, p.title, tg.name as tag
FROM users u
JOIN transactions t ON u.id = t.user_id
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN tags tg ON t.tag_id = tg.id
WHERE u.wallet = '0x123...';
```

### Relational Algebra

```
π wallet, tx_hash, amount, title, name (
    (σ wallet = '0x123...' users) 
    ⋈ id = user_id transactions 
    ⟕ project_id = id projects 
    ⟕ tag_id = id tags
)
```

### Join Order Optimization

1. Start with most selective operation: `σ wallet = '0x123...' users` (returns 1 row)
2. Join with transactions using index on user_id
3. Left join with projects (may have nulls)
4. Left join with tags (may have nulls)

**Estimated cardinality at each step:**
```
users (filtered)     →  1 row
⋈ transactions       →  ~50 rows (avg per user)
⟕ projects          →  ~50 rows (preserved)
⟕ tags              →  ~50 rows (preserved)
```

---

## Join Strategy Summary

| Scenario | Recommended Join | Reason |
|:---|:---|:---|
| Small × Large with index | Nested Loop | Index lookup efficient |
| Large × Large, no index | Hash Join | O(n+m) vs O(n×m) |
| Pre-sorted data | Merge Join | Already ordered |
| Aggregation queries | Hash Join | Build once, probe all |

---

## Index Utilization in Relational Algebra

Selection operations benefit from indexes:

```
σ user_id = 123 (transactions)
```

**Without index:** Full table scan O(n)
**With index on user_id:** Index scan O(log n) + fetch

The composite index `(user_id, created_at)` supports:
```
σ user_id = 123 ∧ created_at > '2024-01-01' (transactions)
```

This is a **covering index** for queries that only need user_id and created_at.
