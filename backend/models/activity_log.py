from sqlalchemy import Column, Integer, Float, BigInteger, ForeignKey, DateTime
from database import Base
from datetime import datetime


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False, index=True)

    # 🏃 Activity reference
    activity_id = Column(BigInteger, nullable=False, index=True)

    # 📊 Contribution
    distance = Column(Float)
    points_earned = Column(Integer)

    # 🕒 Metadata
    created_at = Column(DateTime, default=datetime.utcnow)