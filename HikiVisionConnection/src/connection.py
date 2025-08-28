import asyncio
import httpx
import os
from datetime import datetime
import json
import traceback
from schemas import EnterEvent
from config import settings
from producer import init_rabbit , close_rabbit , publish_event



CAMERAS = [
    
    # {
    #     "device_ip": "192.168.0.51",
    #     "username": settings.camera.username,
    #     "password": settings.camera.password,
    #     "camera_type": "enter"
    # }
    {
        "device_ip": "192.168.88.101",
        "username": settings.camera.username,
        "password": settings.camera.password,
        "camera_type": "enter"
    },
    {
        "device_ip": "192.168.88.102",
        "username": settings.camera.username,
        "password": settings.camera.password,
        "camera_type": "exit"
    },
    {
        "device_ip": "192.168.88.103",
        "username": settings.camera.username,
        "password": settings.camera.password,
        "camera_type": "enter"
    },
    {
        "device_ip": "192.168.88.104",
        "username": settings.camera.username,
        "password": settings.camera.password,
        "camera_type": "exit"
    },
    {
        "device_ip": "192.168.88.105",
        "username": settings.camera.username,
        "password": settings.camera.password,
        "camera_type": "enter"
    },
    {
        "device_ip": "192.168.88.106",
        "username": settings.camera.username,
        "password": settings.camera.password,
        "camera_type": "exit"
    }
]


class HikiVisionConnection:
    def __init__(self, device_ip: str , username:str, password:str ,camera_type: str):
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.url = f"http://{self.device_ip}/ISAPI/Event/notification/alertStream?format=json"
        self.boundary = b"--MIME_boundary"
        self.camera_type = camera_type
        

    async def connection_stream(self):
        """Connect to Hikvision device and yield each multipart 'part' as bytes."""
        auth = httpx.DigestAuth(self.username, self.password)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", self.url, auth=auth) as response:
                if response.status_code != 200:
                    print(f"[ERROR] Failed to connect: {response.status_code}")
                    return

                print(f"[INFO] Connected to {self.device_ip}. Waiting for events...")

                buffer = b""
                async for chunk in response.aiter_bytes():
                    buffer += chunk
                    while True:
                        boundary_index = buffer.find(self.boundary)
                        if boundary_index == -1:
                            break

                        part = buffer[:boundary_index]
                        buffer = buffer[boundary_index + len(self.boundary):]
                        part = part.lstrip(b"\r\n")

                        if part.strip():
                            yield part

    def save_image(self, image_bytes: bytes):
        """Save image to images/ with timestamp and update user log."""
        os.makedirs("images", exist_ok=True)
        filename = f"images/{datetime.now():%Y%m%d_%H%M%S_%f}.jpg"
        with open(filename, "wb") as f:
            f.write(image_bytes)

        print(f"[📷] Image saved: {filename}")
        return filename

    async def process_part(self, part: bytes):
        """Process one part of the multipart stream."""
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            return

        headers_raw = part[:header_end].decode(errors="ignore")
        content = part[header_end + 4:]

        if "application/json" in headers_raw:
            try:
                json_data = json.loads(content.decode(errors="ignore"))
                event_type = json_data.get("eventType")
                dt = json_data.get("dateTime")

                if event_type == "AccessControllerEvent":
                    name = json_data.get("AccessControllerEvent", {}).get("employeeNoString")
                    person = name if name else "unknown"
                    
                    if person == "unknown":
                        pass
                    else:
                        event = EnterEvent(
                            user_id=person, 
                            time=dt,
                            camera_type=self.camera_type
                            )
                        await publish_event(event=event)
                        print(f"[✅] Published AccessControllerEvent: {event.model_dump()}, data: {json_data}")

                elif event_type == "Non-AccessControllerEvent":
                    print(f"[ℹ️] Ignored Non-AccessControllerEvent: {json_data}")

                else:
                    print(f"[WARN] Unknown event type: {event_type}, data: {json_data}")

            except Exception as e:
                print(f"[ERROR] Failed to parse JSON: {e}")
                print(traceback.format_exc())

        # elif "image/jpeg" in headers_raw:
        #     self.save_image(content)
        else:
            print("[WARN] Unknown content type in part")


    async def stream_events(self):
        """Main loop: read parts from the stream and process them. Includes reconnection logic."""
        while True:
            try:
                print(f"[INFO] Attempting to connect to {self.device_ip}...")
                async for part in self.connection_stream():
                    await self.process_part(part)
            except (httpx.ConnectError, httpx.ReadError) as e:
                print(f"[ERROR] Connection to {self.device_ip} failed: {e}")
                print(f"[INFO] Retrying connection in 30 seconds...")
                await asyncio.sleep(30)
            except Exception as e:
                print(f"[ERROR] Unhandled streaming error from {self.device_ip}: {e}")
                print(traceback.format_exc())
                print(f"[INFO] Retrying connection in 30 seconds...")
                await asyncio.sleep(30)


async def main():
    await init_rabbit()

    connections = [
        HikiVisionConnection(**cam) for cam in CAMERAS
    ]

    await asyncio.gather(*(conn.stream_events() for conn in connections))

    await close_rabbit()


if __name__ == "__main__":
    asyncio.run(main())
