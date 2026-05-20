import asyncio
import logging
from urllib.parse import urljoin

import httpx

from application.exceptions import (
    CatalogServiceError,
    NotificationServiceError,
    PaymentServiceError,
)
from domain.exceptions import ItemNotFoundError

logger = logging.getLogger(__name__)


class BaseClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"

    def _headers(self):
        return {"X-API-Key": self.api_key}


class CatalogClient(BaseClient):
    async def get_item(self, item_id: str):
        url = urljoin(self.base_url, f"api/catalog/items/{item_id}")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    url=url,
                    headers=self._headers(),
                )
        except httpx.RequestError:
            raise CatalogServiceError("Catalog is unavailable")

        if response.status_code == 404:
            raise ItemNotFoundError("Item does not exist")

        if response.status_code != 200:
            raise CatalogServiceError("Catalog service error")

        return response.json()


class PaymentsClient(BaseClient):
    async def create_payment(self, order_id, amount, callback_url, idempotency_key):
        try:
            url = urljoin(self.base_url, "api/payments")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    url=url,
                    headers=self._headers(),
                    json={
                        "order_id": order_id,
                        "amount": str(amount),
                        "callback_url": callback_url,
                        "idempotency_key": idempotency_key,
                    },
                )
        except httpx.RequestError:
            raise PaymentServiceError("Payment service is unavailable")
        if response.status_code >= 500:
            raise PaymentServiceError("Payment service error")

        if response.status_code not in (200, 201):
            raise PaymentServiceError("Failed to create payment")

        return response.json()


class NotificationServiceClient(BaseClient):
    async def send_notification(self, message, reference_id, idempotency_key):
        delays = [0.0, 0.5, 1.0]

        for attempt, delay in enumerate(delays, start=1):
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                logger.info(
                    "[УВЕДОМЛЕНИЕ] Пытаемся отправить: "
                    "message='%s', reference_id=%s, "
                    "idempotency_key=%s, попытка=%s",
                    message,
                    reference_id,
                    idempotency_key,
                    attempt,
                )
                url = urljoin(self.base_url, "api/notifications")

                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        url=url,
                        headers=self._headers(),
                        json={
                            "message": message,
                            "reference_id": reference_id,
                            "idempotency_key": idempotency_key,
                        },
                    )
            except httpx.RequestError:
                logger.warning("[УВЕДОМЛЕНИЕ] Ошибка сети: попытка=%s", attempt)
                if attempt == len(delays):
                    raise NotificationServiceError(
                        "Notification service is unavailable"
                    )
                continue
            if response.status_code in (200, 201):
                logger.info(
                    "[УВЕДОМЛЕНИЕ] Успешно отправлено: status=%s, message=%s",
                    response.status_code,
                    message,
                )
                return response.json()
            if response.status_code >= 500:
                logger.warning(
                    "[УВЕДОМЛЕНИЕ] Ошибка сервиса (5xx): status=%s, попытка=%s",
                    response.status_code,
                    attempt,
                )
                if attempt == len(delays):
                    raise NotificationServiceError(
                        f"Notification failed: {response.status_code}"
                    )
                continue
            raise NotificationServiceError(
                f"Notification failed: {response.status_code}"
            )
