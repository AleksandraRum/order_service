import asyncio
import logging

from infrastructure.db.session import SessionLocal
from infrastructure.kafka.producer import send_event
from infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


async def run_outbox_worker():

    while True:
        session = SessionLocal()
        try:
            uow = UnitOfWork(session)
            events = uow.outbox.get_pending()
            for event in events:
                await send_event(
                    topic="student_system-order.events", payload=event.payload
                )
                uow.outbox.mark_as_sent(event)
            uow.commit()

        except Exception:
            logger.exception("Unexpected error while processing outbox events")
        finally:
            session.close()
        await asyncio.sleep(1)
