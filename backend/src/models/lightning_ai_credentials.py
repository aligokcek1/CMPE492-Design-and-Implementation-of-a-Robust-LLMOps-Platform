from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LightningAICredentialRequest(BaseModel):
    lightning_user_id: str = Field(
        ...,
        description="Lightning AI platform user UUID (LIGHTNING_USER_ID). Stored plaintext.",
    )
    api_key: str = Field(
        ..., description="Raw Lightning AI API key. Encrypted at rest; never returned."
    )


class LightningAICredentialStatus(BaseModel):
    configured: bool
    validation_status: str | None = None
    validation_error_message: str | None = None
    last_validated_at: datetime | None = None


__all__ = ["LightningAICredentialRequest", "LightningAICredentialStatus"]
