import unittest
from unittest.mock import patch

from core.password_health import PasswordHealth


class PasswordHealthTests(unittest.TestCase):

    @patch("core.password_health.PasswordGenerator.check_strength")
    def test_protected_password_is_not_analyzed(self, mock_strength):
        """Protected passwords must not be scored as the placeholder string."""

        mock_strength.return_value = {
            "score": 8,
            "max_score": 8,
            "label": "Very Strong",
            "feedback": [],
        }

        passwords = [
            {
                "service": "Normal Service",
                "password": "StrongPassword!123",
                "password_protected": False,
            },
            {
                "service": "Protected Service",
                "password": "[Secret-Protected]",
                "password_protected": True,
            },
        ]

        result = PasswordHealth.analyze_vault(passwords)

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["analyzable"], 1)
        self.assertEqual(result["protected"], 1)

        self.assertEqual(result["strong"], 1)
        self.assertEqual(result["weak"], 0)
        self.assertEqual(result["reused"], 0)

        protected_entry = result["entries"][1]

        self.assertTrue(protected_entry["protected"])
        self.assertIsNone(protected_entry["reused"])
        self.assertEqual(
            protected_entry["strength"]["label"],
            "Protected",
        )

        # Only the real, unlocked password should have been
        # passed to the strength analyzer.
        mock_strength.assert_called_once_with(
            "StrongPassword!123"
        )

    @patch("core.password_health.PasswordGenerator.check_strength")
    def test_protected_password_is_excluded_from_reuse(self, mock_strength):
        """
        A protected password must not be considered reused based on
        the placeholder value.
        """

        mock_strength.return_value = {
            "score": 8,
            "max_score": 8,
            "label": "Very Strong",
            "feedback": [],
        }

        passwords = [
            {
                "service": "Service A",
                "password": "SamePassword!123",
                "password_protected": False,
            },
            {
                "service": "Service B",
                "password": "SamePassword!123",
                "password_protected": False,
            },
            {
                "service": "Service C",
                "password": "[Secret-Protected]",
                "password_protected": True,
            },
        ]

        result = PasswordHealth.analyze_vault(passwords)

        self.assertEqual(result["total"], 3)
        self.assertEqual(result["analyzable"], 2)
        self.assertEqual(result["protected"], 1)

        # The two real passwords are reused.
        self.assertTrue(result["entries"][0]["reused"])
        self.assertTrue(result["entries"][1]["reused"])

        # The protected entry is not evaluated for reuse.
        self.assertIsNone(
            result["entries"][2]["reused"]
        )

        self.assertEqual(result["reused"], 2)

        # Only the two actual passwords should be analyzed.
        self.assertEqual(
            mock_strength.call_count,
            2,
        )

    @patch("core.password_health.BreachChecker.check_password")
    def test_protected_password_is_not_sent_to_breach_checker(
        self,
        mock_breach_check,
    ):
        """
        Protected passwords must never be sent to the external
        breach-checking service.
        """

        mock_breach_check.return_value = {
            "breached": False,
            "count": 0,
            "safe": True,
            "status": "safe",
        }

        passwords = [
            {
                "service": "Normal Service",
                "password": "NormalPassword!123",
                "password_protected": False,
            },
            {
                "service": "Protected Service",
                "password": "[Secret-Protected]",
                "password_protected": True,
            },
        ]

        results = PasswordHealth.check_breaches(passwords)

        self.assertEqual(len(results), 2)

        # Normal password was checked.
        self.assertEqual(
            results[0]["status"],
            "safe",
        )

        # Protected password was explicitly skipped.
        self.assertEqual(
            results[1]["status"],
            "protected",
        )

        self.assertFalse(results[1]["breached"])
        self.assertEqual(results[1]["breach_count"], 0)

        # Only the real password reached BreachChecker.
        mock_breach_check.assert_called_once_with(
            "NormalPassword!123"
        )


if __name__ == "__main__":
    unittest.main()