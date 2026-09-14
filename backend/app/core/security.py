import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import bcrypt
from app.config import settings
from app.db.session import get_db
from app.models.entities import User

DEMO_USER_EMAIL = "tenant@clauselens.ai"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Returns current authenticated user or automatically seeds/returns
    the default demo tenant user if no auth token is provided yet.
    """
    user = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
        except JWTError:
            pass

    if not user:
        # Guarantee a standard tenant user exists in DB
        user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=DEMO_USER_EMAIL,
                password_hash=get_password_hash("clauselens_demo_pass"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    return user
