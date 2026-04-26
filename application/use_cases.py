from datetime import UTC, datetime
from decimal import Decimal

from application.dto import (
    CreateOrderDTO,
    PaymentCallbackDTO,
    PaymentCallbackStatusEnum,
    ShipmentEventDTO,
    ShipmentEventTypeEnum,
)
from domain.exceptions import PaymentCreationError
from domain.models import Order, OrderStatusEnum
from infrastructure.exceptions import (
    NotEnoughStockError,
    NotificationServiceError,
    OrderNotFoundError,
    PaymentServiceError,
)
from infrastructure.kafka.producer import send_event


class CreateOrderUseCase:
    def __init__(
        self, catalog, uow, payments_client, notification_client, callback_url
    ):
        self.catalog = catalog
        self.uow = uow
        self.payments_client = payments_client
        self.notification_client = notification_client
        self.callback_url = callback_url

    def __call__(self, dto: CreateOrderDTO):
        existing_order = self.uow.orders.get_by_idempotency_key(dto.idempotency_key)
        if existing_order:
            return existing_order
        item_in_catalog = self.catalog.get_item(dto.item_id)
        if item_in_catalog["available_qty"] < dto.quantity:
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
            updated_at=now,
        )
        saved_order = self.uow.orders.save(domain_order)
        self.uow.commit()
        order_id = saved_order.id

        message = "NEW: Ваш заказ создан и ожидает оплаты"
        idempotency_key_notification = f"Notification:{order_id}:new"
        try:
            self.notification_client.send_notification(
                message=message,
                reference_id=order_id,
                idempotency_key=idempotency_key_notification,
            )
        except NotificationServiceError:
            print(
                "Notification service is unavailable. Message about new order wasn't sent."
            )
        idempotency_key = saved_order.idempotency_key
        callback_url = f"{self.callback_url}/api/orders/payment-callback"

        amount = Decimal(item_in_catalog["price"]) * saved_order.quantity

        try:
            self.payments_client.create_payment(
                order_id=order_id,
                amount=str(amount),
                callback_url=callback_url,
                idempotency_key=idempotency_key,
            )

        except PaymentServiceError:
            saved_order = self.uow.orders.update_status(
                order_id, OrderStatusEnum.CANCELLED
            )
            self.uow.commit()
            message = "CANCELLED: Ваш заказ отменен. Причина: Payment failed"
            idempotency_key_notification = f"Notification:{order_id}:cancelled"
            try:
                self.notification_client.send_notification(
                    message=message,
                    reference_id=order_id,
                    idempotency_key=idempotency_key_notification,
                )
            except NotificationServiceError:
                print(
                    "Notification service is unavailable. Message about cancelled order wasn't sent."
                )
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
    def __init__(self, uow, notification_client):
        self.uow = uow
        self.notification_client = notification_client

    def __call__(self, dto: PaymentCallbackDTO):
        order = self.uow.orders.get_by_id(dto.order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")
        if order.status == OrderStatusEnum.NEW:
            if dto.status == PaymentCallbackStatusEnum.SUCCEEDED:
                updated_order = self.uow.orders.update_status(
                    dto.order_id, OrderStatusEnum.PAID
                )
                payload = {
                    "event_type": "order.paid",
                    "order_id": order.id,
                    "item_id": order.item_id,
                    "quantity": order.quantity,
                    "idempotency_key": order.idempotency_key,
                }
                self.uow.outbox.create(
                    event_type="order.paid",
                    payload=payload,
                )

                self.uow.commit()
                message = "PAID: Ваш заказ успешно оплачен и готов к отправке"
                idempotency_key_notification = f"Notification:{updated_order.id}:paid"
                try:
                    self.notification_client.send_notification(
                        message=message,
                        reference_id=updated_order.id,
                        idempotency_key=idempotency_key_notification,
                    )
                except NotificationServiceError:
                    print(
                        "Notification service is unavailable. Message about payment wasn't sent."
                    )
                send_event("student_system-order.events", payload)

            elif dto.status == PaymentCallbackStatusEnum.FAILED:
                updated_order = self.uow.orders.update_status(
                    dto.order_id, OrderStatusEnum.CANCELLED
                )
                self.uow.commit()
                message = "CANCELLED: Ваш заказ отменен. Причина: Payment failed"
                idempotency_key_notification = (
                    f"Notification:{updated_order.id}:cancelled"
                )
                try:
                    self.notification_client.send_notification(
                        message=message,
                        reference_id=updated_order.id,
                        idempotency_key=idempotency_key_notification,
                    )
                except NotificationServiceError:
                    print(
                        "Notification service is unavailable. Message about cancelled order wasn't sent."
                    )
            return updated_order
        return order


class ShipmentEventUseCase:
    def __init__(self, uow, notification_client):
        self.uow = uow
        self.notification_client = notification_client

    def __call__(self, dto: ShipmentEventDTO):
        event_type = dto.event_type.value
        order_id = dto.order_id
        payload = {
            "item_id": dto.item_id,
            "quantity": dto.quantity,
            "shipment_id": dto.shipment_id,
            "reason": dto.reason,
        }

        res = self.uow.inbox.try_create(
            event_type=event_type, order_id=order_id, payload=payload
        )
        if not res:
            return None

        order = self.uow.orders.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError("Order with that id doesn't exist")

        if event_type == ShipmentEventTypeEnum.SHIPPED.value:
            updated_order = self.uow.orders.update_status(
                order_id, OrderStatusEnum.SHIPPED
            )
            self.uow.commit()
            message = "SHIPPED: Ваш заказ отправлен в доставку"
            idempotency_key_notification = f"Notification:{updated_order.id}:shipped"
            try:
                self.notification_client.send_notification(
                    message=message,
                    reference_id=updated_order.id,
                    idempotency_key=idempotency_key_notification,
                )
            except NotificationServiceError:
                print(
                    "Notification service is unavailable. Message about shipping order wasn't sent."
                )
        elif event_type == ShipmentEventTypeEnum.CANCELLED.value:
            updated_order = self.uow.orders.update_status(
                order_id, OrderStatusEnum.CANCELLED
            )
            self.uow.commit()
            message = f"CANCELLED: Ваш заказ отменен. Причина: {dto.reason}"
            idempotency_key_notification = f"Notification:{updated_order.id}:cancelled"
            try:
                self.notification_client.send_notification(
                    message=message,
                    reference_id=updated_order.id,
                    idempotency_key=idempotency_key_notification,
                )
            except NotificationServiceError:
                print(
                    "Notification service is unavailable. Message about cancelled order wasn't sent."
                )
        else:
            return None

        return updated_order
