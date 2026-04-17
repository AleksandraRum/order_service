import pytest

from domain.models import OrderStatusEnum
from domain.exceptions import InvalidQuantityError


def test_order_is_created_with_valid_data(order_factory):
    order = order_factory()

    assert order.quantity == 2
    assert order.status == OrderStatusEnum.NEW


def test_order_raises_error_when_quantity_is_not_positive(order_factory):
    with pytest.raises(InvalidQuantityError):
        order_factory(quantity=0)