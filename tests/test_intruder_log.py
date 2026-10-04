import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.intruder_log import IntruderLog


class IntruderLogTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "audit.log"

        self.original_log_path = IntruderLog.LOG_PATH
        IntruderLog.LOG_PATH = self.log_path

    def tearDown(self):
        IntruderLog.LOG_PATH = self.original_log_path
        self.temp_dir.cleanup()

    def test_nine_failed_attempts_do_not_lock_out(self):
        log = IntruderLog()

        base_time = 1_000_000.0

        with patch("core.intruder_log.time.time", return_value=base_time):
            for _ in range(9):
                log.record_failed_attempt()

            locked, remaining = log.is_locked_out()

        self.assertFalse(locked)
        self.assertEqual(remaining, 0)

    def test_ten_failed_attempts_trigger_lockout(self):
        log = IntruderLog()

        base_time = 1_000_000.0

        with patch("core.intruder_log.time.time", return_value=base_time):
            for _ in range(10):
                log.record_failed_attempt()

            locked, remaining = log.is_locked_out()

        self.assertTrue(locked)
        self.assertGreater(remaining, 0)
        self.assertLessEqual(
            remaining,
            IntruderLog.LOCKOUT_SECONDS,
        )

    def test_lockout_expires_after_five_minutes(self):
        log = IntruderLog()

        base_time = 1_000_000.0

        with patch("core.intruder_log.time.time", return_value=base_time):
            for _ in range(10):
                log.record_failed_attempt()

        with patch(
            "core.intruder_log.time.time",
            return_value=base_time + IntruderLog.LOCKOUT_SECONDS + 1,
        ):
            locked, remaining = log.is_locked_out()

        self.assertFalse(locked)
        self.assertEqual(remaining, 0)


if __name__ == "__main__":
    unittest.main()