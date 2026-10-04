import tempfile
import unittest
import sqlite3
from pathlib import Path

from core.tamper_detection import TamperDetection


class TamperDetectionTests(unittest.TestCase):

    def test_integrity_record_detects_file_modification(self):
        """A modified vault file must fail integrity verification."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            vault_path = tmp_path / "vault.db"
            integrity_path = tmp_path / "integrity.json"

            key = b"k" * 32

            vault_path.write_bytes(b"original vault contents")

            original_integrity_path = TamperDetection.INTEGRITY_FILE

            try:
                TamperDetection.INTEGRITY_FILE = integrity_path

                detector = TamperDetection(
                    str(vault_path),
                    key,
                )

                # Create the trusted baseline.
                detector.create_integrity_record()

                # Baseline must verify successfully.
                result = detector.verify_integrity()

                self.assertTrue(result["intact"])
                self.assertTrue(result["details"]["hmac_match"])
                self.assertTrue(result["details"]["size_match"])

                # Simulate external modification.
                vault_path.write_bytes(
                    b"modified vault contents"
                )

                result = detector.verify_integrity()

                self.assertFalse(result["intact"])
                self.assertFalse(result["details"]["hmac_match"])

            finally:
                TamperDetection.INTEGRITY_FILE = original_integrity_path

    def test_wrong_key_fails_integrity_verification(self):
        """A different key must not validate an existing integrity record."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            vault_path = tmp_path / "vault.db"
            integrity_path = tmp_path / "integrity.json"

            correct_key = b"a" * 32
            wrong_key = b"b" * 32

            vault_path.write_bytes(
                b"original vault contents"
            )

            original_integrity_path = TamperDetection.INTEGRITY_FILE

            try:
                TamperDetection.INTEGRITY_FILE = integrity_path

                detector = TamperDetection(
                    str(vault_path),
                    correct_key,
                )

                detector.create_integrity_record()

                # The correct key must validate.
                result = detector.verify_integrity()

                self.assertTrue(result["intact"])

                # A different key must fail the HMAC check.
                wrong_detector = TamperDetection(
                    str(vault_path),
                    wrong_key,
                )

                result = wrong_detector.verify_integrity()

                self.assertFalse(result["intact"])
                self.assertFalse(result["details"]["hmac_match"])

            finally:
                TamperDetection.INTEGRITY_FILE = original_integrity_path

    def test_missing_integrity_baseline_is_reported(self):
        """No baseline must be distinguishable from an intact vault."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            vault_path = tmp_path / "vault.db"
            integrity_path = tmp_path / "integrity.json"

            vault_path.write_bytes(
                b"vault contents"
            )

            original_integrity_path = TamperDetection.INTEGRITY_FILE

            try:
                TamperDetection.INTEGRITY_FILE = integrity_path

                detector = TamperDetection(
                    str(vault_path),
                    b"k" * 32,
                )

                result = detector.verify_integrity()

                self.assertTrue(result["intact"])
                self.assertFalse(result["baseline_exists"])
                self.assertFalse(
                    result["details"]["baseline_exists"]
                )
                self.assertEqual(
                    result["warnings"],
                    ["No integrity baseline found"],
                )

            finally:
                TamperDetection.INTEGRITY_FILE = original_integrity_path

    def test_changes_to_another_vault_do_not_trigger_tamper(self):
        """Changes to the decoy vault must not invalidate the real vault."""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            database_path = tmp_path / "vault.db"
            real_key = b"r" * 32
            real_vault_id = "real-vault"
            decoy_vault_id = "decoy-vault"

            conn = sqlite3.connect(database_path)
            try:
                conn.executescript(
                    """
                    CREATE TABLE vault_credentials (
                        id INTEGER PRIMARY KEY,
                        salt BLOB,
                        verify_hash TEXT,
                        vault_id TEXT
                    );
                    CREATE TABLE entries (
                        id INTEGER PRIMARY KEY,
                        service BLOB,
                        username BLOB,
                        password BLOB,
                        url BLOB,
                        notes BLOB,
                        category TEXT,
                        favorite INTEGER,
                        vault_id TEXT,
                        per_pass_salt BLOB,
                        per_pass_hash BLOB,
                        created_at TEXT,
                        updated_at TEXT
                    );
                    CREATE TABLE totp_entries (
                        id INTEGER PRIMARY KEY,
                        label BLOB,
                        secret BLOB,
                        issuer BLOB,
                        digits INTEGER,
                        period INTEGER,
                        algorithm TEXT,
                        vault_id TEXT,
                        created_at TEXT
                    );
                    CREATE TABLE otp_settings (
                        id INTEGER PRIMARY KEY,
                        vault_id TEXT,
                        enabled INTEGER,
                        secret TEXT,
                        issuer TEXT,
                        digits INTEGER,
                        interval INTEGER,
                        algorithm TEXT,
                        created_at TEXT
                    );
                    """
                )
                conn.executemany(
                    "INSERT INTO vault_credentials VALUES (?, ?, ?, ?)",
                    [
                        (1, b"real-salt", "real-hash", real_vault_id),
                        (2, b"decoy-salt", "decoy-hash", decoy_vault_id),
                    ],
                )
                conn.execute(
                    "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (1, b"real", b"user", b"secret", None, None, "password", 0,
                     real_vault_id, None, None, "", ""),
                )
                conn.execute(
                    "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (2, b"decoy", b"user", b"secret", None, None, "password", 0,
                     decoy_vault_id, None, None, "", ""),
                )
                conn.execute(
                    "INSERT INTO totp_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (1, b"real", b"secret", None, 6, 30, "sha1", real_vault_id, ""),
                )
                conn.execute(
                    "INSERT INTO totp_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (2, b"decoy", b"secret", None, 6, 30, "sha1", decoy_vault_id, ""),
                )
                conn.execute(
                    "INSERT INTO otp_settings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (1, real_vault_id, 1, "real", "issuer", 6, 30, "sha1", ""),
                )
                conn.execute(
                    "INSERT INTO otp_settings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (2, decoy_vault_id, 1, "decoy", "issuer", 6, 30, "sha1", ""),
                )
                conn.commit()
            finally:
                conn.close()

            original_integrity_dir = TamperDetection.INTEGRITY_DIR
            try:
                TamperDetection.INTEGRITY_DIR = tmp_path / "integrity"
                detector = TamperDetection(
                    str(database_path),
                    real_key,
                    real_vault_id,
                )
                detector.create_integrity_record()

                conn = sqlite3.connect(database_path)
                try:
                    conn.execute(
                        "UPDATE entries SET password = ? WHERE vault_id = ?",
                        (b"changed", decoy_vault_id),
                    )
                    conn.execute(
                        "UPDATE totp_entries SET secret = ? WHERE vault_id = ?",
                        (b"changed", decoy_vault_id),
                    )
                    conn.execute(
                        "UPDATE otp_settings SET secret = ? WHERE vault_id = ?",
                        ("changed", decoy_vault_id),
                    )
                    conn.commit()
                finally:
                    conn.close()

                result = detector.verify_integrity()
                self.assertTrue(result["intact"])
            finally:
                TamperDetection.INTEGRITY_DIR = original_integrity_dir


if __name__ == "__main__":
    unittest.main()