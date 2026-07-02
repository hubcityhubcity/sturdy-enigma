import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", "./storage"))
ORIGINALS_DIR = STORAGE_ROOT / "originals"


def ensure_dirs() -> None:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)


def get_extension(filename: str | None) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lower()[:12]


def make_upload_path(project_id: str, filename: str | None) -> Path:
    ensure_dirs()
    folder = ORIGINALS_DIR / project_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{uuid4()}{get_extension(filename)}"


async def save_uploaded_file(project_id: str, upload: UploadFile) -> Path:
    destination = make_upload_path(project_id, upload.filename)
    contents = await upload.read()
    destination.write_bytes(contents)
    return destination
