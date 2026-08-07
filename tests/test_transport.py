import httpx
import pytest

from pterodactyl import NotFoundError, Pterodactyl, RateLimitError


@pytest.mark.asyncio
async def test_request_headers_url_query_and_json_decoding() -> None:
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200,
            json={"object": "list", "data": []},
            headers={"Content-Type": "application/json"},
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with http:
        panel = Pterodactyl("https://panel.example/", "ptlc_secret", http_client=http)
        result = await panel.client.servers.list(
            include=["allocations", "egg"],
            filters={"name": "Lobby"},
            page=2,
            per_page=25,
        )

    request = captured["request"]
    assert str(request.url).startswith("https://panel.example/api/client?")
    assert request.url.params["include"] == "allocations,egg"
    assert request.url.params["filter[name]"] == "Lobby"
    assert request.headers["Authorization"] == "Bearer ptlc_secret"
    assert result == {"object": "list", "data": []}


@pytest.mark.asyncio
async def test_empty_and_text_responses() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/contents"):
            return httpx.Response(200, text="hello", headers={"Content-Type": "text/plain"})
        return httpx.Response(204)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with http:
        panel = Pterodactyl("https://panel.example", "key", http_client=http)
        assert await panel.client.servers.files.contents("abc", "/hello.txt") == "hello"
        assert await panel.client.servers.power("abc", "start") is None


@pytest.mark.asyncio
async def test_typed_api_errors_preserve_details() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("missing"):
            return httpx.Response(
                404,
                json={"errors": [{"code": "NotFoundHttpException", "detail": "Missing"}]},
            )
        return httpx.Response(
            429, json={"errors": [{"detail": "Slow down"}]}, headers={"Retry-After": "4"}
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with http:
        panel = Pterodactyl("https://panel.example", "key", http_client=http)
        with pytest.raises(NotFoundError) as not_found:
            await panel.client.servers.get("missing")
        assert not_found.value.errors[0]["detail"] == "Missing"

        with pytest.raises(RateLimitError) as limited:
            await panel.request("GET", "/api/limited")
        assert limited.value.retry_after == 4


@pytest.mark.asyncio
async def test_async_pagination_iterator() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        return httpx.Response(
            200,
            json={
                "data": [{"attributes": {"id": page}}],
                "meta": {"pagination": {"current_page": page, "total_pages": 3}},
            },
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    async with http:
        panel = Pterodactyl("https://panel.example", "key", http_client=http)
        items = [item async for item in panel.application.servers.iter(per_page=1)]
    assert [item["attributes"]["id"] for item in items] == [1, 2, 3]
