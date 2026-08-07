from __future__ import annotations

import asyncio
import json
from typing import Any

import websockets
from websockets.legacy.client import WebSocketClientProtocol

from .client import PterodactylClient
from .exceptions import WebSocketError


class PterodactylWebSocket:
    def __init__(self, panel_url: str, api_key: str, server_id: str, *, timeout: int = 30) -> None:
        self.client = PterodactylClient(panel_url, api_key, timeout=timeout)
        self.server_id = server_id
        self._websocket: WebSocketClientProtocol | None = None
        self._receive_task: asyncio.Task[None] | None = None
        self._event_handlers: dict[str, list[callable]] = {}
        self._connect_lock = asyncio.Lock()

    async def _get_websocket_token(self) -> dict[str, Any]:
        return await self.client.websocket_token(self.server_id)

    async def connect(self) -> None:
        async with self._connect_lock:
            if self._websocket is not None and not self._websocket.closed:
                return
            token_data = await self._get_websocket_token()
            token = token_data.get("token")
            socket_url = token_data.get("socket")
            if not token or not socket_url:
                raise WebSocketError("Invalid websocket token response")

            try:
                self._websocket = await websockets.connect(
                    socket_url,
                    extra_headers={
                        "Authorization": f"Bearer {token}",
                        "Origin": self.client.base_url,
                    },
                    ping_interval=20,
                    close_timeout=10,
                )
            except Exception as exc:
                raise WebSocketError("Failed to connect to websocket") from exc

            auth_payload = {"event": "auth", "args": [token]}
            await self._websocket.send(json.dumps(auth_payload))
            self._receive_task = asyncio.create_task(self._receive_loop())

    async def disconnect(self) -> None:
        if self._receive_task is not None:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
            self._receive_task = None

        if self._websocket is not None and not self._websocket.closed:
            await self._websocket.close()
            self._websocket = None

        await self.client.close()

    async def _receive_loop(self) -> None:
        assert self._websocket is not None
        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    continue
                await self._dispatch_event(data)
        except websockets.ConnectionClosed as exc:
            await self._dispatch_event({"event": "closed", "args": [exc.code, exc.reason]})
        except Exception as exc:
            raise WebSocketError("Websocket receive loop failed") from exc

    async def _dispatch_event(self, payload: dict[str, Any]) -> None:
        event_name = payload.get("event")
        args = payload.get("args", [])
        if not event_name:
            return

        for handler in self._event_handlers.get(event_name, []):
            result = handler(args)
            if asyncio.iscoroutine(result):
                await result

    def on(self, event: str, handler: callable) -> None:
        self._event_handlers.setdefault(event, []).append(handler)

    def off(self, event: str, handler: callable) -> None:
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)

    async def send_command(self, command: str) -> None:
        await self._ensure_connected()
        assert self._websocket is not None
        await self._websocket.send(json.dumps({"event": "send command", "args": [command]}))

    async def set_power_state(self, state: str) -> None:
        await self._ensure_connected()
        assert self._websocket is not None
        await self._websocket.send(json.dumps({"event": "set state", "args": [state]}))

    async def _ensure_connected(self) -> None:
        if self._websocket is None or self._websocket.closed:
            await self.connect()

    async def ping(self) -> None:
        await self._ensure_connected()
        assert self._websocket is not None
        await self._websocket.ping()
