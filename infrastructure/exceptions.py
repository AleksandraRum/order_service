class ItemNotFoundError(Exception):
    pass


class NotEnoughStockError(Exception):
    pass


class CatalogServiceError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class PaymentServiceError(Exception):
    pass


class UnknownTypeEvent(Exception):
    pass


class NotificationServiceError(Exception):
    pass
