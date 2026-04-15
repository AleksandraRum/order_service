from application.dto import CreateOrderDTO
from domain.models import Order, OrderStatusEnum
from infrastructure.exceptions import NotEnoughStockError, OrderNotFoundError
from datetime import datetime, UTC


class CreateOrderUseCase:
    def __init__(self, catalog, repository):
        self.catalog = catalog
        self.repository = repository


    def __call__(self, dto: CreateOrderDTO):
        existing_order = self.repository.get_by_idempotency_key(dto.idempotency_key)
        if existing_order:
            return existing_order
        item_in_catalog = self.catalog.get_item(dto.item_id)
        if  item_in_catalog["available_qty"] < dto.quantity:
            raise NotEnoughStockError("Not enough items in stock")
        now = datetime.now(UTC)
        domain_order = Order(
            id=None,
            user_id=dto.user_id,
            item_id=dto.item_id,
            quantity=dto.quantity,
            status=OrderStatusEnum.NEW,
            created_at=now,
            updated_at=now
        )
        saved_order = self.repository.save(dto.idempotency_key, domain_order)
        return saved_order
    

class GetOrderUseCase:
    def __init__(self, repository):
        self.repository = repository
    
    def __call__(self, order_id):
        order = self.repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        return order
