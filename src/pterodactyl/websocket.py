"""Async client for the Pterodactyl Wings WebSocket protocol."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import websockets

from .errors import PterodactylTransportError
from .transport import AsyncTransport


@dataclass(frozen=True)
class WebSocketEvent:
    """A message received from Wings."""

    event: str
    args: list[Any]
    raw: Mapping[str, Any]

    @property
    def data(self) -> Any:
        """Return the first event argument, which is where Wings normally stores its data."""

        return self.args[0] if self.args else None


class PterodactylWebSocket:
    """An authenticated connection to a single server's Wings socket."""

    def __init__(
        self,
        socket: Any,
        credential_provider: Callable[[], Awaitable[Any]],
        token: str,
        *,
        auto_refresh_token: bool = True,
    ) -> None:
        self._socket = socket
        self._credential_provider = credential_provider
        self._token = token
        self.auto_refresh_token = auto_refresh_token

    @classmethod
    async def connect(
        cls,
        credential_provider: Callable[[], Awaitable[Any]],
        *,
        origin: str | None = None,
        auto_refresh_token: bool = True,
        **connect_kwargs: Any,
    ) -> PterodactylWebSocket:
        credentials = cls._parse_credentials(await credential_provider())
        kwargs = dict(connect_kwargs)
        kwargs.setdefault("subprotocols", ["pterodactyl"])
        if origin is not None:
            kwargs.setdefault("origin", origin)
        try:
            socket = await websockets.connect(credentials["socket"], **kwargs)
            connection = cls(
                socket,
                credential_provider,
                credentials["token"],
                auto_refresh_token=auto_refresh_token,
            )
            await connection.authenticate()
            return connection
        except (OSError, websockets.WebSocketException) as exc:
            raise PterodactylTransportError(f"WebSocket connection failed: {exc}") from exc

    @staticmethod
    def _parse_credentials(payload: Any) -> dict[str, str]:
        if not isinstance(payload, dict):
            raise PterodactylTransportError("Invalid WebSocket credential response")
        value = payload.get("data", payload)
        if isinstance(value, dict) and isinstance(value.get("attributes"), dict):
            value = value["attributes"]
        if not isinstance(value, dict) or not value.get("token") or not value.get("socket"):
            raise PterodactylTransportError("WebSocket response has no token or socket URL")
        return {"token": str(value["token"]), "socket": str(value["socket"])}

    @property
    def closed(self) -> bool:
        state = getattr(self._socket, "state", None)
        if state is not None:
            return getattr(state, "name", "").upper() == "CLOSED"
        return bool(getattr(self._socket, "closed", False))

    async def send_event(self, event: str, *args: Any) -> None:
        await self._socket.send(json.dumps({"event": event, "args": list(args)}))

    async def authenticate(self, token: str | None = None) -> None:
        if token is not None:
            self._token = token
        await self.send_event("auth", self._token)

    async def refresh_token(self) -> None:
        credentials = self._parse_credentials(await self._credential_provider())
        await self.authenticate(credentials["token"])

    async def send_command(self, command: str) -> None:
        await self.send_event("send command", command)

    async def set_power(self, state: str) -> None:
        if state not in {"start", "stop", "restart", "kill"}:
            raise ValueError("state must be one of: start, stop, restart, kill")
        await self.send_event("set state", state)

    async def request_logs(self) -> None:
        await self.send_event("send logs")

    async def request_stats(self) -> None:
        await self.send_event("send stats")

    async def receive(self) -> WebSocketEvent:
        raw_message = await self._socket.recv()
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8")
        try:
            payload = json.loads(raw_message)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PterodactylTransportError("Wings returned an invalid WebSocket message") from exc
        if not isinstance(payload, dict):
            raise PterodactylTransportError("Wings returned an invalid WebSocket event")
        event = str(payload.get("event", ""))
        args = payload.get("args", [])
        if not isinstance(args, list):
            args = [args]
        message = WebSocketEvent(event=event, args=args, raw=payload)
        if event == "token expiring" and self.auto_refresh_token:
            await self.refresh_token()
        return message

    async def wait_for(self, event: str, *, timeout: float | None = None) -> WebSocketEvent:
        async def receive_until() -> WebSocketEvent:
            while True:
                message = await self.receive()
                if message.event == event:
                    return message

        if timeout is None:
            return await receive_until()
        return await asyncio.wait_for(receive_until(), timeout=timeout)

    async def events(self) -> AsyncIterator[WebSocketEvent]:
        while not self.closed:
            try:
                yield await self.receive()
            except websockets.ConnectionClosed:
                return

    def __aiter__(self) -> AsyncIterator[WebSocketEvent]:
        return self.events()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        await self._socket.close(code=code, reason=reason)

    async def __aenter__(self) -> PterodactylWebSocket:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        await self.close()


class WebSocketManager:
    """Creates authenticated Wings connections using the Client API."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def credentials(self, server: str) -> Any:
        from .api.base import path_id

        return await self._transport.request("GET", f"/client/servers/{path_id(server)}/websocket")

    async def connect(self, server: str, **kwargs: Any) -> PterodactylWebSocket:
        async def provider() -> Any:
            return await self.credentials(server)

        parsed = urlsplit(self._transport.panel_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        return await PterodactylWebSocket.connect(provider, origin=origin, **kwargs)
