from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from auth.schemas import LoginRequest, LogoutResponse, TokenResponse
from auth.service import authenticate_user, create_access_token
from database import User, get_db

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    return TokenResponse(
        token=create_access_token(user.id, user.role),
        user_id=user.id,
        role=user.role,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(_current_user: User = Depends(get_current_user)):
    # Stateless JWT — the token expires on its own schedule.
    # Implement a token blocklist here if immediate revocation is needed.
    return LogoutResponse(ok=True)
