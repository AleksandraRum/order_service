from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading

from presentation.api import router
from infrastructure.db.models import Base
from infrastructure.db.session import engine
from infrastructure.kafka.consumer import run_consumer


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