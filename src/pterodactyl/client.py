"""Public asynchronous Pterodactyl client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from .api.application import ApplicationAPI
from .api.client import ClientAPI
from .transport import AsyncTransport
from .websocket import WebSocketManager


class Pterodactyl:
    """Access the Client, Application, and WebSocket APIs asynchronously.

    The supplied key determines which namespaces the Panel authorizes. A Client
    key normally cannot call Application endpoints and vice versa.
    """

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
        self._transport = AsyncTransport(
            panel_url,
            api_key,
            timeout=timeout,
            verify=verify,
            user_agent=user_agent,
            http_client=http_client,
        )
        self.client = ClientAPI(self._transport)
        self.application = ApplicationAPI(self._transport)
        self.websocket = WebSocketManager(self._transport)

    @property
    def panel_url(self) -> str:
        return self._transport.panel_url

    @property
    def http_client(self) -> httpx.AsyncClient:
        return self._transport.http_client

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
        """Call a custom or newly introduced Panel endpoint."""

        return await self._transport.request(
            method,
            path,
            params=params,
            json_data=json_data,
            content=content,
            data=data,
            files=files,
            headers=headers,
            authenticate=authenticate,
            raw=raw,
        )

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> Pterodactyl:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        await self.close()


AsyncPterodactyl = Pterodactyl
PterodactylClient = Pterodactyl
