"""Shared API resource utilities."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping
from typing import Any
from urllib.parse import quote

from ..transport import AsyncTransport


def path_id(value: Any) -> str:
    """Encode a resource identifier for safe use in a URL path."""

    return quote(str(value), safe="")


def query_params(
    params: Mapping[str, Any] | None = None,
    *,
    include: str | Iterable[str] | None = None,
    page: int | None = None,
    per_page: int | None = None,
    filters: Mapping[str, Any] | None = None,
    sort: str | Iterable[str] | None = None,
) -> dict[str, Any]:
    result = {key: value for key, value in (params or {}).items() if value is not None}
    if include is not None:
        result["include"] = include if isinstance(include, str) else ",".join(include)
    if page is not None:
        result["page"] = page
    if per_page is not None:
        result["per_page"] = per_page
    if filters:
        result.update(
            {f"filter[{key}]": value for key, value in filters.items() if value is not None}
        )
    if sort is not None:
        result["sort"] = sort if isinstance(sort, str) else ",".join(sort)
    return result


class APIResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return await self._transport.request(method, path, **kwargs)

    async def _iter_list(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        current_page = int(query.pop("page", None) or 1)
        while True:
            request_params = query_params(params, page=current_page, **query)
            payload = await self._request("GET", path, params=request_params)
            if not isinstance(payload, dict):
                return
            data = payload.get("data", [])
            if not isinstance(data, list):
                return
            for item in data:
                if isinstance(item, dict):
                    yield item
            pagination = payload.get("meta", {}).get("pagination", {})
            total_pages = int(pagination.get("total_pages", current_page))
            if current_page >= total_pages:
                return
            current_page += 1
