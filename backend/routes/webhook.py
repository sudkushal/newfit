from fastapi import APIRouter, Request, BackgroundTasks
import os
import asyncio
from dotenv import load_dotenv

from database import SessionLocal
from models.user import User
from models.activity import Activity
from models.activity_log import ActivityLog
from models.challenge_participant import ChallengeParticipant

from services.strava import fetch_activity
from services.challenge_engine import process_activity_for_challenges

load_dotenv()

router = APIRouter()

VERIFY_TOKEN = os.getenv("STRAVA_VERIFY_TOKEN")


# =========================================
# ✅ Webhook Verification
# =========================================
@router.get("/webhook")
def verify(request: Request):
    params = request.query_params

    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if verify_token == VERIFY_TOKEN:
        return {"hub.challenge": challenge}

    return {"error": "invalid token"}


# =========================================
# 🔁 Fetch with retry (important)
# =========================================
async def fetch_with_retry(user, activity_id):
    for attempt in range(3):
        data = await fetch_activity(user, activity_id)

        if data and "id" in data:
            return data

        print(f"⏳ Retry fetch ({attempt+1})...")
        await asyncio.sleep(2)

    print("❌ Failed to fetch activity after retries")
    return None


# =========================================
# 🟢 CREATE handler
# =========================================
async def handle_activity_create(db, user, activity_data):
    existing = db.query(Activity).filter(
        Activity.strava_id == activity_data["id"]
    ).first()

    if existing:
        print("⚠️ Activity already exists, skipping insert")
    else:
        activity = Activity(
            strava_id=activity_data["id"],
            athlete_id=user.athlete_id,

            name=activity_data.get("name"),
            type=activity_data.get("type"),
            sport_type=activity_data.get("sport_type"),

            distance=activity_data.get("distance"),
            moving_time=activity_data.get("moving_time"),
            elapsed_time=activity_data.get("elapsed_time"),

            total_elevation_gain=activity_data.get("total_elevation_gain"),
            average_speed=activity_data.get("average_speed"),
            max_speed=activity_data.get("max_speed"),
            average_heartrate=activity_data.get("average_heartrate"),
            max_heartrate=activity_data.get("max_heartrate"),
            calories=activity_data.get("calories"),

            start_date=activity_data.get("start_date"),
            timezone=activity_data.get("timezone"),

            raw_data=activity_data
        )

        db.add(activity)
        db.commit()

        print("✅ Activity stored:", activity_data["id"])

    # Always evaluate challenges
    await process_activity_for_challenges(db, user, activity_data)


# =========================================
# 🟡 UPDATE handler
# =========================================
async def handle_activity_update(db, user, activity_data):
    print("🔄 Updating activity + recalculating points")

    logs = db.query(ActivityLog).filter(
        ActivityLog.activity_id == activity_data["id"]
    ).all()

    for log in logs:
        participant = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.user_id == log.user_id,
            ChallengeParticipant.challenge_id == log.challenge_id
        ).first()

        if participant:
            participant.total_points = (participant.total_points or 0) - log.points_earned
            participant.total_distance = (participant.total_distance or 0) - log.distance

        db.delete(log)

    db.commit()

    # Re-evaluate
    await process_activity_for_challenges(db, user, activity_data)


# =========================================
# 🔴 DELETE handler
# =========================================
async def handle_activity_delete(db, user, activity_id):
    print("🗑️ Deleting activity and reversing points")

    logs = db.query(ActivityLog).filter(
        ActivityLog.activity_id == activity_id
    ).all()

    for log in logs:
        participant = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.user_id == log.user_id,
            ChallengeParticipant.challenge_id == log.challenge_id
        ).first()

        if participant:
            participant.total_points = (participant.total_points or 0) - log.points_earned
            participant.total_distance = (participant.total_distance or 0) - log.distance

        db.delete(log)

    db.query(Activity).filter(
        Activity.strava_id == activity_id
    ).delete()

    db.commit()


# =========================================
# 🔄 Process webhook event
# =========================================
async def process_event(event: dict):
    db = SessionLocal()

    try:
        print("⚙️ Processing event:", event)

        user = db.query(User).filter(
            User.athlete_id == event.get("owner_id")
        ).first()

        if not user:
            print("❌ No user found for athlete_id:", event.get("owner_id"))
            return

        aspect_type = event.get("aspect_type")
        activity_id = event.get("object_id")

        # 🟢 CREATE
        if aspect_type == "create":
            activity_data = await fetch_with_retry(user, activity_id)
            if not activity_data:
                return
            await handle_activity_create(db, user, activity_data)

        # 🟡 UPDATE
        elif aspect_type == "update":
            activity_data = await fetch_with_retry(user, activity_id)
            if not activity_data:
                return
            await handle_activity_update(db, user, activity_data)

        # 🔴 DELETE
        elif aspect_type == "delete":
            await handle_activity_delete(db, user, activity_id)

    except Exception as e:
        print("🔥 Error processing event:", e)
        raise e

    finally:
        db.close()


# =========================================
# 📩 Webhook receiver
# =========================================
@router.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    event = await request.json()

    print("📩 Webhook event received:", event)

    async def retry():
        for attempt in range(3):
            try:
                await process_event(event)
                break
            except Exception as e:
                print(f"⚠️ Retry {attempt + 1} failed:", e)
                await asyncio.sleep(2)

    background_tasks.add_task(retry)

    return {"status": "received"}