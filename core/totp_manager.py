"""
Built-in TOTP Authenticator — Generate 2FA codes without a separate app.

Implements RFC 6238 (TOTP) with:
- Standard 30-second time steps
- SHA-1, SHA-256, SHA-512 support
- 6 or 8 digit codes
- QR code parsing support (via URI)
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time


class TOTPManager:
    """Generate and manage TOTP (Time-based One-Time Password) codes."""

    def __init__(self, secret: str, digits: int = 6, interval: int = 30,
                 algorithm: str = "sha1"):
        self.secret = self._decode_secret(secret)
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm

    def generate_code(self, timestamp: float = None) -> str:
        """Generate the current TOTP code."""
        if timestamp is None:
            timestamp = time.time()

        time_counter = int(timestamp // self.interval)
        counter_bytes = struct.pack(">Q", time_counter)

        hash_algo = getattr(hashlib, self.algorithm)
        hmac_hash = hmac.new(self.secret, counter_bytes, hash_algo).digest()

        offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack(">I", hmac_hash[offset:offset + 4])[0]
        truncated &= 0x7FFFFFFF

        code = truncated % (10 ** self.digits)
        return str(code).zfill(self.digits)

    def get_remaining_seconds(self, timestamp: float = None) -> int:
        """Get seconds remaining until the current code expires."""
        if timestamp is None:
            timestamp = time.time()
        return self.interval - int(timestamp % self.interval)

    def verify_code(self, code: str, window: int = 1, timestamp: float = None) -> bool:
        """
        Verify a TOTP code with a tolerance window.
        window=1 means we check current, previous, and next intervals.
        """
        if not code:
            return False

        code = str(code).strip()
        current_time = time.time() if timestamp is None else timestamp
        for offset in range(-window, window + 1):
            check_time = current_time + (offset * self.interval)
            if self.generate_code(check_time) == code:
                return True
        return False

    @staticmethod
    def generate_secret(length: int = 20) -> str:
        """Create a random base32 secret suitable for TOTP."""
        return base64.b32encode(secrets.token_bytes(length)).decode("ascii").rstrip("=")

    @staticmethod
    def parse_otpauth_uri(uri: str) -> dict:
        """
        Parse an otpauth:// URI (from QR codes).
        Format: otpauth://totp/Label?secret=BASE32&issuer=Example&digits=6&period=30
        """
        from urllib.parse import parse_qs, unquote, urlparse
        parsed = urlparse(uri)
        params = parse_qs(parsed.query)
        label = unquote(parsed.path.lstrip('/'))

        return {
            "label": label,
            "secret": params.get("secret", [""])[0],
            "issuer": params.get("issuer", [label.split(":")[0] if ":" in label else ""])[0],
            "digits": int(params.get("digits", [6])[0]),
            "period": int(params.get("period", [30])[0]),
            "algorithm": params.get("algorithm", ["sha1"])[0].lower(),
        }

    @staticmethod
    def _decode_secret(secret: str) -> bytes:
        """Decode a base32-encoded secret."""
        if not secret:
            raise ValueError("TOTP secret cannot be empty")

        normalized = secret.replace(" ", "").replace("-", "").upper()
        missing_padding = len(normalized) % 8
        if missing_padding:
            normalized += "=" * (8 - missing_padding)
        return base64.b32decode(normalized, casefold=True)


def validate_totp_code(secret: str, code: str, digits: int = 6, interval: int = 30,
                       algorithm: str = "sha1", timestamp: float = None,
                       window: int = 1) -> bool:
    """Validate a TOTP code using the supplied secret."""
    if not code:
        return False
    manager = TOTPManager(secret, digits=digits, interval=interval, algorithm=algorithm)
    return manager.verify_code(code, window=window, timestamp=timestamp)