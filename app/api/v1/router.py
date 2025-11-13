from fastapi import APIRouter
from app.api.v1.endpoints import user, graph_rag

api_router = APIRouter()

api_router.include_router(
    user.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    graph_rag.router,
    prefix="/graph-rag",
    tags=["Graph RAG"]
)