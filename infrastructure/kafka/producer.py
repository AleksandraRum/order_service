import json
import logging

from confluent_kafka import Producer

from infrastructure.config import settings

logger = logging.getLogger(__name__)


def get_producer():
    bootstrap = settings.KAFKA_BOOTSTRAP_SERVERS
    if not bootstrap:
        logger.error("Kafka not configured")
        return None

    return Producer({"bootstrap.servers": bootstrap})


def send_event(topic: str, payload: dict):
    producer = get_producer()
    if not producer:
        return
    logger.info("Sending Kafka event: topic=%s payload=%s", topic, payload)
    producer.produce(topic=topic, value=json.dumps(payload).encode("utf-8"))
    producer.flush()
    logger.info("Kafka event sent: topic=%s", topic)
