import unittest

from core.crypto_context import CryptoContext


class CryptoContextTests(unittest.TestCase):

    def test_same_context_produces_same_aad(self):
        aad1 = CryptoContext.entry(
            "real-vault",
            "entry-123",
            "password",
        )

        aad2 = CryptoContext.entry(
            "real-vault",
            "entry-123",
            "password",
        )

        self.assertEqual(aad1, aad2)

    def test_different_vault_produces_different_aad(self):
        real_aad = CryptoContext.entry(
            "real-vault",
            "entry-123",
            "password",
        )

        decoy_aad = CryptoContext.entry(
            "decoy-vault",
            "entry-123",
            "password",
        )

        self.assertNotEqual(real_aad, decoy_aad)

    def test_different_entry_produces_different_aad(self):
        aad1 = CryptoContext.entry(
            "real-vault",
            "entry-1",
            "password",
        )

        aad2 = CryptoContext.entry(
            "real-vault",
            "entry-2",
            "password",
        )

        self.assertNotEqual(aad1, aad2)

    def test_different_field_produces_different_aad(self):
        password_aad = CryptoContext.entry(
            "real-vault",
            "entry-1",
            "password",
        )

        username_aad = CryptoContext.entry(
            "real-vault",
            "entry-1",
            "username",
        )

        self.assertNotEqual(password_aad, username_aad)

    def test_per_password_context_does_not_depend_on_vault(self):
        """Per-password AAD should depend on the entry UUID, not vault ID."""
        aad1 = CryptoContext.per_password(
            "11111111-1111-4111-8111-111111111111"
        )
        aad2 = CryptoContext.per_password(
            "11111111-1111-4111-8111-111111111111"
        )

        self.assertEqual(aad1, aad2)

    def test_per_password_context_changes_with_entry_uuid(self):
        """Changing the entry UUID must change the per-password AAD."""
        aad1 = CryptoContext.per_password(
            "11111111-1111-4111-8111-111111111111"
        )
        aad2 = CryptoContext.per_password(
            "22222222-2222-4222-8222-222222222222"
        )

        self.assertNotEqual(aad1, aad2)

    def test_context_is_bytes(self):
        aad = CryptoContext.entry(
            "real-vault",
            "entry-1",
            "password",
        )

        self.assertIsInstance(aad, bytes)

    def test_invalid_context_is_rejected(self):
        with self.assertRaises(ValueError):
            CryptoContext.entry(
                "",
                "entry-1",
                "password",
            )

        with self.assertRaises(ValueError):
            CryptoContext.entry(
                "real-vault",
                "",
                "password",
            )

        with self.assertRaises(ValueError):
            CryptoContext.entry(
                "real-vault",
                "entry-1",
                "",
            )


if __name__ == "__main__":
    unittest.main()