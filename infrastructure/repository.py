import uuid

from sqlalchemy.orm import Session

from domain.models import Order
from infrastructure.db.models import OrderDB, OutboxDB, OutboxStatusEnum, InboxDB

from datetime import datetime, UTC
from infrastructure.exceptions import OrderNotFoundError

from sqlalchemy.exc import IntegrityError


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

    def save(self, order: Order):

        order_db = OrderDB(
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            idempotency_key=order.idempotency_key,
            status=order.status.value,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

        self.session.add(order_db)
        self.session.flush()

        return self._to_domain(order_db)
    
    def update_status(self, order_id, status):
      
        order_db = (
            self.session.query(OrderDB)
            .filter(OrderDB.id == uuid.UUID(order_id))
            .first()
        )
        if order_db is None:
            raise OrderNotFoundError("Order isn't found")
        
        now = datetime.now(UTC)
        order_db.status=status.value
        order_db.updated_at=now

        return self._to_domain(order_db)


    @staticmethod
    def _to_domain(order_db: OrderDB):
        return Order(
            id=str(order_db.id),
            user_id=order_db.user_id,
            item_id=order_db.item_id,
            quantity=order_db.quantity,
            idempotency_key=order_db.idempotency_key,
            status=order_db.status,
            created_at=order_db.created_at,
            updated_at=order_db.updated_at,
        )
    

class OutboxRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, event_type: str, payload: dict):
        event_outbox = OutboxDB(
            event_type=event_type,
            payload=payload,
            status=OutboxStatusEnum.PENDING.value,
            created_at=datetime.now(UTC),
        )
        self.session.add(event_outbox)


class InboxRepository:
    def __init__(self, session: Session):
        self.session = session

    def try_create(self, event_type:str, order_id: str, payload: dict):
        try:
            event_inbox = InboxDB(
                event_type=event_type,
                order_id=order_id,
                payload=payload,
                created_at=datetime.now(UTC),
            )
            self.session.add(event_inbox)
            self.session.flush()
            return True
        except IntegrityError:
            self.session.rollback()
            return False
        


    