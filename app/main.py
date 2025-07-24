import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from app.core.config import get_settings
from app.core.database import init_db
from app.api.endpoints import upload, process, insights
from app.api.endpoints import websocket  

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    init_db()
    logger.info("Application started successfully")
    yield
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(
    title="AI Insights Platform",
    description="Upload datasets, generate AI insights with real-time updates via WebSocket",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "message": "AI Insights Platform is running"}

# routers
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(process.router, prefix="/api/v1", tags=["Process"])
app.include_router(insights.router, prefix="/api/v1", tags=["Insights"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])  
