from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import JSON

from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)


# Enable WAL mode and foreign-key enforcement for SQLite connections.
@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── ORM models ────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)          # "hers" | "his"
    password_hash = Column(String, nullable=False)


class CoupleProfile(Base):
    __tablename__ = "couple_profile"

    id = Column(Integer, primary_key=True, default=1)
    start_date = Column(String, default="2020-01-01")
    hers_name = Column(String, default="")
    his_name = Column(String, default="")
    couple_photo_url = Column(String, nullable=True)
    partner_avatar_url = Column(String, nullable=True)


class Mood(Base):
    __tablename__ = "moods"

    user_id = Column(String, primary_key=True)
    value = Column(String, default="neutral")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, nullable=False)
    text = Column(Text, default="")

    # Reply context — reply_to_sender_id is stored internally so we can compute
    # reply_to_is_sent from any viewer's perspective without trusting the client.
    reply_to_id = Column(String, nullable=True)
    reply_to_text = Column(String, nullable=True)
    reply_to_sender_id = Column(String, nullable=True)

    reactions = Column(JSON, default=list)
    is_starred = Column(Boolean, default=False)
    is_voice = Column(Boolean, default=False)
    voice_duration_ms = Column(Integer, nullable=True)
    voice_waveform = Column(JSON, nullable=True)
    is_file = Column(Boolean, default=False)
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    sticker_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    # Stored as epoch milliseconds (BigInteger). Named event_date internally
    # to avoid shadowing the SQL DATE keyword in some dialects.
    event_date = Column(BigInteger, nullable=False)
    canvas = Column(JSON, default=list)
    stickers = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    location = Column(String, nullable=True)
    dot_color = Column(BigInteger, nullable=True)
    line_color = Column(BigInteger, nullable=True)
    card_color = Column(BigInteger, nullable=True)
    is_pinned = Column(Boolean, default=False)


# ── Session dependency ────────────────────────────────────────────────────────


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── First-run seeding ─────────────────────────────────────────────────────────


def seed_db() -> None:
    """Create the two fixed users and default rows on first startup.

    Idempotent — safe to call on every boot.
    """
    from passlib.context import CryptContext  # deferred to avoid top-level side-effects

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    try:
        hers = db.query(User).filter(User.role == "hers").first()
        if not hers:
            hers = User(
                id=str(uuid.uuid4()),
                role="hers",
                password_hash=pwd_context.hash(settings.hers_password),
            )
            db.add(hers)

        his = db.query(User).filter(User.role == "his").first()
        if not his:
            his = User(
                id=str(uuid.uuid4()),
                role="his",
                password_hash=pwd_context.hash(settings.his_password),
            )
            db.add(his)

        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            db.add(User(
                id=str(uuid.uuid4()),
                role="admin",
                password_hash=pwd_context.hash(settings.admin_password),
            ))

        db.flush()  # ensure IDs exist before inserting child rows

        if not db.query(CoupleProfile).first():
            db.add(CoupleProfile(id=1))

        if not db.query(Mood).filter(Mood.user_id == hers.id).first():
            db.add(Mood(user_id=hers.id, value="neutral"))
        if not db.query(Mood).filter(Mood.user_id == his.id).first():
            db.add(Mood(user_id=his.id, value="neutral"))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
