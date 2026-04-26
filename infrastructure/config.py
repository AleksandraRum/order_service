import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    BASE_URL = os.environ["BASE_URL"]
    API_KEY = os.environ["API_KEY"]
    CALLBACK_URL = os.environ["CALLBACK_URL"]
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    DATABASE_URL = os.environ.get("POSTGRES_CONNECTION_STRING") or os.environ.get(
        "DATABASE_URL"
    )


settings = Settings()
