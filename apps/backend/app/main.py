from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.main import api_router
from app.core.exception_handlers import (
    http_exception_handler,
    general_exception_handler,
)
from app.db.database import engine
from app.db.models import Base
from app.core.logging import logger
import time

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Task Management API",
    description="A clean, scalable FastAPI application for task management with JWT authentication.",
    version="2.0.0",
)

# Configure CORS - must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"🔵 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    return response

# Register custom exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include the API router
app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Task Management API"}