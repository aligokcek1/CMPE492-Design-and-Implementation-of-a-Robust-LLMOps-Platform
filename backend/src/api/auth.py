from fastapi import APIRouter, Depends, HTTPException

from ..api.auth_helpers import require_session
from ..models.auth import (
    LogoutResponse,
    SessionStatusResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from ..services.huggingface import verify_hf_token
from ..services.session_store import INACTIVITY_TIMEOUT_SECONDS, SessionError, session_store

router = APIRouter()


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(payload: TokenVerifyRequest) -> TokenVerifyResponse:
    try:
        username = await verify_hf_token(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    session = session_store.create_session(username=username, hf_token=payload.token)
    return TokenVerifyResponse(
        username=username,
        session_token=session.session_token,
        expires_at=session.expires_at,
        inactivity_timeout_seconds=INACTIVITY_TIMEOUT_SECONDS,
    )


@router.get("/session", response_model=SessionStatusResponse)
async def get_session_status(
    session=Depends(require_session),
) -> SessionStatusResponse:
    return SessionStatusResponse(
        username=session.username,
        session_token=session.session_token,
        expires_at=session.expires_at,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout_current_session(
    session=Depends(require_session),
) -> LogoutResponse:
    try:
        session_store.revoke(session.session_token)
    except SessionError as exc:
        raise HTTPException(status_code=401, detail=exc.message)
    return LogoutResponse(status="logged_out")
