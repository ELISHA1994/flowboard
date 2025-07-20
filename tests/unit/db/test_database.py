"""
Unit tests for database module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from app.db import database


@pytest.mark.unit
class TestDatabaseConfiguration:
    """Test cases for database configuration."""
    
    def test_database_url_configuration(self):
        """Test that database URL is correctly configured."""
        from app.core.config import settings
        # Should work with both SQLite and PostgreSQL
        assert settings.DATABASE_URL is not None
        assert any(db_type in settings.DATABASE_URL for db_type in ["sqlite", "postgresql", "mysql"])
        # In production, we use PostgreSQL
        if "postgresql" in settings.DATABASE_URL:
            assert "taskmanager" in settings.DATABASE_URL
    
    def test_engine_configuration(self):
        """Test that engine is correctly configured."""
        # Verify engine exists
        assert hasattr(database, 'engine')
        assert database.engine is not None
        
        # Verify it's an SQLAlchemy engine
        assert hasattr(database.engine, 'connect')
        assert hasattr(database.engine, 'dispose')
        assert hasattr(database.engine, 'url')
        
        # Verify database driver is correctly configured
        from app.core.config import settings
        if "postgresql" in settings.DATABASE_URL:
            assert database.engine.url.drivername in ['postgresql', 'postgresql+psycopg2']
        elif "sqlite" in settings.DATABASE_URL:
            assert database.engine.url.drivername == 'sqlite'
    
    def test_session_local_configuration(self):
        """Test that SessionLocal is correctly configured."""
        # Verify SessionLocal exists
        assert hasattr(database, 'SessionLocal')
        assert database.SessionLocal is not None
        
        # Verify it's a sessionmaker
        assert hasattr(database.SessionLocal, '__call__')
        
        # Create a session and verify configuration
        session = database.SessionLocal()
        try:
            assert isinstance(session, Session)
            # In SQLAlchemy 2.0, autocommit and autoflush are on the sessionmaker
            # not the session instance
            assert hasattr(session, 'commit')
            assert hasattr(session, 'rollback')
            assert hasattr(session, 'close')
        finally:
            session.close()
    
    def test_base_configuration(self):
        """Test that Base declarative class is correctly configured."""
        # Verify Base exists
        assert hasattr(database, 'Base')
        assert database.Base is not None
        
        # Verify it's a declarative base
        assert isinstance(database.Base, DeclarativeMeta)
        assert hasattr(database.Base, 'metadata')
        # __tablename__ is on individual model classes, not the Base itself


@pytest.mark.unit
class TestGetDb:
    """Test cases for get_db dependency function."""
    
    @patch('app.db.database.SessionLocal')
    def test_get_db_yields_session(self, mock_session_local):
        """Test that get_db yields a database session."""
        # Mock the session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Get the generator
        gen = database.get_db()
        
        # Get the session
        session = next(gen)
        
        # Verify session is returned
        assert session is mock_session
        mock_session_local.assert_called_once_with()
    
    @patch('app.db.database.SessionLocal')
    def test_get_db_closes_session(self, mock_session_local):
        """Test that get_db closes session after use."""
        # Mock the session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Get the generator
        gen = database.get_db()
        
        # Get the session
        session = next(gen)
        
        # Complete the generator
        try:
            next(gen)
        except StopIteration:
            pass
        
        # Verify session was closed
        mock_session.close.assert_called_once()
    
    @patch('app.db.database.SessionLocal')
    def test_get_db_closes_session_on_exception(self, mock_session_local):
        """Test that get_db closes session even when exception occurs."""
        # Mock the session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Get the generator
        gen = database.get_db()
        
        # Get the session
        session = next(gen)
        
        # Simulate exception
        try:
            gen.throw(ValueError("Test exception"))
        except ValueError:
            pass
        
        # Verify session was still closed
        mock_session.close.assert_called_once()
    
    @patch('app.db.database.SessionLocal')
    def test_get_db_multiple_calls(self, mock_session_local):
        """Test that multiple calls to get_db create separate sessions."""
        # Mock sessions
        mock_session1 = Mock(spec=Session)
        mock_session2 = Mock(spec=Session)
        mock_session_local.side_effect = [mock_session1, mock_session2]
        
        # Get two generators
        gen1 = database.get_db()
        gen2 = database.get_db()
        
        # Get sessions
        session1 = next(gen1)
        session2 = next(gen2)
        
        # Verify different sessions
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
    
    def test_get_db_docstring(self):
        """Test that get_db has proper documentation."""
        assert database.get_db.__doc__ is not None
        assert "database session" in database.get_db.__doc__
        assert "dependency" in database.get_db.__doc__.lower()


@pytest.mark.unit
class TestDatabaseConstants:
    """Test database constants and module attributes."""
    
    def test_module_imports(self):
        """Test that necessary imports are available."""
        # These should be importable from the module
        assert hasattr(database, 'create_engine')
        assert hasattr(database, 'declarative_base')
        assert hasattr(database, 'sessionmaker')
    
    def test_database_configuration(self):
        """Test database-specific configuration."""
        from app.core.config import settings
        
        # Verify we have a valid database URL
        assert settings.DATABASE_URL is not None
        
        # Check database-specific settings
        if "postgresql" in settings.DATABASE_URL:
            # For PostgreSQL, verify connection parameters
            assert settings.DB_HOST
            assert settings.DB_PORT
            assert settings.DB_NAME
            assert settings.DB_USER
        elif "sqlite" in settings.DATABASE_URL:
            # For SQLite, verify file path
            db_path = settings.DATABASE_URL.split("///")[-1]
            assert db_path
    
    def test_engine_creation_verification(self):
        """Test that engine was created with correct database configuration."""
        # Since the engine is created at module import time,
        # we can only verify its current state
        from app.core.config import settings
        
        # Verify engine URL matches settings
        engine_url = str(database.engine.url)
        
        if "postgresql" in settings.DATABASE_URL:
            # Verify it's a PostgreSQL engine
            assert database.engine.dialect.name == 'postgresql'
            assert settings.DB_NAME in engine_url
        elif "sqlite" in settings.DATABASE_URL:
            # Verify it's a SQLite engine
            assert database.engine.dialect.name == 'sqlite'
            assert "tasks.db" in engine_url