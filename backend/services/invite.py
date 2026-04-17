from datetime import datetime
from models.invite_code import InviteCode


def validate_invite_code(db, code: str):
    invite = db.query(InviteCode).filter(
        InviteCode.code == code,
        InviteCode.is_active == True
    ).first()

    if not invite:
        return None, "Invalid code"

    if invite.expires_at and invite.expires_at < datetime.utcnow():
        return None, "Code expired"

    if invite.used_count >= invite.max_uses:
        return None, "Code fully used"

    return invite, None


def use_invite_code(db, invite: InviteCode):
    invite.used_count += 1
    db.commit()