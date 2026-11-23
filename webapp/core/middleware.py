"""Persist changed SQLite state to R2 at request boundaries."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)
_backup_lock = threading.Lock()


def _sqlite_signature():
    root = Path(settings.ACQUISITION_DATA_DIR)
    if not root.exists():
        return ()
    result = []
    for path in root.rglob("*"):
        if path.is_file() and (".sqlite" in path.name or path.suffix == ".db"):
            try:
                stat = path.stat()
                result.append((str(path), stat.st_size, stat.st_mtime_ns))
            except FileNotFoundError:
                continue
    return tuple(sorted(result))


class StateBackupMiddleware:
    """Snapshot only when a request actually changed a SQLite database file."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        before = _sqlite_signature()
        response = self.get_response(request)
        after = _sqlite_signature()
        if after != before:
            try:
                from webapp.core.state_backup import backup

                with _backup_lock:
                    backup()
            except Exception:
                # Surface durability failures in Container logs without hiding the
                # original response. The startup restore remains fail-closed.
                logger.exception("Failed to persist changed SQLite state to R2")
                response.status_code = 503
                if not getattr(response, "streaming", False):
                    response.content = (
                        b"SQLite data changed, but the durable R2 backup failed. "
                        b"The latest change may not survive a Container restart."
                    )
                response["X-Acquisition-State-Persistence"] = "failed"
        return response
