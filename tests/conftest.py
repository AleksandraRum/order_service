import pytest
from datetime import datetime, UTC

from domain.models import Order, OrderStatusEnum


@pytest.fixture
def order_factory():
    def make_order(**kwargs):
        now = datetime.now(UTC)
        data = {
            "id": "order-1",
            "user_id": "user-1",
            "item_id": "item-1",
            "quantity": 2,
            "status": OrderStatusEnum.NEW,
            "created_at": now,
            "updated_at": now,
        }
        data.update(kwargs)
        return Order(**data)

    return make_order