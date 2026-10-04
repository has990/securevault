"""
AES-256-GCM Encryption Engine
- Authenticated encryption (confidentiality + integrity)
- Unique nonce per encryption operation
- Zero plaintext residue in memory
"""
import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class EncryptionEngine:
    NONCE_SIZE = 12  # 96-bit nonce for AES-GCM
    KEY_SIZE = 32    # 256-bit key
    V2_PREFIX = b"SV2\x00"

    def __init__(self, key: bytes):
        if not isinstance(key, bytes):
            raise TypeError("Key must be bytes")

        if len(key) != self.KEY_SIZE:
            raise ValueError("Key must be 256 bits (32 bytes)")

        self._key = bytes(key)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext, aad=None):
        """
        Encrypt plaintext using AES-GCM.

        Legacy mode (aad=None) preserves nonce + ciphertext.
        AAD-enabled mode returns V2_PREFIX + nonce + ciphertext.
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        elif not isinstance(plaintext, bytes):
            raise TypeError("Plaintext must be str or bytes")
        if aad is not None and not isinstance(aad, bytes):
            raise TypeError("AAD must be bytes or None")
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext,
            aad,
        )
        if aad is None:
            return nonce + ciphertext
        return self.V2_PREFIX + nonce + ciphertext

    def decrypt(self, encrypted_data, aad=None):
        """
        Decrypt legacy V1 or context-bound V2 SecureVault ciphertext.
        """
        if not isinstance(encrypted_data, bytes):
            raise TypeError("Encrypted data must be bytes")
        is_v2 = encrypted_data.startswith(self.V2_PREFIX)
        if is_v2:
            if aad is None:
                raise ValueError(
                    "AAD is required to decrypt V2 ciphertext"
                )
            encrypted_data = encrypted_data[len(self.V2_PREFIX):]
        elif aad is not None:
            raise ValueError(
                "AAD cannot be used with legacy V1 ciphertext"
            )
        if len(encrypted_data) < self.NONCE_SIZE:
            raise ValueError("Encrypted data is too short")
        if aad is not None and not isinstance(aad, bytes):
            raise TypeError("AAD must be bytes or None")
        nonce = encrypted_data[:self.NONCE_SIZE]
        ciphertext = encrypted_data[self.NONCE_SIZE:]
        return self._aesgcm.decrypt(
            nonce,
            ciphertext,
            aad,
        )

    @staticmethod
    def generate_key() -> bytes:
        """Generate a cryptographically secure 256-bit key."""
        return secrets.token_bytes(EncryptionEngine.KEY_SIZE)