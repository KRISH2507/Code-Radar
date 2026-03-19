"""
Admin API  (admin-only endpoints)

GET   /api/admin/users           – List all users
PATCH /api/admin/users/{id}/plan – Manually upgrade or downgrade a user's plan
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import get_current_user, require_admin
from app.models.user import User, Plan

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas (inline — too small to warrant a separate file)
# ---------------------------------------------------------------------------

class AdminUserItem(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    plan: str
    role: str
    scan_count: int
    is_verified: bool

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    users: List[AdminUserItem]
    total: int


class UpdatePlanRequest(BaseModel):
    plan: str  # "free" or "pro"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users. Admin only."""
    base_q = db.query(User)
    total = base_q.count()
    users = (
        base_q
        .order_by(User.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AdminUserListResponse(users=users, total=total)


@router.patch("/users/{user_id}/plan")
def update_user_plan(
    user_id: int,
    payload: UpdatePlanRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Manually set a user's plan. Admin only."""
    if payload.plan not in ("free", "pro"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="plan must be 'free' or 'pro'",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.plan = Plan.FREE if payload.plan == "free" else Plan.PRO
    if payload.plan == "free":
        user.scan_count = 0  # reset counter on downgrade
    db.commit()

    return {
        "id": user.id,
        "email": user.email,
        "plan": user.plan.value,
        "message": f"Plan updated to {payload.plan}",
    }
