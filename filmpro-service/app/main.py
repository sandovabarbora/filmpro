"""
Main application entry point for the FILMPRO script analysis service.
"""
import time
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.endpoints import scripts, breakdowns, auth
from app.core.logging import configure_logging
from app.service_launcher import create_application

# Create FastAPI application
app = create_application()

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0", "service": settings.APP_NAME}

# Include API routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["authentication"]
)

app.include_router(
    scripts.router,
    prefix=f"{settings.API_V1_PREFIX}/scripts",
    tags=["scripts"]
)

app.include_router(
    breakdowns.router,
    prefix=f"{settings.API_V1_PREFIX}/breakdowns",
    tags=["breakdowns"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger = configure_logging()
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)