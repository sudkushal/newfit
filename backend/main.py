from fastapi import FastAPI
from database import Base, engine

# models
import models.user
import models.activity
import models.challenge
import models.challenge_participant
import models.activity_log
import models.invite_code

# routes
import routes.auth as auth
import routes.webhook as webhook
import routes.challenges as challenges
import routes.setup as setup   # ✅ REQUIRED

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(challenges.router)
app.include_router(setup.router)   # ✅ REQUIRED

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "API running"}