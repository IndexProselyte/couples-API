from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import User, get_db
from presence import service
from presence.schemas import PresenceResponse, PresenceUpdate
from ws.manager import manager

router = APIRouter()


@router.get("/presence", response_model=PresenceResponse)
def get_presence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get your own and your partner's online status."""
    return service.get_presence(db, current_user)


@router.put("/presence")
async def update_presence(
    body: PresenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Call with { "online": true } on app foreground, { "online": false } on background/exit."""
    updated = service.set_presence(db, current_user.id, body.online)
    await manager.broadcast(
        {
            "type": "partner_presence",
            "data": {
                "user_id": updated.user_id,
                "is_online": updated.is_online,
                "last_seen": updated.last_seen,
            },
        },
        exclude_user_id=current_user.id,
    )
    return {"ok": True}
