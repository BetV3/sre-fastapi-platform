"""Example items API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel, Field

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.core.redis import cache
from app.models.common import MessageResponse, PaginatedResponse

logger = get_logger(__name__)

router = APIRouter()


# Models
class ItemBase(BaseModel):
    """Base item model."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Item price")
    quantity: int = Field(default=0, ge=0, description="Item quantity")


class ItemCreate(ItemBase):
    """Model for creating an item."""

    pass


class ItemUpdate(BaseModel):
    """Model for updating an item."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    price: float | None = Field(None, gt=0)
    quantity: int | None = Field(None, ge=0)


class Item(ItemBase):
    """Item response model."""

    id: str


# In-memory storage for demo (use a database in production)
_items_db: dict[str, Item] = {
    "1": Item(id="1", name="Widget", description="A useful widget", price=9.99, quantity=100),
    "2": Item(id="2", name="Gadget", description="A cool gadget", price=19.99, quantity=50),
}
_item_counter = 2


# Dependencies
async def get_item_or_404(
    item_id: Annotated[str, Path(description="The item ID")],
) -> Item:
    """Get an item by ID or raise 404."""
    if item_id not in _items_db:
        raise NotFoundError(f"Item with ID '{item_id}' not found")
    return _items_db[item_id]


# Endpoints
@router.get(
    "",
    response_model=PaginatedResponse[Item],
    summary="List Items",
    description="Get a paginated list of all items.",
)
async def list_items(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
) -> PaginatedResponse[Item]:
    """List all items with pagination."""
    items = list(_items_db.values())
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]

    return PaginatedResponse.create(
        items=paginated_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    summary="Create Item",
    description="Create a new item.",
)
async def create_item(item: ItemCreate) -> Item:
    """Create a new item."""
    global _item_counter
    _item_counter += 1
    item_id = str(_item_counter)

    new_item = Item(id=item_id, **item.model_dump())
    _items_db[item_id] = new_item

    logger.info("item_created", item_id=item_id, name=item.name)

    # Invalidate any list cache
    await cache.delete("items:list")

    return new_item


@router.get(
    "/{item_id}",
    response_model=Item,
    summary="Get Item",
    description="Get a specific item by ID.",
)
async def get_item(
    item: Annotated[Item, Depends(get_item_or_404)],
) -> Item:
    """Get an item by ID."""
    return item


@router.put(
    "/{item_id}",
    response_model=Item,
    summary="Update Item",
    description="Update an existing item.",
)
async def update_item(
    item_id: Annotated[str, Path(description="The item ID")],
    update: ItemUpdate,
    item: Annotated[Item, Depends(get_item_or_404)],
) -> Item:
    """Update an item."""
    update_data = update.model_dump(exclude_unset=True)
    updated_item = item.model_copy(update=update_data)
    _items_db[item_id] = updated_item

    logger.info("item_updated", item_id=item_id)

    return updated_item


@router.delete(
    "/{item_id}",
    response_model=MessageResponse,
    summary="Delete Item",
    description="Delete an item.",
)
async def delete_item(
    item_id: Annotated[str, Path(description="The item ID")],
    item: Annotated[Item, Depends(get_item_or_404)],
) -> MessageResponse:
    """Delete an item."""
    del _items_db[item_id]

    logger.info("item_deleted", item_id=item_id)

    return MessageResponse(message=f"Item '{item_id}' deleted successfully")
