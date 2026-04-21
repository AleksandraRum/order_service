import json
from infrastructure.unit_of_work import UnitOfWork
from application.dto import ShipmentEventDTO
from infrastructure.db.session import SessionLocal
from application.use_cases import ShipmentEventUseCase
from pydantic import ValidationError
from infrastructure.exceptions import OrderNotFoundError, UnknownTypeEvent


def handle_message(raw_message):
    try:
        data = json.loads(raw_message.decode("utf-8"))
        dto = ShipmentEventDTO(**data)
    except json.JSONDecodeError:
        print("Invalid JSON:", raw_message)
        return
    except ValidationError as e:
        print("Invalid DTO:", e)
        return
    
    session = SessionLocal()
    try:
        uow = UnitOfWork(session)
        use_case = ShipmentEventUseCase(uow=uow)
        use_case(dto)
    except OrderNotFoundError:
        print(f"Order not found: {dto.order_id}")
    except UnknownTypeEvent:
        print(f"Unknown event type: {dto.event_type}")
    except Exception as e:
        print("Unexpected error:", e)
    finally:
        session.close()

        
    