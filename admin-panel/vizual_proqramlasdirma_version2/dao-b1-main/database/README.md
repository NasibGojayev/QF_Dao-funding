# DAO Database Module

PostgreSQL database implementation for the Quadratic Funding DAO platform.

## Structure

```
database/
├── config.py           # Database connection settings
├── models.py           # SQLAlchemy ORM models
├── schema.sql          # Full DDL schema
├── indexes.sql         # All index definitions
├── materialized_views.sql  # Materialized views
├── seed_data.py        # Seed data script
├── queries.py          # Common query functions
├── explain_analysis.sql    # EXPLAIN plan queries
├── alembic/            # Migrations
│   ├── env.py
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_indexes.py
│   │   └── 003_materialized_views.py
└── requirements.txt    # Python dependencies
```

## Setup

1. Install PostgreSQL and create database:
```bash
createdb dao_db
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure connection in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dao_db
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Seed data:
```bash
python seed_data.py
```

## Quick Test
```bash
python -c "from config import engine; print(engine.connect())"
```
