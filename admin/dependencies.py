from __future__ import annotations

from fastapi import Depends, HTTPException, status

from auth.dependencies import get_current_user
from database import User

_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Admin access required",
)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise _FORBIDDEN
    return current_user
