from fastapi import APIRouter

from app.api.v1 import auth, jobs, visits, websocket

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(visits.router, tags=["visits"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(websocket.router, tags=["websocket"])

