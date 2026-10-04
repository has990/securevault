import tempfile
import unittest
import uuid
from pathlib import Path

from core.database import VaultDatabase
from core.per_password_lock import PerPasswordLock


class PerPasswordIntegrationTests(unittest.TestCase):

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

    def test_v2_protected_password_survives_database_round_trip(self):
        """
        Verify the complete V2 protected-password flow:

        encrypt → database → retrieve → decrypt
        """

        vault_id = "real-vault"

        entry_uuid = str(uuid.uuid4())

        password = "MyProtectedPassword!123"
        secret_phrase = "MyPrivateSecret"

        lock = PerPasswordLock()

        protected = lock.encrypt_with_secret(
            password,
            secret_phrase,
            vault_id=vault_id,
            entry_uuid=entry_uuid,
        )

        self.assertEqual(
            protected["encryption_version"],
            2,
        )

        # Store the protected password exactly as the application does.
        returned_uuid = self.db.add_entry(
            service=b"encrypted-service",
            username=b"encrypted-user",
            password=protected["encrypted_password"],
            vault_id=vault_id,
            per_pass_salt=protected["salt"],
            per_pass_hash=protected["verify_hash"],
            entry_uuid=entry_uuid,
            per_pass_version=protected["encryption_version"],
        )

        self.assertEqual(
            returned_uuid,
            entry_uuid,
        )

        # Retrieve the entry from SQLite.
        entries = self.db.get_entries_by_vault(
            vault_id
        )

        self.assertEqual(
            len(entries),
            1,
        )

        stored = entries[0]

        self.assertEqual(
            stored["entry_uuid"],
            entry_uuid,
        )

        self.assertEqual(
            stored["per_pass_version"],
            2,
        )

        # Reconstruct the encrypted-data envelope exactly as the
        # application does during unlocking.
        encrypted_data = {
            "encrypted_password": stored["password"],
            "salt": stored["per_pass_salt"],
            "verify_hash": stored["per_pass_hash"],
            "encryption_version": stored["per_pass_version"],
        }

        decrypted = lock.decrypt_with_secret(
            encrypted_data,
            secret_phrase,
            entry_id=entry_uuid,
            vault_id=vault_id,
            entry_uuid=stored["entry_uuid"],
        )

        self.assertEqual(
            decrypted,
            password.encode("utf-8"),
        )

    def test_v2_protected_password_cannot_be_moved_to_another_entry(self):
        """
        Copying V2 protected ciphertext to another entry context
        must fail authentication.
        """

        vault_id = "real-vault"

        original_uuid = str(uuid.uuid4())
        different_uuid = str(uuid.uuid4())

        password = "ProtectedPassword!123"
        secret_phrase = "MyPrivateSecret"

        lock = PerPasswordLock()

        protected = lock.encrypt_with_secret(
            password,
            secret_phrase,
            vault_id=vault_id,
            entry_uuid=original_uuid,
        )

        encrypted_data = {
            "encrypted_password": protected["encrypted_password"],
            "salt": protected["salt"],
            "verify_hash": protected["verify_hash"],
            "encryption_version": 2,
        }

        # The original context works.
        original = lock.decrypt_with_secret(
            encrypted_data,
            secret_phrase,
            entry_id=original_uuid,
            vault_id=vault_id,
            entry_uuid=original_uuid,
        )

        self.assertEqual(
            original,
            password.encode("utf-8"),
        )

        # A different entry context must fail.
        from cryptography.exceptions import InvalidTag

        with self.assertRaises(InvalidTag):
            lock.decrypt_with_secret(
                encrypted_data,
                secret_phrase,
                entry_id=different_uuid,
                vault_id=vault_id,
                entry_uuid=different_uuid,
            )


if __name__ == "__main__":
    unittest.main()