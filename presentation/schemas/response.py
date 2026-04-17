from pydantic import BaseModel
from datetime import datetime


class OrderResponse(BaseModel):
    id: str | None
    user_id: str
    quantity: int
    item_id: str
    status: str
    created_at: datetime
    updated_at: datetime