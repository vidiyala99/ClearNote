from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.middleware.clerk_auth import ClerkAuthMiddleware

app = FastAPI(title="ClearNote API", version="0.1.0")

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

