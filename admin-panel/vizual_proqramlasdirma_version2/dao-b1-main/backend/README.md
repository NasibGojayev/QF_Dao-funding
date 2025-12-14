# Django backend (minimal scaffold)

This folder contains a minimal Django REST API scaffold for the DAO frontend.

Quick start:

1. Create and activate a Python venv (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run migrations and start server:

```powershell
python manage.py migrate
python manage.py runserver
```

This scaffold uses SQLite for simplicity. Add environment variables for production.

FastAPI microservice
---------------------

There is also a FastAPI microservice scaffold at `backend/fastapi_service` which provides lightweight APIs, a GraphQL endpoint, WebSocket events, and a JSON-RPC stub useful for indexer/admin features.

Start FastAPI service:

```powershell
cd backend/fastapi_service
uvicorn main:app --reload --port 8001
```

