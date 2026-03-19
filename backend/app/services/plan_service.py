"""
Plan / subscription service.

Handles:
- Monthly scan counter resets
- Scan limit enforcement for free-tier users
- Pro limit = unlimited
"""

from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, Plan

FREE_SCAN_LIMIT = 3


def check_and_increment_scan(user: User, db: Session) -> None:
    """
    Called before every scan trigger.

    1. Resets monthly counter if we're in a new month.
    2. Raises 403 if free user has hit the limit.
    3. Increments scan_count.
    """
    today = date.today()

    # Reset counter at start of each month
    if user.scan_reset_date.month != today.month or user.scan_reset_date.year != today.year:
        user.scan_count = 0
        user.scan_reset_date = today

    # Enforce free-plan limit
    if user.plan == Plan.FREE and user.scan_count >= FREE_SCAN_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You have used all {FREE_SCAN_LIMIT} free scans this month. "
                "Upgrade to Pro for unlimited scans."
            ),
        )

    user.scan_count += 1
    db.commit()
