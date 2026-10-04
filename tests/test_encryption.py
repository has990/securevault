import unittest

from cryptography.exceptions import InvalidTag

from core.crypto_context import CryptoContext
from core.encryption import EncryptionEngine


class EncryptionTests(unittest.TestCase):

    def setUp(self):
        self.key = b"k" * 32
        self.engine = EncryptionEngine(self.key)

    def test_encrypt_and_decrypt_with_same_aad(self):
        """The same AAD must successfully decrypt the ciphertext."""

        plaintext = b"SecureVault test password"
        aad = b"SecureVault:v1:real-vault:entry-1:password"

        encrypted = self.engine.encrypt(
            plaintext,
            aad=aad,
        )

        decrypted = self.engine.decrypt(
            encrypted,
            aad=aad,
        )

        self.assertEqual(
            decrypted,
            plaintext,
        )

    def test_wrong_aad_fails_decryption(self):
        """Changing AAD must invalidate AES-GCM authentication."""

        plaintext = b"SecureVault secret"

        correct_aad = (
            b"SecureVault:v1:real-vault:entry-1:password"
        )

        wrong_aad = (
            b"SecureVault:v1:real-vault:entry-2:password"
        )

        encrypted = self.engine.encrypt(
            plaintext,
            aad=correct_aad,
        )

        with self.assertRaises(InvalidTag):
            self.engine.decrypt(
                encrypted,
                aad=wrong_aad,
            )

    def test_missing_aad_fails_when_aad_was_used(self):
        """Ciphertext authenticated with AAD must not decrypt without it."""

        plaintext = b"SecureVault secret"

        aad = (
            b"SecureVault:v1:real-vault:entry-1:password"
        )

        encrypted = self.engine.encrypt(
            plaintext,
            aad=aad,
        )

        with self.assertRaises(ValueError):
            self.engine.decrypt(
                encrypted,
            )

    def test_legacy_no_aad_encryption_still_works(self):
        """
        Existing ciphertext produced without AAD must remain
        compatible with the current EncryptionEngine API.
        """

        plaintext = b"Legacy SecureVault data"

        encrypted = self.engine.encrypt(
            plaintext,
        )

        decrypted = self.engine.decrypt(
            encrypted,
        )

        self.assertEqual(
            decrypted,
            plaintext,
        )

    def test_modified_ciphertext_fails(self):
        """Changing ciphertext must fail AES-GCM authentication."""

        plaintext = b"Sensitive SecureVault data"

        encrypted = bytearray(
            self.engine.encrypt(plaintext)
        )

        # Flip one bit in the authenticated ciphertext.
        encrypted[-1] ^= 0x01

        with self.assertRaises(InvalidTag):
            self.engine.decrypt(
                bytes(encrypted)
            )

    def test_different_key_fails(self):
        """A different AES key must not decrypt the ciphertext."""

        plaintext = b"Sensitive SecureVault data"

        encrypted = self.engine.encrypt(
            plaintext,
            aad=b"test-context",
        )

        different_engine = EncryptionEngine(
            b"d" * 32
        )

        with self.assertRaises(InvalidTag):
            different_engine.decrypt(
                encrypted,
                aad=b"test-context",
            )

    def test_aad_ciphertext_contains_v2_marker(self):
        """AAD-enabled ciphertext must identify itself as V2."""
        plaintext = b"SecureVault V2 data"
        aad = b"SecureVault:v2:test-context"
        encrypted = self.engine.encrypt(
            plaintext,
            aad=aad,
        )
        self.assertTrue(
            encrypted.startswith(
                EncryptionEngine.V2_PREFIX
            )
        )

    def test_v2_ciphertext_can_be_decrypted_only_with_aad(self):
        """V2 ciphertext must require its authenticated context."""
        plaintext = b"Sensitive V2 data"
        aad = b"SecureVault:v2:test-context"
        encrypted = self.engine.encrypt(
            plaintext,
            aad=aad,
        )
        with self.assertRaises(ValueError):
            self.engine.decrypt(encrypted)
        decrypted = self.engine.decrypt(
            encrypted,
            aad=aad,
        )
        self.assertEqual(decrypted, plaintext)

    def test_entry_uuid_is_cryptographically_bound_to_password(self):
        """
        A password encrypted for one entry UUID must not decrypt when
        presented as belonging to another entry.
        """
        from core.crypto_context import CryptoContext

        plaintext = b"My SecureVault Password"
        vault_id = "real-vault"
        original_entry_uuid = "11111111-1111-4111-8111-111111111111"
        different_entry_uuid = "22222222-2222-4222-8222-222222222222"
        original_aad = CryptoContext.entry(
            vault_id,
            original_entry_uuid,
            "password",
        )
        different_aad = CryptoContext.entry(
            vault_id,
            different_entry_uuid,
            "password",
        )
        encrypted = self.engine.encrypt(
            plaintext,
            aad=original_aad,
        )

        decrypted = self.engine.decrypt(
            encrypted,
            aad=original_aad,
        )
        self.assertEqual(decrypted, plaintext)

        with self.assertRaises(InvalidTag):
            self.engine.decrypt(
                encrypted,
                aad=different_aad,
            )

    def test_all_entry_fields_are_bound_to_their_context(self):
        """
        Each encrypted entry field must only decrypt with the
        correct vault, entry UUID, and field name.
        """
        vault_id = "real-vault"
        entry_uuid = "11111111-1111-4111-8111-111111111111"
        fields = {
            "service": b"Example Service",
            "username": b"example-user",
            "password": b"ExamplePassword!123",
            "url": b"https://example.com",
            "notes": b"Sensitive notes",
        }
        encrypted_fields = {}

        # Encrypt every field with its own context.
        for field_name, plaintext in fields.items():
            aad = CryptoContext.entry(
                vault_id,
                entry_uuid,
                field_name,
            )
            encrypted_fields[field_name] = self.engine.encrypt(
                plaintext,
                aad=aad,
            )

        # Every field must decrypt with its own context.
        for field_name, plaintext in fields.items():
            aad = CryptoContext.entry(
                vault_id,
                entry_uuid,
                field_name,
            )
            self.assertEqual(
                self.engine.decrypt(
                    encrypted_fields[field_name],
                    aad=aad,
                ),
                plaintext,
            )

        password_ciphertext = encrypted_fields["password"]
        username_aad = CryptoContext.entry(
            vault_id,
            entry_uuid,
            "username",
        )
        wrong_vault_aad = CryptoContext.entry(
            "other-vault",
            entry_uuid,
            "password",
        )
        wrong_uuid_aad = CryptoContext.entry(
            vault_id,
            "22222222-2222-4222-8222-222222222222",
            "password",
        )

        for invalid_aad in (
            username_aad,
            wrong_vault_aad,
            wrong_uuid_aad,
        ):
            with self.assertRaises(InvalidTag):
                self.engine.decrypt(
                    password_ciphertext,
                    aad=invalid_aad,
                )


if __name__ == "__main__":
    unittest.main()