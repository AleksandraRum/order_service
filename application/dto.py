from pydantic import BaseModel


class CreateOrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: str
    idempotency_key: str
