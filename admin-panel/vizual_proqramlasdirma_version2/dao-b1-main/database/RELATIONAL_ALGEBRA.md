# Relational Algebra Review
# ==========================
# SQL to relational algebra translations with join analysis

## Notation Reference

| Symbol | Operation     | SQL Equivalent |
|--------|---------------|----------------|
| σ      | Selection     | WHERE          |
| π      | Projection    | SELECT columns |
| ⋈      | Natural Join  | JOIN ON        |
| ⟕      | Left Join     | LEFT JOIN      |
| γ      | Aggregation   | GROUP BY       |

---

## Query 1: User Transaction History

### SQL
```sql
SELECT t.tx_hash, t.amount, t.created_at, p.title
FROM transactions t
LEFT JOIN projects p ON t.project_id = p.id
WHERE t.user_id = 123
ORDER BY t.created_at DESC
LIMIT 50;
```

### Relational Algebra
```
π_{tx_hash, amount, created_at, title} (
    σ_{user_id = 123} (
        transactions ⟕_{project_id = id} projects
    )
)
```

### Optimized Form (Push Selection Down)
```
π_{tx_hash, amount, created_at, title} (
    (σ_{user_id = 123} transactions) ⟕_{project_id = id} projects
)
```

### Join Strategy
- **Nested Loop with Index Lookup**
- Outer: Index scan on ix_transactions_user_created
- Inner: PK lookup on projects

---

## Query 2: Dashboard Summary

### SQL
```sql
SELECT tag_name, SUM(total_amount), COUNT(*)
FROM mv_tx_summary_by_tag
WHERE day >= '2024-01-01'
GROUP BY tag_name;
```

### Relational Algebra
```
γ_{tag_name; SUM(total_amount), COUNT(*)} (
    σ_{day >= '2024-01-01'} (mv_tx_summary_by_tag)
)
```

### Why Materialized View
Original aggregation:
```
γ_{day, tag_name; COUNT(*), SUM(amount)} (
    transactions ⟕_{tag_id = id} tags
)
```
- Without MV: Hash Join + GroupAggregate (100+ ms)
- With MV: Simple scan (< 1 ms)

---

## Query 3: Projects with Tags (Many-to-Many)

### SQL
```sql
SELECT p.title, array_agg(t.name)
FROM projects p
JOIN project_tags pt ON p.id = pt.project_id
JOIN tags t ON pt.tag_id = t.id
WHERE p.owner_id = 1
GROUP BY p.id, p.title;
```

### Relational Algebra
```
γ_{id, title; array_agg(name)} (
    (σ_{owner_id = 1} projects) 
    ⋈_{id = project_id} project_tags 
    ⋈_{tag_id = id} tags
)
```

### Join Order Optimization
1. Filter projects first (smallest result set)
2. Join with project_tags using index
3. Join with tags using index

---

## Join Strategy Comparison

| Scenario                  | Strategy     | When Used                    |
|---------------------------|--------------|------------------------------|
| Small × Large + Index     | Nested Loop  | User transaction lookup      |
| Large × Large             | Hash Join    | Full aggregations            |
| Pre-sorted data           | Merge Join   | Time-series with ORDER BY    |
| Aggregation queries       | Hash Agg     | GROUP BY operations          |

---

## Index Impact on Selection

```
σ_{user_id = 123} (transactions)
```

| Scenario       | Plan          | Complexity |
|----------------|---------------|------------|
| Without index  | Seq Scan      | O(n)       |
| With index     | Index Scan    | O(log n)   |

Composite index `(user_id, created_at)` enables:
```
σ_{user_id = 123 ∧ created_at > '2024-01-01'} (transactions)
```
To use a single index scan covering both conditions.
