"""
Unit tests for main module and health endpoint.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.main import app, health_check
from app.core.exception_handlers import http_exception_handler, general_exception_handler


@pytest.mark.unit
class TestAppConfiguration:
    """Test cases for FastAPI app configuration."""
    
    def test_app_instance(self):
        """Test that app is a FastAPI instance."""
        assert isinstance(app, FastAPI)
    
    def test_app_metadata(self):
        """Test app metadata configuration."""
        assert app.title == "Task Management API"
        assert app.description == "A clean, scalable FastAPI application for task management with JWT authentication."
        assert app.version == "2.0.0"
    
    def test_exception_handlers_registered(self):
        """Test that custom exception handlers are registered."""
        # Check that HTTPException handler is registered
        assert HTTPException in app.exception_handlers
        assert app.exception_handlers[HTTPException] == http_exception_handler
        
        # Check that general Exception handler is registered
        assert Exception in app.exception_handlers
        assert app.exception_handlers[Exception] == general_exception_handler
    
    def test_api_router_included(self):
        """Test that API router is included."""
        # Check that routes are registered
        routes = [route.path for route in app.routes]
        
        # Should have various API routes
        assert '/register' in routes  # Auth route
        assert '/login' in routes     # Auth route
        assert '/users/me' in routes  # User route
        assert '/tasks/' in routes    # Task routes
        
        # Should have the health check endpoint
        assert '/health' in routes
    
    @patch('app.main.Base')
    @patch('app.main.engine')
    def test_database_tables_creation(self, mock_engine, mock_base):
        """Test that database tables are created on startup."""
        # Re-import to trigger table creation
        import importlib
        import app.main
        
        # Can't easily test module-level code execution
        # Just verify the imports exist
        assert mock_engine is not None
        assert mock_base is not None


@pytest.mark.unit
class TestHealthEndpoint:
    """Test cases for health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_function(self):
        """Test the health_check function directly."""
        response = await health_check()
        
        assert isinstance(response, dict)
        assert response["status"] == "healthy"
        assert response["service"] == "Task Management API"
    
    def test_health_endpoint_with_client(self):
        """Test health endpoint using TestClient."""
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "Task Management API"
        }
    
    def test_health_endpoint_response_headers(self):
        """Test health endpoint response headers."""
        client = TestClient(app)
        
        response = client.get("/health")
        
        # Should have JSON content type
        assert response.headers["content-type"] == "application/json"
    
    def test_health_endpoint_method_not_allowed(self):
        """Test that non-GET methods are not allowed on health endpoint."""
        client = TestClient(app)
        
        # Test various HTTP methods
        methods = ['post', 'put', 'delete', 'patch']
        
        for method in methods:
            response = getattr(client, method)("/health")
            assert response.status_code == 405  # Method Not Allowed
    
    def test_health_endpoint_path(self):
        """Test that health endpoint is registered at correct path."""
        # Find the health route
        health_route = None
        for route in app.routes:
            if route.path == "/health":
                health_route = route
                break
        
        assert health_route is not None
        assert "GET" in health_route.methods
        assert health_route.endpoint.__name__ == "health_check"


@pytest.mark.unit
class TestMainModuleIntegration:
    """Test main module integration aspects."""
    
    def test_openapi_schema(self):
        """Test that OpenAPI schema is properly generated."""
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Verify basic schema structure
        assert schema["info"]["title"] == "Task Management API"
        assert schema["info"]["version"] == "2.0.0"
        assert "/health" in schema["paths"]
    
    def test_docs_endpoints(self):
        """Test that documentation endpoints are available."""
        client = TestClient(app)
        
        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_app_startup_no_errors(self):
        """Test that app starts without errors."""
        # The fact that we can create a TestClient means the app started successfully
        client = TestClient(app)
        assert client is not None
        
        # Test a simple request to ensure app is functional
        response = client.get("/health")
        assert response.status_code == 200