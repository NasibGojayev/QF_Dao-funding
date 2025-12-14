# Database Architecture Documentation

## Overview

This project uses a **dual-ORM architecture** to separate concerns between the API layer and the analytics/indexer layer.

---

## Architecture Design

### 1. Django ORM (API Layer)

**Location:** `backend/api/models.py`

**Purpose:** Handles the REST API data models for the web application

**Models:**
- `Project` - Project metadata and ownership
- `Round` - Funding round information
- `Grant` - Grant requests and allocations

**Database:** SQLite (development) / PostgreSQL (production recommended)

**Usage:**
```python
from api.models import Project, Round, Grant

# Create a project via Django ORM
project = Project.objects.create(
    title="My Project",
    description="Description",
    owner=request.user
)
```

**Migrations:**
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

---

### 2. SQLAlchemy ORM (Analytics/Indexer Layer)

**Location:** `backend/models.py`

**Purpose:** Handles blockchain event indexing, analytics, and Sprint 2 requirements

**Models:**
- `User` - Extended user profiles with analytics
- `Project` - Detailed project tracking (separate from Django)
- `Transaction` - Blockchain transaction records
- `Tag` - Project categorization
- `Milestone` - Project milestone tracking
- `ProjectTag` - Many-to-many relationship

**Database:** SQLite (same database, different tables)

**Usage:**
```python
from models import User, Transaction, Milestone
from db import SessionLocal

# Use SQLAlchemy for analytics queries
with SessionLocal() as session:
    transactions = session.query(Transaction).filter_by(
        project_id=project_id
    ).all()
```

**Migrations:**
```bash
cd backend
alembic upgrade head
```

---

## Why Two ORMs?

### Separation of Concerns

1. **Django ORM:**
   - Optimized for CRUD operations
   - Integrated with Django REST Framework
   - Handles user authentication and permissions
   - Simple API endpoints

2. **SQLAlchemy:**
   - Better for complex analytics queries
   - Blockchain event indexing
   - Materialized views and advanced SQL
   - Sprint 2/3 data science requirements

### Benefits

- **Modularity:** Each layer can evolve independently
- **Performance:** Use the right tool for each job
- **Flexibility:** SQLAlchemy for complex queries, Django for simple CRUD
- **Sprint Requirements:** Meets both web app and analytics needs

---

## Data Flow

```
Blockchain Events
      ↓
  Indexer (SQLAlchemy)
      ↓
Transaction/Milestone tables
      ↓
Analytics & ML Models
      
      
User Web Requests
      ↓
Django REST API
      ↓
Project/Round/Grant tables
      ↓
Frontend Display
```

---

## Database Schema

### Django Tables (Managed by Django)
- `api_project`
- `api_round`
- `api_grant`
- `auth_user` (Django's built-in)
- `authtoken_token`

### SQLAlchemy Tables (Managed by Alembic)
- `users` (extended profiles)
- `projects` (analytics version)
- `transactions`
- `tags`
- `milestones`
- `project_tags`

---

## Important Notes

> [!WARNING]
> **Avoid Table Name Conflicts**
> 
> Django and SQLAlchemy use different table naming conventions:
> - Django: `app_modelname` (e.g., `api_project`)
> - SQLAlchemy: `modelname` (e.g., `projects`)
> 
> This prevents conflicts when sharing the same database.

> [!IMPORTANT]
> **Migration Management**
> 
> - Django migrations: `python manage.py migrate`
> - SQLAlchemy migrations: `alembic upgrade head`
> 
> Run both to ensure all tables are created.

---

## Production Recommendations

### Database Configuration

For production, use PostgreSQL:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

```python
# db.py (SQLAlchemy)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/dbname')
engine = create_engine(DATABASE_URL)
```

### Connection Pooling

- Django: Built-in connection pooling
- SQLAlchemy: Configure pool size in `create_engine()`

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20
)
```

---

## Querying Best Practices

### When to Use Django ORM

✅ Simple CRUD operations  
✅ User authentication  
✅ REST API endpoints  
✅ Admin panel operations

### When to Use SQLAlchemy

✅ Complex joins and aggregations  
✅ Blockchain event processing  
✅ Analytics and reporting  
✅ Materialized views  
✅ Raw SQL queries

---

## Example: Cross-ORM Query

If you need data from both systems:

```python
from api.models import Project as DjangoProject
from models import Transaction
from db import SessionLocal

# Get project from Django
django_project = DjangoProject.objects.get(id=1)

# Get transactions from SQLAlchemy using project title as reference
with SessionLocal() as session:
    transactions = session.query(Transaction).filter_by(
        project_name=django_project.title
    ).all()
```

---

## Troubleshooting

### Issue: "Table already exists"

**Solution:** One ORM is trying to create a table the other already created.

Check table names don't conflict:
```bash
# List all tables
python manage.py dbshell
.tables  # (SQLite)
\dt      # (PostgreSQL)
```

### Issue: "No such table"

**Solution:** Run migrations for both ORMs:
```bash
python manage.py migrate
alembic upgrade head
```

---

## Summary

| Aspect | Django ORM | SQLAlchemy |
|--------|-----------|------------|
| **Purpose** | API Layer | Analytics Layer |
| **Models** | Project, Round, Grant | User, Transaction, Milestone |
| **Migrations** | Django migrations | Alembic |
| **Use Cases** | CRUD, Auth, API | Analytics, Indexing, ML |
| **Tables** | `api_*` prefix | No prefix |

Both ORMs coexist peacefully by using different table names and serving different purposes.

---

*Last updated: December 8, 2025*
