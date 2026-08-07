from __future__ import annotations

from typing import Any

from .api import BasePterodactylAPI


class PterodactylApplicationClient(BasePterodactylAPI):
    def __init__(self, panel_url: str, api_key: str, *, timeout: int = 30) -> None:
        base_url = f"{panel_url.rstrip('/')}/api/application"
        super().__init__(base_url, api_key, timeout=timeout)

    async def list_users(self, *, include: str | None = None, page: int | None = None, per_page: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if include is not None:
            params["include"] = include
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return await self.get("/users", params=params)

    async def get_user(self, user_id: str, *, include: str | None = None) -> Any:
        params = {"include": include} if include else None
        return await self.get(f"/users/{user_id}", params=params)

    async def create_user(self, payload: dict[str, Any]) -> Any:
        return await self.post("/users", json=payload)

    async def update_user(self, user_id: str, payload: dict[str, Any]) -> Any:
        return await self.patch(f"/users/{user_id}", json=payload)

    async def delete_user(self, user_id: str) -> Any:
        return await self.delete(f"/users/{user_id}")

    async def list_servers(self, *, include: str | None = None, page: int | None = None, per_page: int | None = None, filter: dict[str, Any] | None = None, sort: str | None = None) -> Any:
        params: dict[str, Any] = {}
        if include is not None:
            params["include"] = include
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if sort is not None:
            params["sort"] = sort
        if filter is not None:
            params.update({f"filter[{key}]": value for key, value in filter.items()})
        return await self.get("/servers", params=params)

    async def get_server(self, server_id: str, *, include: str | None = None) -> Any:
        params = {"include": include} if include else None
        return await self.get(f"/servers/{server_id}", params=params)

    async def create_server(self, payload: dict[str, Any]) -> Any:
        return await self.post("/servers", json=payload)

    async def update_server(self, server_id: str, payload: dict[str, Any]) -> Any:
        return await self.patch(f"/servers/{server_id}", json=payload)

    async def suspend_server(self, server_id: str) -> Any:
        return await self.post(f"/servers/{server_id}/suspend")

    async def unsuspend_server(self, server_id: str) -> Any:
        return await self.post(f"/servers/{server_id}/unsuspend")

    async def reinstall_server(self, server_id: str) -> Any:
        return await self.post(f"/servers/{server_id}/reinstall")

    async def delete_server(self, server_id: str) -> Any:
        return await self.delete(f"/servers/{server_id}")

    async def list_nodes(self, *, include: str | None = None, page: int | None = None, per_page: int | None = None, sort: str | None = None, filter: dict[str, Any] | None = None) -> Any:
        params: dict[str, Any] = {}
        if include is not None:
            params["include"] = include
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if sort is not None:
            params["sort"] = sort
        if filter is not None:
            params.update({f"filter[{key}]": value for key, value in filter.items()})
        return await self.get("/nodes", params=params)

    async def get_node(self, node_id: str, *, include: str | None = None) -> Any:
        params = {"include": include} if include else None
        return await self.get(f"/nodes/{node_id}", params=params)

    async def create_node(self, payload: dict[str, Any]) -> Any:
        return await self.post("/nodes", json=payload)

    async def update_node(self, node_id: str, payload: dict[str, Any]) -> Any:
        return await self.patch(f"/nodes/{node_id}", json=payload)

    async def delete_node(self, node_id: str) -> Any:
        return await self.delete(f"/nodes/{node_id}")

    async def list_locations(self, *, page: int | None = None, per_page: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return await self.get("/locations", params=params)

    async def get_location(self, location_id: str) -> Any:
        return await self.get(f"/locations/{location_id}")

    async def create_location(self, payload: dict[str, Any]) -> Any:
        return await self.post("/locations", json=payload)

    async def update_location(self, location_id: str, payload: dict[str, Any]) -> Any:
        return await self.patch(f"/locations/{location_id}", json=payload)

    async def delete_location(self, location_id: str) -> Any:
        return await self.delete(f"/locations/{location_id}")

    async def list_nests(self, *, page: int | None = None, per_page: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return await self.get("/nests", params=params)

    async def get_nest(self, nest_id: str) -> Any:
        return await self.get(f"/nests/{nest_id}")

    async def list_eggs(self, *, include: str | None = None, page: int | None = None, per_page: int | None = None, filter: dict[str, Any] | None = None) -> Any:
        params: dict[str, Any] = {}
        if include is not None:
            params["include"] = include
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if filter is not None:
            params.update({f"filter[{key}]": value for key, value in filter.items()})
        return await self.get("/eggs", params=params)

    async def get_egg(self, egg_id: str, *, include: str | None = None) -> Any:
        params = {"include": include} if include else None
        return await self.get(f"/eggs/{egg_id}", params=params)
