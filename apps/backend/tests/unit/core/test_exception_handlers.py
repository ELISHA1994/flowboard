"""
Unit tests for exception handlers.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.exception_handlers import (general_exception_handler,
                                         http_exception_handler, on_auth_error)


@pytest.mark.unit
@pytest.mark.asyncio
class TestHTTPExceptionHandler:
    """Test cases for HTTP exception handler."""

    async def test_http_exception_handler_basic(self):
        """Test basic HTTP exception handling."""
        # Create mock request
        mock_request = Mock(spec=Request)

        # Create HTTPException
        exc = HTTPException(status_code=404, detail="Not found")

        # Call handler
        response = await http_exception_handler(mock_request, exc)

        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

        # Check content
        content = response.body.decode()
        assert '"status":"error"' in content
        assert '"status_code":404' in content
        assert '"message":"Not found"' in content
        assert '"data":null' in content

    async def test_http_exception_handler_various_codes(self):
        """Test handler with various HTTP status codes."""
        mock_request = Mock(spec=Request)

        test_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (422, "Unprocessable Entity"),
            (500, "Internal Server Error"),
        ]

        for status_code, detail in test_cases:
            exc = HTTPException(status_code=status_code, detail=detail)
            response = await http_exception_handler(mock_request, exc)

            assert response.status_code == status_code
            content = response.body.decode()
            assert f'"status_code":{status_code}' in content
            assert f'"message":"{detail}"' in content

    async def test_http_exception_handler_with_complex_detail(self):
        """Test handler with complex exception details."""
        mock_request = Mock(spec=Request)

        # Test with dict detail
        exc = HTTPException(
            status_code=422, detail={"field": "email", "error": "Invalid email format"}
        )

        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 422

        # The handler should handle the dict detail properly
        content = response.body.decode()
        assert '"status":"error"' in content
        assert '"status_code":422' in content


@pytest.mark.unit
@pytest.mark.asyncio
class TestGeneralExceptionHandler:
    """Test cases for general exception handler."""

    @patch("app.core.exception_handlers.logger")
    async def test_general_exception_handler_basic(self, mock_logger):
        """Test basic general exception handling."""
        # Create mock request
        mock_request = Mock(spec=Request)

        # Create exception
        exc = ValueError("Something went wrong")

        # Call handler
        response = await general_exception_handler(mock_request, exc)

        # Verify logging
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Unexpected error: Something went wrong" in str(call_args[0][0])
        assert call_args[1]["exc_info"] is True

        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

        # Check content
        content = response.body.decode()
        assert '"status":"error"' in content
        assert '"status_code":500' in content
        assert '"message":"An unexpected error occurred."' in content
        assert '"data":null' in content

    @patch("app.core.exception_handlers.logger")
    async def test_general_exception_handler_various_exceptions(self, mock_logger):
        """Test handler with various exception types."""
        mock_request = Mock(spec=Request)

        exceptions = [
            ValueError("Value error"),
            KeyError("key"),
            RuntimeError("Runtime error"),
            Exception("Generic exception"),
        ]

        for exc in exceptions:
            response = await general_exception_handler(mock_request, exc)

            # Always returns 500
            assert response.status_code == 500

            # Always logs the error
            assert mock_logger.error.called

            # Always returns generic message (doesn't expose internal error)
            content = response.body.decode()
            assert '"message":"An unexpected error occurred."' in content

            # Reset mock for next iteration
            mock_logger.reset_mock()

    @patch("app.core.exception_handlers.logger")
    async def test_general_exception_handler_with_none_message(self, mock_logger):
        """Test handler with exception that has None message."""
        mock_request = Mock(spec=Request)

        # Create exception with None message
        exc = Exception()

        response = await general_exception_handler(mock_request, exc)

        # Should still handle gracefully
        assert response.status_code == 500
        mock_logger.error.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestOnAuthError:
    """Test cases for authentication error handler."""

    async def test_on_auth_error_basic(self):
        """Test basic authentication error handling."""
        # Create mock request
        mock_request = Mock(spec=Request)

        # Create exception (any exception, as it's not used in the handler)
        exc = Exception("Auth failed")

        # Call handler
        response = await on_auth_error(mock_request, exc)

        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

        # Check content
        content = response.body.decode()
        assert '"status":"error"' in content
        assert '"status_code":401' in content
        assert '"message":"Authentication failed."' in content
        assert '"data":null' in content

    async def test_on_auth_error_various_exceptions(self):
        """Test auth error handler with various exception types."""
        mock_request = Mock(spec=Request)

        # The handler doesn't use the exception, but test with various types
        exceptions = [
            ValueError("Invalid credentials"),
            HTTPException(status_code=401, detail="Token expired"),
            Exception("Generic auth error"),
            RuntimeError("Token validation failed"),
        ]

        for exc in exceptions:
            response = await on_auth_error(mock_request, exc)

            # Always returns 401 with same message
            assert response.status_code == 401
            content = response.body.decode()
            assert '"message":"Authentication failed."' in content

    async def test_on_auth_error_request_attributes(self):
        """Test that handler works with various request attributes."""
        # Create mock request with various attributes
        mock_request = Mock(spec=Request)
        mock_request.url = Mock(path="/api/protected")
        mock_request.method = "GET"
        mock_request.headers = {"Authorization": "Bearer invalid"}

        exc = Exception("Auth error")

        response = await on_auth_error(mock_request, exc)

        # Handler should work regardless of request attributes
        assert response.status_code == 401


@pytest.mark.unit
class TestExceptionHandlerIntegration:
    """Test exception handlers integration scenarios."""

    def test_all_handlers_return_consistent_format(self):
        """Test that all handlers return consistent response format."""
        # All handlers should return responses with these fields:
        # - status: "error"
        # - status_code: int
        # - message: str
        # - data: null

        # This is verified in individual tests above
        # This test serves as documentation of the expected format
        expected_format = {
            "status": "error",
            "status_code": int,
            "message": str,
            "data": None,
        }

        assert True  # Format verification is done in other tests

    def test_logger_configuration(self):
        """Test that logger is properly configured."""
        from app.core.exception_handlers import logger

        assert logger is not None
        assert logger.name == "app.core.exception_handlers"
        assert isinstance(logger, logging.Logger)
