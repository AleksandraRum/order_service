import time
from urllib.parse import urljoin

import httpx

from infrastructure.exceptions import (
    CatalogServiceError,
    ItemNotFoundError,
    NotificationServiceError,
    PaymentServiceError,
)


class CatalogClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def get_item(self, item_id):
        try:
            url = urljoin(self.base_url, f"api/catalog/items/{item_id}")
            response = httpx.get(url=url, headers={"X-API-Key": self.api_key})
        except httpx.RequestError:
            raise CatalogServiceError("Catalog is unavailable")

        if response.status_code == 404:
            raise ItemNotFoundError("Item does not exist")

        if response.status_code != 200:
            raise CatalogServiceError("Catalog service error")

        data = response.json()

        return data


class PaymentsClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def create_payment(self, order_id, amount, callback_url, idempotency_key):
        try:
            url = urljoin(self.base_url, "api/payments")
            response = httpx.post(
                url=url,
                headers={"X-API-Key": self.api_key},
                json={
                    "order_id": order_id,
                    "amount": str(amount),
                    "callback_url": callback_url,
                    "idempotency_key": idempotency_key,
                },
                timeout=5.0,
            )
        except httpx.RequestError:
            raise PaymentServiceError("Payment service is unavailable")
        if response.status_code >= 500:
            raise PaymentServiceError("Payment service error")

        if response.status_code not in (200, 201):
            raise PaymentServiceError("Failed to create payment")

        return response.json()


class NotificationServiceClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def send_notification(self, message, reference_id, idempotency_key):
        delays = [0.0, 0.5, 1.0]

        for attempt, delay in enumerate(delays, start=1):
            if delay > 0:
                time.sleep(delay)
            try:
                url = urljoin(self.base_url, "api/notifications")
                response = httpx.post(
                    url=url,
                    headers={"X-API-Key": self.api_key},
                    json={
                        "message": message,
                        "reference_id": reference_id,
                        "idempotency_key": idempotency_key,
                    },
                    timeout=5.0,
                )
            except httpx.RequestError:
                if attempt == len(delays):
                    raise NotificationServiceError(
                        "Notification service is unavailable"
                    )
                continue
            if response.status_code in (200, 201):
                return response.json()
            if response.status_code >= 500:
                if attempt == len(delays):
                    raise NotificationServiceError(
                        f"Notification failed: {response.status_code}"
                    )
                continue
            raise NotificationServiceError(
                f"Notification failed: {response.status_code}"
            )
