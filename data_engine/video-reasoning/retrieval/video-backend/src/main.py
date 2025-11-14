"""
Video Reasoning Backend - Main FastAPI Application
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import get_settings
from src.api.v1 import auth, search, videos, config, streaming, frontend_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for video reasoning with semantic search",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["streaming"])
app.include_router(frontend_config.router, prefix="/api/v1/frontend", tags=["frontend"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f"{settings.app_name} v{settings.app_version} starting up")
    logger.info(f"VastDB endpoint: {settings.vdb_endpoint}")
    logger.info(f"VastDB collection: {settings.vdb_bucket}/{settings.vdb_schema}/{settings.vdb_collection}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    
    if settings.dev_mode:
        logger.warning("DEV MODE ENABLED - Authentication bypass active!")
    
    logger.info("Application ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Application shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

