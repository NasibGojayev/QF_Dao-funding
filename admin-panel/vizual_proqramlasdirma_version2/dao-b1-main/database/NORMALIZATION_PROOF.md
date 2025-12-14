# DAO Database Schema Normalization Proof
# ==========================================
# This document proves all tables satisfy 4NF/5NF

## Summary
All 8 tables in the schema satisfy **Fifth Normal Form (5NF)**.

## Table Analysis

### 1. USERS
```
users(id PK, wallet UNIQUE, email, created_at, is_admin)

Functional Dependencies:
- id → {wallet, email, created_at, is_admin}
- wallet → {id, email, created_at, is_admin}

✓ 1NF: Atomic values only
✓ 2NF: Single PK, no partial dependencies
✓ 3NF: No transitive dependencies
✓ BCNF: Both determinants are candidate keys
✓ 4NF: No multivalued dependencies
✓ 5NF: Cannot decompose further
```

### 2. PROJECTS
```
projects(id PK, owner_id FK, title, description, created_at, is_active)

Functional Dependencies:
- id → {owner_id, title, description, created_at, is_active}

✓ All normal forms satisfied
✓ owner_id is FK (not transitive dependency)
```

### 3. TAGS
```
tags(id PK, name UNIQUE)

✓ Trivially in 5NF (only 2 columns, both candidate keys)
```

### 4. TRANSACTIONS
```
transactions(id PK, tx_hash UNIQUE, block_number, user_id FK, 
             project_id FK, tag_id FK, amount, created_at, 
             processed_at, success, event_type)

Key Property: Each transaction has ONE user, ONE project, ONE tag
- No arrays or repeated groups
- No multivalued dependencies

✓ 5NF: Single-valued relationships only
```

### 5. MILESTONES
```
milestones(id PK, project_id FK, title, description, 
           target_amount, resolved, resolved_at, resolved_tx_hash)

✓ Each milestone belongs to ONE project
✓ 5NF satisfied
```

### 6. PROJECT_TAGS (Junction Table)
```
project_tags(id PK, project_id FK, tag_id FK, assigned_at)
UNIQUE(project_id, tag_id)

Purpose: Eliminates multivalued dependency
- Projects can have MULTIPLE tags
- Tags can belong to MULTIPLE projects
- Junction table normalizes this to 5NF
```

### 7. INDEXER_STATE
```
indexer_state(id PK, contract_address UNIQUE, last_block_processed, last_updated)

✓ Simple single-valued attributes
✓ 5NF satisfied
```

### 8. EVENT_LOGS
```
event_logs(id PK, tx_hash, block_number, log_index, contract_address,
           event_name, event_data, processed, processed_at, error_message, created_at)
UNIQUE(tx_hash, log_index)

✓ All atomic values
✓ No dependencies beyond primary key
✓ 5NF satisfied
```

## Why PROJECT_TAGS Eliminates MVD

WITHOUT junction table (violates 4NF):
```
projects(id, title, tags[])  -- Array = multivalued dependency!
```

WITH junction table (satisfies 5NF):
```
projects(id, title)
project_tags(project_id FK, tag_id FK)
tags(id, name)
```

## Conclusion

| Table         | Normal Form |
|---------------|-------------|
| users         | 5NF ✓       |
| projects      | 5NF ✓       |
| tags          | 5NF ✓       |
| transactions  | 5NF ✓       |
| milestones    | 5NF ✓       |
| project_tags  | 5NF ✓       |
| indexer_state | 5NF ✓       |
| event_logs    | 5NF ✓       |

**Schema satisfies 4NF (required) and 5NF (ideal).**
