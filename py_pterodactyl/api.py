from __future__ import annotations

import aiohttp
from aiohttp import ClientSession
from aiohttp.client_exceptions import ContentTypeError
from typing import Any

from .exceptions import PterodactylAPIError


class BasePterodactylAPI:
    def __init__(self, base_url: str, api_key: str, *, timeout: int = 30, session: ClientSession | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session = session
        self._default_headers = {
            "Accept": "Application/vnd.pterodactyl.v1+json",
            "Authorization": f"Bearer {api_key}",
        }

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self._default_headers,
            )

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "BasePterodactylAPI":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        await self._ensure_session()
        url = self._build_url(path)
        request_headers = dict(self._default_headers)
        if headers:
            request_headers.update(headers)

        async with self._session.request(
            method.upper(),
            url,
            params=params,
            json=json,
            data=data,
            headers=request_headers,
        ) as response:
            text = await response.text()
            if response.status >= 400:
                body: Any = text
                try:
                    body = await response.json()
                except ContentTypeError:
                    pass
                raise PterodactylAPIError(response.status, body)

            if response.status == 204 or not text:
                return {}

            try:
                return await response.json()
            except ContentTypeError:
                return text

    async def get(self, path: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        return await self.request("GET", path, params=params, headers=headers)

    async def post(self, path: str, *, json: Any | None = None, data: Any | None = None, headers: dict[str, str] | None = None) -> Any:
        return await self.request("POST", path, json=json, data=data, headers=headers)

    async def put(self, path: str, *, json: Any | None = None, headers: dict[str, str] | None = None) -> Any:
        return await self.request("PUT", path, json=json, headers=headers)

    async def patch(self, path: str, *, json: Any | None = None, headers: dict[str, str] | None = None) -> Any:
        return await self.request("PATCH", path, json=json, headers=headers)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        return await self.request("DELETE", path, params=params, headers=headers)
