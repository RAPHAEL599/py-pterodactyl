"""Fully asynchronous Pterodactyl Panel API client."""

from .client import AsyncPterodactyl, Pterodactyl, PterodactylClient
from .errors import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    PterodactylAPIError,
    PterodactylError,
    PterodactylTimeoutError,
    PterodactylTransportError,
    RateLimitError,
    ValidationError,
)
from .websocket import PterodactylWebSocket, WebSocketEvent

__version__ = "0.1.0"

__all__ = [
    "AsyncPterodactyl",
    "AuthenticationError",
    "NotFoundError",
    "PermissionDeniedError",
    "Pterodactyl",
    "PterodactylAPIError",
    "PterodactylClient",
    "PterodactylError",
    "PterodactylTimeoutError",
    "PterodactylTransportError",
    "PterodactylWebSocket",
    "RateLimitError",
    "ValidationError",
    "WebSocketEvent",
]
