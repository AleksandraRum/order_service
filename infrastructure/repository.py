import uuid

from sqlalchemy.orm import Session

from domain.models import Order
from infrastructure.db.models import OrderDB


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_idempotency_key(self, key: str):
        order_db = (
            self.session.query(OrderDB)
            .filter(OrderDB.idempotency_key == key)
            .first()
        )

        if order_db is None:
            return None

        return self._to_domain(order_db)

    def get_by_id(self, order_id: str):
        order_db = (
            self.session.query(OrderDB)
            .filter(OrderDB.id == uuid.UUID(order_id))
            .first()
        )

        if order_db is None:
            return None

        return self._to_domain(order_db)

    def save(self, key: str, order: Order):

        order_db = OrderDB(
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            idempotency_key=key,
            status=order.status.value,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

        self.session.add(order_db)
        self.session.commit()
        self.session.refresh(order_db)

        return self._to_domain(order_db)

    @staticmethod
    def _to_domain(order_db: OrderDB):
        return Order(
            id=str(order_db.id),
            user_id=order_db.user_id,
            item_id=order_db.item_id,
            quantity=order_db.quantity,
            status=order_db.status,
            created_at=order_db.created_at,
            updated_at=order_db.updated_at,
        )
