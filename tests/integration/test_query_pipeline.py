import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_query_validation_empty_string(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/query",
        json={
            "query": "",
            "top_k": 8,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_query_validation_top_k_zero(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/query",
        json={
            "query": "test query",
            "top_k": 0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_status_nonexistent_document(client: AsyncClient, auth_headers: dict):
    response = await client.get("/status/nonexistent-doc-id", headers=auth_headers)
    assert response.status_code in (404, 200)


@pytest.mark.asyncio
async def test_evaluate_endpoint(client: AsyncClient):
    response = await client.post("/evaluate", json={"sample_size": 5})
    assert response.status_code == 200
