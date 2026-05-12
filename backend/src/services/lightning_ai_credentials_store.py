"""Persistence-layer service for per-user Lightning AI API keys.

Mirrors credentials_store.py in structure. The API key is Fernet-encrypted
at rest and never returned to callers — only validation status is exposed.
The Lightning AI platform user UUID (lightning_user_id) is stored plaintext
because it is not secret.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select

from ..db import get_session_factory
from ..db.models import LightningAICredentialsRow
from .crypto import decrypt, encrypt
from .lightning_ai_provider import LightningAIProvider


@dataclass(frozen=True)
class LightningAICredentialStatus:
    configured: bool
    validation_status: str | None
    validation_error_message: str | None
    last_validated_at: datetime | None


@dataclass(frozen=True)
class LightningAICredentials:
    """Decrypted credentials ready for SDK use."""

    api_key: str
    lightning_user_id: str


class LightningAICredentialsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class LightningAICredentialsStore:
    async def save(
        self,
        *,
        user_id: str,
        lightning_user_id: str,
        api_key: str,
        provider: LightningAIProvider,
    ) -> LightningAICredentialStatus:
        """Validate and save credentials. Raises LightningAIAuthError on bad credentials."""
        await provider.validate_api_key(api_key=api_key, lightning_user_id=lightning_user_id)
        encrypted_blob = encrypt(api_key)
        now = datetime.now(UTC)

        session_factory = get_session_factory()
        with session_factory() as db:
            existing = db.execute(
                select(LightningAICredentialsRow).where(
                    LightningAICredentialsRow.user_id == user_id
                )
            ).scalar_one_or_none()

            if existing is None:
                row = LightningAICredentialsRow(
                    user_id=user_id,
                    lightning_user_id=lightning_user_id,
                    api_key_encrypted=encrypted_blob,
                    validation_status="valid",
                    validation_error_message=None,
                    last_validated_at=now,
                    created_at=now,
                    updated_at=now,
                )
                db.add(row)
            else:
                existing.lightning_user_id = lightning_user_id
                existing.api_key_encrypted = encrypted_blob
                existing.validation_status = "valid"
                existing.validation_error_message = None
                existing.last_validated_at = now
                existing.updated_at = now

            db.commit()

        return await self.get_status(user_id=user_id)

    async def get_status(self, *, user_id: str) -> LightningAICredentialStatus:
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.execute(
                select(LightningAICredentialsRow).where(
                    LightningAICredentialsRow.user_id == user_id
                )
            ).scalar_one_or_none()

        if row is None:
            return LightningAICredentialStatus(
                configured=False,
                validation_status=None,
                validation_error_message=None,
                last_validated_at=None,
            )
        return LightningAICredentialStatus(
            configured=True,
            validation_status=row.validation_status,
            validation_error_message=row.validation_error_message,
            last_validated_at=row.last_validated_at,
        )

    async def get_credentials(self, *, user_id: str) -> Optional[LightningAICredentials]:
        """Return the decrypted API key and Lightning AI user ID, or None if not configured."""
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.execute(
                select(LightningAICredentialsRow).where(
                    LightningAICredentialsRow.user_id == user_id
                )
            ).scalar_one_or_none()
        if row is None:
            return None
        if not row.lightning_user_id:
            return None
        return LightningAICredentials(
            api_key=decrypt(row.api_key_encrypted),
            lightning_user_id=row.lightning_user_id,
        )

    async def get_decrypted_key(self, *, user_id: str) -> str | None:
        """Return the raw API key if configured, else None. Legacy alias."""
        creds = await self.get_credentials(user_id=user_id)
        return creds.api_key if creds else None

    async def delete(self, *, user_id: str) -> None:
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.execute(
                select(LightningAICredentialsRow).where(
                    LightningAICredentialsRow.user_id == user_id
                )
            ).scalar_one_or_none()
            if row is None:
                return
            db.delete(row)
            db.commit()

    async def record_key_invalid(self, *, user_id: str, error: Exception) -> None:
        """Flip validation_status to 'invalid' when an SDK call fails with an auth error."""
        now = datetime.now(UTC)
        session_factory = get_session_factory()
        with session_factory() as db:
            row = db.execute(
                select(LightningAICredentialsRow).where(
                    LightningAICredentialsRow.user_id == user_id
                )
            ).scalar_one_or_none()
            if row is None:
                return
            row.validation_status = "invalid"
            row.validation_error_message = str(error)
            row.last_validated_at = now
            row.updated_at = now
            db.commit()


lightning_ai_credentials_store = LightningAICredentialsStore()


__all__ = [
    "lightning_ai_credentials_store",
    "LightningAICredentialsStore",
    "LightningAICredentialStatus",
    "LightningAICredentials",
    "LightningAICredentialsError",
]
