from confluent_kafka import Consumer
from infrastructure.kafka.handler import handle_message
import os


def run_consumer():
    conf = {
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "group.id": "order-service-group",
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(conf)
    consumer.subscribe(["student_system-shipment.events"])

    print("Kafka consumer started")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print("Kafka error:", msg.error())
                continue

            handle_message(msg.value())

    finally:
        consumer.close()