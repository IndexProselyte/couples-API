from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from couple import service
from couple.schemas import CoupleProfileResponse, CoupleProfileUpdate
from database import User, get_db

router = APIRouter()


@router.get("/couple/profile", response_model=CoupleProfileResponse)
def get_couple_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_profile(db, current_user)


@router.put("/couple/profile")
def update_couple_profile(
    body: CoupleProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.update_profile(db, current_user, body)
    return {"ok": True}
