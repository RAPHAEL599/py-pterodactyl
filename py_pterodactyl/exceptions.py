from __future__ import annotations
from typing import Any

class PterodactylAPIError(Exception):
    """Raised when a Pterodactyl API request returns a non-success status."""

    def __init__(self, status: int, body: Any, message: str | None = None) -> None:
        self.status = status
        self.body = body
        self.message = message or self._extract_message(body)
        super().__init__(self.message)

    @staticmethod
    def _extract_message(body: Any) -> str:
        if isinstance(body, dict):
            if "errors" in body and isinstance(body["errors"], list):
                return "; ".join(str(error) for error in body["errors"])
            if "error" in body:
                return str(body["error"])
            if "message" in body:
                return str(body["message"])
            return str(body)
        return str(body)


class WebSocketError(Exception):
    """Raised for WebSocket connect/send/receive failures."""
    pass
