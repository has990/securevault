"""
SecureVault cryptographic context helpers.

Provides deterministic Authenticated Associated Data (AAD) for
AES-GCM operations.

AAD is not encrypted. It is authenticated, meaning ciphertext cannot
be moved to a different security context without causing decryption
to fail.
"""

import json
from typing import Any


class CryptoContext:
    """Build canonical AAD values for SecureVault encryption."""

    DOMAIN = "SecureVault"
    VERSION = 1

    @classmethod
    def _build(cls, context_type: str, **values: Any) -> bytes:
        """
        Build deterministic AAD using canonical JSON.

        The resulting representation is stable across Python runs and
        avoids delimiter-collision problems that can occur with simple
        strings such as 'vault|entry|field'.
        """

        if not context_type:
            raise ValueError("context_type is required")

        payload = {
            "domain": cls.DOMAIN,
            "version": cls.VERSION,
            "context": context_type,
            **values,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return canonical.encode("utf-8")

    @classmethod
    def entry(
        cls,
        vault_id: str,
        entry_id: str,
        field: str,
    ) -> bytes:
        """
        Build AAD for a password-manager entry field.

        Example fields:
            service
            username
            password
            url
            notes
        """

        if not vault_id:
            raise ValueError("vault_id is required")

        if not entry_id:
            raise ValueError("entry_id is required")

        if not field:
            raise ValueError("field is required")

        return cls._build(
            "entry",
            vault_id=vault_id,
            entry_id=str(entry_id),
            field=field,
        )

    @classmethod
    def per_password(
        cls,
        entry_uuid: str,
    ) -> bytes:
        """
        Build AAD for the independent per-password protection layer.

        The context intentionally excludes vault_id so protected password
        ciphertext can survive a legitimate backup/restore into another
        vault.
        """
        if not entry_uuid:
            raise ValueError("entry_uuid is required")

        return cls._build(
            "per_password",
            entry_uuid=str(entry_uuid),
        )

    @classmethod
    def totp(
        cls,
        vault_id: str,
        entry_id: str,
        field: str,
    ) -> bytes:
        """Build AAD for a TOTP entry field."""

        if not vault_id:
            raise ValueError("vault_id is required")

        if not entry_id:
            raise ValueError("entry_id is required")

        if not field:
            raise ValueError("field is required")

        return cls._build(
            "totp",
            vault_id=vault_id,
            entry_id=str(entry_id),
            field=field,
        )

    @classmethod
    def otp_settings(
        cls,
        vault_id: str,
        field: str,
    ) -> bytes:
        """Build AAD for vault-level OTP settings."""

        if not vault_id:
            raise ValueError("vault_id is required")

        if not field:
            raise ValueError("field is required")

        return cls._build(
            "otp_settings",
            vault_id=vault_id,
            field=field,
        )

    @classmethod
    def vault_credential(
        cls,
        vault_id: str,
        field: str,
    ) -> bytes:
        """Build AAD for vault credential metadata."""

        if not vault_id:
            raise ValueError("vault_id is required")

        if not field:
            raise ValueError("field is required")

        return cls._build(
            "vault_credential",
            vault_id=vault_id,
            field=field,
        )