import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.core.rate_limit import limiter
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_strict_current_user,
)
from app.models.entities import User, AuditEvent
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register_user(
    request: Request,
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new tenant user account.
    Returns JWT access token and user info.
    """
    normalized_email = payload.email.lower().strip()

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(payload.password)

    new_user = User(
        id=user_id,
        email=normalized_email,
        password_hash=hashed_pwd,
    )
    db.add(new_user)

    # Log audit event
    audit = AuditEvent(
        id=str(uuid.uuid4()),
        user_id=user_id,
        event_type="auth_register",
        metadata_json={"email": normalized_email},
    )
    db.add(audit)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.id, "email": new_user.email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            created_at=new_user.created_at,
        ),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
def login_user(
    request: Request,
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials and issue a signed JWT access token.
    """
    normalized_email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log audit event
    audit = AuditEvent(
        id=str(uuid.uuid4()),
        user_id=user.id,
        event_type="auth_login",
        metadata_json={"email": normalized_email},
    )
    db.add(audit)
    db.commit()

    token = create_access_token(data={"sub": user.id, "email": user.email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_strict_current_user),
):
    """
    Retrieve current authenticated user profile.
    Strictly requires a valid Bearer token (raises 401 if missing or invalid).
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )
