from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import User, get_db
from messages import service
from messages.schemas import MessageCreate, MessageResponse, MessagesResponse, ReactionUpdate, StarUpdate
from ws.manager import manager

router = APIRouter()


@router.get("/messages", response_model=MessagesResponse)
def list_messages(
    limit: int = Query(100, ge=1, le=500),
    before: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_messages(db, current_user, limit, before)


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = service.create_message(db, current_user, body)
    await manager.broadcast(
        {"type": "message", "data": result.model_dump()},
        exclude_user_id=current_user.id,
    )
    return result


@router.put("/messages/{msg_id}/reactions")
async def update_reactions(
    msg_id: str,
    body: ReactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = service.update_reactions(db, msg_id, body.emoji, body.action)
    await manager.broadcast(
        {
            "type": "message_update",
            "data": {"id": msg_id, "reactions": result["reactions"]},
        },
        exclude_user_id=current_user.id,
    )
    return result


@router.put("/messages/{msg_id}/star")
async def star_message(
    msg_id: str,
    body: StarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.star_message(db, msg_id, body.starred)
    await manager.broadcast(
        {
            "type": "message_update",
            "data": {"id": msg_id, "is_starred": body.starred},
        },
        exclude_user_id=current_user.id,
    )
    return {"ok": True}


@router.delete("/messages/{msg_id}")
async def delete_message(
    msg_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_message(db, msg_id)
    await manager.broadcast(
        {"type": "message_delete", "data": {"id": msg_id}},
        exclude_user_id=current_user.id,
    )
    return {"ok": True}
