from sqlalchemy import Column, Integer, String, Float, BigInteger, JSON
from database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)

    # Core identifiers
    strava_id = Column(BigInteger, unique=True, index=True)
    athlete_id = Column(BigInteger, index=True)

    # Basic info
    name = Column(String)
    type = Column(String)
    sport_type = Column(String)

    # Metrics
    distance = Column(Float)
    moving_time = Column(Integer)
    elapsed_time = Column(Integer)

    # Performance
    total_elevation_gain = Column(Float)
    average_speed = Column(Float)
    max_speed = Column(Float)
    average_heartrate = Column(Float)
    max_heartrate = Column(Float)
    calories = Column(Float)

    # Metadata
    start_date = Column(String)
    timezone = Column(String)

    # Raw data (VERY IMPORTANT)
    raw_data = Column(JSON)