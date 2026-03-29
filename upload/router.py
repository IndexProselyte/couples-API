from __future__ import annotations

import logging
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth.dependencies import get_current_user
from config import get_settings
from database import User

router = APIRouter()
logger = logging.getLogger(__name__)

_ALLOWED_CONTENT_TYPES = {
    # Images
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
    # Video
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    # Audio
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/aac",
    # Documents
    "application/pdf",
    "text/plain",
    "application/msword",                                                    # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",                                             # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",    # .xlsx
    "application/vnd.ms-powerpoint",                                        # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "text/csv",
    "application/rtf",
    # Archives
    "application/zip",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "application/vnd.rar",
    "application/x-7z-compressed",
    "application/gzip",
    # Binaries / executables
    "application/x-msdownload",         # .exe
    "application/x-msdos-program",      # .exe (alternate)
    "application/octet-stream",         # .bin, .dll, and Flutter fallback
    "application/x-sharedlib",          # .so
    "application/x-dosexec",
}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
):
    settings = get_settings()

    logger.info(
        "Upload attempt — filename: %r  content_type: %r",
        file.filename,
        file.content_type,
    )

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        logger.warning("Rejected upload — unsupported content_type: %r", file.content_type)
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

    base = settings.base_url.rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = f"http://{base}"
    return {"url": f"{base}/uploads/{filename}"}
