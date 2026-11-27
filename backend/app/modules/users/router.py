"""User administration. Admin only."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import WeakPasswordError
from app.modules.auth.deps import actor_of, require_roles
from app.modules.users import service
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserOut

router = APIRouter(prefix="/users", tags=["users (admin only)"])
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
DB = Annotated[Session, Depends(get_db)]


class UserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: str = Field(min_length=1, max_length=80)
    role: Role
    password: SecretStr


class RoleChangeIn(BaseModel):
    role: Role
    reason: str = Field(min_length=3, max_length=300)


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)


class ResetPasswordIn(BaseModel):
    new_password: SecretStr


def _get(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


def _run(db: Session, action: object) -> None:
    """Translate service errors into safe HTTP errors and commit on success."""
    try:
        action()  # type: ignore[operator]
    except service.PermissionDeniedError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from None
    except (service.UserError, WeakPasswordError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    db.commit()


@router.get("", response_model=list[UserOut])
def list_users(_: AdminUser, db: DB) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreateIn, admin: AdminUser, db: DB) -> User:
    created: list[User] = []
    _run(
        db,
        lambda: created.append(
            service.create_user(
                db,
                actor=actor_of(admin),
                username=body.username,
                display_name=body.display_name,
                role=body.role,
                password=body.password.get_secret_value(),
            )
        ),
    )
    return created[0]


@router.post("/{user_id}/role", response_model=UserOut)
def change_role(user_id: int, body: RoleChangeIn, admin: AdminUser, db: DB) -> User:
    user = _get(db, user_id)
    _run(
        db,
        lambda: service.change_role(
            db, actor=actor_of(admin), user=user, new_role=body.role, reason=body.reason
        ),
    )
    return user


@router.post("/{user_id}/deactivate", response_model=UserOut)
def deactivate(user_id: int, body: ReasonIn, admin: AdminUser, db: DB) -> User:
    user = _get(db, user_id)
    _run(
        db,
        lambda: service.deactivate_user(db, actor=actor_of(admin), user=user, reason=body.reason),
    )
    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(user_id: int, body: ResetPasswordIn, admin: AdminUser, db: DB) -> None:
    """Also unlocks a locked account and logs the user out everywhere."""
    user = _get(db, user_id)
    _run(
        db,
        lambda: service.set_password(
            db, actor=actor_of(admin), user=user, new_password=body.new_password.get_secret_value()
        ),
    )
