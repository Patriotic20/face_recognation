import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile


async def save_file(file: UploadFile, upload_dir: str = "uploads") -> str:
    """Save uploaded file and return its path"""
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = Path(upload_dir) / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return str(file_path)
