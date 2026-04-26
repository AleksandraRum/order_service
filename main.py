from dotenv import load_dotenv

load_dotenv()

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infrastructure.db.models import Base
from infrastructure.db.session import engine
from infrastructure.kafka.consumer import run_consumer
from presentation.api import router

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()

    print("Kafka consumer started")

    yield

    print("Application shutting down")


app = FastAPI(lifespan=lifespan)
app.include_router(router)
