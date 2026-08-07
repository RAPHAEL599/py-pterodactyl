from __future__ import annotations

from typing import Any

from .api import BasePterodactylAPI


class PterodactylClient(BasePterodactylAPI):
    def __init__(self, panel_url: str, api_key: str, *, timeout: int = 30) -> None:
        base_url = f"{panel_url.rstrip('/')}/api/client"
        super().__init__(base_url, api_key, timeout=timeout)

    @staticmethod
    def _build_params(
        include: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        filter: dict[str, Any] | None = None,
        sort: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if include is not None:
            params["include"] = include
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if filter is not None:
            params.update({f"filter[{key}]": value for key, value in filter.items()})
        if sort is not None:
            params["sort"] = sort
        if extra is not None:
            params.update(extra)
        return params

    async def account(self) -> Any:
        return await self.get("/")

    async def request_client(self, path: str, method: str = "GET", **kwargs: Any) -> Any:
        return await self.request(method, path, **kwargs)

    async def list_servers(
        self,
        *,
        include: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        filter: dict[str, Any] | None = None,
        sort: str | None = None,
    ) -> Any:
        params = self._build_params(include, page, per_page, filter, sort)
        return await self.get("/servers", params=params)

    async def get_server(self, server_id: str, *, include: str | None = None) -> Any:
        params = self._build_params(include)
        return await self.get(f"/servers/{server_id}", params=params)

    async def power_action(self, server_id: str, action: str) -> Any:
        return await self.post(f"/servers/{server_id}/power", json={"signal": action})

    async def send_console_command(self, server_id: str, command: str) -> Any:
        return await self.post(f"/servers/{server_id}/command", json={"command": command})

    async def websocket_token(self, server_id: str) -> Any:
        response = await self.get(f"/servers/{server_id}/websocket")
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    async def list_files(self, server_id: str, *, directory: str = "/", page: int | None = None, per_page: int | None = None) -> Any:
        params = self._build_params(extra={"directory": directory}, page=page, per_page=per_page)
        return await self.get(f"/servers/{server_id}/files", params=params)

    async def read_file(self, server_id: str, file: str) -> Any:
        return await self.get(f"/servers/{server_id}/files/contents", params={"file": file})

    async def download_file(self, server_id: str, file: str) -> Any:
        return await self.get(f"/servers/{server_id}/files/contents", params={"file": file, "download": "true"})

    async def create_directory(self, server_id: str, root: str, name: str) -> Any:
        return await self.post(f"/servers/{server_id}/files/create-folder", json={"root": root, "name": name})

    async def delete_file(self, server_id: str, file: str) -> Any:
        return await self.delete(f"/servers/{server_id}/files", params={"file": file})

    async def rename_file(self, server_id: str, location: str, name: str, root: str | None = None) -> Any:
        payload = {"location": location, "name": name}
        if root is not None:
            payload["root"] = root
        return await self.post(f"/servers/{server_id}/files/rename", json=payload)

    async def copy_file(self, server_id: str, location: str, target: str, root: str | None = None) -> Any:
        payload = {"location": target, "target": location}
        if root is not None:
            payload["root"] = root
        return await self.post(f"/servers/{server_id}/files/copy", json=payload)

    async def compress_file(self, server_id: str, root: str, files: list[str]) -> Any:
        return await self.post(f"/servers/{server_id}/files/compress", json={"root": root, "files": files})

    async def list_databases(self, server_id: str, *, page: int | None = None, per_page: int | None = None) -> Any:
        params = self._build_params(page=page, per_page=per_page)
        return await self.get(f"/servers/{server_id}/databases", params=params)

    async def create_database(self, server_id: str, database: str, remote: str) -> Any:
        return await self.post(f"/servers/{server_id}/databases", json={"database": database, "remote": remote})

    async def rotate_database_password(self, server_id: str, database_id: str) -> Any:
        return await self.post(f"/servers/{server_id}/databases/{database_id}/rotate")

    async def delete_database(self, server_id: str, database_id: str) -> Any:
        return await self.delete(f"/servers/{server_id}/databases/{database_id}")

    async def list_schedules(self, server_id: str, *, page: int | None = None, per_page: int | None = None) -> Any:
        params = self._build_params(page=page, per_page=per_page)
        return await self.get(f"/servers/{server_id}/schedules", params=params)

    async def get_schedule(self, server_id: str, schedule_id: str) -> Any:
        return await self.get(f"/servers/{server_id}/schedules/{schedule_id}")

    async def create_schedule(self, server_id: str, payload: dict[str, Any]) -> Any:
        return await self.post(f"/servers/{server_id}/schedules", json=payload)

    async def update_schedule(self, server_id: str, schedule_id: str, payload: dict[str, Any]) -> Any:
        return await self.patch(f"/servers/{server_id}/schedules/{schedule_id}", json=payload)

    async def delete_schedule(self, server_id: str, schedule_id: str) -> Any:
        return await self.delete(f"/servers/{server_id}/schedules/{schedule_id}")

    async def execute_schedule(self, server_id: str, schedule_id: str) -> Any:
        return await self.post(f"/servers/{server_id}/schedules/{schedule_id}/execute")

    async def list_allocations(self, server_id: str) -> Any:
        return await self.get(f"/servers/{server_id}/network/allocations")

    async def list_users(self, server_id: str, *, page: int | None = None, per_page: int | None = None) -> Any:
        params = self._build_params(page=page, per_page=per_page)
        return await self.get(f"/servers/{server_id}/users", params=params)

    async def create_subuser(self, server_id: str, payload: dict[str, Any]) -> Any:
        return await self.post(f"/servers/{server_id}/users", json=payload)

    async def delete_subuser(self, server_id: str, subuser_id: str) -> Any:
        return await self.delete(f"/servers/{server_id}/users/{subuser_id}")

    async def list_backups(self, server_id: str) -> Any:
        return await self.get(f"/servers/{server_id}/backups")

    async def create_backup(self, server_id: str, payload: dict[str, Any]) -> Any:
        return await self.post(f"/servers/{server_id}/backups", json=payload)

    async def delete_backup(self, server_id: str, backup_id: str) -> Any:
        return await self.delete(f"/servers/{server_id}/backups/{backup_id}")
