from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from threading import BoundedSemaphore
from typing import Any

from sqlalchemy import text

from app.ai.query_validator import validate_readonly_sql
from app.core.config import get_settings
from app.core.database import get_engine


class QueryBusyError(RuntimeError):
    pass


class QueryTimeoutError(RuntimeError):
    pass


class ReadOnlyQueryExecutor:
    """Single gateway for bounded, parameterized SELECT queries."""

    def __init__(self, allowed_views: set[str]):
        settings = get_settings()
        self.allowed_views = allowed_views
        self.max_rows = settings.db_max_rows
        self.timeout_seconds = settings.db_query_timeout_ms / 1000
        self._slots = BoundedSemaphore(settings.db_max_concurrent_queries)
        self._workers = ThreadPoolExecutor(max_workers=settings.db_max_concurrent_queries)

    def fetch_all(self, sql: str, parameters: dict[str, Any] | None = None) -> list[dict]:
        validate_readonly_sql(sql, self.allowed_views)
        if not self._slots.acquire(blocking=False):
            raise QueryBusyError("Limite de consultas simultâneas atingido")
        try:
            future = self._workers.submit(self._execute, sql, parameters or {})
            try:
                return future.result(timeout=self.timeout_seconds + 1)
            except FutureTimeout as exc:
                future.cancel()
                raise QueryTimeoutError("A consulta excedeu o tempo permitido") from exc
        finally:
            self._slots.release()

    def _execute(self, sql: str, parameters: dict[str, Any]) -> list[dict]:
        with get_engine().connect() as connection:
            with connection.begin():
                rows = connection.execute(text(sql), parameters).mappings().fetchmany(self.max_rows + 1)
                if len(rows) > self.max_rows:
                    raise ValueError(f"A consulta excedeu o limite de {self.max_rows} linhas")
                return [dict(row) for row in rows]

