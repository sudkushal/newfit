from sqlalchemy import Column, Integer, Float, Boolean, ForeignKey, DateTime
from database import Base
from datetime import datetime


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)

    # 📊 Progress tracking
    total_distance = Column(Float, default=0)
    total_points = Column(Integer, default=0)
    total_activities = Column(Integer, default=0)

    # ✅ Completion status
    completed = Column(Boolean, default=False)

    # 🕒 Metadata
    joined_at = Column(DateTime, default=datetime.utcnow)