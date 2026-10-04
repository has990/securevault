import json
import tempfile
import unittest
from pathlib import Path

from core.intruder_log import IntruderLog


class AuditLogTests(unittest.TestCase):

    def test_records_structured_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            original_path = IntruderLog.LOG_PATH

            try:
                IntruderLog.LOG_PATH = log_path

                log = IntruderLog()

                log.record_failed_attempt()
                log.record_successful_login(
                    vault_id="vault-1",
                    is_decoy=False,
                )
                log.record_vault_access(
                    "open_vault",
                    vault_id="vault-1",
                )

                # Audit records are encrypted at rest, so read them
                # through the log store instead of parsing the raw file.
                entries = log.get_recent_events(
                    within_seconds=3600
                )

                self.assertEqual(len(entries), 3)

                self.assertEqual(
                    entries[0]["type"],
                    "failed_login",
                )

                self.assertEqual(
                    entries[1]["type"],
                    "successful_login",
                )

                self.assertEqual(
                    entries[1]["details"]["vault_id"],
                    "vault-1",
                )

                self.assertEqual(
                    entries[2]["type"],
                    "vault_access",
                )

                # Verify that the file on disk is not plaintext JSON.
                raw_lines = [
                    line
                    for line in log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if line.strip()
                ]

                self.assertEqual(len(raw_lines), 3)

                for line in raw_lines:
                    with self.assertRaises(json.JSONDecodeError):
                        json.loads(line)

            finally:
                IntruderLog.LOG_PATH = original_path


if __name__ == "__main__":
    unittest.main()