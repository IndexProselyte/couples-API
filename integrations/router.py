from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user
from database import User

router = APIRouter()


@router.get("/integrations/status")
def get_integrations_status(_current_user: User = Depends(get_current_user)):
    """Stub — replace individual fields with real integration checks when wired."""
    return {
        "discord":   {"status": "offline", "detail": ""},
        "instagram": {"status": "offline", "detail": ""},
        "steam":     {"status": "offline", "detail": ""},
        "spotify":   {"status": "offline", "detail": ""},
    }
