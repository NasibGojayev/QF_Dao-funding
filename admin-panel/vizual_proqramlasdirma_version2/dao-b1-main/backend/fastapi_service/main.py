from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel
import logging
import os
import asyncio
import strawberry
from strawberry.fastapi import GraphQLRouter
from jsonrpcserver import method, async_dispatch as dispatch


logger = logging.getLogger("fastapi_service")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="DAO Indexer Service")
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TXResponse(BaseModel):
    hash: str
    status: str
    block_number: int | None = None


@app.get('/api/history')
async def history():
    logger.info("/api/history requested")
    # Return a mock history — replace with DB/indexer queries
    return [{"hash": "0xabc123", "status": "confirmed", "block": 12345}]


@app.get('/api/tx/{tx_hash}', response_model=TXResponse)
async def tx_detail(tx_hash: str):
    logger.info(f"/api/tx/{tx_hash} requested")
    # Mock response
    return TXResponse(hash=tx_hash, status="confirmed", block_number=12345)


def admin_token_auth(token: str | None = None):
    expected = os.environ.get('ADMIN_TOKEN', 'dev-token')
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    return True


class ResolveRequest(BaseModel):
    id: int
    action: str


@app.post('/admin/resolve')
async def admin_resolve(req: ResolveRequest, authorized: bool = Depends(admin_token_auth)):
    logger.info(f"admin.resolve called for id={req.id} action={req.action}")
    # Placeholder — implement real logic
    return {"ok": True, "id": req.id, "action": req.action}




@method
def echo(msg: str) -> str:
    return msg


@app.post('/json-rpc')
async def json_rpc_endpoint(request: Request):
    request_text = await request.body()
    response = await dispatch(request_text.decode())
    return response


# WebSocket events broadcaster (mock)
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: str):
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()


@app.websocket('/ws/events')
async def ws_events(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; in a real system we'd push events
            data = await ws.receive_text()
            await manager.broadcast(f"echo:{data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)


# GraphQL stub using Strawberry
@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello from GraphQL"


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# Background task sending heartbeat events to websockets (demo)
@app.on_event('startup')
async def startup_event():
    async def heartbeat():
        while True:
            await manager.broadcast('heartbeat')
            await asyncio.sleep(10)

    asyncio.create_task(heartbeat())
