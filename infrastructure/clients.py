import httpx
from infrastructure.exceptions import ItemNotFoundError, CatalogServiceError, PaymentServiceError


class CatalogClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    
    def get_item(self, item_id):
        try:
            response = httpx.get(
                f"{self.base_url}/api/catalog/items/{item_id}",
                headers={"X-API-Key": self.api_key}
            )
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
            response = httpx.post(
                f"{self.base_url}/api/payments",
                headers={"X-API-Key": self.api_key},
                json={
                    "order_id": order_id,
                    "amount": str(amount),
                    "callback_url": callback_url,
                    "idempotency_key": idempotency_key
                }
            )
        except httpx.RequestError:
            raise PaymentServiceError("Payment service is unavailable")
        if response.status_code >= 500:
            raise PaymentServiceError("Payment service error")

        if response.status_code not in (200, 201):
            raise PaymentServiceError("Failed to create payment")
        
        return response.json()

        
    
