# Index Documentation

This document details all database indexes, their SQL definitions, and justifications for their creation.

---

## Index Summary

| Index Name | Table | Columns | Type | Purpose |
|:---|:---|:---|:---|:---|
| `ix_users_wallet` | users | wallet | Unique B-Tree | Wallet address lookups |
| `ix_projects_owner` | projects | owner_id | B-Tree | Projects by owner |
| `ix_transactions_txhash` | transactions | tx_hash | Unique B-Tree | Transaction lookup by hash |
| `ix_transactions_user_id` | transactions | user_id | B-Tree | User's transactions |
| `ix_transactions_project_id` | transactions | project_id | B-Tree | Project's donations |
| `ix_transactions_created_at` | transactions | created_at | B-Tree | Time-based queries |
| `ix_transactions_user_created` | transactions | (user_id, created_at) | Composite | User history ordered |
| `ix_transactions_project_created` | transactions | (project_id, created_at) | Composite | Project history ordered |
| `ix_transactions_tag` | transactions | tag_id | B-Tree | Filter by tag |
| `ix_milestones_project` | milestones | project_id | B-Tree | Project milestones |
| `ix_project_tags_project` | project_tags | project_id | B-Tree | Tags for project |
| `ix_project_tags_tag` | project_tags | tag_id | B-Tree | Projects with tag |

---

## SQL CREATE INDEX Statements

### Users Table

```sql
-- Wallet address lookup (Web3 authentication)
CREATE UNIQUE INDEX ix_users_wallet ON users(wallet);
```

**Justification:** Every Web3 login requires finding user by wallet address. Unique constraint also enforces data integrity.

---

### Projects Table

```sql
-- Find all projects owned by a user
CREATE INDEX ix_projects_owner ON projects(owner_id);
```

**Justification:** Dashboard shows "My Projects" list, filtering by owner_id.

---

### Transactions Table

```sql
-- Lookup transaction by blockchain hash (idempotent indexer writes)
CREATE UNIQUE INDEX ix_transactions_txhash ON transactions(tx_hash);

-- User's transaction history
CREATE INDEX ix_transactions_user_id ON transactions(user_id);

-- Project donation history
CREATE INDEX ix_transactions_project_id ON transactions(project_id);

-- Time-series queries (recent activity, dashboards)
CREATE INDEX ix_transactions_created_at ON transactions(created_at);

-- Filter transactions by tag
CREATE INDEX ix_transactions_tag ON transactions(tag_id);

-- COMPOSITE: User's transactions ordered by time (hot path!)
CREATE INDEX ix_transactions_user_created ON transactions(user_id, created_at DESC);

-- COMPOSITE: Project's transactions ordered by time
CREATE INDEX ix_transactions_project_created ON transactions(project_id, created_at DESC);
```

**Justification for Composite Indexes:**

The composite index `(user_id, created_at)` supports this common query pattern:
```sql
SELECT * FROM transactions 
WHERE user_id = ? 
ORDER BY created_at DESC 
LIMIT 50;
```

Without composite index: 
- Index scan on user_id → fetch rows → sort by created_at

With composite index:
- Single index scan returns data already sorted → no additional sort step

---

### Milestones Table

```sql
-- Get all milestones for a project
CREATE INDEX ix_milestones_project ON milestones(project_id);
```

**Justification:** Project detail page shows all milestones.

---

### Project_Tags Table

```sql
-- Get all tags for a project
CREATE INDEX ix_project_tags_project ON project_tags(project_id);

-- Get all projects with a specific tag
CREATE INDEX ix_project_tags_tag ON project_tags(tag_id);

-- Ensure no duplicate tag assignments
CREATE UNIQUE INDEX ix_project_tags_unique ON project_tags(project_id, tag_id);
```

**Justification:** Both navigation patterns are common:
1. Show tags on project page (by project_id)
2. Show projects filtered by tag (by tag_id)

---

## Query Patterns and Index Usage

### Pattern 1: User Authentication
```sql
SELECT * FROM users WHERE wallet = '0x...';
-- Uses: ix_users_wallet (index-only scan)
```

### Pattern 2: User Transaction History
```sql
SELECT * FROM transactions 
WHERE user_id = 123 
ORDER BY created_at DESC LIMIT 50;
-- Uses: ix_transactions_user_created (sorted index scan)
```

### Pattern 3: Idempotent Event Processing
```sql
SELECT id FROM transactions WHERE tx_hash = '0xabc...';
-- Uses: ix_transactions_txhash (unique lookup)
```

### Pattern 4: Dashboard Aggregation
```sql
SELECT tag_id, COUNT(*), SUM(amount) 
FROM transactions 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY tag_id;
-- Uses: ix_transactions_created_at + ix_transactions_tag
```

---

## Partial Index Recommendations (PostgreSQL)

For frequently filtered conditions, consider partial indexes:

```sql
-- Only successful transactions (most queries filter on success=true)
CREATE INDEX ix_transactions_success_true ON transactions(user_id, created_at) 
WHERE success = true;

-- Only unresolved milestones
CREATE INDEX ix_milestones_unresolved ON milestones(project_id) 
WHERE resolved = false;
```

---

## Index Maintenance Notes

1. **ANALYZE**: Run after bulk imports to update statistics
   ```sql
   ANALYZE transactions;
   ```

2. **REINDEX**: Rebuild fragmented indexes periodically
   ```sql
   REINDEX INDEX ix_transactions_user_created;
   ```

3. **Monitor**: Use `pg_stat_user_indexes` to track usage
   ```sql
   SELECT indexrelname, idx_scan, idx_tup_read 
   FROM pg_stat_user_indexes 
   WHERE schemaname = 'public';
   ```
