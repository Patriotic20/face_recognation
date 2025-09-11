import asyncio
import aio_pika
import json
from pydantic import BaseModel 
from datetime import datetime 
from user_logs.service import UserLogService
from core.utils.db_helper import db_helper
from fastapi import FastAPI
from contextlib import asynccontextmanager

# RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/"
RABBIT_URL = "amqp://guest:guest@localhost"
QUEUE_NAME = "camera_events"

class Event(BaseModel):
    user_id: str | None = None
    time: datetime
    camera_type: str
    
class EnterEvent(BaseModel):
    user_id: str | None = None
    enter_time: datetime
    
class ExitEvent(BaseModel):
    user_id: str | None = None
    exit_time: datetime


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            event_data = json.loads(message.body.decode())
            event = Event(**event_data)
            print(f"[Consumer] Processing event: {event}")

            async with db_helper.session_factory() as session:
                service = UserLogService(session=session)
                if event.camera_type == "enter":
                    enter_event = EnterEvent(user_id=event.user_id , enter_time=event.time)
                    await service.create_user_logs(user_log_create=enter_event)
                elif event.camera_type == "exit":
                    exit_event = ExitEvent(user_id=event.user_id ,  exit_time=event.time)
                    await service.update_user_log_exit_time(user_id=exit_event.user_id , exit_time=exit_event.exit_time)
                else:
                    print(f"[Consumer] Unknown camera_type: {event.camera_type}")
                    

        except Exception as e:
            print(f"[Consumer] Error processing message: {e}")


async def main():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.consume(process_message)

        print("[Consumer] Waiting for messages...")
        await asyncio.Future()  


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(main())
    print("[Lifespan] RabbitMQ consumer started.")
        
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        print("[Lifespan] RabbitMQ consumer stopped.")
        

# if __name__ == "__main__":
#     asyncio.run(main())
