import json
import logging

from aiokafka import AIOKafkaProducer

from infrastructure.config import settings

logger = logging.getLogger(__name__)


async def get_producer():
    bootstrap = settings.KAFKA_BOOTSTRAP_SERVERS
    if not bootstrap:
        logger.error("Kafka not configured")
        return None
    
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap,
    )

    return producer


async def send_event(topic: str, payload: dict):
    producer = await get_producer()
    if not producer:
        return
    await producer.start()
    try:
        logger.info("Sending Kafka event: topic=%s payload=%s", topic, payload)
        await producer.send_and_wait(
            topic,
            json.dumps(payload).encode("utf-8"),
        )
        logger.info("Kafka event sent: topic=%s", topic)
    finally:
        await producer.stop()
