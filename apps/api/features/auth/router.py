"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.features.auth.roles import has_researcher_access, is_admin
from apps.api.features.auth.service import AuthError, auth_service
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_required
from apps.api.shared.models import User
from apps.api.shared.schemas.common import (
    AuthResponse,
    LoginOtpRequest,
    OtpRequestResponse,
    OtpVerify,
    RegisterRequest,
    UserMeResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _auth_response(user: User, token: str) -> AuthResponse:
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        phone_number=user.phone_number or "",
        email=user.email,
        full_name=user.full_name,
        whatsapp_opt_in=user.whatsapp_opt_in,
        role=user.role,
    )


def _otp_response(
    expires_in: int,
    dev_code: str | None,
    email_hint: str | None,
    *,
    action: str,
) -> OtpRequestResponse:
    if dev_code:
        message = "Email is not configured; use the development code shown below."
    elif email_hint:
        message = f"Verification code sent to {email_hint}."
    else:
        message = f"Verification code sent to your email ({action})."
    return OtpRequestResponse(
        message=message,
        expires_in_seconds=expires_in,
        dev_code=dev_code,
        email_hint=email_hint,
        phone_hint=None,
    )


@router.post("/register", response_model=OtpRequestResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        expires_in, dev_code, email_hint = auth_service.register_and_request_otp(
            db,
            full_name=payload.full_name,
            email=payload.email,
            phone_number=payload.phone_number,
            whatsapp_opt_in=payload.whatsapp_opt_in,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _otp_response(expires_in, dev_code, email_hint, action="registration")


@router.post("/login/otp/request", response_model=OtpRequestResponse)
def request_login_otp(payload: LoginOtpRequest, db: Session = Depends(get_db)):
    try:
        expires_in, dev_code, email_hint = auth_service.request_login_otp(
            db,
            email=payload.email,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _otp_response(expires_in, dev_code, email_hint, action="sign-in")


@router.post("/otp/verify", response_model=AuthResponse)
def verify_otp(payload: OtpVerify, db: Session = Depends(get_db)):
    try:
        user, token = auth_service.verify_otp(db, email=payload.email, code=payload.code)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return _auth_response(user, token)


@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user_required)):
    return UserMeResponse(
        id=current_user.id,
        phone_number=current_user.phone_number or "",
        email=current_user.email,
        full_name=current_user.full_name,
        whatsapp_opt_in=current_user.whatsapp_opt_in,
        role=current_user.role,
        is_admin=is_admin(current_user),
        can_access_admin=is_admin(current_user),
        can_use_research_features=has_researcher_access(current_user),
    )
