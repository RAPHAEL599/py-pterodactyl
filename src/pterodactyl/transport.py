"""Asynchronous HTTP transport shared by all API resources."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import httpx

from .errors import (
    STATUS_EXCEPTIONS,
    PterodactylAPIError,
    PterodactylTimeoutError,
    PterodactylTransportError,
    RateLimitError,
)

DEFAULT_ACCEPT = "Application/vnd.pterodactyl.v1+json"


class AsyncTransport:
    """Small, reusable wrapper around :class:`httpx.AsyncClient`."""

    def __init__(
        self,
        panel_url: str,
        api_key: str,
        *,
        timeout: float | httpx.Timeout = 30.0,
        verify: bool = True,
        user_agent: str = "py-pterodactyl/0.1.0",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not panel_url.strip():
            raise ValueError("panel_url cannot be empty")
        if not api_key.strip():
            raise ValueError("api_key cannot be empty")

        self.panel_url = panel_url.rstrip("/")
        self.api_key = api_key
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=timeout,
            verify=verify,
            follow_redirects=True,
            headers={"Accept": DEFAULT_ACCEPT, "User-Agent": user_agent},
        )

    @property
    def http_client(self) -> httpx.AsyncClient:
        return self._client

    def url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        normalized = path if path.startswith("/") else f"/{path}"
        if not normalized.startswith("/api/") and normalized != "/api":
            normalized = f"/api{normalized}"
        return f"{self.panel_url}{normalized}"

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_data: Any = None,
        content: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Mapping[str, str] | None = None,
        authenticate: bool = True,
        raw: bool = False,
    ) -> Any:
        request_headers = dict(headers or {})
        if authenticate:
            request_headers.setdefault("Authorization", f"Bearer {self.api_key}")
        if json_data is not None:
            request_headers.setdefault("Content-Type", "application/json")

        url = self.url(path)
        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                json=json_data,
                content=content,
                data=data,
                files=files,
                headers=request_headers,
            )
        except httpx.TimeoutException as exc:
            raise PterodactylTimeoutError(f"Request to {url} timed out") from exc
        except httpx.HTTPError as exc:
            raise PterodactylTransportError(f"Request to {url} failed: {exc}") from exc

        if response.is_error:
            self._raise_api_error(response)
        if raw:
            return response
        return self._decode(response)

    @staticmethod
    def _decode(response: httpx.Response) -> Any:
        if response.status_code in (204, 205) or not response.content:
            return None
        content_type = response.headers.get("content-type", "").lower()
        if "json" in content_type:
            try:
                return response.json()
            except json.JSONDecodeError as exc:
                raise PterodactylTransportError("Panel returned malformed JSON") from exc
        if content_type.startswith("text/"):
            return response.text
        return response.content

    @staticmethod
    def _raise_api_error(response: httpx.Response) -> None:
        errors = []
        message = response.reason_phrase or "Unknown API error"
        try:
            body = response.json()
            if isinstance(body, dict):
                candidate = body.get("errors", [])
                if isinstance(candidate, list):
                    errors = [item for item in candidate if isinstance(item, dict)]
                if errors:
                    detail = errors[0].get("detail") or errors[0].get("code")
                    if detail:
                        message = str(detail)
                elif body.get("message"):
                    message = str(body["message"])
        except (ValueError, json.JSONDecodeError):
            if response.text.strip():
                message = response.text.strip()

        exception_type = STATUS_EXCEPTIONS.get(response.status_code, PterodactylAPIError)
        kwargs = {
            "url": str(response.request.url),
            "errors": errors,
            "response": response,
        }
        if exception_type is RateLimitError:
            retry_value = response.headers.get("Retry-After")
            try:
                retry_after = float(retry_value) if retry_value is not None else None
            except ValueError:
                retry_after = None
            raise exception_type(response.status_code, message, retry_after=retry_after, **kwargs)
        raise exception_type(response.status_code, message, **kwargs)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
