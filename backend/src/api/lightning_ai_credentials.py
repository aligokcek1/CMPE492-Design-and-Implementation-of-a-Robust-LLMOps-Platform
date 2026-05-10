from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..models.lightning_ai_credentials import (
    LightningAICredentialRequest,
    LightningAICredentialStatus,
)
from ..services.lightning_ai_credentials_store import lightning_ai_credentials_store
from ..services.lightning_ai_provider import LightningAIAuthError, LightningAIProvider
from ..services.session_store import SessionContext
from .auth_helpers import require_session
from .dependencies import get_lightning_ai_provider

router = APIRouter()


def _to_response(status_obj) -> LightningAICredentialStatus:
    return LightningAICredentialStatus(
        configured=status_obj.configured,
        validation_status=status_obj.validation_status,
        validation_error_message=status_obj.validation_error_message,
        last_validated_at=status_obj.last_validated_at,
    )


@router.get("", response_model=LightningAICredentialStatus)
async def get_credentials_status(
    session: SessionContext = Depends(require_session),
) -> LightningAICredentialStatus:
    status_obj = await lightning_ai_credentials_store.get_status(user_id=session.username)
    return _to_response(status_obj)


@router.post("", response_model=LightningAICredentialStatus)
async def save_credentials(
    payload: LightningAICredentialRequest,
    session: SessionContext = Depends(require_session),
    provider: LightningAIProvider = Depends(get_lightning_ai_provider),
) -> LightningAICredentialStatus:
    try:
        status_obj = await lightning_ai_credentials_store.save(
            user_id=session.username,
            api_key=payload.api_key,
            provider=provider,
        )
    except LightningAIAuthError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "lightning_auth_error", "message": exc.message},
        ) from exc

    return _to_response(status_obj)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credentials(
    session: SessionContext = Depends(require_session),
) -> Response:
    await lightning_ai_credentials_store.delete(user_id=session.username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
