import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from infrastructure.db.models import Base
from infrastructure.db.session import engine
from infrastructure.kafka.consumer import run_consumer
from infrastructure.kafka.outbox_worker import run_outbox_worker
from presentation.api import router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):

    consumer_task = asyncio.create_task(run_consumer())
    outbox_task = asyncio.create_task(run_outbox_worker())

    logger.info("Kafka consumer started")
    logger.info("Outbox worker started")

    try:
        yield
    finally:
        consumer_task.cancel()
        outbox_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consumer_task
        with contextlib.suppress(asyncio.CancelledError):
            await outbox_task
        logger.info("Application shutting down")


app = FastAPI(lifespan=lifespan)
app.include_router(router)
