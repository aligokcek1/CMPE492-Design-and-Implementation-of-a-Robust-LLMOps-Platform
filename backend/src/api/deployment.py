from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from ..api.auth_helpers import require_session
from ..models.deployment import MockDeploymentRequest, MockDeploymentResponse
from ..services.mock_gcp import mock_deploy
from ..services.session_store import SessionError, session_store

router = APIRouter()


@router.post("/mock", response_model=MockDeploymentResponse)
async def start_mock_deployment(
    payload: MockDeploymentRequest,
    idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
    session=Depends(require_session),
) -> MockDeploymentResponse:
    request_fingerprint = f"{payload.model_repository}|{payload.resource_type.value}"
    try:
        replay = session_store.check_idempotency(
            username=session.username,
            operation_type="deploy",
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
        )
    except SessionError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    if replay is not None:
        return MockDeploymentResponse(**replay.response_body)

    try:
        response = await mock_deploy(payload.model_repository, payload.resource_type)
        session_store.store_idempotency_result(
            username=session.username,
            operation_type="deploy",
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            status_code=200,
            response_body=response.model_dump(),
        )
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
