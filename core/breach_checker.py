"""
Breach Checker — Check passwords against HaveIBeenPwned database.

Uses the k-Anonymity model:
- Only the first 5 characters of the SHA-1 hash are sent.
- The full password NEVER leaves your machine.
- The API returns possible hash matches; matching is performed locally.
"""

import hashlib
import ssl
import urllib.request


class BreachChecker:
    """Check if passwords appear in known data breaches."""

    API_URL = "https://api.pwnedpasswords.com/range/"

    @staticmethod
    def check_password(password: str) -> dict:
        """
        Check a password against the HaveIBeenPwned database.

        Returns one of three meaningful states:

            BREACHED:
                {
                    "breached": True,
                    "count": int,
                    "safe": False,
                    "status": "breached"
                }

            SAFE:
                {
                    "breached": False,
                    "count": 0,
                    "safe": True,
                    "status": "safe"
                }

            UNKNOWN:
                {
                    "breached": False,
                    "count": 0,
                    "safe": None,
                    "status": "unknown",
                    "error": "..."
                }

        "unknown" is used when the service cannot be reached or
        the response cannot be processed reliably.
        """

        if not isinstance(password, str):
            raise TypeError("password must be a string")

        sha1_hash = hashlib.sha1(
            password.encode("utf-8")
        ).hexdigest().upper()

        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        try:
            ctx = ssl.create_default_context()

            request = urllib.request.Request(
                f"{BreachChecker.API_URL}{prefix}",
                headers={
                    "User-Agent": "SecureVault-PasswordManager"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=5,
                context=ctx,
            ) as response:
                data = response.read().decode("utf-8")

        except Exception as exc:
            return {
                "breached": False,
                "count": 0,
                "safe": None,
                "status": "unknown",
                "error": f"Could not reach API: {exc}",
            }

        try:
            for line in data.splitlines():
                if ":" not in line:
                    continue

                hash_suffix, count = line.split(":", 1)

                if hash_suffix.strip().upper() == suffix:
                    return {
                        "breached": True,
                        "count": int(count.strip()),
                        "safe": False,
                        "status": "breached",
                    }

        except (ValueError, TypeError) as exc:
            return {
                "breached": False,
                "count": 0,
                "safe": None,
                "status": "unknown",
                "error": f"Invalid API response: {exc}",
            }

        return {
            "breached": False,
            "count": 0,
            "safe": True,
            "status": "safe",
        }

    @staticmethod
    def check_multiple(passwords: list) -> list:
        """Check multiple passwords and return their results."""

        return [
            BreachChecker.check_password(password)
            for password in passwords
        ]