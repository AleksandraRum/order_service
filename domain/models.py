from domain.exceptions import InvalidQuantityError
from enum import StrEnum


class OrderStatusEnum(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class Order:
    def __init__(self, id, user_id, item_id, quantity, status, created_at, updated_at):
        self.id = id
        self.user_id = user_id
        self.item_id = item_id
        if quantity <= 0:
            raise InvalidQuantityError("Quantity has to be positive")
        self.quantity = quantity
        self.status = OrderStatusEnum(status)
        self.created_at = created_at
        self.updated_at = updated_at