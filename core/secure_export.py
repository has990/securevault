"""
Encrypted Export/Import — Secure backup and restore.

Exports the vault as an AES-256-GCM encrypted JSON file.
The export is protected by its own password (separate from master).
"""
import json
import time
from core.encryption import EncryptionEngine
from core.key_derivation import KeyDerivation

class SecureExport:
    """Export and import vault data with independent encryption."""

    EXPORT_VERSION = "2.0"

    @staticmethod
    def _to_json_safe(value):
        if isinstance(value, bytes):
            return {"__type__": "bytes", "hex": value.hex()}
        if isinstance(value, dict):
            return {key: SecureExport._to_json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [SecureExport._to_json_safe(item) for item in value]
        return value

    @staticmethod
    def _from_json_safe(value):
        if isinstance(value, dict):
            if value.get("__type__") == "bytes" and "hex" in value:
                return bytes.fromhex(value["hex"])
            return {key: SecureExport._from_json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [SecureExport._from_json_safe(item) for item in value]
        return value

    @staticmethod
    def export_vault(entries: list, export_password: str, filepath: str) -> dict:
        """
        Export all vault entries to an encrypted file.
        
        Args:
            entries: list of decrypted entry dicts
            export_password: password to encrypt the export file
            filepath: output file path (.svault)
        """
        # Derive export key
        key, salt = KeyDerivation.derive_key(export_password)
        engine = EncryptionEngine(key)

        # Serialize entries
        payload = json.dumps({
            "version": SecureExport.EXPORT_VERSION,
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "entry_count": len(entries),
            "entries": SecureExport._to_json_safe(entries),
        })

        # Encrypt
        encrypted_data = engine.encrypt(payload)

        # Write to file
        export_data = {
            "format": "SecureVault Encrypted Export",
            "version": SecureExport.EXPORT_VERSION,
            "salt": salt.hex(),
            "data": encrypted_data.hex(),
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        return {"status": "success", "entries_exported": len(entries), "filepath": filepath}

    @staticmethod
    def import_vault(filepath: str, import_password: str) -> list:
        """
        Import entries from an encrypted export file.
        
        Returns:
            list of decrypted entry dicts
        """
        with open(filepath, 'r') as f:
            export_data = json.load(f)

        if export_data.get("format") != "SecureVault Encrypted Export":
            raise ValueError("Invalid export file format")

        salt = bytes.fromhex(export_data["salt"])
        encrypted_data = bytes.fromhex(export_data["data"])

        # Derive key and decrypt
        key, _ = KeyDerivation.derive_key(import_password, salt)
        engine = EncryptionEngine(key)

        payload = json.loads(engine.decrypt(encrypted_data))
        return SecureExport._from_json_safe(payload.get("entries", []))