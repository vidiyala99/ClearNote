import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.middleware.clerk_auth import ClerkAuthMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.api.v1.websocket import manager

    redis_listener = asyncio.create_task(manager.listen_to_redis())
    try:
        yield
    finally:
        redis_listener.cancel()
        with suppress(asyncio.CancelledError):
            await redis_listener


app = FastAPI(title="ClearNote API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    ClerkAuthMiddleware,
    jwks_url=settings.clerk_jwks_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
