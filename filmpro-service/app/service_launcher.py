"""
Service launcher for setting up the application.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db, close_db
from app.core.logging import configure_logging

logger = logging.getLogger("filmpro")


async def startup_db_client(app: FastAPI):
    """
    Initialize database connection on application startup.
    """
    app.mongodb_client = await init_db()


async def shutdown_db_client(app: FastAPI):
    """
    Close database connection on application shutdown.
    """
    await close_db(app.mongodb_client)


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.
    """
    # Configure logging
    configure_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        description="FILMPRO Script Analysis Service API",
        version="0.1.0",
        debug=settings.DEBUG
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register startup and shutdown events
    app.add_event_handler("startup", lambda: startup_db_client(app))
    app.add_event_handler("shutdown", lambda: shutdown_db_client(app))
    
    return app