from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import os
import httpx
from dotenv import load_dotenv

from database import SessionLocal
from models.user import User
from services.auth import create_access_token

load_dotenv()

router = APIRouter()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

REDIRECT_URI = "http://localhost:8000/auth/callback"
FRONTEND_URL = "http://localhost:3000"


# =========================================
# 🔐 Step 1: Redirect to Strava
# =========================================
@router.get("/auth/strava")
def auth_strava():
    url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=activity:read_all"
    )
    return RedirectResponse(url)


# =========================================
# 🔄 Step 2: Callback from Strava
# =========================================
@router.get("/auth/callback")
async def auth_callback(code: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )

        data = response.json()

    db = SessionLocal()

    athlete = data["athlete"]
    athlete_id = athlete["id"]

    name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()

    user = db.query(User).filter(User.athlete_id == athlete_id).first()

    if user:
        # 🔄 Update existing user
        user.access_token = data["access_token"]
        user.refresh_token = data["refresh_token"]
        user.expires_at = data["expires_at"]
        user.name = name
    else:
        # ➕ Create new user
        user = User(
            athlete_id=athlete_id,
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["expires_at"],
            name=name,
            is_onboarded=False  # 👈 IMPORTANT
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # 🔐 Create JWT
    token = create_access_token({
        "user_id": user.id
    })

    db.close()

    # =========================================
    # 🚀 Redirect to frontend with token
    # =========================================
    if not user.is_onboarded:
        return RedirectResponse(
            f"{FRONTEND_URL}/setup?token={token}"
        )
    else:
        return RedirectResponse(
            f"{FRONTEND_URL}/?token={token}"
        )