from pydantic import BaseModel
from enum import StrEnum


class PaymentCallbackStatusEnum(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ShipmentEventTypeEnum(StrEnum):
    SHIPPED = "order.shipped"
    CANCELLED = "order.cancelled"


class CreateOrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: str
    idempotency_key: str


class PaymentCallbackDTO(BaseModel):
    order_id: str
    status: PaymentCallbackStatusEnum


class ShipmentEventDTO(BaseModel):
    event_type: ShipmentEventTypeEnum
    order_id: str
    item_id:str
    quantity: int
    shipment_id: str | None
    reason: str | None


