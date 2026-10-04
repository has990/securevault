import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.database import VaultDatabase
from core.duress_handler import DuressHandler


class DuressHandlerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "vault.db"

        self.original_db_path = VaultDatabase.DB_PATH
        VaultDatabase.DB_PATH = self.db_path

        self.db = VaultDatabase()

    def tearDown(self):
        self.db.close()
        VaultDatabase.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_duress_wipes_real_secret_data(self):
        real_vault_id = "real-vault"
        decoy_vault_id = "decoy-vault"

        # Create the two vault credential records.
        self.db.conn.execute(
            """
            INSERT INTO vault_credentials
                (salt, verify_hash, vault_id)
            VALUES (?, ?, ?)
            """,
            (b"real-salt", "real-hash", real_vault_id),
        )

        self.db.conn.execute(
            """
            INSERT INTO vault_credentials
                (salt, verify_hash, vault_id)
            VALUES (?, ?, ?)
            """,
            (b"decoy-salt", "decoy-hash", decoy_vault_id),
        )

        # Password entries.
        self.db.conn.execute(
            """
            INSERT INTO entries
                (vault_id, service, username, password)
            VALUES (?, ?, ?, ?)
            """,
            (
                real_vault_id,
                b"real-service",
                b"real-user",
                b"real-password",
            ),
        )

        self.db.conn.execute(
            """
            INSERT INTO entries
                (vault_id, service, username, password)
            VALUES (?, ?, ?, ?)
            """,
            (
                decoy_vault_id,
                b"decoy-service",
                b"decoy-user",
                b"decoy-password",
            ),
        )

        # TOTP entries.
        self.db.conn.execute(
            """
            INSERT INTO totp_entries
                (label, secret, issuer, digits, period, algorithm, vault_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                b"real-label",
                b"real-secret",
                b"real-issuer",
                6,
                30,
                "sha1",
                real_vault_id,
            ),
        )

        self.db.conn.execute(
            """
            INSERT INTO totp_entries
                (label, secret, issuer, digits, period, algorithm, vault_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                b"decoy-label",
                b"decoy-secret",
                b"decoy-issuer",
                6,
                30,
                "sha1",
                decoy_vault_id,
            ),
        )

        # OTP settings.
        self.db.conn.execute(
            """
            INSERT INTO otp_settings
                (vault_id, enabled, secret, issuer, digits, interval, algorithm)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                real_vault_id,
                1,
                "real-otp-secret",
                "Real",
                6,
                30,
                "sha1",
            ),
        )

        self.db.conn.execute(
            """
            INSERT INTO otp_settings
                (vault_id, enabled, secret, issuer, digits, interval, algorithm)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decoy_vault_id,
                1,
                "decoy-otp-secret",
                "Decoy",
                6,
                30,
                "sha1",
            ),
        )

        self.db.conn.commit()

        handler = DuressHandler(self.db)

        # Execute the real-vault wipe.
        self.assertTrue(handler._wipe_real_vault())

        # Real password entries must be gone.
        real_entries = self.db.conn.execute(
            "SELECT COUNT(*) FROM entries WHERE vault_id = ?",
            (real_vault_id,),
        ).fetchone()[0]

        self.assertEqual(real_entries, 0)

        # Real TOTP entries must be gone.
        real_totp = self.db.conn.execute(
            "SELECT COUNT(*) FROM totp_entries WHERE vault_id = ?",
            (real_vault_id,),
        ).fetchone()[0]

        self.assertEqual(real_totp, 0)

        # Real OTP settings must be gone.
        real_otp = self.db.conn.execute(
            "SELECT COUNT(*) FROM otp_settings WHERE vault_id = ?",
            (real_vault_id,),
        ).fetchone()[0]

        self.assertEqual(real_otp, 0)

        # Decoy password entries must survive.
        decoy_entries = self.db.conn.execute(
            "SELECT COUNT(*) FROM entries WHERE vault_id = ?",
            (decoy_vault_id,),
        ).fetchone()[0]

        self.assertEqual(decoy_entries, 1)

        # Decoy TOTP entries must survive.
        decoy_totp = self.db.conn.execute(
            "SELECT COUNT(*) FROM totp_entries WHERE vault_id = ?",
            (decoy_vault_id,),
        ).fetchone()[0]

        self.assertEqual(decoy_totp, 1)

        # Decoy OTP settings must survive.
        decoy_otp = self.db.conn.execute(
            "SELECT COUNT(*) FROM otp_settings WHERE vault_id = ?",
            (decoy_vault_id,),
        ).fetchone()[0]

        self.assertEqual(decoy_otp, 1)


if __name__ == "__main__":
    unittest.main()