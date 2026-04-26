import json

from confluent_kafka import Producer

from infrastructure.config import settings


def get_producer():
    bootstrap = settings.KAFKA_BOOTSTRAP_SERVERS
    if not bootstrap:
        print("Kafka not configured")
        return None

    return Producer({"bootstrap.servers": bootstrap})


def send_event(topic: str, payload: dict):
    producer = get_producer()
    if not producer:
        return

    producer.produce(topic=topic, value=json.dumps(payload).encode("utf-8"))
    producer.flush()
