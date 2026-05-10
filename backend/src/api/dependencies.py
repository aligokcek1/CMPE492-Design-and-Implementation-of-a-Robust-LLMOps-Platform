"""DI helpers shared between FastAPI routes.

Kept in a separate module so route files can `Depends(get_gcp_provider)`
without pulling in `src.main` (which would be a circular import).
"""
from __future__ import annotations

import os

from ..services.gcp_fake_provider import FakeGCPProvider
from ..services.gcp_provider import GCPProvider
from ..services.lightning_ai_provider import LightningAIProvider, RealLightningAIProvider

_gcp_provider_instance: GCPProvider | None = None
_lightning_ai_provider_instance: LightningAIProvider | None = None


def _build_default_gcp_provider() -> GCPProvider:
    if os.environ.get("LLMOPS_USE_FAKE_GCP") == "1":
        return FakeGCPProvider()
    from ..services.gcp_real_provider import (
        RealGCPProvider,  # noqa: WPS433 - intentional lazy import
    )

    return RealGCPProvider()


def get_gcp_provider() -> GCPProvider:
    """FastAPI dependency returning the active GCPProvider.

    Tests override via ``app.dependency_overrides[get_gcp_provider] = ...``.
    """
    global _gcp_provider_instance
    if _gcp_provider_instance is None:
        _gcp_provider_instance = _build_default_gcp_provider()
    return _gcp_provider_instance


def reset_gcp_provider_for_tests() -> None:
    global _gcp_provider_instance
    _gcp_provider_instance = None


def get_lightning_ai_provider() -> LightningAIProvider:
    """FastAPI dependency returning the active LightningAIProvider.

    Tests override via ``app.dependency_overrides[get_lightning_ai_provider] = ...``.
    """
    global _lightning_ai_provider_instance
    if _lightning_ai_provider_instance is None:
        _lightning_ai_provider_instance = RealLightningAIProvider()
    return _lightning_ai_provider_instance


def reset_lightning_ai_provider_for_tests() -> None:
    global _lightning_ai_provider_instance
    _lightning_ai_provider_instance = None


__all__ = [
    "get_gcp_provider",
    "reset_gcp_provider_for_tests",
    "get_lightning_ai_provider",
    "reset_lightning_ai_provider_for_tests",
]
