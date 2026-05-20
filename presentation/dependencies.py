from infrastructure.clients import (
    CatalogClient,
    NotificationServiceClient,
    PaymentsClient,
)
from infrastructure.config import settings
from infrastructure.db.session import SessionLocal


def get_catalog_client():
    return CatalogClient(
        base_url=settings.BASE_URL,
        api_key=settings.API_KEY,
    )


def get_payments_client():
    return PaymentsClient(
        base_url=settings.BASE_URL,
        api_key=settings.API_KEY,
    )


def get_notification_client():
    return NotificationServiceClient(
        base_url=settings.BASE_URL,
        api_key=settings.API_KEY,
    )


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
