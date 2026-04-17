from pydantic import BaseModel
from application.dto import PaymentCallbackStatusEnum


class CreateOrderRequest(BaseModel):
    user_id: str
    quantity: int
    item_id: str
    idempotency_key: str


class PaymentCallbackRequest(BaseModel):
    payment_id: str
    order_id: str
    status: PaymentCallbackStatusEnum
    amount: str
    error_message: str | None
