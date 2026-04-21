from application.dto import CreateOrderDTO, PaymentCallbackDTO, PaymentCallbackStatusEnum, ShipmentEventDTO, ShipmentEventTypeEnum
from domain.models import Order, OrderStatusEnum
from domain.exceptions import PaymentCreationError
from infrastructure.exceptions import NotEnoughStockError, OrderNotFoundError, PaymentServiceError
from datetime import datetime, UTC
import os
from decimal import Decimal


class CreateOrderUseCase:
    def __init__(self, catalog, uow, payments_client):
        self.catalog = catalog
        self.uow = uow
        self.payments_client = payments_client


    def __call__(self, dto: CreateOrderDTO):
        existing_order = self.uow.orders.get_by_idempotency_key(dto.idempotency_key)
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
            idempotency_key=dto.idempotency_key,
            status=OrderStatusEnum.NEW,
            created_at=now,
            updated_at=now
        )
        saved_order = self.uow.orders.save(domain_order)
        self.uow.commit()
        callback_url_base = os.environ["CALLBACK_URL"]
        callback_url = f"{callback_url_base}/api/orders/payment-callback"
        order_id = saved_order.id
        idempotency_key = saved_order.idempotency_key
        amount = Decimal(item_in_catalog["price"]) * saved_order.quantity
        
        try:
            self.payments_client.create_payment(
                order_id=order_id,
                amount=str(amount),
                callback_url=callback_url,
                idempotency_key=idempotency_key,
            )
            
        except PaymentServiceError:
            saved_order = self.uow.orders.update_status(order_id, OrderStatusEnum.CANCELLED)
            self.uow.commit()
            raise PaymentCreationError("Payment has failed")
    
        return saved_order
    


class GetOrderUseCase:
    def __init__(self, uow):
        self.uow = uow
    
    def __call__(self, order_id):
        order = self.uow.orders.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        return order
    

class CallBackPaymentsUseCase:
    def __init__(self, uow):
        self.uow = uow

    def __call__(self, dto: PaymentCallbackDTO):
        order = self.uow.orders.get_by_id(dto.order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        if order.status == OrderStatusEnum.NEW:
            if dto.status == PaymentCallbackStatusEnum.SUCCEEDED:
                updated_order = self.uow.orders.update_status(dto.order_id, OrderStatusEnum.PAID)
                self.uow.outbox.create(
                    event_type="order.paid",
                    payload={
                        "order_id": order.id,
                        "item_id": order.item_id,
                        "quantity": order.quantity,
                        "idempotency_key": order.idempotency_key
                    },
                )
                self.uow.commit()
            elif dto.status == PaymentCallbackStatusEnum.FAILED:
                updated_order = self.uow.orders.update_status(dto.order_id, OrderStatusEnum.CANCELLED)
                self.uow.commit()
            return updated_order
        return order
    

class ShipmentEventUseCase:
    def __init__(self, uow):
        self.uow = uow

    def __call__ (self, dto: ShipmentEventDTO):
        event_type = dto.event_type.value
        order_id = dto.order_id
        payload = {
            "item_id": dto.item_id,
            "quantity": dto.quantity,
            "shipment_id": dto.shipment_id,
            "reason": dto.reason
        }

        res = self.uow.inbox.try_create(event_type=event_type, order_id=order_id, payload=payload)
        if not res:
            return None
        
        order = self.uow.orders.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        
        if event_type == ShipmentEventTypeEnum.SHIPPED.value:
            updated_order = self.uow.orders.update_status(order_id, OrderStatusEnum.SHIPPED)
        elif event_type == ShipmentEventTypeEnum.CANCELLED.value:
            updated_order = self.uow.orders.update_status(order_id, OrderStatusEnum.CANCELLED)
        else:
            return None
        self.uow.commit()
        return updated_order
