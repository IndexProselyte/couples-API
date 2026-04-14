from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import Mood, User, get_db
from mood import service
from mood.schemas import MoodResponse, MoodUpdate
from ws.manager import manager

router = APIRouter()


@router.get("/mood", response_model=MoodResponse)
def get_mood(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_moods(db, current_user)


@router.put("/mood")
async def set_mood(
    body: MoodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.set_mood(db, current_user, body.mood)

    # Push mood_update to the partner so their dashboard refreshes in real time.
    partner = db.query(User).filter(
        User.id != current_user.id, User.role != "admin"
    ).first()
    if partner:
        partner_own_mood = db.query(Mood).filter(Mood.user_id == partner.id).first()
        await manager.send_to(
            partner.id,
            {
                "type": "mood_update",
                "data": {
                    # From the partner's point of view:
                    # "your_mood" is their own stored mood (unchanged).
                    # "partner_mood" is the mood the caller just set.
                    "your_mood": partner_own_mood.value if partner_own_mood else "neutral",
                    "partner_mood": body.mood,
                },
            },
        )

    return {"ok": True}
