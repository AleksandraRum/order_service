import logging

from aiokafka import AIOKafkaConsumer

from infrastructure.config import settings
from infrastructure.kafka.handler import handle_message
from presentation.dependencies import get_notification_client

logger = logging.getLogger(__name__)


async def run_consumer():
    bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
    if not bootstrap_servers:
        logger.warning("KAFKA_BOOTSTRAP_SERVERS is not set, consumer will not start")
        return

    consumer = AIOKafkaConsumer(
        "student_system-shipment.events",
        bootstrap_servers=bootstrap_servers,
        group_id="order-service-group-v2",
        auto_offset_reset="earliest",
    )

    await consumer.start()

    logger.info("Kafka subscribed to student_system-shipment.events")
    notification_client = get_notification_client()
    try:
        async for msg in consumer:
            logger.info("KAFKA MESSAGE RECEIVED: %s", msg.value)

            await handle_message(msg.value, notification_client=notification_client)

    finally:
        await consumer.stop()
