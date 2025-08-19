import asyncio
import httpx
import os
import json
import traceback
from datetime import datetime
from typing import AsyncGenerator, Optional

# your modules
from schemas import EnterEvent
from producer import init_rabbit, close_rabbit, publish_event

# ==== CONFIG ====
CAMERAS = [
    {"device_ip": "192.168.10.1", "username": "admin", "password": "nokia113", "camera_type": "enter"},
    {"device_ip": "192.168.10.2", "username": "admin", "password": "nokia113", "camera_type": "exit"},
]

STREAM_ENDPOINT = "/ISAPI/Event/notification/alertStream?format=json"
CONNECT_TIMEOUT_SECONDS = 5            # fail fast on dead IPs
READ_TIMEOUT_SECONDS = None            # stream shouldn't have a read timeout
RECONNECT_BASE_DELAY = 3               # seconds (exponential backoff)
RECONNECT_MAX_DELAY = 30               # cap backoff
QUEUE_MAXSIZE = 1000                   # prevent unbounded memory growth

# ============

class HikiVisionConnection:
    def __init__(self, device_ip: str, username: str, password: str, camera_type: str):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.url = f"http://{self.device_ip}{STREAM_ENDPOINT}"
        self.camera_type = camera_type
        # default boundary used by many Hikvision firmwares, but we'll try to auto-detect too
        self.boundary = b"--MIME_boundary"

    def _save_image(self, image_bytes: bytes) -> str:
        os.makedirs("images", exist_ok=True)
        filename = f"images/{datetime.now():%Y%m%d_%H%M%S_%f}.jpg"
        with open(filename, "wb") as f:
            f.write(image_bytes)
        print(f"[📷] Image saved: {filename}")
        return filename

    async def _connection_stream(self) -> AsyncGenerator[bytes, None]:
        """
        Connect to Hikvision alert stream and yield each multipart 'part' (headers+body) as bytes.
        Auto-detects boundary from the first response if available.
        """
        auth = httpx.DigestAuth(self.username, self.password)
        timeout = httpx.Timeout(connect=CONNECT_TIMEOUT_SECONDS, read=READ_TIMEOUT_SECONDS)
        limits = httpx.Limits(keepalive_expiry=None, max_keepalive_connections=10)

        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            async with client.stream("GET", self.url, auth=auth) as response:
                if response.status_code != 200:
                    text = await response.aread()
                    print(f"[ERROR] {self.device_ip} connect failed: {response.status_code} body={text[:200]!r}")
                    return

                ctype = response.headers.get("Content-Type", "")
                # Try to detect boundary like: multipart/mixed; boundary=--MIME_boundary
                if "boundary=" in ctype:
                    b = ctype.split("boundary=", 1)[1].strip()
                    # ensure starts with two dashes per RFC
                    if not b.startswith("--"):
                        b = f"--{b}"
                    self.boundary = b.encode("utf-8", "ignore")
                    print(f"[INFO] {self.device_ip} boundary detected: {self.boundary!r}")
                else:
                    print(f"[WARN] {self.device_ip} boundary not in headers, using default {self.boundary!r}")

                print(f"[INFO] {self.device_ip} connected. Waiting for events...")

                buffer = b""
                async for chunk in response.aiter_bytes():
                    if not chunk:
                        # keep-alive/no data; continue
                        await asyncio.sleep(0)
                        continue

                    buffer += chunk

                    # Split by boundary; there may be multiple parts per chunk
                    while True:
                        idx = buffer.find(self.boundary)
                        if idx == -1:
                            # not enough data for a full part yet
                            break

                        part = buffer[:idx]
                        buffer = buffer[idx + len(self.boundary):]
                        part = part.lstrip(b"\r\n")  # trim leading CRLF between parts

                        if part.strip():
                            yield part

    @staticmethod
    def _split_headers_body(part: bytes) -> tuple[bytes, bytes]:
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            return b"", b""
        return part[:header_end], part[header_end + 4:]

    async def handle_part(self, part: bytes, queue: "asyncio.Queue[EnterEvent]") -> None:
        headers_raw, content = self._split_headers_body(part)
        if not headers_raw:
            return

        headers_text = headers_raw.decode(errors="ignore")

        if "application/json" in headers_text:
            try:
                json_data = json.loads(content.decode(errors="ignore"))

                event_type = json_data.get("eventType")
                dt = json_data.get("dateTime")

                if event_type == "AccessControllerEvent":
                    name = json_data.get("AccessControllerEvent", {}).get("name") or "unknown"
                    if name != "unknown":
                        event = EnterEvent(user_id=name, time=dt, camera_type=self.camera_type)
                        # Non-blocking: put into queue (waits if queue is full)
                        await queue.put(event)
                        print(f"[✅] {self.device_ip} queued AccessControllerEvent: {event.model_dump()}")
                    else:
                        # No name → ignore silently or log
                        pass

                elif event_type == "Non-AccessControllerEvent":
                    print(f"[ℹ️] {self.device_ip} ignored Non-AccessControllerEvent")

                else:
                    print(f"[WARN] {self.device_ip} unknown event type: {event_type}")

            except Exception as e:
                print(f"[ERROR] {self.device_ip} JSON parse failed: {e}")
                print(traceback.format_exc())

        elif "image/jpeg" in headers_text:
            # Uncomment if you want snapshots
            # self._save_image(content)
            pass
        else:
            # Other content types (e.g., text/plain keepalives) → ignore
            pass

    async def stream_once(self, queue: "asyncio.Queue[EnterEvent]") -> None:
        """
        One streaming session (until an exception / disconnect happens).
        """
        try:
            async for part in self._connection_stream():
                await self.handle_part(part, queue)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[ERROR] {self.device_ip} streaming error: {e}")
            print(traceback.format_exc())


async def run_camera(conn: HikiVisionConnection, queue: "asyncio.Queue[EnterEvent]") -> None:
    """
    Forever loop: start stream, on failure wait with backoff and retry.
    """
    delay = RECONNECT_BASE_DELAY
    while True:
        try:
            await conn.stream_once(queue)
            # If stream returns normally (EOF), treat as failure & reconnect
            print(f"[INFO] {conn.device_ip} stream ended, reconnecting in {delay}s...")
        except asyncio.CancelledError:
            print(f"[INFO] {conn.device_ip} task cancelled. Stopping.")
            raise
        except Exception as e:
            print(f"[ERROR] {conn.device_ip} fatal stream error: {e}")

        await asyncio.sleep(delay)
        delay = min(delay * 2, RECONNECT_MAX_DELAY)  # backoff


async def event_consumer(queue: "asyncio.Queue[EnterEvent]") -> None:
    """
    Pull events from queue and publish to RabbitMQ. Keeps running forever.
    """
    while True:
        try:
            event = await queue.get()
            try:
                await publish_event(event=event)
                print(f"[📨] Published: {event.model_dump()}")
            except Exception as e:
                # If RabbitMQ is temporarily down, wait a bit and requeue
                print(f"[ERROR] publish failed: {e}")
                await asyncio.sleep(1)
                # Re-queue (careful to avoid infinite tight loop)
                await queue.put(event)
            finally:
                queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[ERROR] consumer loop: {e}")
            await asyncio.sleep(1)


async def main():
    await init_rabbit()

    queue: asyncio.Queue[EnterEvent] = asyncio.Queue(maxsize=QUEUE_MAXSIZE)

    # Start one resilient task per camera
    camera_tasks = [asyncio.create_task(run_camera(HikiVisionConnection(**cam), queue)) for cam in CAMERAS]

    # Start one consumer task for publishing (you can spawn more if needed)
    consumer_task = asyncio.create_task(event_consumer(queue))

    try:
        # Run forever
        await asyncio.gather(*camera_tasks)
    finally:
        # If we ever exit, cancel consumer & close rabbit
        consumer_task.cancel()
        with contextlib.suppress(Exception):
            await close_rabbit()


if __name__ == "__main__":
    import contextlib
    asyncio.run(main())
