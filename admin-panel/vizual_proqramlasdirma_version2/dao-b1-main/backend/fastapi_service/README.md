# FastAPI microservice

This service provides lightweight APIs, WebSocket events, a GraphQL endpoint, and a JSON-RPC stub for the DAO project indexer and admin features.

Quick start (PowerShell):

```powershell
# from repo root
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend/fastapi_service
uvicorn main:app --reload --port 8001
```

Endpoints:
- `GET /api/history` — returns mock transaction history
- `GET /api/tx/{hash}` — returns mock tx details
- `POST /admin/resolve` — admin-only stub (token-based)
- `GET /graphql` — GraphQL explorer (GraphiQL)
- `ws://localhost:8001/ws/events` — WebSocket events stream
- `POST /json-rpc` — JSON-RPC endpoint stub
