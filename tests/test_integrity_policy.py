import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from core.database import VaultDatabase
from core.tamper_detection import TamperDetection
from gui.app import SecureVaultApp


class IntegrityPolicyTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "vault.db"
        self.integrity_dir = Path(self.temp_dir.name) / "integrity"

        self.original_db_path = VaultDatabase.DB_PATH
        VaultDatabase.DB_PATH = self.db_path
        self.db = VaultDatabase()

        self.original_integrity_dir = TamperDetection.INTEGRITY_DIR
        TamperDetection.INTEGRITY_DIR = self.integrity_dir

    def tearDown(self):
        self.db.close()
        VaultDatabase.DB_PATH = self.original_db_path
        TamperDetection.INTEGRITY_DIR = self.original_integrity_dir
        self.temp_dir.cleanup()

    def _build_fake_app(self):
        """Build only the attributes needed by the policy method."""
        app = object.__new__(SecureVaultApp)
        app.current_vault_id = "test-vault"
        app._vault_key = b"k" * 32
        app.db = SimpleNamespace(DB_PATH=self.db_path)
        app.security_events = []

        class FakeIntruderLog:

            def __init__(self, events):
                self.events = events

            def record_security_event(self, event_type, **details):
                self.events.append({
                    "event_type": event_type,
                    "details": details,
                })

        app.intruder_log = FakeIntruderLog(app.security_events)
        app.tamper_warnings = []

        def fake_show_tamper_warning(warnings):
            app.tamper_warnings.extend(warnings)

        app._show_tamper_warning = fake_show_tamper_warning
        return app

    def _detector(self, app):
        return TamperDetection(
            str(self.db_path),
            app._vault_key,
            app.current_vault_id,
        )

    def test_new_vault_creates_missing_baseline(self):
        app = self._build_fake_app()

        result = app._update_tamper_baseline(is_new_vault=True)

        self.assertTrue(result)
        verification = self._detector(app).verify_integrity()
        self.assertTrue(verification["baseline_exists"])
        self.assertTrue(verification["intact"])

    def test_existing_vault_with_missing_baseline_is_blocked(self):
        app = self._build_fake_app()

        result = app._update_tamper_baseline(is_new_vault=False)

        self.assertFalse(result)
        self.assertTrue(any(
            event["event_type"] == "integrity_baseline_missing"
            for event in app.security_events
        ))
        self.assertTrue(any(
            "Integrity baseline is missing" in warning
            for warning in app.tamper_warnings
        ))

        verification = self._detector(app).verify_integrity()
        self.assertFalse(verification["baseline_exists"])

    def test_existing_valid_baseline_is_accepted(self):
        app = self._build_fake_app()
        detector = self._detector(app)
        detector.create_integrity_record()

        result = app._update_tamper_baseline(is_new_vault=False)

        self.assertTrue(result)
        verification = detector.verify_integrity()
        self.assertTrue(verification["baseline_exists"])
        self.assertTrue(verification["intact"])

    def test_existing_tampered_vault_is_blocked(self):
        app = self._build_fake_app()
        detector = self._detector(app)
        detector.create_integrity_record()

        integrity_file = detector._vault_integrity_file()
        original_baseline = integrity_file.read_text(encoding="utf-8")

        self.db.conn.execute(
            """
            INSERT INTO entries
                (entry_uuid, service, username, password, vault_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "11111111-1111-4111-8111-111111111111",
                b"service",
                b"username",
                b"password",
                "test-vault",
            ),
        )
        self.db.conn.commit()

        result = app._update_tamper_baseline(is_new_vault=False)

        self.assertFalse(result)
        self.assertEqual(
            integrity_file.read_text(encoding="utf-8"),
            original_baseline,
        )
        self.assertTrue(any(
            event["event_type"] == "tamper_detected"
            for event in app.security_events
        ))


if __name__ == "__main__":
    unittest.main()
