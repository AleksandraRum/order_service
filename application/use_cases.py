from application.dto import CreateOrderDTO, PaymentCallbackDTO, PaymentCallbackStatusEnum
from domain.models import Order, OrderStatusEnum
from domain.exceptions import PaymentCreationError
from infrastructure.exceptions import NotEnoughStockError, OrderNotFoundError, PaymentServiceError
from datetime import datetime, UTC
import os
from decimal import Decimal


class CreateOrderUseCase:
    def __init__(self, catalog, repository, payments_client):
        self.catalog = catalog
        self.repository = repository
        self.payments_client = payments_client


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
        callback_url_base = os.environ["CALLBACK_URL"]
        callback_url = f"{callback_url_base}/api/orders/payment-callback"
        order_id = saved_order.id
        idempotency_key = dto.idempotency_key
        amount = Decimal(item_in_catalog["price"]) * saved_order.quantity
        
        try:
            self.payments_client.create_payment(
                order_id=order_id,
                amount=str(amount),
                callback_url=callback_url,
                idempotency_key=idempotency_key,
            )
            
        except PaymentServiceError:
            saved_order = self.repository.update_status(order_id, OrderStatusEnum.CANCELLED)
            raise PaymentCreationError("Payment has failed")
    
        return saved_order
    


class GetOrderUseCase:
    def __init__(self, repository):
        self.repository = repository
    
    def __call__(self, order_id):
        order = self.repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        return order
    

class CallBackPaymentsUseCase:
    def __init__(self, repository):
        self.repository = repository

    def __call__(self, dto: PaymentCallbackDTO):
        order = self.repository.get_by_id(dto.order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        if order.status == OrderStatusEnum.NEW:
            if dto.status == PaymentCallbackStatusEnum.SUCCEEDED:
                return self.repository.update_status(dto.order_id, OrderStatusEnum.PAID)
            if dto.status == PaymentCallbackStatusEnum.FAILED:
                return self.repository.update_status(dto.order_id, OrderStatusEnum.CANCELLED)
        
        return order