import hashlib
import unittest
from unittest.mock import MagicMock, patch

from core.breach_checker import BreachChecker


class BreachCheckerTests(unittest.TestCase):

    def _mock_response(self, text: str):
        """Create a fake urllib response context manager."""

        response = MagicMock()
        response.read.return_value = text.encode("utf-8")

        context_manager = MagicMock()
        context_manager.__enter__.return_value = response
        context_manager.__exit__.return_value = False

        return context_manager

    def test_breached_password_is_detected(self):
        """A matching hash suffix must be reported as breached."""

        password = "TestPassword123!"

        full_hash = hashlib.sha1(
            password.encode("utf-8")
        ).hexdigest().upper()

        prefix = full_hash[:5]
        suffix = full_hash[5:]

        api_response = (
            f"{suffix}:42\n"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:1\n"
        )

        with patch(
            "core.breach_checker.urllib.request.urlopen",
            return_value=self._mock_response(api_response),
        ) as mock_urlopen:

            result = BreachChecker.check_password(password)

        self.assertTrue(result["breached"])
        self.assertFalse(result["safe"])
        self.assertEqual(result["status"], "breached")
        self.assertEqual(result["count"], 42)

        # Verify that only the five-character hash prefix
        # appears in the requested URL.
        requested_url = mock_urlopen.call_args.args[0].full_url

        self.assertTrue(
            requested_url.endswith(prefix)
        )

        self.assertNotIn(
            password,
            requested_url,
        )

    def test_password_not_found_is_reported_safe(self):
        """A valid API response with no matching suffix is safe."""

        password = "DefinitelyUnusedTestPassword987!"

        full_hash = hashlib.sha1(
            password.encode("utf-8")
        ).hexdigest().upper()

        suffix = full_hash[5:]

        api_response = (
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:5\n"
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB:12\n"
        )

        # Make sure our fake response does not accidentally contain
        # the password's real suffix.
        self.assertNotIn(
            suffix,
            api_response,
        )

        with patch(
            "core.breach_checker.urllib.request.urlopen",
            return_value=self._mock_response(api_response),
        ):

            result = BreachChecker.check_password(password)

        self.assertFalse(result["breached"])
        self.assertTrue(result["safe"])
        self.assertEqual(result["status"], "safe")
        self.assertEqual(result["count"], 0)

    def test_network_failure_is_unknown_not_safe(self):
        """An API/network failure must never be reported as safe."""

        password = "NetworkFailureTestPassword!"

        with patch(
            "core.breach_checker.urllib.request.urlopen",
            side_effect=OSError("simulated network failure"),
        ):

            result = BreachChecker.check_password(password)

        self.assertFalse(result["breached"])
        self.assertIsNone(result["safe"])
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["count"], 0)

        self.assertIn(
            "Could not reach API",
            result["error"],
        )


if __name__ == "__main__":
    unittest.main()