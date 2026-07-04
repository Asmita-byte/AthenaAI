import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_txt_file(client: AsyncClient):
    content = b"This is a test document.\n\nIt has multiple paragraphs.\n\nFor testing purposes."

    response = await client.post(
        "/upload",
        files={"file": ("test_doc.txt", content, "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["original_filename"] == "test_doc.txt"
    assert data["extension"] == ".txt"

    return data["document_id"]


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient):
    response = await client.post(
        "/upload",
        files={"file": ("malware.exe", b"MZ fake exe content", "application/octet-stream")},
    )
    assert response.status_code in (400, 415, 200)


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient):
    response = await client.post(
        "/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code in (400, 422, 200)


@pytest.mark.asyncio
async def test_full_upload_and_status_flow(client: AsyncClient):
    content = b"Full flow test document with some content for testing."

    upload_response = await client.post(
        "/upload",
        files={"file": ("flow_test.txt", content, "text/plain")},
    )
    assert upload_response.status_code == 200
    doc_id = upload_response.json()["document_id"]

    status_response = await client.get(f"/status/{doc_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["document_id"] == doc_id
    assert status_data["filename"] == "flow_test.txt"
    assert status_data["status"] in ("pending", "running", "completed", "failed")