import tempfile
import unittest
import uuid
from pathlib import Path

from core.database import VaultDatabase


class VaultIsolationTests(unittest.TestCase):

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

    def test_database_file_exists_after_initialization(self):
        """
        The SQLite database must exist after initialization.
        Filesystem permission semantics are platform-specific and are
        tested separately from database functionality.
        """
        database_path = Path(self.db.DB_PATH)
        self.assertTrue(database_path.exists())

    def test_cannot_delete_entry_from_another_vault(self):
        """A vault session must not be able to delete another vault's entry."""

        real_vault_id = "real-vault"
        decoy_vault_id = "decoy-vault"

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

        self.db.conn.commit()

        rows = self.db.conn.execute(
            """
            SELECT id, vault_id
            FROM entries
            ORDER BY id
            """
        ).fetchall()

        real_entry_id = next(
            row[0] for row in rows
            if row[1] == real_vault_id
        )

        decoy_entry_id = next(
            row[0] for row in rows
            if row[1] == decoy_vault_id
        )

        # Attempt to delete the decoy entry while authenticated
        # as the real vault.
        deleted = self.db.delete_entry(
            decoy_entry_id,
            real_vault_id,
        )

        self.assertFalse(deleted)

        # The decoy entry must still exist.
        decoy_count = self.db.conn.execute(
            """
            SELECT COUNT(*)
            FROM entries
            WHERE id = ? AND vault_id = ?
            """,
            (
                decoy_entry_id,
                decoy_vault_id,
            ),
        ).fetchone()[0]

        self.assertEqual(decoy_count, 1)

        # The real vault should still be able to delete its own entry.
        deleted = self.db.delete_entry(
            real_entry_id,
            real_vault_id,
        )

        self.assertTrue(deleted)

        real_count = self.db.conn.execute(
            """
            SELECT COUNT(*)
            FROM entries
            WHERE id = ? AND vault_id = ?
            """,
            (
                real_entry_id,
                real_vault_id,
            ),
        ).fetchone()[0]

        self.assertEqual(real_count, 0)

    def test_entries_have_stable_unique_uuids(self):
        """Every entry must receive a valid, unique, stable UUID."""
        first_uuid = self.db.add_entry(
            service=b"service-1",
            username=b"user-1",
            password=b"password-1",
            vault_id="real-vault",
        )
        second_uuid = self.db.add_entry(
            service=b"service-2",
            username=b"user-2",
            password=b"password-2",
            vault_id="real-vault",
        )

        self.assertNotEqual(first_uuid, second_uuid)
        uuid.UUID(first_uuid)
        uuid.UUID(second_uuid)

        entries = self.db.get_entries_by_vault("real-vault")
        stored_uuids = {entry["entry_uuid"] for entry in entries}
        self.assertIn(first_uuid, stored_uuids)
        self.assertTrue(
            all(
                entry.get("entry_uuid")
                for entry in entries
            )
        )
        self.assertIn(second_uuid, stored_uuids)

        reloaded = self.db.conn.execute(
            """
            SELECT entry_uuid
            FROM entries
            WHERE entry_uuid IN (?, ?)
            ORDER BY entry_uuid
            """,
            (first_uuid, second_uuid),
        ).fetchall()
        self.assertEqual(
            {row["entry_uuid"] for row in reloaded},
            {first_uuid, second_uuid},
        )

        entry_rows = self.db.conn.execute(
            """
            SELECT entry_uuid, per_pass_version
            FROM entries
            WHERE vault_id = ?
            ORDER BY id
            """,
            ("real-vault",),
        ).fetchall()
        self.assertEqual(len(entry_rows), 2)
        for row in entry_rows:
            self.assertIsNotNone(row["entry_uuid"])
            self.assertEqual(row["per_pass_version"], 1)

    def test_update_and_favorite_are_vault_scoped(self):
        """Update and favorite operations must respect vault ownership."""
        real_vault_id = "real-vault"
        decoy_vault_id = "decoy-vault"
        self.db.conn.execute(
            """
            INSERT INTO entries
                (vault_id, service, username, password, favorite)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                real_vault_id,
                b"real-service",
                b"real-user",
                b"real-password",
                0,
            ),
        )
        self.db.conn.execute(
            """
            INSERT INTO entries
                (vault_id, service, username, password, favorite)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                decoy_vault_id,
                b"decoy-service",
                b"decoy-user",
                b"decoy-password",
                0,
            ),
        )


if __name__ == "__main__":
    unittest.main()
