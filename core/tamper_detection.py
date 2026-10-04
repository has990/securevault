"""Tamper Detection - verify generic and vault-scoped integrity."""

import hashlib
import hmac
import json
import os
import sqlite3
from pathlib import Path


class TamperDetection:
    """Detect unauthorized modifications to SecureVault data."""

    # Legacy/general integrity location.
    INTEGRITY_FILE = Path.home() / ".securevault" / ".integrity"

    # Vault-scoped integrity records.
    INTEGRITY_DIR = Path.home() / ".securevault" / "integrity"
    SNAPSHOT_VERSION = 1

    def __init__(
        self,
        vault_path: str,
        key: bytes,
        vault_id: str = None,
    ):
        if not isinstance(key, bytes):
            raise TypeError("Integrity key must be bytes")
        if len(key) != 32:
            raise ValueError("Integrity key must be 32 bytes")
        self.vault_path = vault_path
        self.key = key
        self.vault_id = vault_id

    def create_integrity_record(self):
        """Create a trusted integrity baseline."""
        if self.vault_id is None:
            record = {
                "hmac": self._compute_file_hmac(),
                "size": os.path.getsize(self.vault_path),
                "mtime": os.path.getmtime(self.vault_path),
            }
            self.INTEGRITY_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.INTEGRITY_FILE.write_text(json.dumps(record))
            return

        snapshot = self._create_vault_snapshot()
        record = {
            "version": self.SNAPSHOT_VERSION,
            "vault_id": self.vault_id,
            "snapshot": snapshot,
            "hmac": self._compute_snapshot_hmac(snapshot),
        }
        integrity_file = self._vault_integrity_file()
        integrity_file.parent.mkdir(parents=True, exist_ok=True)
        integrity_file.write_text(json.dumps(record, sort_keys=True))

    def verify_integrity(self) -> dict:
        """Verify the current generic file or vault-scoped snapshot."""
        if self.vault_id is None:
            return self._verify_file_integrity()

        integrity_file = self._vault_integrity_file()
        if not integrity_file.exists():
            return {
                "intact": True,
                "baseline_exists": False,
                "warnings": ["No integrity baseline found"],
                "details": {
                    "baseline_exists": False,
                },
            }

        try:
            record = json.loads(integrity_file.read_text())
            snapshot = self._create_vault_snapshot()
            details = {
                "baseline_exists": True,
                "version_match": record.get("version") == self.SNAPSHOT_VERSION,
                "vault_id_match": record.get("vault_id") == self.vault_id,
                "hmac_match": hmac.compare_digest(
                    self._compute_snapshot_hmac(record.get("snapshot", {})),
                    record.get("hmac", ""),
                ),
                "snapshot_match": snapshot == record.get("snapshot"),
            }
            warnings = []
            if not details["version_match"]:
                warnings.append("Integrity baseline version is unsupported")
            if not details["vault_id_match"]:
                warnings.append("Integrity baseline belongs to another vault")
            if not details["hmac_match"]:
                warnings.append("Integrity baseline authentication failed")
            if not details["snapshot_match"]:
                warnings.append("Vault-scoped data has been modified externally")
            return {
                "intact": all(details.values()),
                "baseline_exists": True,
                "warnings": warnings,
                "details": details,
            }
        except (OSError, json.JSONDecodeError, sqlite3.Error, TypeError, ValueError) as exc:
            return {
                "intact": False,
                "warnings": [f"Integrity check failed: {exc}"],
                "details": {},
            }

    def _verify_file_integrity(self) -> dict:
        warnings = []
        details = {}

        if not self.INTEGRITY_FILE.exists():
            return {
                "intact": True,
                "baseline_exists": False,
                "warnings": ["No integrity baseline found"],
                "details": {
                    "baseline_exists": False,
                },
            }

        try:
            record = json.loads(self.INTEGRITY_FILE.read_text())
            current_hmac = self._compute_file_hmac()
            details["hmac_match"] = current_hmac == record.get("hmac")
            details["baseline_exists"] = True
            if not details["hmac_match"]:
                warnings.append("Vault file content has been modified externally!")

            current_size = os.path.getsize(self.vault_path)
            details["size_match"] = current_size == record.get("size")
            if not details["size_match"]:
                warnings.append(
                    f"Vault file size changed: {record.get('size')} -> {current_size}"
                )

            return {
                "intact": all(details.values()),
                "baseline_exists": True,
                "warnings": warnings,
                "details": details,
            }
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return {
                "intact": False,
                "warnings": [f"Integrity check failed: {exc}"],
                "details": {},
            }

    def _create_vault_snapshot(self) -> dict:
        conn = sqlite3.connect(self.vault_path)
        try:
            conn.row_factory = sqlite3.Row
            return {
                "vault_credentials": self._query_rows(
                    conn,
                    """
                    SELECT * FROM vault_credentials
                    WHERE vault_id = ?
                    ORDER BY id
                    """,
                    self.vault_id,
                ),
                "entries": self._query_rows(
                    conn,
                    """
                    SELECT * FROM entries
                    WHERE vault_id = ?
                    ORDER BY id
                    """,
                    self.vault_id,
                ),
                "totp_entries": self._query_rows(
                    conn,
                    """
                    SELECT * FROM totp_entries
                    WHERE vault_id = ?
                    ORDER BY id
                    """,
                    self.vault_id,
                ),
                "otp_settings": self._query_rows(
                    conn,
                    """
                    SELECT * FROM otp_settings
                    WHERE vault_id = ?
                    ORDER BY id
                    """,
                    self.vault_id,
                ),
            }
        finally:
            conn.close()

    def _query_rows(self, conn, query: str, vault_id: str) -> list:
        rows = conn.execute(query, (vault_id,)).fetchall()
        return [
            {key: self._json_value(value) for key, value in dict(row).items()}
            for row in rows
        ]

    @staticmethod
    def _json_value(value):
        if isinstance(value, bytes):
            return {"__bytes__": value.hex()}
        return value

    def _compute_snapshot_hmac(self, snapshot: dict) -> str:
        payload = json.dumps(
            snapshot,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def _vault_integrity_file(self) -> Path:
        vault_hash = hashlib.sha256(self.vault_id.encode("utf-8")).hexdigest()
        return self.INTEGRITY_DIR / f"{vault_hash}.json"

    def _compute_file_hmac(self) -> str:
        """Compute HMAC-SHA256 of the vault file."""
        digest = hmac.new(self.key, digestmod=hashlib.sha256)
        with open(self.vault_path, "rb") as vault_file:
            while chunk := vault_file.read(8192):
                digest.update(chunk)
        return digest.hexdigest()
