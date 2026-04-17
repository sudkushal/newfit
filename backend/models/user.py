from sqlalchemy import Boolean, Column, Integer, String, BigInteger, DateTime
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Strava linkage
    athlete_id = Column(BigInteger, unique=True, index=True, nullable=False)

    # 🔐 OAuth tokens
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(Integer, nullable=False)

    # 👤 App user info (for UI later)
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)

    # 🕒 Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    invite_code = Column(String, nullable=True)
    is_onboarded = Column(Boolean, default=False)