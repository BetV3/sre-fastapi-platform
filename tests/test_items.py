"""Tests for items API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient) -> None:
    """Test listing items."""
    response = await client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_get_item(client: AsyncClient) -> None:
    """Test getting a single item."""
    response = await client.get("/api/v1/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert "name" in data
    assert "price" in data


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent item."""
    response = await client.get("/api/v1/items/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient) -> None:
    """Test creating an item."""
    response = await client.post(
        "/api/v1/items",
        json={
            "name": "Test Item",
            "description": "A test item",
            "price": 29.99,
            "quantity": 10,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 29.99
    assert "id" in data


@pytest.mark.asyncio
async def test_create_item_validation_error(client: AsyncClient) -> None:
    """Test creating an item with invalid data."""
    response = await client.post(
        "/api/v1/items",
        json={
            "name": "",  # Invalid: empty name
            "price": -10,  # Invalid: negative price
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient) -> None:
    """Test updating an item."""
    response = await client.put(
        "/api/v1/items/1",
        json={"name": "Updated Widget"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Widget"


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient) -> None:
    """Test deleting an item."""
    # First create an item
    create_response = await client.post(
        "/api/v1/items",
        json={"name": "To Delete", "price": 5.99},
    )
    item_id = create_response.json()["id"]

    # Then delete it
    response = await client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await client.get(f"/api/v1/items/{item_id}")
    assert get_response.status_code == 404
