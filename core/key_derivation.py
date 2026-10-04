"""
Argon2id Key Derivation
- Memory-hard (resistant to GPU/ASIC attacks)
- Unique salt per user
- Configurable parameters for future-proofing
"""
import os
import hashlib
from argon2.low_level import hash_secret_raw, Type

class KeyDerivation:
    # Argon2id parameters (OWASP recommended)
    TIME_COST = 3           # iterations
    MEMORY_COST = 65536     # 64 MB
    PARALLELISM = 4         # threads
    HASH_LEN = 32           # 256-bit derived key
    SALT_LEN = 16           # 128-bit salt

    @staticmethod
    def derive_key(master_password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """Derive a 256-bit encryption key from the master password."""
        if salt is None:
            salt = os.urandom(KeyDerivation.SALT_LEN)

        key = hash_secret_raw(
            secret=master_password.encode('utf-8'),
            salt=salt,
            time_cost=KeyDerivation.TIME_COST,
            memory_cost=KeyDerivation.MEMORY_COST,
            parallelism=KeyDerivation.PARALLELISM,
            hash_len=KeyDerivation.HASH_LEN,
            type=Type.ID  # Argon2id
        )
        return key, salt

    @staticmethod
    def create_verification_hash(key: bytes) -> str:
        """Create a hash of the derived key for master password verification."""
        return hashlib.sha256(key).hexdigest()