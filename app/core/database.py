from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=5,
        connect_args={"connect_timeout": 5, "read_timeout": 10, "write_timeout": 5},
    )
    @event.listens_for(engine, "connect")
    def configure_readonly_session(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={settings.db_query_timeout_ms}")
            cursor.execute("SET SESSION TRANSACTION READ ONLY")
        finally:
            cursor.close()
    return engine
