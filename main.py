from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from presentation.api import router
from infrastructure.db.models import Base
from infrastructure.db.session import engine

Base.metadata.create_all(bind=engine)


app = FastAPI()
app.include_router(router)
