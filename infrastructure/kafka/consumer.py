from confluent_kafka import Consumer
from infrastructure.kafka.handler import handle_message
import os


def run_consumer():
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap_servers:
        print("KAFKA_BOOTSTRAP_SERVERS is not set, consumer will not start")
        return
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": "order-service-group-v2",
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(conf)
    consumer.subscribe(["student_system-shipment.events"])
    print("Kafka subscribed to student_system-shipment.events")

    print("Kafka consumer started")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                print("Kafka error:", msg.error())
                continue

            print("KAFKA MESSAGE RECEIVED:", msg.value())
            handle_message(msg.value())

    finally:
        consumer.close()