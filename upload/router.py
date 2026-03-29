from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth.dependencies import get_current_user
from config import get_settings
from database import User

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    settings = get_settings()

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}",
        )

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds size limit")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Use a UUID filename to prevent path traversal and collisions.
    suffix = Path(file.filename).suffix if file.filename else ""
    filename = f"{uuid.uuid4()}{suffix}"
    dest = upload_dir / filename

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    return {"url": f"{settings.base_url}/uploads/{filename}"}
