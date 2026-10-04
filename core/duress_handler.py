"""
Duress Handler — Emergency Actions Under Coercion.
When duress password is entered:
  1. Opens the decoy vault (looks normal to attacker)
  2. Silently wipes real vault data in background
  3. Logs the incident
"""
import time
import json
import secrets
import threading
from pathlib import Path
from core.key_derivation import KeyDerivation
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from core.secure_log_store import SecureLogStore


class DuressHandler:
    """Handles panic/duress situations with configurable responses."""

    DURESS_LOG = Path.home() / ".securevault" / ".duress_log.enc"

    class Action:
        WIPE_REAL_VAULT = "wipe_real_vault"
        LOG_INCIDENT = "log_incident"
        OPEN_DECOY = "open_decoy"

    def __init__(self, db):
        self.db = db
        self._store = SecureLogStore()
        # WIPE IS NOW ENABLED BY DEFAULT
        self._actions = [
            self.Action.OPEN_DECOY,
            self.Action.WIPE_REAL_VAULT,
            self.Action.LOG_INCIDENT,
        ]

    def set_duress_password(self, duress_password, decoy_key=None,
                             decoy_vault_id=None):
        """Set the duress/panic password and link to decoy vault."""
        duress_key, duress_salt = KeyDerivation.derive_key(duress_password)
        verify_hash = KeyDerivation.create_verification_hash(duress_key)
        self.db.set_duress_credentials(duress_salt, verify_hash)

        if decoy_key is not None and decoy_vault_id is not None:
            nonce = secrets.token_bytes(12)
            aesgcm = AESGCM(duress_key)
            encrypted_decoy_key = aesgcm.encrypt(nonce, decoy_key, None)
            self.db.set_duress_decoy_link(encrypted_decoy_key, decoy_vault_id, nonce)
            return True
        return False

    def is_duress_password(self, password):
        """Check if the entered password is the duress password."""
        creds = self.db.get_duress_credentials()
        if not creds:
            return False

        salt, stored_hash = creds
        try:
            key, _ = KeyDerivation.derive_key(password, salt)
            verify_hash = KeyDerivation.create_verification_hash(key)
            return verify_hash == stored_hash
        except Exception:
            return False

    def get_decoy_vault_from_duress(self, duress_password):
        """Decrypt the decoy vault key using the duress password."""
        from core.encryption import EncryptionEngine

        creds = self.db.get_duress_credentials()
        if not creds:
            return None

        salt, _ = creds

        try:
            duress_key, _ = KeyDerivation.derive_key(duress_password, salt)
        except Exception:
            return None

        link = self.db.get_duress_decoy_link()
        if not link:
            return None

        try:
            aesgcm = AESGCM(duress_key)
            decoy_key = aesgcm.decrypt(
                link["nonce"],
                link["encrypted_decoy_key"],
                None
            )
            engine = EncryptionEngine(decoy_key)
            return {
                "engine": engine,
                "vault_id": link["decoy_vault_id"],
                "key": decoy_key,
            }
        except Exception:
            return None

    def trigger_duress(self, password):
        """Execute duress actions — wipe runs BEFORE returning to caller."""
        # Run wipe SYNCHRONOUSLY so it completes before vault opens
        self._execute_actions()

    def _execute_actions(self):
        for action in self._actions:
            try:
                if action == self.Action.WIPE_REAL_VAULT:
                    self._wipe_real_vault()
                elif action == self.Action.LOG_INCIDENT:
                    self._log_incident()
            except Exception:
                pass

    def _wipe_real_vault(self):
        """
        Remove all secret-bearing data belonging to the real vault.
        The real vault is identified as the first-created vault.
        Credentials and the decoy-vault configuration are preserved
        so the duress password can continue opening the decoy vault.
        """
        all_creds = self.db.get_all_vault_credentials()
        if not all_creds:
            return False
        real_vault_id = all_creds[0][2]
        self.db.wipe_vault_secret_data(real_vault_id)
        return True

    def _log_incident(self):
        self.DURESS_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "event": "duress_triggered",
        }
        self._store.append_json(self.DURESS_LOG, entry)