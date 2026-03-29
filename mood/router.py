from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database import User, get_db
from mood import service
from mood.schemas import MoodResponse, MoodUpdate

router = APIRouter()


@router.get("/mood", response_model=MoodResponse)
def get_mood(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_moods(db, current_user)


@router.put("/mood")
def set_mood(
    body: MoodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.set_mood(db, current_user, body.mood)
    return {"ok": True}
