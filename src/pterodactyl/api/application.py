"""Complete asynchronous implementation of the Pterodactyl Application API."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from typing import Any

from .base import APIResource, path_id, query_params


class ApplicationCollection(APIResource):
    path = ""

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
        return await self._request("GET", self.path, params=query)

    def iter(self, **query: Any) -> AsyncIterator[dict[str, Any]]:
        return self._iter_list(self.path, **query)

    async def get(self, resource_id: Any, *, include: str | Iterable[str] | None = None) -> Any:
        return await self._request(
            "GET", f"{self.path}/{path_id(resource_id)}", params=query_params(include=include)
        )


class ApplicationUsersResource(ApplicationCollection):
    path = "/application/users"

    async def get_by_external_id(
        self, external_id: str, *, include: str | Iterable[str] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            f"{self.path}/external/{path_id(external_id)}",
            params=query_params(include=include),
        )

    async def create(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        *,
        password: str | None = None,
        external_id: str | None = None,
        root_admin: bool | None = None,
        language: str | None = None,
        **extra: Any,
    ) -> Any:
        payload = {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            **extra,
        }
        optional = {
            "password": password,
            "external_id": external_id,
            "root_admin": root_admin,
            "language": language,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})
        return await self._request("POST", self.path, json_data=payload)

    async def update(self, user: int, **data: Any) -> Any:
        return await self._request("PATCH", f"{self.path}/{path_id(user)}", json_data=data)

    async def delete(self, user: int) -> None:
        await self._request("DELETE", f"{self.path}/{path_id(user)}")


class NodeAllocationsResource(APIResource):
    def _path(self, node: int, suffix: str = "") -> str:
        return f"/application/nodes/{path_id(node)}/allocations{suffix}"

    async def list(
        self,
        node: int,
        *,
        page: int | None = None,
        per_page: int | None = None,
        filters: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return await self._request(
            "GET",
            self._path(node),
            params=query_params(params, page=page, per_page=per_page, filters=filters),
        )

    async def create(
        self,
        node: int,
        ip: str,
        ports: Sequence[str | int],
        *,
        alias: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"ip": ip, "ports": list(ports)}
        if alias is not None:
            payload["alias"] = alias
        return await self._request("POST", self._path(node), json_data=payload)

    async def delete(self, node: int, allocation: int) -> None:
        await self._request("DELETE", self._path(node, f"/{path_id(allocation)}"))


class ApplicationNodesResource(ApplicationCollection):
    path = "/application/nodes"

    def __init__(self, transport: Any) -> None:
        super().__init__(transport)
        self.allocations = NodeAllocationsResource(transport)

    async def deployable(
        self,
        *,
        memory: int | None = None,
        disk: int | None = None,
        location_ids: Sequence[int] | None = None,
        include: str | Iterable[str] | None = None,
    ) -> Any:
        params = {"memory": memory, "disk": disk}
        if location_ids is not None:
            params["location_ids"] = ",".join(str(item) for item in location_ids)
        return await self._request(
            "GET", f"{self.path}/deployable", params=query_params(params, include=include)
        )

    async def configuration(self, node: int) -> Any:
        return await self._request("GET", f"{self.path}/{path_id(node)}/configuration")

    async def create(self, **data: Any) -> Any:
        return await self._request("POST", self.path, json_data=data)

    async def update(self, node: int, **data: Any) -> Any:
        return await self._request("PATCH", f"{self.path}/{path_id(node)}", json_data=data)

    async def delete(self, node: int) -> None:
        await self._request("DELETE", f"{self.path}/{path_id(node)}")


class ApplicationLocationsResource(ApplicationCollection):
    path = "/application/locations"

    async def create(self, short: str, *, long: str | None = None) -> Any:
        payload = {"short": short}
        if long is not None:
            payload["long"] = long
        return await self._request("POST", self.path, json_data=payload)

    async def update(self, location: int, **data: Any) -> Any:
        return await self._request("PATCH", f"{self.path}/{path_id(location)}", json_data=data)

    async def delete(self, location: int) -> None:
        await self._request("DELETE", f"{self.path}/{path_id(location)}")


class ApplicationDatabasesResource(APIResource):
    def _path(self, server: int, suffix: str = "") -> str:
        return f"/application/servers/{path_id(server)}/databases{suffix}"

    async def list(
        self,
        server: int,
        *,
        include: str | Iterable[str] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> Any:
        return await self._request(
            "GET",
            self._path(server),
            params=query_params(include=include, page=page, per_page=per_page),
        )

    async def get(
        self, server: int, database: int, *, include: str | Iterable[str] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            self._path(server, f"/{path_id(database)}"),
            params=query_params(include=include),
        )

    async def create(self, server: int, database: str, remote: str, host: int, **extra: Any) -> Any:
        payload = {"database": database, "remote": remote, "host": host, **extra}
        return await self._request("POST", self._path(server), json_data=payload)

    async def update(self, server: int, database: int, **data: Any) -> Any:
        """Compatibility route present in PteroAPI but not in unmodified Panel 1.x."""

        return await self._request(
            "PATCH", self._path(server, f"/{path_id(database)}"), json_data=data
        )

    async def reset_password(self, server: int, database: int) -> Any:
        return await self._request(
            "POST", self._path(server, f"/{path_id(database)}/reset-password")
        )

    async def delete(self, server: int, database: int) -> None:
        await self._request("DELETE", self._path(server, f"/{path_id(database)}"))


class ApplicationServersResource(ApplicationCollection):
    path = "/application/servers"

    def __init__(self, transport: Any) -> None:
        super().__init__(transport)
        self.databases = ApplicationDatabasesResource(transport)

    async def get_by_external_id(
        self, external_id: str, *, include: str | Iterable[str] | None = None
    ) -> Any:
        return await self._request(
            "GET",
            f"{self.path}/external/{path_id(external_id)}",
            params=query_params(include=include),
        )

    async def create(self, **data: Any) -> Any:
        return await self._request("POST", self.path, json_data=data)

    async def update_details(self, server: int, **data: Any) -> Any:
        return await self._request(
            "PATCH", f"{self.path}/{path_id(server)}/details", json_data=data
        )

    async def update_build(self, server: int, **data: Any) -> Any:
        return await self._request("PATCH", f"{self.path}/{path_id(server)}/build", json_data=data)

    async def update_startup(self, server: int, **data: Any) -> Any:
        return await self._request(
            "PATCH", f"{self.path}/{path_id(server)}/startup", json_data=data
        )

    async def suspend(self, server: int) -> None:
        await self._request("POST", f"{self.path}/{path_id(server)}/suspend")

    async def unsuspend(self, server: int) -> None:
        await self._request("POST", f"{self.path}/{path_id(server)}/unsuspend")

    async def reinstall(self, server: int) -> None:
        await self._request("POST", f"{self.path}/{path_id(server)}/reinstall")

    async def delete(self, server: int, *, force: bool = False) -> None:
        suffix = "/force" if force else ""
        await self._request("DELETE", f"{self.path}/{path_id(server)}{suffix}")


class NestEggsResource(APIResource):
    def _path(self, nest: int, suffix: str = "") -> str:
        return f"/application/nests/{path_id(nest)}/eggs{suffix}"

    async def list(
        self,
        nest: int,
        *,
        include: str | Iterable[str] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> Any:
        return await self._request(
            "GET",
            self._path(nest),
            params=query_params(include=include, page=page, per_page=per_page),
        )

    async def get(self, nest: int, egg: int, *, include: str | Iterable[str] | None = None) -> Any:
        return await self._request(
            "GET",
            self._path(nest, f"/{path_id(egg)}"),
            params=query_params(include=include),
        )


class ApplicationNestsResource(ApplicationCollection):
    path = "/application/nests"

    def __init__(self, transport: Any) -> None:
        super().__init__(transport)
        self.eggs = NestEggsResource(transport)


class ApplicationAPI(APIResource):
    def __init__(self, transport: Any) -> None:
        super().__init__(transport)
        self.users = ApplicationUsersResource(transport)
        self.nodes = ApplicationNodesResource(transport)
        self.locations = ApplicationLocationsResource(transport)
        self.servers = ApplicationServersResource(transport)
        self.nests = ApplicationNestsResource(transport)

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        path = path if path.startswith("/application") else f"/application/{path.lstrip('/')}"
        return await self._request(method, path, **kwargs)
