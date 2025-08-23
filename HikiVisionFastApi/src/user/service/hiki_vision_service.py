import httpx
import json
import os


class HikiUserService:
    def __init__(self, ip_address: str, username: str, password: str):
        self.ip_address = ip_address
        self.username = username
        self.password = password

        # Base URLs
        self.user_record_url = f"http://{self.ip_address}/ISAPI/AccessControl/UserInfo/Record?format=json"
        self.user_modify_url = f"http://{self.ip_address}/ISAPI/AccessControl/UserInfo/Modify?format=json"
        self.user_delete_url = f"http://{self.ip_address}/ISAPI/AccessControl/UserInfo/Delete?format=json"
        self.face_data_url = f"http://{self.ip_address}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
        self.card_search_url = f"http://{self.ip_address}/ISAPI/AccessControl/CardInfo/Search?format=json"

        # Always use digest auth
        self.auth = httpx.DigestAuth(self.username, self.password)

    async def create_user(self, user_id: str, user_name: str) -> bool:
        """Create a user in Hikvision device."""
        payload = {
            "UserInfo": {
                "employeeNo": user_id,
                "name": user_name,
                "userType": "normal",
                "gender": "unknown",
                "Valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2037-12-31T23:59:59"
                },
                "doorRight": "1", 
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": 1,
                        "timeSegment": [
                            {
                                "beginTime": "00:00:00",
                                "endTime": "23:59:59"
                            }
                        ]
                    }
                ]
            }
        }


        print(f"Attempting to create user record for '{user_name}'...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.post(
                    self.user_record_url,
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(payload),
                    timeout=10,
                )
                response.raise_for_status()
                print("✅ User record created successfully.")
                return True
            except httpx.HTTPStatusError as err:
                print(f"❌ Failed to create user record. {err}")
                print(f"Response: {err.response.text}")
            except httpx.RequestError as err:
                print(f"❌ Request error: {err}")
        return False

    async def upload_face_image(self, user_id: str, image_path: str) -> bool:
        """Upload face image for a user."""
        if not os.path.exists(image_path):
            print(f"❌ Error: Image not found at '{image_path}'")
            return False

        print(f"Attempting to upload face image for user ID '{user_id}'...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                with open(image_path, "rb") as f:
                    files = {
                        "FaceDataRecord": (
                            None,
                            json.dumps({
                                "faceLibType": "blackFD",  # or "whiteFD"
                                "FDID": "1",
                                "FPID": user_id
                            }),
                            "application/json"
                        ),
                        "FaceImage": (os.path.basename(image_path), f, "image/jpeg")
                    }

                    response = await client.post(self.face_data_url, files=files, timeout=20)
                    response.raise_for_status()
                    print("✅ Face image uploaded successfully.")
                    return True
            except httpx.HTTPStatusError as err:
                print(f"❌ Failed to upload face image. {err}")
                print(f"Response: {err.response.text}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
        return False

    async def register_with_face(self, user_id: str, user_name: str, image_path: str) -> bool:
        """High-level method to register user and upload face image."""
        user_created = await self.create_user(user_id, user_name)
        if user_created:
            return await self.upload_face_image(user_id, image_path)
        return False

    async def search_card_info(self, employee_no: str, max_results: int = 20):
        """
        Async search for card information by employee number (user ID).
        """
        payload = {
            "CardInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": max_results,
                "EmployeeNoString": employee_no
            }
        }

        async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
            try:
                response = await client.post(
                    self.card_search_url,
                    headers={"Content-Type": "application/json"},
                    content=json.dumps(payload)
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

            except httpx.RequestError as e:
                return {"error": "Request failed", "details": str(e)}

    async def modify_user(self, user_id: str, new_name: str = None,
                          new_gender: str = None, new_validity: dict = None) -> bool:
        """Modify existing user information."""
        payload = {"UserInfo": {"employeeNo": user_id}}

        if new_name:
            payload["UserInfo"]["name"] = new_name
        if new_gender:
            payload["UserInfo"]["gender"] = new_gender
        if new_validity:
            payload["UserInfo"]["Valid"] = {
                "enable": True,
                "beginTime": new_validity.get("beginTime", "2020-01-01T00:00:00"),
                "endTime": new_validity.get("endTime", "2037-12-31T23:59:59")
            }

        print(f"Attempting to modify user ID '{user_id}'...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.put(
                    self.user_modify_url,
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(payload),
                    timeout=10,
                )
                response.raise_for_status()
                print("✅ User modified successfully.")
                return True
            except httpx.HTTPStatusError as err:
                print(f"❌ Failed to modify user. {err}")
                print(f"Response: {err.response.text}")
            except httpx.RequestError as err:
                print(f"❌ Request error: {err}")
        return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user by employeeNo."""
        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [{"employeeNo": user_id}]
            }
        }
        print(f"Attempting to delete user ID '{user_id}'...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.put(
                    self.user_delete_url,
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(payload),
                    timeout=10,
                )
                response.raise_for_status()
                print("✅ User deleted successfully.")
                return True
            except httpx.HTTPStatusError as err:
                print(f"❌ Failed to delete user. {err}")
                print(f"Response: {err.response.text}")
            except httpx.RequestError as err:
                print(f"❌ Request error: {err}")
        return False
