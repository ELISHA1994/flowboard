"""
Unit tests for db_instance module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from app.db import db_instance
from app.db.database import get_db as original_get_db


@pytest.mark.unit
class TestDbInstance:
    """Test cases for db_instance module."""
    
    def test_get_db_is_reexported(self):
        """Test that get_db is correctly re-exported from database module."""
        # Verify get_db is the same function as the original
        assert db_instance.get_db is original_get_db
        assert db_instance.get_db.__name__ == original_get_db.__name__
        assert db_instance.get_db.__module__ == original_get_db.__module__
    
    def test_get_postgres_connector_returns_get_db(self):
        """Test that get_postgres_connector returns the get_db function."""
        connector = db_instance.get_postgres_connector()
        assert connector is db_instance.get_db
        assert connector is original_get_db
    
    @patch('app.db.database.SessionLocal')
    def test_get_db_generator_behavior(self, mock_session_local):
        """Test the generator behavior of get_db."""
        # Mock the session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Get the generator
        gen = db_instance.get_db()
        
        # Get the session
        session = next(gen)
        assert session is mock_session
        mock_session_local.assert_called_once()
        
        # Ensure close is called when generator is closed
        try:
            next(gen)
        except StopIteration:
            pass
        
        mock_session.close.assert_called_once()
    
    @patch('app.db.database.SessionLocal')
    def test_get_db_generator_exception_handling(self, mock_session_local):
        """Test that get_db closes session even on exception."""
        # Mock the session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Get the generator
        gen = db_instance.get_db()
        
        # Get the session
        session = next(gen)
        assert session is mock_session
        
        # Simulate an exception during usage
        try:
            gen.throw(ValueError("Test exception"))
        except ValueError:
            pass
        
        # Ensure close is still called
        mock_session.close.assert_called_once()
    
    @patch('app.db.database.SessionLocal')
    def test_get_postgres_connector_usage(self, mock_session_local):
        """Test using get_postgres_connector as a dependency."""
        # Mock the session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Get the connector function
        connector = db_instance.get_postgres_connector()
        
        # Use it as a generator
        gen = connector()
        session = next(gen)
        
        assert session is mock_session
        mock_session_local.assert_called_once()
        
        # Clean up
        try:
            next(gen)
        except StopIteration:
            pass
        
        mock_session.close.assert_called_once()
    
    def test_module_attributes(self):
        """Test that expected module attributes exist."""
        # Check that main functions are exposed
        assert hasattr(db_instance, 'get_db')
        assert hasattr(db_instance, 'get_postgres_connector')
        
        # Check that they are callable
        assert callable(db_instance.get_db)
        assert callable(db_instance.get_postgres_connector)
    
    def test_get_postgres_connector_docstring(self):
        """Test that get_postgres_connector has proper documentation."""
        assert db_instance.get_postgres_connector.__doc__ is not None
        assert "compatibility" in db_instance.get_postgres_connector.__doc__
        assert "SQLite" in db_instance.get_postgres_connector.__doc__
    
    @patch('app.db.database.SessionLocal')
    def test_multiple_get_db_calls(self, mock_session_local):
        """Test that multiple calls to get_db create separate sessions."""
        # Mock sessions
        mock_session1 = Mock(spec=Session)
        mock_session2 = Mock(spec=Session)
        mock_session_local.side_effect = [mock_session1, mock_session2]
        
        # Get two generators
        gen1 = db_instance.get_db()
        gen2 = db_instance.get_db()
        
        # Get sessions
        session1 = next(gen1)
        session2 = next(gen2)
        
        # Verify they are different sessions
        assert session1 is mock_session1
        assert session2 is mock_session2
        assert session1 is not session2
        
        # Clean up both
        for gen in [gen1, gen2]:
            try:
                next(gen)
            except StopIteration:
                pass
        
        # Both should be closed
        mock_session1.close.assert_called_once()
        mock_session2.close.assert_called_once()