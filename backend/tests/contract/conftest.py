from __future__ import annotations

import pytest
from httpx import ASGITransport

from src.main import app
from src.services.session_store import session_store


@pytest.fixture
def transport() -> ASGITransport:
    return ASGITransport(app=app)


@pytest.fixture(autouse=True)
def reset_session_store() -> None:
    session_store._sessions.clear()  # noqa: SLF001 - test-only cleanup
    session_store._idempotency.clear()  # noqa: SLF001 - test-only cleanup
