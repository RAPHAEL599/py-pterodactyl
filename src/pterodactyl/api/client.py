"""Complete asynchronous implementation of the Pterodactyl Client API."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from typing import Any

from .base import APIResource, path_id, query_params


def _body(data: Mapping[str, Any] | None, values: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(data or {})
    payload.update({key: value for key, value in values.items() if value is not None})
    return payload


class AccountResource(APIResource):
    async def get(self) -> Any:
        return await self._request("GET", "/client/account")

    async def two_factor(self) -> Any:
        return await self._request("GET", "/client/account/two-factor")

    async def enable_two_factor(self, code: str) -> Any:
        return await self._request("POST", "/client/account/two-factor", json_data={"code": code})

    async def disable_two_factor(self, password: str) -> None:
        await self._request(
            "POST", "/client/account/two-factor/disable", json_data={"password": password}
        )

    async def update_email(self, email: str, password: str) -> Any:
        return await self._request(
            "PUT", "/client/account/email", json_data={"email": email, "password": password}
        )

    async def update_password(
        self, current_password: str, password: str, password_confirmation: str | None = None
    ) -> None:
        await self._request(
            "PUT",
            "/client/account/password",
            json_data={
                "current_password": current_password,
                "password": password,
                "password_confirmation": password_confirmation or password,
            },
        )

    async def activity(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        filters: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        query = query_params(params, page=page, per_page=per_page, filters=filters)
        return await self._request("GET", "/client/account/activity", params=query)

    async def api_keys(self) -> Any:
        return await self._request("GET", "/client/account/api-keys")

    async def create_api_key(
        self, description: str, allowed_ips: Sequence[str] | None = None
    ) -> Any:
        return await self._request(
            "POST",
            "/client/account/api-keys",
            json_data={"description": description, "allowed_ips": list(allowed_ips or [])},
        )

    async def delete_api_key(self, identifier: str) -> None:
        await self._request("DELETE", f"/client/account/api-keys/{path_id(identifier)}")

    async def ssh_keys(self) -> Any:
        return await self._request("GET", "/client/account/ssh-keys")

    async def add_ssh_key(self, name: str, public_key: str) -> Any:
        return await self._request(
            "POST", "/client/account/ssh-keys", json_data={"name": name, "public_key": public_key}
        )

    async def remove_ssh_key(self, fingerprint: str) -> None:
        await self._request(
            "POST", "/client/account/ssh-keys/remove", json_data={"fingerprint": fingerprint}
        )


class ServerSubresource(APIResource):
    prefix = ""

    def _path(self, server: str, suffix: str = "") -> str:
        return f"/client/servers/{path_id(server)}/{self.prefix}{suffix}"


class ClientDatabasesResource(ServerSubresource):
    prefix = "databases"

    async def list(self, server: str, *, include: str | Iterable[str] | None = None) -> Any:
        return await self._request("GET", self._path(server), params=query_params(include=include))

    async def create(self, server: str, database: str, remote: str = "%") -> Any:
        return await self._request(
            "POST", self._path(server), json_data={"database": database, "remote": remote}
        )

    async def rotate_password(self, server: str, database: str) -> Any:
        return await self._request(
            "POST", self._path(server, f"/{path_id(database)}/rotate-password")
        )

    async def delete(self, server: str, database: str) -> None:
        await self._request("DELETE", self._path(server, f"/{path_id(database)}"))


class FilesResource(ServerSubresource):
    prefix = "files"

    async def list(self, server: str, directory: str = "/") -> Any:
        return await self._request(
            "GET", self._path(server, "/list"), params={"directory": directory}
        )

    async def contents(self, server: str, file: str) -> str:
        return await self._request("GET", self._path(server, "/contents"), params={"file": file})

    async def write(self, server: str, file: str, content: str | bytes) -> None:
        await self._request(
            "POST",
            self._path(server, "/write"),
            params={"file": file},
            content=content,
            headers={"Content-Type": "text/plain"},
        )

    async def download_url(self, server: str, file: str) -> Any:
        return await self._request("GET", self._path(server, "/download"), params={"file": file})

    async def upload_url(self, server: str, directory: str = "/") -> Any:
        return await self._request(
            "GET", self._path(server, "/upload"), params={"directory": directory}
        )

    async def upload(self, signed_url: str, files: Any, *, data: Any = None) -> Any:
        """Upload multipart data to a signed Wings URL without leaking the Panel API key."""

        return await self._transport.request(
            "POST", signed_url, files=files, data=data, authenticate=False
        )

    async def rename(self, server: str, root: str, files: Sequence[Mapping[str, str]]) -> None:
        await self._request(
            "PUT", self._path(server, "/rename"), json_data={"root": root, "files": list(files)}
        )

    async def copy(self, server: str, location: str) -> None:
        await self._request("POST", self._path(server, "/copy"), json_data={"location": location})

    async def compress(self, server: str, root: str, files: Sequence[str]) -> Any:
        return await self._request(
            "POST",
            self._path(server, "/compress"),
            json_data={"root": root, "files": list(files)},
        )

    async def decompress(self, server: str, root: str, file: str) -> None:
        await self._request(
            "POST",
            self._path(server, "/decompress"),
            json_data={"root": root, "file": file},
        )

    async def delete(self, server: str, root: str, files: Sequence[str]) -> None:
        await self._request(
            "POST",
            self._path(server, "/delete"),
            json_data={"root": root, "files": list(files)},
        )

    async def create_folder(self, server: str, root: str, name: str) -> None:
        await self._request(
            "POST",
            self._path(server, "/create-folder"),
            json_data={"root": root, "name": name},
        )

    async def chmod(self, server: str, root: str, files: Sequence[Mapping[str, Any]]) -> None:
        await self._request(
            "POST",
            self._path(server, "/chmod"),
            json_data={"root": root, "files": list(files)},
        )

    async def pull(
        self,
        server: str,
        url: str,
        directory: str,
        *,
        filename: str | None = None,
        use_header: bool | None = None,
        foreground: bool | None = None,
    ) -> None:
        payload = _body(
            None,
            {
                "url": url,
                "directory": directory,
                "filename": filename,
                "use_header": use_header,
                "foreground": foreground,
            },
        )
        await self._request("POST", self._path(server, "/pull"), json_data=payload)


class SchedulesResource(ServerSubresource):
    prefix = "schedules"

    async def list(self, server: str, *, include: str | Iterable[str] | None = None) -> Any:
        return await self._request("GET", self._path(server), params=query_params(include=include))

    async def get(
        self, server: str, schedule: int, *, include: str | Iterable[str] | None = None
    ) -> Any:
        return await self._request(
            "GET", self._path(server, f"/{path_id(schedule)}"), params=query_params(include=include)
        )

    async def create(
        self,
        server: str,
        name: str,
        minute: str,
        hour: str,
        day_of_month: str,
        month: str,
        day_of_week: str,
        *,
        is_active: bool = True,
        only_when_online: bool = True,
    ) -> Any:
        return await self._request(
            "POST",
            self._path(server),
            json_data={
                "name": name,
                "minute": minute,
                "hour": hour,
                "day_of_month": day_of_month,
                "month": month,
                "day_of_week": day_of_week,
                "is_active": is_active,
                "only_when_online": only_when_online,
            },
        )

    async def update(self, server: str, schedule: int, **data: Any) -> Any:
        return await self._request(
            "POST", self._path(server, f"/{path_id(schedule)}"), json_data=data
        )

    async def execute(self, server: str, schedule: int) -> None:
        await self._request("POST", self._path(server, f"/{path_id(schedule)}/execute"))

    async def delete(self, server: str, schedule: int) -> None:
        await self._request("DELETE", self._path(server, f"/{path_id(schedule)}"))

    async def list_tasks(self, server: str, schedule: int) -> Any:
        """Compatibility endpoint documented by PteroAPI; current Panels include tasks on get()."""

        return await self._request("GET", self._path(server, f"/{path_id(schedule)}/tasks"))

    async def create_task(
        self,
        server: str,
        schedule: int,
        action: str,
        payload: str,
        time_offset: int = 0,
        *,
        continue_on_failure: bool = False,
    ) -> Any:
        return await self._request(
            "POST",
            self._path(server, f"/{path_id(schedule)}/tasks"),
            json_data={
                "action": action,
                "payload": payload,
                "time_offset": time_offset,
                "continue_on_failure": continue_on_failure,
            },
        )

    async def update_task(self, server: str, schedule: int, task: int, **data: Any) -> Any:
        return await self._request(
            "POST",
            self._path(server, f"/{path_id(schedule)}/tasks/{path_id(task)}"),
            json_data=data,
        )

    async def delete_task(self, server: str, schedule: int, task: int) -> None:
        await self._request(
            "DELETE", self._path(server, f"/{path_id(schedule)}/tasks/{path_id(task)}")
        )


class NetworkResource(ServerSubresource):
    prefix = "network/allocations"

    async def list(self, server: str) -> Any:
        return await self._request("GET", self._path(server))

    async def assign(self, server: str) -> Any:
        return await self._request("POST", self._path(server))

    async def update(self, server: str, allocation: int, notes: str | None) -> Any:
        return await self._request(
            "POST",
            self._path(server, f"/{path_id(allocation)}"),
            json_data={"notes": notes},
        )

    async def set_primary(self, server: str, allocation: int) -> Any:
        return await self._request("POST", self._path(server, f"/{path_id(allocation)}/primary"))

    async def delete(self, server: str, allocation: int) -> None:
        await self._request("DELETE", self._path(server, f"/{path_id(allocation)}"))


class SubusersResource(ServerSubresource):
    prefix = "users"

    async def list(self, server: str) -> Any:
        return await self._request("GET", self._path(server))

    async def get(self, server: str, user: str) -> Any:
        return await self._request("GET", self._path(server, f"/{path_id(user)}"))

    async def create(self, server: str, email: str, permissions: Sequence[str]) -> Any:
        return await self._request(
            "POST",
            self._path(server),
            json_data={"email": email, "permissions": list(permissions)},
        )

    async def update(self, server: str, user: str, permissions: Sequence[str]) -> Any:
        return await self._request(
            "POST",
            self._path(server, f"/{path_id(user)}"),
            json_data={"permissions": list(permissions)},
        )

    async def delete(self, server: str, user: str) -> None:
        await self._request("DELETE", self._path(server, f"/{path_id(user)}"))


class BackupsResource(ServerSubresource):
    prefix = "backups"

    async def list(self, server: str) -> Any:
        return await self._request("GET", self._path(server))

    async def get(self, server: str, backup: str) -> Any:
        return await self._request("GET", self._path(server, f"/{path_id(backup)}"))

    async def create(
        self,
        server: str,
        *,
        name: str | None = None,
        ignored: str | None = None,
        is_locked: bool | None = None,
    ) -> Any:
        payload = _body(None, {"name": name, "ignored": ignored, "is_locked": is_locked})
        return await self._request("POST", self._path(server), json_data=payload)

    async def download_url(self, server: str, backup: str) -> Any:
        return await self._request("GET", self._path(server, f"/{path_id(backup)}/download"))

    async def toggle_lock(self, server: str, backup: str) -> None:
        await self._request("POST", self._path(server, f"/{path_id(backup)}/lock"))

    async def restore(
        self,
        server: str,
        backup: str,
        *,
        truncate: bool = False,
        download_url: str | None = None,
    ) -> Any:
        return await self._request(
            "POST",
            self._path(server, f"/{path_id(backup)}/restore"),
            json_data=_body(None, {"truncate": truncate, "download_url": download_url}),
        )

    async def delete(self, server: str, backup: str) -> None:
        await self._request("DELETE", self._path(server, f"/{path_id(backup)}"))


class StartupResource(ServerSubresource):
    prefix = "startup"

    async def get(self, server: str) -> Any:
        return await self._request("GET", self._path(server))

    async def update_variable(self, server: str, key: str, value: str) -> Any:
        return await self._request(
            "PUT", self._path(server, "/variable"), json_data={"key": key, "value": value}
        )


class SettingsResource(ServerSubresource):
    prefix = "settings"

    async def rename(self, server: str, name: str, description: str | None = None) -> None:
        await self._request(
            "POST",
            self._path(server, "/rename"),
            json_data=_body(None, {"name": name, "description": description}),
        )

    async def reinstall(self, server: str) -> Any:
        return await self._request("POST", self._path(server, "/reinstall"))

    async def update_docker_image(self, server: str, docker_image: str) -> None:
        await self._request(
            "PUT",
            self._path(server, "/docker-image"),
            json_data={"docker_image": docker_image},
        )


class ClientServersResource(APIResource):
    def __init__(self, transport: Any) -> None:
        super().__init__(transport)
        self.databases = ClientDatabasesResource(transport)
        self.files = FilesResource(transport)
        self.schedules = SchedulesResource(transport)
        self.network = NetworkResource(transport)
        self.users = SubusersResource(transport)
        self.backups = BackupsResource(transport)
        self.startup = StartupResource(transport)
        self.settings = SettingsResource(transport)

    def _path(self, server: str, suffix: str = "") -> str:
        return f"/client/servers/{path_id(server)}{suffix}"

    async def list(
        self,
        *,
        include: str | Iterable[str] | None = None,
        page: int | None = None,
        per_page: int | None = None,
        filters: Mapping[str, Any] | None = None,
        sort: str | Iterable[str] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        query = query_params(
            params, include=include, page=page, per_page=per_page, filters=filters, sort=sort
        )
        return await self._request("GET", "/client", params=query)

    def iter(self, **query: Any) -> AsyncIterator[dict[str, Any]]:
        return self._iter_list("/client", **query)

    async def permissions(self) -> Any:
        return await self._request("GET", "/client/permissions")

    async def get(self, server: str, *, include: str | Iterable[str] | None = None) -> Any:
        return await self._request("GET", self._path(server), params=query_params(include=include))

    async def resources(self, server: str) -> Any:
        return await self._request("GET", self._path(server, "/resources"))

    async def activity(
        self,
        server: str,
        *,
        page: int | None = None,
        per_page: int | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> Any:
        return await self._request(
            "GET",
            self._path(server, "/activity"),
            params=query_params(page=page, per_page=per_page, filters=filters),
        )

    async def websocket_credentials(self, server: str) -> Any:
        return await self._request("GET", self._path(server, "/websocket"))

    async def send_command(self, server: str, command: str) -> None:
        await self._request("POST", self._path(server, "/command"), json_data={"command": command})

    async def power(self, server: str, signal: str) -> None:
        if signal not in {"start", "stop", "restart", "kill"}:
            raise ValueError("signal must be one of: start, stop, restart, kill")
        await self._request("POST", self._path(server, "/power"), json_data={"signal": signal})


class ClientAPI(APIResource):
    def __init__(self, transport: Any) -> None:
        super().__init__(transport)
        self.account = AccountResource(transport)
        self.servers = ClientServersResource(transport)

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        path = path if path.startswith("/client") else f"/client/{path.lstrip('/')}"
        return await self._request(method, path, **kwargs)
