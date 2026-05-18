from typing import Any, Protocol


class CatalogPort(Protocol):
    async def get_item(self, item_id: str) -> dict: ...


class PaymentsPort(Protocol):
    async def create_payment(
        self,
        order_id: str,
        amount: str,
        callback_url: str,
        idempotency_key: str,
    ) -> dict: ...


class NotificationPort(Protocol):
    async def send_notification(
        self,
        message: str,
        reference_id: str,
        idempotency_key: str,
    ) -> dict: ...


class UnitOfWorkPort(Protocol):
    orders: Any
    inbox: Any
    outbox: Any

    def commit(self) -> None: ...
