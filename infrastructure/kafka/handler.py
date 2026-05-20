import json
import logging

from pydantic import ValidationError

from application.dto import ShipmentEventDTO
from application.use_cases import ShipmentEventUseCase
from domain.exceptions import OrderNotFoundError
from infrastructure.db.session import SessionLocal
from infrastructure.exceptions import UnknownTypeEvent
from infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


async def handle_message(raw_message, notification_client):
    try:
        data = json.loads(raw_message.decode("utf-8"))
        dto = ShipmentEventDTO(**data)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON: %s", raw_message)
        return
    except ValidationError as e:
        logger.warning("Invalid DTO: %s", e)
        return

    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        use_case = ShipmentEventUseCase(
            uow=uow, notification_client=notification_client
        )
        await use_case(dto)
    except OrderNotFoundError:
        logger.warning("Order not found: %s", dto.order_id)
    except UnknownTypeEvent:
        logger.warning("Unknown event type: %s", dto.event_type)
    except Exception:
        logger.exception("Unexpected error while handling Kafka message")
    finally:
        session.close()
