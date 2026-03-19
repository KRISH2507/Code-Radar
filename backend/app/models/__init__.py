# ============================================================================
# MODELS PACKAGE
# ============================================================================
# This file ensures all SQLAlchemy models are properly imported and registered.
# 
# WHY THIS IS CRITICAL:
# SQLAlchemy's Base.metadata only knows about models that have been imported.
# By importing all models here, we ensure they're registered before create_all()
# is called in database.py or main.py.
#
# IMPORTANT: Every new model MUST be added to this file!
# ============================================================================

# Import all models
from app.models.user import User, Plan, Role
from app.models.otp import OTP
from app.models.repository import Repository, SourceType, RepositoryStatus
from app.models.scan import Scan, ScanStatus
from app.models.issue import Issue, IssueSeverity, IssueType
from app.models.file_metrics import FileMetrics
from app.models.payment import Payment, PaymentStatus

# ============================================================================
# PUBLIC API
# ============================================================================
__all__ = [
    "User", "OTP", "Plan", "Role",
    "Repository", "SourceType", "RepositoryStatus",
    "Scan", "ScanStatus",
    "Issue", "IssueSeverity", "IssueType",
    "FileMetrics",
    "Payment", "PaymentStatus",
]

# ============================================================================
# MODEL REGISTRY
# ============================================================================
# This ensures all models are registered with SQLAlchemy's metadata
# You can access all models via this list
ALL_MODELS = [
    User,
    OTP,
    Repository,
    Scan,
    Issue,
    FileMetrics,
    Payment,
]
