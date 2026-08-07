from typing import Any

import pytest

from pterodactyl.api.application import ApplicationAPI
from pterodactyl.api.client import ClientAPI


class RecordingTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        return {"ok": True}


@pytest.mark.asyncio
async def test_client_route_contracts() -> None:
    transport = RecordingTransport()
    api = ClientAPI(transport)  # type: ignore[arg-type]

    await api.account.enable_two_factor("123456")
    await api.servers.send_command("abc/unsafe", "say hi")
    await api.servers.files.rename("abc", "/", [{"from": "a", "to": "b"}])
    await api.servers.schedules.update_task("abc", 1, 2, payload="restart")
    await api.servers.network.set_primary("abc", 42)
    await api.servers.backups.restore("abc", "uuid", truncate=True)
    await api.servers.settings.update_docker_image("abc", "image:latest")

    assert [(method, path) for method, path, _ in transport.calls] == [
        ("POST", "/client/account/two-factor"),
        ("POST", "/client/servers/abc%2Funsafe/command"),
        ("PUT", "/client/servers/abc/files/rename"),
        ("POST", "/client/servers/abc/schedules/1/tasks/2"),
        ("POST", "/client/servers/abc/network/allocations/42/primary"),
        ("POST", "/client/servers/abc/backups/uuid/restore"),
        ("PUT", "/client/servers/abc/settings/docker-image"),
    ]


@pytest.mark.asyncio
async def test_application_route_contracts() -> None:
    transport = RecordingTransport()
    api = ApplicationAPI(transport)  # type: ignore[arg-type]

    await api.users.get_by_external_id("billing/123")
    await api.nodes.configuration(3)
    await api.nodes.allocations.create(3, "127.0.0.1", [25565, "25570-25575"])
    await api.locations.update(4, short="br-sp")
    await api.servers.update_build(5, memory=4096)
    await api.servers.delete(5, force=True)
    await api.servers.databases.reset_password(5, 6)
    await api.nests.eggs.get(1, 2, include="variables")

    assert [(method, path) for method, path, _ in transport.calls] == [
        ("GET", "/application/users/external/billing%2F123"),
        ("GET", "/application/nodes/3/configuration"),
        ("POST", "/application/nodes/3/allocations"),
        ("PATCH", "/application/locations/4"),
        ("PATCH", "/application/servers/5/build"),
        ("DELETE", "/application/servers/5/force"),
        ("POST", "/application/servers/5/databases/6/reset-password"),
        ("GET", "/application/nests/1/eggs/2"),
    ]


@pytest.mark.asyncio
async def test_power_signal_is_validated_before_request() -> None:
    api = ClientAPI(RecordingTransport())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="start, stop, restart, kill"):
        await api.servers.power("abc", "explode")
