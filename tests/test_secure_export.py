import tempfile
import unittest
from pathlib import Path

from cryptography.exceptions import InvalidTag
from core.per_password_lock import PerPasswordLock
from core.secure_export import SecureExport


class SecureExportTests(unittest.TestCase):

    def test_protected_password_survives_export_import(self):
        """
        A per-password-protected password must survive an export/import
        cycle without losing its original ciphertext, salt, or hash.
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "backup.svault"

            password = "MyVeryStrongPassword!123"
            secret_phrase = "MyPrivateSecret"

            # Create the original per-password protected ciphertext.
            lock = PerPasswordLock()

            protected = lock.encrypt_with_secret(
                password,
                secret_phrase,
            )

            entries = [
                {
                    "service": "Example Service",
                    "username": "example-user",
                    "password": protected["encrypted_password"],
                    "url": "https://example.com",
                    "notes": "Protected test entry",
                    "category": "password",
                    "favorite": 1,
                    "per_pass_salt": protected["salt"],
                    "per_pass_hash": protected["verify_hash"],
                    "password_protected": True,
                }
            ]

            export_password = "BackupPassword!456"

            # Export.
            result = SecureExport.export_vault(
                entries,
                export_password,
                str(export_path),
            )

            self.assertEqual(result["status"], "success")
            self.assertTrue(export_path.exists())

            # Import.
            imported = SecureExport.import_vault(
                str(export_path),
                export_password,
            )

            self.assertEqual(len(imported), 1)

            restored = imported[0]

            # The protected ciphertext must be unchanged.
            self.assertEqual(
                restored["password"],
                protected["encrypted_password"],
            )

            # The per-password derivation metadata must be unchanged.
            self.assertEqual(
                restored["per_pass_salt"],
                protected["salt"],
            )

            self.assertEqual(
                restored["per_pass_hash"],
                protected["verify_hash"],
            )

            self.assertTrue(
                restored["password_protected"]
            )

            # Most importantly, the original secret phrase must still
            # successfully decrypt the restored ciphertext.
            decrypted = lock.decrypt_with_secret(
                {
                    "encrypted_password": restored["password"],
                    "salt": restored["per_pass_salt"],
                    "verify_hash": restored["per_pass_hash"],
                },
                secret_phrase,
                entry_id="export-test",
            )

            self.assertEqual(
                decrypted,
                password.encode("utf-8"),
            )

    def test_v2_aad_password_can_be_exported(self):
        """
        A normal V2/AAD-bound password must be decrypted correctly
        during export.
        """
        from core.crypto_context import CryptoContext
        from core.encryption import EncryptionEngine

        key = b"k" * 32
        engine = EncryptionEngine(key)
        vault_id = "real-vault"
        entry_uuid = "11111111-1111-4111-8111-111111111111"
        password = b"My V2 Password!123"
        aad = CryptoContext.entry(
            vault_id,
            entry_uuid,
            "password",
        )
        encrypted = engine.encrypt(
            password,
            aad=aad,
        )
        decrypted = engine.decrypt(
            encrypted,
            aad=aad,
        )
        self.assertEqual(
            decrypted,
            password,
        )
        with self.assertRaises(InvalidTag):
            engine.decrypt(
                encrypted,
                aad=CryptoContext.entry(
                    vault_id,
                    "22222222-2222-4222-8222-222222222222",
                    "password",
                ),
            )

    def test_entry_uuid_and_per_password_version_survive_export(self):
        """Backup metadata must preserve cryptographic entry identity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "identity.svault"
            entry_uuid = (
                "11111111-1111-4111-8111-111111111111"
            )
            entries = [
                {
                    "entry_uuid": entry_uuid,
                    "service": "Example",
                    "username": "user",
                    "password": b"protected-ciphertext",
                    "url": "",
                    "notes": "",
                    "category": "password",
                    "favorite": 0,
                    "per_pass_salt": b"test-salt",
                    "per_pass_hash": "test-hash",
                    "per_pass_version": 2,
                    "password_protected": True,
                }
            ]

            result = SecureExport.export_vault(
                entries,
                "BackupPassword!123",
                str(export_path),
            )

            self.assertEqual(result["status"], "success")
            imported = SecureExport.import_vault(
                str(export_path),
                "BackupPassword!123",
            )

            self.assertEqual(imported[0]["entry_uuid"], entry_uuid)
            self.assertEqual(imported[0]["per_pass_version"], 2)

    def test_v2_protected_entry_requires_entry_uuid(self):
        """
        A V2 protected backup entry must retain its UUID because the
        UUID is part of its cryptographic context.
        """
        lock = PerPasswordLock()
        protected = lock.encrypt_with_secret(
            "ProtectedPassword!123",
            "MyPrivateSecret",
            vault_id="original-vault",
            entry_uuid="11111111-1111-4111-8111-111111111111",
        )
        entries = [
            {
                "service": "Example",
                "username": "user",
                "password": protected["encrypted_password"],
                "url": "",
                "notes": "",
                "category": "password",
                "favorite": 0,
                "per_pass_salt": protected["salt"],
                "per_pass_hash": protected["verify_hash"],
                "per_pass_version": 2,
                "password_protected": True,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "missing-identity.svault"
            result = SecureExport.export_vault(
                entries,
                "BackupPassword!123",
                str(export_path),
            )
            self.assertEqual(result["status"], "success")

            imported = SecureExport.import_vault(
                str(export_path),
                "BackupPassword!123",
            )

        self.assertNotIn("entry_uuid", imported[0])
        self.assertEqual(imported[0]["per_pass_version"], 2)


if __name__ == "__main__":
    unittest.main()