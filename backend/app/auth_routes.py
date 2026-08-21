from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import (
    hash_password, verify_password, create_access_token,
    generate_refresh_token, hash_refresh_token,
)
from app.auth_schemas import SignupRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from app.database import get_db
from app.db_models import Organization, User, RefreshToken
from app.deps import get_current_user, CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(user_id=user.id, organization_id=user.organization_id)
    raw_refresh, refresh_hash, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=refresh_hash, expires_at=expires_at))
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Creates a new organization and its first (admin) user. Each signup
    creates its own isolated organization — this is the B2B tenant boundary."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    org = Organization(name=payload.organization_name)
    db.add(org)
    db.flush()  # get org.id without committing yet

    user = User(
        organization_id=org.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        # Same error for "no such user" and "wrong password" — don't leak
        # which one it was, that helps an attacker enumerate valid emails.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if stored is None or stored.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired, please log in again")

    user = db.query(User).filter(User.id == stored.user_id, User.is_active == True).first()  # noqa: E712
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Rotate: revoke the used refresh token and issue a new pair. Limits
    # damage if a refresh token is ever stolen (it becomes single-use).
    stored.revoked = True
    db.commit()
    return _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored:
        stored.revoked = True
        db.commit()
    return None


@router.get("/me", response_model=UserResponse)
def me(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == current.organization_id).first()
    return UserResponse(
        id=current.user_id, email=current.email, full_name=current.full_name,
        role=current.role, organization_id=current.organization_id,
        organization_name=org.name if org else "",
    )
