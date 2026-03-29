from __future__ import annotations

from sqlalchemy.orm import Session

from couple.schemas import CoupleProfileResponse, CoupleProfileUpdate
from database import CoupleProfile, User


def get_profile(db: Session, user: User) -> CoupleProfileResponse:
    profile = _get_or_create(db)

    your_name, partner_name = _names_for_role(profile, user.role)

    return CoupleProfileResponse(
        start_date=profile.start_date or "2020-01-01",
        your_name=your_name,
        partner_name=partner_name,
        couple_photo_url=profile.couple_photo_url,
        partner_avatar_url=profile.partner_avatar_url,
    )


def update_profile(db: Session, user: User, body: CoupleProfileUpdate) -> None:
    profile = _get_or_create(db)

    if body.start_date is not None:
        profile.start_date = body.start_date

    # your_name / partner_name are perspective-relative — map back to DB columns.
    # Admin writes directly: your_name → hers_name, partner_name → his_name.
    if user.role in ("hers", "admin"):
        if body.your_name is not None:
            profile.hers_name = body.your_name
        if body.partner_name is not None:
            profile.his_name = body.partner_name
    else:
        if body.your_name is not None:
            profile.his_name = body.your_name
        if body.partner_name is not None:
            profile.hers_name = body.partner_name

    db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_or_create(db: Session) -> CoupleProfile:
    profile = db.query(CoupleProfile).first()
    if not profile:
        profile = CoupleProfile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _names_for_role(profile: CoupleProfile, role: str) -> tuple[str, str]:
    """Return (your_name, partner_name) from the perspective of *role*.

    Admin has no personal name in the couple — it observes from the hers
    perspective so the response shape stays consistent.
    """
    hers = profile.hers_name or ""
    his = profile.his_name or ""
    if role in ("hers", "admin"):
        return hers, his
    return his, hers
