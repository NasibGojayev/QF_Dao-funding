# Database Schema Normalization Proof

This document demonstrates that the DAO Quadratic Funding database schema satisfies **Fourth Normal Form (4NF)** and approaches **Fifth Normal Form (5NF)**.

---

## Normalization Prerequisites

| Normal Form | Requirement | Status |
|:---|:---|:---:|
| **1NF** | Atomic values, no repeating groups | ✅ |
| **2NF** | No partial dependencies on composite keys | ✅ |
| **3NF** | No transitive dependencies | ✅ |
| **BCNF** | Every determinant is a candidate key | ✅ |
| **4NF** | No multivalued dependencies | ✅ |
| **5NF** | No join dependencies not implied by candidate keys | ✅ |

---

## Table-by-Table Analysis

### 1. USERS Table

```sql
users(id PK, wallet UNIQUE, email, created_at, is_admin)
```

**Functional Dependencies:**
- `id → wallet, email, created_at, is_admin`
- `wallet → id, email, created_at, is_admin` (wallet is also a candidate key)

**Normalization Proof:**
- **1NF**: All columns are atomic (no arrays, no repeating groups)
- **2NF**: Single-column PK, so no partial dependencies possible
- **3NF**: No transitive dependencies (email, created_at, is_admin all depend directly on id)
- **BCNF**: Both determinants (id, wallet) are candidate keys
- **4NF**: No multivalued dependencies (a user doesn't have independent sets of values)
- **5NF**: No join dependencies; table cannot be decomposed further without loss

✅ **USERS is in 5NF**

---

### 2. PROJECTS Table

```sql
projects(id PK, owner_id FK→users, title, description, created_at)
```

**Functional Dependencies:**
- `id → owner_id, title, description, created_at`

**Normalization Proof:**
- **1NF**: All columns atomic
- **2NF**: Single PK, no partial dependencies
- **3NF**: All non-key attributes depend only on PK (owner_id is a FK, not a transitive dependency)
- **BCNF**: Only determinant is the PK
- **4NF**: No multivalued dependencies
- **5NF**: Cannot be decomposed without loss

✅ **PROJECTS is in 5NF**

---

### 3. TRANSACTIONS Table

```sql
transactions(id PK, tx_hash UNIQUE, user_id FK, project_id FK, amount, created_at, success, tag_id FK)
```

**Functional Dependencies:**
- `id → tx_hash, user_id, project_id, amount, created_at, success, tag_id`
- `tx_hash → id, user_id, project_id, amount, created_at, success, tag_id`

**Normalization Proof:**
- **1NF**: All columns atomic
- **2NF**: Single PK, no partial dependencies
- **3NF**: No transitive dependencies; all attributes depend directly on id
  - `user_id`, `project_id`, `tag_id` are FKs (not transitive, they're direct relationships)
- **BCNF**: Both id and tx_hash are candidate keys, both are determinants
- **4NF**: No multivalued dependencies
  - A transaction has ONE user, ONE project, ONE tag (not independent sets)
- **5NF**: No join dependencies beyond those implied by keys

✅ **TRANSACTIONS is in 5NF**

---

### 4. TAGS Table

```sql
tags(id PK, name UNIQUE)
```

**Functional Dependencies:**
- `id → name`
- `name → id`

**Normalization Proof:**
- **1NF**: Both columns atomic
- **2NF-5NF**: Trivially satisfied (only two columns, both candidate keys)

✅ **TAGS is in 5NF**

---

### 5. MILESTONES Table

```sql
milestones(id PK, project_id FK, title, resolved, resolved_at)
```

**Functional Dependencies:**
- `id → project_id, title, resolved, resolved_at`

**Normalization Proof:**
- **1NF**: All columns atomic
- **2NF**: Single PK
- **3NF**: No transitive dependencies (resolved_at depends on resolved conceptually, but both depend on id functionally)
- **BCNF/4NF/5NF**: Only determinant is PK, no multivalued or join dependencies

✅ **MILESTONES is in 5NF**

---

### 6. PROJECT_TAGS Table (Junction Table)

```sql
project_tags(id PK, project_id FK, tag_id FK, UNIQUE(project_id, tag_id))
```

**Purpose:** Implements many-to-many relationship between Projects and Tags WITHOUT multivalued dependencies.

**Functional Dependencies:**
- `id → project_id, tag_id`
- `(project_id, tag_id) → id` (composite candidate key)

**Normalization Proof:**
- **1NF**: Atomic columns
- **2NF**: No partial dependencies (both FKs depend on full key)
- **3NF**: No transitive dependencies
- **BCNF**: Both id and (project_id, tag_id) are candidate keys
- **4NF**: This table ELIMINATES the multivalued dependency that would exist if tags were stored in projects table
- **5NF**: Pure join table, cannot be decomposed

✅ **PROJECT_TAGS is in 5NF**

---

## Why 4NF Matters for This Schema

**Without PROJECT_TAGS table**, we might have stored tags as:
```sql
projects(id, owner_id, title, tags[])  -- VIOLATES 1NF and 4NF!
```

This would create a **multivalued dependency** where a project independently determines:
1. Its metadata (title, description)
2. Its set of tags

By decomposing into `projects` + `project_tags`, we eliminate this MVD and achieve 4NF.

---

## Conclusion

| Table | Normal Form Achieved |
|:---|:---:|
| users | 5NF |
| projects | 5NF |
| transactions | 5NF |
| tags | 5NF |
| milestones | 5NF |
| project_tags | 5NF |

**All tables satisfy 4NF (required) and 5NF (ideal).**

The schema avoids:
- ❌ Repeating groups
- ❌ Partial dependencies
- ❌ Transitive dependencies  
- ❌ Multivalued dependencies
- ❌ Join dependencies not implied by candidate keys
