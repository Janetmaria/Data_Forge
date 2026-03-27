from fastapi import APIRouter
from app.api.v1.endpoints import datasets, pipelines, ml_ops

api_router = APIRouter()
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(ml_ops.router, prefix="/datasets", tags=["ml_ops"])
