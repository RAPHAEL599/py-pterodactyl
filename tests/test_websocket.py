import json
from typing import Any

import pytest

from pterodactyl.websocket import PterodactylWebSocket


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.messages = [
            json.dumps({"event": "token expiring", "args": []}),
            json.dumps({"event": "console output", "args": ["Server started"]}),
        ]
        self.closed = False

    async def send(self, value: str) -> None:
        self.sent.append(json.loads(value))

    async def recv(self) -> str:
        return self.messages.pop(0)

    async def close(self, **kwargs: Any) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_websocket_auth_events_and_token_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    socket = FakeSocket()
    tokens = iter(["first-token", "second-token"])

    async def credentials() -> dict[str, Any]:
        return {"data": {"token": next(tokens), "socket": "wss://node.example/ws"}}

    async def connect(url: str, **kwargs: Any) -> FakeSocket:
        assert url == "wss://node.example/ws"
        assert kwargs["subprotocols"] == ["pterodactyl"]
        return socket

    monkeypatch.setattr("pterodactyl.websocket.websockets.connect", connect)
    connection = await PterodactylWebSocket.connect(credentials, origin="https://panel.example")
    assert socket.sent == [{"event": "auth", "args": ["first-token"]}]

    expiring = await connection.receive()
    assert expiring.event == "token expiring"
    assert socket.sent[-1] == {"event": "auth", "args": ["second-token"]}

    output = await connection.receive()
    assert output.event == "console output"
    assert output.data == "Server started"

    await connection.send_command("list")
    await connection.set_power("restart")
    assert socket.sent[-2:] == [
        {"event": "send command", "args": ["list"]},
        {"event": "set state", "args": ["restart"]},
    ]
