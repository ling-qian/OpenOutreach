"""Persist SQLite state to R2 after mutating requests."""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)
_backup_lock = threading.Lock()


class StateBackupMiddleware:
    """Best-effort request-boundary snapshot; startup restore is performed by entrypoint."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and response.status_code < 500:
            try:
                from webapp.core.state_backup import backup

                with _backup_lock:
                    backup()
            except Exception:
                # Do not turn a successful user action into a 500, but surface the
                # durability failure in Container logs for operator follow-up.
                logger.exception("Failed to persist SQLite snapshot to R2")
        return response
