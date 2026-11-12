from datetime import datetime, timedelta, timezone
import uuid
import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

ph = PasswordHasher()
bearer = HTTPBearer(auto_error=False)

def hash_pw(p: str) -> str: return ph.hash(p)
def verify_pw(h: str, p: str) -> bool:
    try: return ph.verify(h, p)
    except Exception: return False

def make_token(user_id) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.SECRET_KEY, "HS256")

def current_user(cred=Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred: raise HTTPException(401, "Not authenticated")
    try:
        uid = uuid.UUID(jwt.decode(cred.credentials, settings.SECRET_KEY, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user: raise HTTPException(401, "User not found")
    return user

def require_role(*roles):
    def dep(u: User = Depends(current_user)):
        if u.role not in roles: raise HTTPException(403, "Forbidden")
        return u
    return dep
