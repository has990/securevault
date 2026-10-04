import tempfile
import unittest
from pathlib import Path

from core.database import VaultDatabase
from core.totp_manager import TOTPManager, validate_totp_code


class TOTPManagerTests(unittest.TestCase):

    def test_verify_code_accepts_explicit_timestamp(self):
        secret = "JBSWY3DPEHPK3PXP"
        manager = TOTPManager(secret, digits=6, interval=30, algorithm="sha1")

        code = manager.generate_code(timestamp=1700000000)

        self.assertTrue(
            manager.verify_code(code, timestamp=1700000000)
        )
        self.assertTrue(
            validate_totp_code(
                secret,
                code,
                timestamp=1700000000,
            )
        )

    def test_verify_code_rejects_wrong_code(self):
        secret = "JBSWY3DPEHPK3PXP"
        manager = TOTPManager(secret, digits=6, interval=30, algorithm="sha1")

        self.assertFalse(
            manager.verify_code(
                "000000",
                timestamp=1700000000,
            )
        )

    def test_totp_entry_is_saved_with_correct_fields(self):
        """Ensure TOTP database values are stored in the correct columns."""

        with tempfile.TemporaryDirectory() as temp_dir:
            original_db_path = VaultDatabase.DB_PATH

            try:
                VaultDatabase.DB_PATH = Path(temp_dir) / "test_vault.db"

                db = VaultDatabase()

                vault_id = "test-vault-123"
                label = b"encrypted-label"
                secret = b"encrypted-secret"
                issuer = b"encrypted-issuer"

                db.add_totp_entry(
                    label=label,
                    secret=secret,
                    vault_id=vault_id,
                    issuer=issuer,
                    digits=6,
                    period=30,
                    algorithm="sha1",
                )

                entries = db.get_totp_entries(vault_id)

                self.assertEqual(len(entries), 1)

                entry = entries[0]

                self.assertEqual(entry["label"], label)
                self.assertEqual(entry["secret"], secret)
                self.assertEqual(entry["issuer"], issuer)
                self.assertEqual(entry["digits"], 6)
                self.assertEqual(entry["period"], 30)
                self.assertEqual(entry["algorithm"], "sha1")
                self.assertEqual(entry["vault_id"], vault_id)

                db.close()

            finally:
                VaultDatabase.DB_PATH = original_db_path


if __name__ == "__main__":
    unittest.main()