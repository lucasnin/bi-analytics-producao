import time
from threading import Lock
from typing import Any, Callable


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get_or_set(self, key: str, factory: Callable[[], Any]) -> Any:
        now = time.monotonic()
        with self._lock:
            cached = self._items.get(key)
            if cached and cached[0] > now:
                return cached[1]
        value = factory()
        with self._lock:
            self._items[key] = (now + self.ttl_seconds, value)
        return value

