from confluent_kafka import Producer
import os
import json


def get_producer():
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap:
        print("Kafka not configured")
        return None

    return Producer({
        "bootstrap.servers": bootstrap
    })


def send_event(topic: str, payload: dict):
    producer = get_producer()
    if not producer:
        return

    producer.produce(
        topic=topic,
        value=json.dumps(payload).encode("utf-8")
    )
    producer.flush()