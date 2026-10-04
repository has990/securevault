import unittest

from cryptography.exceptions import InvalidTag

from core.per_password_lock import PerPasswordLock


class PerPasswordLockTests(unittest.TestCase):

    def setUp(self):
        self.lock = PerPasswordLock()
        self.password = "MyStrongPassword!123"
        self.secret_phrase = "MyPrivateSecret"
        self.vault_id = "real-vault"
        self.entry_uuid = (
            "11111111-1111-4111-8111-111111111111"
        )

    def test_v2_protected_password_round_trip(self):
        """A V2 protected password must decrypt correctly."""
        protected = self.lock.encrypt_with_secret(
            self.password,
            self.secret_phrase,
            vault_id=self.vault_id,
            entry_uuid=self.entry_uuid,
        )

        self.assertEqual(
            protected["encryption_version"],
            2,
        )

        decrypted = self.lock.decrypt_with_secret(
            protected,
            self.secret_phrase,
            vault_id=self.vault_id,
            entry_uuid=self.entry_uuid,
        )

        self.assertEqual(decrypted, self.password.encode())

    def test_v2_wrong_entry_uuid_fails(self):
        protected = self.lock.encrypt_with_secret(
            self.password,
            self.secret_phrase,
            vault_id=self.vault_id,
            entry_uuid=self.entry_uuid,
        )

        with self.assertRaises(InvalidTag):
            self.lock.decrypt_with_secret(
                protected,
                self.secret_phrase,
                vault_id=self.vault_id,
                entry_uuid=(
                    "22222222-2222-4222-8222-222222222222"
                ),
            )

    def test_v2_protected_password_survives_vault_restore(self):
        """
        A V2 protected password should remain decryptable when the
        entry is restored into another vault, provided the entry UUID
        and secret phrase remain unchanged.
        """
        protected = self.lock.encrypt_with_secret(
            self.password,
            self.secret_phrase,
            vault_id=self.vault_id,
            entry_uuid=self.entry_uuid,
        )

        restored = self.lock.decrypt_with_secret(
            protected,
            self.secret_phrase,
            entry_id=self.entry_uuid,
            vault_id="restored-vault",
            entry_uuid=self.entry_uuid,
        )

        self.assertEqual(
            restored,
            self.password.encode("utf-8"),
        )

    def test_v2_wrong_secret_fails(self):
        protected = self.lock.encrypt_with_secret(
            self.password,
            self.secret_phrase,
            vault_id=self.vault_id,
            entry_uuid=self.entry_uuid,
        )

        with self.assertRaises(ValueError):
            self.lock.decrypt_with_secret(
                protected,
                "DifferentSecret",
                vault_id=self.vault_id,
                entry_uuid=self.entry_uuid,
            )

    def test_v1_legacy_ciphertext_still_works(self):
        protected = self.lock.encrypt_with_secret(
            self.password,
            self.secret_phrase,
        )

        self.assertEqual(protected["version"], 1)
        decrypted = self.lock.decrypt_with_secret(
            protected,
            self.secret_phrase,
        )

        self.assertEqual(decrypted, self.password.encode())

    def test_v2_requires_context(self):
        protected = self.lock.encrypt_with_secret(
            self.password,
            self.secret_phrase,
            vault_id=self.vault_id,
            entry_uuid=self.entry_uuid,
        )

        with self.assertRaises(ValueError):
            self.lock.decrypt_with_secret(
                protected,
                self.secret_phrase,
            )


if __name__ == "__main__":
    unittest.main()
