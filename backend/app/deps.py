"""
FastAPI dependencies for auth. get_current_user is what every protected
endpoint depends on — it's the single enforcement point that guarantees a
request can only ever see data belonging to its own organization.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.database import get_db
from app.db_models import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user_id: str
    organization_id: str
    email: str
    full_name: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()  # noqa: E712
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Defense in depth: trust the DB's current org assignment, not just the
    # token claim, in case a user was ever moved between orgs.
    return CurrentUser(
        user_id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )
