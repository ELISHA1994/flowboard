import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "status_code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "status_code": 500,
            "message": "An unexpected error occurred.",
            "data": None,
        },
    )


async def on_auth_error(request: Request, exc: Exception):
    """Handle authentication errors"""
    return JSONResponse(
        status_code=401,
        content={
            "status": "error",
            "status_code": 401,
            "message": "Authentication failed.",
            "data": None,
        },
    )
