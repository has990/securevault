"""
Per-Password Secret Key System

Each stored password has an ADDITIONAL layer of encryption with its own
unique secret phrase. Even if the vault is unlocked, individual passwords
remain hidden until their specific secret is entered.

Architecture:
- Vault encryption (AES-256-GCM with master key) protects all metadata
- Per-password encryption adds a SECOND AES-256-GCM layer on the password field
- The per-password key is derived from the secret phrase via Argon2id
- A verification hash confirms the correct secret was entered
- Failed attempts are rate-limited

This means even if someone accesses the unlocked vault (e.g., you stepped away),
they still can't see individual passwords without each password's secret.
"""
import os
import hashlib
import hmac
import time
from core.crypto_context import CryptoContext
from core.key_derivation import KeyDerivation
from core.encryption import EncryptionEngine

class PerPasswordLock:
    """Manages individual secret keys for each password entry."""

    # Rate limiting for secret phrase attempts
    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 30

    def __init__(self):
        self._attempt_tracker = {}  # entry_id -> (attempts, last_attempt_time)

    def encrypt_with_secret(
        self,
        plaintext_password: str,
        secret_phrase: str,
        vault_id: str = None,
        entry_uuid: str = None,
    ) -> dict:
        """
        Encrypt a password using a separate per-password secret.
        Optional vault and entry context binds new ciphertext to its entry.
        """
        if len(secret_phrase) < 4:
            raise ValueError(
                "Secret phrase must be at least 4 characters"
            )

        per_key, per_salt = KeyDerivation.derive_key(
            secret_phrase,
        )

        verify_hash = hashlib.sha256(
            b"per_pass:" + per_key
        ).hexdigest()

        engine = EncryptionEngine(per_key)
        version = 1
        if vault_id and entry_uuid:
            aad = CryptoContext.per_password(
                entry_uuid,
            )
            encrypted_password = engine.encrypt(
                plaintext_password,
                aad=aad,
            )
            version = 2
        else:
            encrypted_password = engine.encrypt(plaintext_password)

        return {
            "encrypted_password": encrypted_password,
            "salt": per_salt,
            "verify_hash": verify_hash,
            "version": version,
            "encryption_version": version,
        }

    def decrypt_with_secret(
        self,
        encrypted_data: dict,
        secret_phrase: str,
        entry_id: str = None,
        vault_id: str = None,
        entry_uuid: str = None,
    ) -> bytes:
        """
        Decrypt a per-password-protected password in legacy V1 or
        context-bound V2 format.
        """
        if entry_id and not self._check_rate_limit(entry_id):
            remaining = self._get_lockout_remaining(entry_id)
            raise PermissionError(
                f"Too many failed attempts. "
                f"Try again in {remaining:.0f}s"
            )

        per_key, _ = KeyDerivation.derive_key(
            secret_phrase,
            salt=encrypted_data["salt"],
        )

        verify_hash = hashlib.sha256(
            b"per_pass:" + per_key
        ).hexdigest()
        if not hmac.compare_digest(
            verify_hash,
            encrypted_data["verify_hash"],
        ):
            if entry_id:
                self._record_failed_attempt(entry_id)
            raise ValueError("Incorrect secret phrase")

        if entry_id:
            self._reset_attempts(entry_id)

        engine = EncryptionEngine(per_key)
        version = encrypted_data.get(
            "version",
            encrypted_data.get("encryption_version", 1),
        )
        if version == 1:
            return engine.decrypt(encrypted_data["encrypted_password"])
        if version != 2:
            raise ValueError("Unsupported per-password encryption version")
        if not vault_id or not entry_uuid:
            raise ValueError(
                "vault_id and entry_uuid are required for V2 decryption"
            )
        aad = CryptoContext.per_password(
            entry_uuid,
        )
        return engine.decrypt(
            encrypted_data["encrypted_password"],
            aad=aad,
        )

    def _check_rate_limit(self, entry_id: str) -> bool:
        """Check if the entry is currently rate-limited."""
        if entry_id not in self._attempt_tracker:
            return True
        attempts, last_time = self._attempt_tracker[entry_id]
        if attempts >= self.MAX_ATTEMPTS:
            if time.time() - last_time < self.LOCKOUT_SECONDS:
                return False
            else:
                self._reset_attempts(entry_id)
                return True
        return True

    def _record_failed_attempt(self, entry_id: str):
        if entry_id not in self._attempt_tracker:
            self._attempt_tracker[entry_id] = (0, 0)
        attempts, _ = self._attempt_tracker[entry_id]
        self._attempt_tracker[entry_id] = (attempts + 1, time.time())

    def _reset_attempts(self, entry_id: str):
        self._attempt_tracker.pop(entry_id, None)

    def _get_lockout_remaining(self, entry_id: str) -> float:
        if entry_id not in self._attempt_tracker:
            return 0
        _, last_time = self._attempt_tracker[entry_id]
        return max(0, self.LOCKOUT_SECONDS - (time.time() - last_time))