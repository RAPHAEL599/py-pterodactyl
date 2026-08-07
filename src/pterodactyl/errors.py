"""Exceptions raised by the Pterodactyl client."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class PterodactylError(Exception):
    """Base exception for this package."""


class PterodactylTransportError(PterodactylError):
    """The Panel could not be reached or returned an invalid transport response."""


class PterodactylTimeoutError(PterodactylTransportError):
    """The request timed out."""


class PterodactylAPIError(PterodactylError):
    """An HTTP error response returned by the Panel."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        url: str = "",
        errors: Sequence[Mapping[str, Any]] | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.url = url
        self.errors = list(errors or [])
        self.response = response

    def __str__(self) -> str:
        location = f" ({self.url})" if self.url else ""
        return f"Pterodactyl API returned HTTP {self.status_code}: {self.message}{location}"


class AuthenticationError(PterodactylAPIError):
    """The API key is absent or invalid (HTTP 401)."""


class PermissionDeniedError(PterodactylAPIError):
    """The API key cannot perform this operation (HTTP 403)."""


class NotFoundError(PterodactylAPIError):
    """The requested resource does not exist (HTTP 404)."""


class ValidationError(PterodactylAPIError):
    """The request payload failed validation (HTTP 422)."""


class RateLimitError(PterodactylAPIError):
    """The Panel rate limit was exceeded (HTTP 429)."""

    def __init__(self, *args: Any, retry_after: float | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


STATUS_EXCEPTIONS = {
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
}
