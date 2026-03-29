from __future__ import annotations

from sqlalchemy.orm import Session

from database import Mood, User
from mood.schemas import MoodItem, MoodResponse


def get_moods(db: Session, user: User) -> MoodResponse:
    if user.role == "admin":
        # Admin has no personal mood — returns hers/his moods as your/partner.
        hers_user = db.query(User).filter(User.role == "hers").first()
        his_user = db.query(User).filter(User.role == "his").first()
        hers_mood = (
            db.query(Mood).filter(Mood.user_id == hers_user.id).first()
            if hers_user else None
        )
        his_mood = (
            db.query(Mood).filter(Mood.user_id == his_user.id).first()
            if his_user else None
        )
        return MoodResponse(
            your_mood=MoodItem(value=hers_mood.value if hers_mood else "neutral"),
            partner_mood=MoodItem(value=his_mood.value if his_mood else "neutral"),
        )

    # Exclude admin from partner lookup so an admin account is never surfaced
    # as "partner" to one of the couple users.
    partner = db.query(User).filter(
        User.id != user.id, User.role != "admin"
    ).first()

    your_mood = db.query(Mood).filter(Mood.user_id == user.id).first()
    partner_mood = (
        db.query(Mood).filter(Mood.user_id == partner.id).first()
        if partner
        else None
    )

    return MoodResponse(
        your_mood=MoodItem(value=your_mood.value if your_mood else "neutral"),
        partner_mood=MoodItem(
            value=partner_mood.value if partner_mood else "neutral"
        ),
    )


def set_mood(db: Session, user: User, mood_value: str) -> None:
    mood = db.query(Mood).filter(Mood.user_id == user.id).first()
    if mood:
        mood.value = mood_value
    else:
        db.add(Mood(user_id=user.id, value=mood_value))
    db.commit()
