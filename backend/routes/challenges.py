from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import SessionLocal
from models.challenge import Challenge
from models.challenge_participant import ChallengeParticipant
from models.user import User

router = APIRouter(prefix="/challenges", tags=["Challenges"])


# =========================================
# 📦 DB Dependency
# =========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================
# 🧾 Request Schemas
# =========================================
class ChallengeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules: dict
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class JoinChallenge(BaseModel):
    user_id: int


# =========================================
# 🔐 Helper: Enforce onboarding
# =========================================
def require_onboarded_user(db, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None, {"error": "User not found"}

    if not user.is_onboarded:
        return None, {"error": "Complete setup (invite code required)"}

    return user, None


# =========================================
# 🟢 Create Challenge (Admin)
# =========================================
@router.post("/")
def create_challenge(payload: ChallengeCreate, db=Depends(get_db)):
    challenge = Challenge(
        name=payload.name,
        description=payload.description,
        rules=payload.rules,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="active"
    )

    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    return {"message": "Challenge created", "challenge_id": challenge.id}


# =========================================
# 📋 List Challenges (BLOCK if not onboarded)
# =========================================
from dependencies.auth import get_current_user

@router.get("/")
def list_challenges(current_user=Depends(get_current_user), db=Depends(get_db)):
    
    if not current_user.is_onboarded:
        return {"error": "Complete setup first"}

    challenges = db.query(Challenge).all()
    return challenges


# =========================================
# 🙋 Join Challenge (BLOCK if not onboarded)
# =========================================
@router.post("/{challenge_id}/join")
def join_challenge(challenge_id: int, payload: JoinChallenge, db=Depends(get_db)):
    user, error = require_onboarded_user(db, payload.user_id)

    if error:
        return error

    existing = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.user_id == payload.user_id,
        ChallengeParticipant.challenge_id == challenge_id
    ).first()

    if existing:
        return {"message": "Already joined"}

    participant = ChallengeParticipant(
        user_id=payload.user_id,
        challenge_id=challenge_id,
        total_distance=0,
        total_points=0,
        total_activities=0
    )

    db.add(participant)
    db.commit()

    return {"message": "Joined challenge successfully"}


# =========================================
# 👥 Participants (BLOCK if not onboarded)
# =========================================
@router.get("/{challenge_id}/participants")
def get_participants(challenge_id: int, user_id: int, db=Depends(get_db)):
    user, error = require_onboarded_user(db, user_id)

    if error:
        return error

    participants = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id
    ).all()

    return participants


# =========================================
# 🏆 Leaderboard (BLOCK if not onboarded)
# =========================================
@router.get("/{challenge_id}/leaderboard")
def leaderboard(challenge_id: int, user_id: int, db=Depends(get_db)):
    user, error = require_onboarded_user(db, user_id)

    if error:
        return error

    participants = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id
    ).order_by(ChallengeParticipant.total_points.desc()).all()

    return participants