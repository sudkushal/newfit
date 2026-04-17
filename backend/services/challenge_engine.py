from models.challenge import Challenge
from models.challenge_participant import ChallengeParticipant
from models.activity_log import ActivityLog
from datetime import datetime


async def process_activity_for_challenges(db, user, activity_data):
    print("🏁 Processing challenges for activity:", activity_data.get("id"))

    challenges = db.query(Challenge).filter(Challenge.status == "active").all()

    for challenge in challenges:

        participant = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.user_id == user.id,
            ChallengeParticipant.challenge_id == challenge.id
        ).first()

        if not participant:
            continue

        # 🔥 FIX: Handle NULL values safely
        participant.total_points = participant.total_points or 0
        participant.total_distance = participant.total_distance or 0
        participant.total_activities = participant.total_activities or 0

        # 🔥 Prevent duplicate scoring
        existing_log = db.query(ActivityLog).filter(
            ActivityLog.activity_id == activity_data["id"],
            ActivityLog.challenge_id == challenge.id
        ).first()

        if existing_log:
            print("⚠️ Already processed")
            continue

        rules = challenge.rules
        distance = activity_data.get("distance", 0)
        points = 0

        if rules["type"] == "per_activity":
            if distance >= rules.get("min_distance", 0):
                points = rules.get("points", 0)
                participant.total_activities += 1

        elif rules["type"] == "cumulative":
            participant.total_distance += distance

            if participant.total_distance >= rules.get("target_distance", 0):
                points = rules.get("points", 0)

        elif rules["type"] == "single_activity":
            if distance >= rules.get("min_distance", 0):
                points = rules.get("points", 0)

        if points > 0:
            participant.total_points += points
            participant.total_distance += distance

            log = ActivityLog(
                user_id=user.id,
                challenge_id=challenge.id,
                activity_id=activity_data["id"],
                distance=distance,
                points_earned=points
            )

            db.add(log)

            print(f"✅ User {user.id} earned {points} points")

    db.commit()