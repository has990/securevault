"""
Decoy Vault Manager — Creates and manages plausible deniability vaults.
"""
import hashlib
from core.key_derivation import KeyDerivation
from core.encryption import EncryptionEngine


class DecoyVaultManager:
    """Creates and identifies real vs decoy vaults."""

    def __init__(self, db):
        self.db = db
        # These hold the decoy key temporarily so duress can link to it
        self._last_decoy_key = None
        self._last_decoy_vault_id = None

    @staticmethod
    def _derive_vault_id(key: bytes) -> str:
        """Derive a unique vault ID from the encryption key."""
        return hashlib.sha256(key).hexdigest()[:16]

    def create_decoy_vault(self, decoy_password, decoy_entries=None):
        """Create a decoy vault. Stores key temporarily for duress linking."""
        if len(decoy_password) < 8:
            raise ValueError("Decoy password must be at least 8 characters")

        key, salt = KeyDerivation.derive_key(decoy_password)
        verify_hash = KeyDerivation.create_verification_hash(key)
        vault_id = self._derive_vault_id(key)

        # Store key temporarily so duress setup can grab it
        self._last_decoy_key = key
        self._last_decoy_vault_id = vault_id

        self.db.add_vault_credentials(salt, verify_hash, vault_id)

        # Add fake entries if provided
        if decoy_entries:
            engine = EncryptionEngine(key)
            for entry in decoy_entries:
                self.db.add_entry(
                    service=engine.encrypt(entry.get("service", "Example")),
                    username=engine.encrypt(entry.get("username", "user@email.com")),
                    password=engine.encrypt(entry.get("password", "P@ssword123")),
                    url=engine.encrypt(entry.get("url", "")),
                    notes=engine.encrypt(entry.get("notes", "")),
                    vault_id=vault_id,
                )

        return {"vault_id": vault_id, "key": key}

    def identify_vault(self, password):
        """Try to open any vault with the given password."""
        all_creds = self.db.get_all_vault_credentials()

        for salt, stored_hash, vault_id in all_creds:
            try:
                key, _ = KeyDerivation.derive_key(password, salt)
                verify_hash = KeyDerivation.create_verification_hash(key)
                if verify_hash == stored_hash:
                    engine = EncryptionEngine(key)
                    return {
                        "engine": engine,
                        "vault_id": vault_id,
                        "key": key,
                    }
            except Exception:
                continue

        return None