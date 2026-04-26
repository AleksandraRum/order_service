from unittest.mock import MagicMock

import pytest

from application.dto import CreateOrderDTO
from application.use_cases import CreateOrderUseCase
from infrastructure.exceptions import NotEnoughStockError


def test_create_order_returns_existing_order_when_idempotency_key_exists(order_factory):
    existing_order = order_factory()

    repository = MagicMock()
    repository.get_by_idempotency_key.return_value = existing_order

    catalog = MagicMock()
    payments_client = MagicMock()

    use_case = CreateOrderUseCase(
        catalog=catalog,
        repository=repository,
        payments_client=payments_client,
    )

    dto = CreateOrderDTO(
        user_id="user-1",
        quantity=2,
        item_id="item-1",
        idempotency_key="same-key",
    )

    result = use_case(dto)

    assert result == existing_order
    catalog.get_item.assert_not_called()
    repository.save.assert_not_called()
    payments_client.create_payment.assert_not_called()


def test_create_order_raises_error_when_not_enough_stock():
    repository = MagicMock()
    repository.get_by_idempotency_key.return_value = None

    catalog = MagicMock()
    catalog.get_item.return_value = {"available_qty": 1, "price": "100.00"}

    payments_client = MagicMock()

    use_case = CreateOrderUseCase(
        catalog=catalog,
        repository=repository,
        payments_client=payments_client,
    )

    dto = CreateOrderDTO(
        user_id="user-1",
        quantity=5,
        item_id="item-1",
        idempotency_key="key-1",
    )

    with pytest.raises(NotEnoughStockError):
        use_case(dto)

    repository.save.assert_not_called()
    payments_client.create_payment.assert_not_called()


def test_create_order_successful_case(order_factory, monkeypatch):
    monkeypatch.setenv("CALLBACK_URL", "http://test-service")

    repository = MagicMock()
    repository.get_by_idempotency_key.return_value = None
    saved_order = order_factory()
    repository.save.return_value = saved_order
    catalog = MagicMock()
    catalog.get_item.return_value = {
        "id": "item-1",
        "name": "Product Name",
        "price": "100.00",
        "available_qty": 10,
        "created_at": "2024-01-01T00:00:00Z",
    }

    payments_client = MagicMock()

    use_case = CreateOrderUseCase(
        catalog=catalog,
        repository=repository,
        payments_client=payments_client,
    )

    dto = CreateOrderDTO(
        user_id="user-1",
        quantity=2,
        item_id="item-1",
        idempotency_key="key-1",
    )

    result = use_case(dto)

    assert result == saved_order
    repository.save.assert_called_once()
    payments_client.create_payment.assert_called_once()
