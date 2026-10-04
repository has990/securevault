"""
Password Health Analyzer
Checks: strength, reuse, age, and breach status of all stored passwords.
"""
import hashlib
from collections import Counter
from core.password_generator import PasswordGenerator
from core.breach_checker import BreachChecker


class PasswordHealth:
    """Analyze the overall health of stored passwords."""

    STRENGTH_LABELS = {
        range(0, 3): ("Weak", "danger"),
        range(3, 5): ("Fair", "warning"),
        range(5, 7): ("Strong", "accent"),
        range(7, 10): ("Very Strong", "success"),
    }

    @staticmethod
    def analyze_vault(decrypted_passwords: list[dict]) -> dict:
        """
        Analyze the overall health of stored passwords.
        Passwords protected by the per-password lock are not decrypted
        for analysis. They are reported as protected rather than having
        the placeholder value analyzed as if it were a real password.
        """
        total = len(decrypted_passwords)
        if total == 0:
            return {
                "overall_score": 100,
                "total": 0,
                "analyzable": 0,
                "protected": 0,
                "weak": 0,
                "reused": 0,
                "breached": 0,
                "strong": 0,
                "entries": [],
            }

        entries = []
        analyzable_passwords = []

        # Analyze passwords that are actually available.
        for item in decrypted_passwords:
            password = item.get("password")
            service = item.get("service", "Unknown")
            password_protected = bool(
                item.get("password_protected", False)
            )

            if password_protected:
                entries.append({
                    "service": service,
                    "protected": True,
                    "reused": False,
                    "strength": {
                        "label": "Protected",
                        "color": "accent",
                    },
                })
                continue

            if not isinstance(password, str):
                continue

            strength = PasswordGenerator.check_strength(password)
            entries.append({
                "service": service,
                "strength": strength,
                "protected": False,
            })
            analyzable_passwords.append(password)

        # Detect reuse
        password_hashes = [
            hashlib.sha256(password.encode()).hexdigest()
            for password in analyzable_passwords
        ]
        hash_counts = Counter(password_hashes)
        reused_hashes = {h for h, c in hash_counts.items() if c > 1}

        analyzable_index = 0
        for entry in entries:
            if entry["protected"]:
                continue
            entry["reused"] = (
                password_hashes[analyzable_index] in reused_hashes
            )
            analyzable_index += 1

        # Protected passwords cannot be evaluated for reuse because
        # their plaintext is intentionally unavailable.
        for entry in entries:
            if entry.get("protected"):
                entry["reused"] = None

        # Count categories
        weak = sum(1 for e in entries if e["strength"]["label"] in ("Weak", "Fair"))
        reused = sum(1 for e in entries if e["reused"])
        strong = sum(1 for e in entries if e["strength"]["label"] in ("Strong", "Very Strong"))
        analyzable = len(analyzable_passwords)
        protected = sum(1 for e in entries if e["protected"])

        # Overall score (0-100)
        score = 100
        if analyzable > 0:
            score -= (weak / analyzable) * 40
            score -= (reused / analyzable) * 30
            score = max(0, min(100, score))

        return {
            "overall_score": round(score),
            "total": total,
            "analyzable": analyzable,
            "protected": protected,
            "weak": weak,
            "reused": reused,
            "breached": 0,  # Filled async if user requests breach check
            "strong": strong,
            "entries": entries,
        }

    @staticmethod
    def check_breaches(decrypted_passwords: list[dict]) -> list[dict]:
        """
        Check available passwords against HaveIBeenPwned.
        Per-password-protected entries are intentionally not decrypted
        for the breach check. They are returned with status
        ``protected`` instead of being sent to the external service.
        """
        results = []
        for item in decrypted_passwords:
            password = item.get("password")
            service = item.get("service", "Unknown")
            password_protected = bool(
                item.get("password_protected", False)
            )

            # Never send a protected entry's placeholder or ciphertext
            # to the breach-checking service.
            if password_protected:
                results.append({
                    "service": service,
                    "breached": False,
                    "breach_count": 0,
                    "status": "protected",
                    "error": None,
                })
                continue

            if not isinstance(password, str):
                results.append({
                    "service": service,
                    "breached": False,
                    "breach_count": 0,
                    "status": "unknown",
                    "error": "Password is unavailable for breach checking.",
                })
                continue

            breach_result = BreachChecker.check_password(password)
            results.append({
                "service": service,
                "breached": breach_result["breached"],
                "breach_count": breach_result["count"],
                "status": breach_result["status"],
                "error": breach_result.get("error"),
            })
        return results