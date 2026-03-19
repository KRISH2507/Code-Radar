"""
Authentication routes — login, signup, OTP verify, Google OAuth, /me.

Error handling principles:
- Every route is wrapped in try/except with traceback.print_exc() for debugging.
- User-facing errors use 400/401/404, never 500 for expected cases.
- None checks happen explicitly before any operation that could crash.
- JWT creation always receives validated, non-None values.
- DB commits are wrapped so failures roll back cleanly.
"""

import os
import random
import traceback
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, get_current_user
from app.models.user import User
from app.models.otp import OTP
from app.schemas.auth import (
    SignupRequest, SignupResponse, LoginRequest,
    VerifyOTPRequest, GoogleAuthRequest, TokenResponse, UserResponse,
    ResendOTPRequest,
)
from app.services.email_service import send_otp_email

router = APIRouter()


# ---------------------------------------------------------------------------
# SIGNUP
# ---------------------------------------------------------------------------

@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == payload.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if not payload.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required",
            )

        user = User(
            email=payload.email,
            name=payload.name,
            hashed_password=hash_password(payload.password),
            auth_provider="email",
            is_verified=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        otp_code = str(random.randint(100000, 999999))
        otp = OTP(
            user_id=user.id,
            code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        db.add(otp)
        db.commit()

        try:
            send_otp_email(user.email, otp_code)
        except Exception as mail_err:
            print(f"[WARN] signup: email send failed for {user.email}: {mail_err}")

        return SignupResponse(
            id=user.id,
            email=user.email,
            is_verified=user.is_verified,
        )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] signup: unexpected error for {payload.email}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        # 1. Check JWT_SECRET is configured
        from app.core.config import settings
        if not settings.JWT_SECRET:
            print("[ERROR] login: JWT_SECRET is not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: JWT_SECRET missing",
            )

        # 2. Look up user
        user = db.query(User).filter(User.email == payload.email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # 3. Guard against Google-only accounts
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account uses Google login. Please sign in with Google.",
            )

        # 4. Verify password
        try:
            password_valid = verify_password(payload.password, user.hashed_password)
        except Exception as pwd_err:
            print(f"[ERROR] login: verify_password crashed: {pwd_err}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password verification failed",
            )

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # 5. Generate + persist OTP
        otp_code = str(random.randint(100000, 999999))
        otp = OTP(
            user_id=user.id,
            code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        db.add(otp)
        try:
            db.commit()
        except Exception as db_err:
            print(f"[ERROR] login: db commit failed: {db_err}")
            traceback.print_exc()
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while saving OTP",
            )

        # 6. Send OTP — non-fatal
        try:
            send_otp_email(user.email, otp_code)
        except Exception as mail_err:
            print(f"[WARN] login: email send failed for {user.email}: {mail_err}")

        return {"message": "OTP sent to your email", "email": user.email}

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] login: unexpected error for {payload.email}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# VERIFY OTP
# ---------------------------------------------------------------------------

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        otp = (
            db.query(OTP)
            .filter(
                OTP.user_id == user.id,
                OTP.code == payload.code,
                OTP.expires_at > datetime.utcnow(),
            )
            .first()
        )
        if otp is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        user.is_verified = True
        db.delete(otp)
        try:
            db.commit()
        except Exception as db_err:
            print(f"[ERROR] verify_otp: db commit failed: {db_err}")
            traceback.print_exc()
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while verifying OTP",
            )

        if user.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User ID is None after commit",
            )

        access_token = create_access_token({"user_id": user.id})
        return TokenResponse(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] verify_otp: unexpected error for {payload.email}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# GOOGLE OAUTH
# ---------------------------------------------------------------------------

@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        # 1. Check server config
        client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        if not client_id:
            print("[ERROR] google_auth: GOOGLE_CLIENT_ID env var is not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth is not configured on this server",
            )

        # 2. Import google-auth library
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
        except ImportError as imp_err:
            print(f"[ERROR] google_auth: google-auth package not installed: {imp_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server missing google-auth package",
            )

        # 3. Verify the token
        try:
            idinfo = id_token.verify_oauth2_token(
                payload.token,
                google_requests.Request(),
                client_id,
            )
        except ValueError as val_err:
            print(f"[WARN] google_auth: invalid token: {val_err}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(val_err)}",
            )
        except Exception as verify_err:
            print(f"[ERROR] google_auth: token verification error: {verify_err}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token verification failed",
            )

        # 4. Extract and validate claims
        email: str = idinfo.get("email", "").strip()
        name: str = idinfo.get("name", "").strip()
        email_verified: bool = idinfo.get("email_verified", False)

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token does not contain an email address",
            )
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is not verified",
            )

        # 5. Find or create user
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                name=name or None,
                auth_provider="google",
                is_verified=True,
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except Exception as db_err:
                print(f"[ERROR] google_auth: db commit failed creating user: {db_err}")
                traceback.print_exc()
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database error while creating Google user",
                )
        else:
            if not user.name and name:
                user.name = name
                try:
                    db.commit()
                except Exception:
                    db.rollback()

        # 6. Create JWT
        if user.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User ID is None after commit",
            )

        access_token = create_access_token({"user_id": user.id})
        return TokenResponse(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] google_auth: unexpected error")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# RESEND OTP
# ---------------------------------------------------------------------------

@router.post("/resend-otp")
def resend_otp(payload: ResendOTPRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        if user is None:
            return {"message": "If an account exists, a new OTP has been sent"}

        db.query(OTP).filter(OTP.user_id == user.id).delete()

        otp_code = str(random.randint(100000, 999999))
        otp = OTP(
            user_id=user.id,
            code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        db.add(otp)
        try:
            db.commit()
        except Exception as db_err:
            print(f"[ERROR] resend_otp: db commit failed: {db_err}")
            traceback.print_exc()
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while generating OTP",
            )

        try:
            send_otp_email(user.email, otp_code)
        except Exception as mail_err:
            print(f"[WARN] resend_otp: email send failed: {mail_err}")

        return {"message": "If an account exists, a new OTP has been sent"}

    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] resend_otp: unexpected error for {payload.email}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend OTP failed: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# /ME
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    try:
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            is_verified=current_user.is_verified,
            plan=current_user.plan.value if hasattr(current_user.plan, "value") else str(current_user.plan),
            role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            scan_count=current_user.scan_count or 0,
            scan_reset_date=current_user.scan_reset_date,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] /me: unexpected error for user {getattr(current_user, 'id', '?')}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user info: {str(exc)}",
        )
