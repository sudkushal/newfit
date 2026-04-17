from fastapi import APIRouter
from database import SessionLocal
from models.activity import Activity

router = APIRouter()

@router.get("/activities")
def get_activities():
    db = SessionLocal()
    activities = db.query(Activity).all()
    db.close()
    return activities