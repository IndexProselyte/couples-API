from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from admin import service
from admin.dependencies import get_current_admin
from admin.schemas import (
    DeleteDataRequest,
    DeleteDataResponse,
    ResetPasswordRequest,
    StatsResponse,
)
from database import User, get_db

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Overview of the couple's data — message count, event count, current moods."""
    return service.get_stats(db)


@router.post("/users/{role}/password")
def reset_password(
    role: str,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Reset the password for the 'hers' or 'his' user."""
    service.reset_password(db, role, body.password)
    return {"ok": True}


@router.delete("/data", response_model=DeleteDataResponse)
def delete_data(
    body: DeleteDataRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Permanently delete chat messages, timeline events, or all data."""
    return service.delete_data(db, body.type)
