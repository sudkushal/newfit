from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import SessionLocal
from models.user import User
from services.invite import validate_invite_code, use_invite_code
from dependencies.auth import get_current_user

router = APIRouter(prefix="/setup", tags=["Setup"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================
# 🧾 Request schema
# =========================================
class SetupRequest(BaseModel):
    invite_code: str


# =========================================
# 🔐 Complete onboarding
# =========================================
@router.post("/")
def complete_setup(
    payload: SetupRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        return {"error": "User not found"}

    invite, error = validate_invite_code(db, payload.invite_code)

    if error:
        return {"error": error}

    # ✅ attach invite
    user.invite_code = payload.invite_code
    user.is_onboarded = True

    use_invite_code(db, invite)

    db.commit()

    return {"message": "Setup complete"}