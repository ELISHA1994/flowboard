from app.db.database import get_db as _get_db

# Re-export get_db for backward compatibility
get_db = _get_db


def get_postgres_connector():
    """
    This function exists for compatibility with the article structure,
    but we're using SQLite. In a production app, you might use this
    to switch between different database connections based on environment.
    """
    return get_db
