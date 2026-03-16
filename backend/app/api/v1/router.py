from fastapi import APIRouter
from app.api.v1 import auth, visits, jobs

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(visits.router, tags=["visits"])
api_router.include_router(jobs.router, tags=["jobs"])

