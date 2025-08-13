import aio_pika
from schemas import EnterEvent
from config import settings

# Global connection & channel
_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.Channel | None = None

async def init_rabbit():
    """Initialize RabbitMQ connection and channel once."""
    global _connection, _channel
    _connection = await aio_pika.connect_robust(settings.rabbit.url)
    _channel = await _connection.channel()
    await _channel.declare_queue(name=settings.rabbit.url, durable=True)
    print("[RabbitMQ] Connection and channel initialized.")

async def publish_event(event: EnterEvent):
    """Publish a Pydantic event to RabbitMQ."""
    if _channel is None:
        raise RuntimeError("RabbitMQ channel not initialized. Call init_rabbit() first.")

    message = aio_pika.Message(
        body=event.model_dump_json().encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )

    await _channel.default_exchange.publish(
        message=message,
        routing_key=settings.rabbit.queue_name
    )

    print(f"[Publisher] Sent event: {event}")

async def close_rabbit():
    """Close RabbitMQ connection."""
    if _connection:
        await _connection.close()
        print("[RabbitMQ] Connection closed.")
