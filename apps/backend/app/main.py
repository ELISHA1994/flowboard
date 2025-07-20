from fastapi import FastAPI, HTTPException
from app.api.main import api_router
from app.core.exception_handlers import (
    http_exception_handler,
    general_exception_handler,
)
from app.db.database import engine
from app.db.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Task Management API",
    description="A clean, scalable FastAPI application for task management with JWT authentication.",
    version="2.0.0",
)

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