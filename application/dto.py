from pydantic import BaseModel
from enum import StrEnum


class PaymentCallbackStatusEnum(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CreateOrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: str
    idempotency_key: str


class PaymentCallbackDTO(BaseModel):
    order_id: str
    status: PaymentCallbackStatusEnum


