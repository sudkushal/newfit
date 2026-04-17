from sqlalchemy import Column, Integer, String, DateTime, JSON
from database import Base
from datetime import datetime


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)

    # 🏁 Basic info
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # 🔥 Flexible rule engine (core of system)
    rules = Column(JSON, nullable=False)

    # 📅 Challenge duration
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # 🟢 Status (optional but useful)
    status = Column(String, default="active")  # active, inactive, completed

    # 🕒 Metadata
    created_at = Column(DateTime, default=datetime.utcnow)