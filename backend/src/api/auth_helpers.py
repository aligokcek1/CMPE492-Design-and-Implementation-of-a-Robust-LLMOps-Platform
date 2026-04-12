from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from ..services.session_store import SessionContext, SessionError, session_store


def _extract_session_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization.removeprefix("Bearer ").strip()


def _session_error_to_http(exc: SessionError) -> HTTPException:
    if exc.code == "idempotency_conflict":
        return HTTPException(
            status_code=409,
            detail={"code": "idempotency_conflict", "message": exc.message},
        )

    code_map = {
        "missing": "session_missing",
        "revoked": "session_revoked",
        "expired": "session_expired",
    }
    return HTTPException(
        status_code=401,
        detail={"code": code_map.get(exc.code, "session_invalid"), "message": exc.message},
    )


def require_session(
    authorization: Annotated[str | None, Header()] = None,
) -> SessionContext:
    token = _extract_session_token(authorization)
    try:
        return session_store.validate_and_touch(token)
    except SessionError as exc:
        raise _session_error_to_http(exc)
