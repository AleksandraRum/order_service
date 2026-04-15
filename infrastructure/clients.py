import httpx
from infrastructure.exceptions import ItemNotFoundError, CatalogServiceError


class CatalogClient:
    def __init__(self, api_key, catalog_url):
        self.api_key = api_key
        self.catalog_url = catalog_url

    
    def get_item(self, item_id):
        try:
            response = httpx.get(
                f"{self.catalog_url}/api/catalog/items/{item_id}",
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