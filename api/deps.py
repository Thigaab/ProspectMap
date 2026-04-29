"""FastAPI dependencies."""
from pathlib import Path
from typing import Generator

from . import _bootstrap  # noqa: F401 — puts cli/ on sys.path

import config  # type: ignore  # from cli/
from cache import Cache  # type: ignore  # from cli/


def get_cache() -> Generator[Cache, None, None]:
    """Per-request SQLite cache. Opens a fresh connection (SQLite isn't
    safe to share across threads) and closes it when the request ends."""
    cache = Cache(Path(config.DB_PATH))
    try:
        yield cache
    finally:
        cache.close()
