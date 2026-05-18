from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.config import settings

DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
