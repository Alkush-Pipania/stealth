from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.api.v1.router import api_router
from app.config import settings
from app.core.events import shutdown_handler, startup_handler


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_handler(app)
    yield
    await shutdown_handler(app)

app = FastAPI(
    title= settings.PROJECT_NAME,
    description= "Stealth API",
    version= settings.VERSION,
    docs_url= "/api/docs",
    redoc_url= "/api/redoc",
    openapi_url= "/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


# Include routers (THIS IS HOW YOU CONNECT ENDPOINTS!)
app.include_router(
    api_router,                    # Your router object
    prefix="/api/v1",              # URL prefix for all routes in this router
    tags=["v1"]                    # OpenAPI tag
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # Add actual checks
        "redis": "connected"
    }


