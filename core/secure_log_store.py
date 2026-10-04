"""
Encrypted local log storage for SecureVault.

Stores JSON events as encrypted newline-delimited records so audit and duress
logs are not readable at rest without the local log key.
"""
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class SecureLogStore:
    """Encrypts and decrypts structured local log records."""

    @staticmethod
    def _restrict_file_permissions(path: Path):
        """
        Restrict a sensitive file to the current user where the
        underlying operating system supports POSIX-style modes.
        On Windows, chmod does not provide full ACL isolation; a
        Windows-specific ACL hardening step can be added separately.
        """
        try:
            os.chmod(path, 0o600)
        except OSError:
            # Permission hardening must not prevent normal operation
            # on platforms that do not support POSIX permissions.
            pass

    KEY_PATH = Path.home() / ".securevault" / ".log_key"

    def __init__(self, key_path: Path = None):
        self.key_path = Path(key_path) if key_path else self.KEY_PATH
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        if self.key_path.exists():
            key = self.key_path.read_bytes().strip()
            if key:
                return key

        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        self._restrict_file_permissions(self.key_path)
        return key

    def append_json(self, log_path: Path, entry: dict):
        """Append one encrypted JSON event to a protected log file."""
        log_path = Path(log_path)
        log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        # Create the file before opening it for append so that
        # restrictive permissions can be applied consistently.
        if not log_path.exists():
            log_path.touch()
        self._restrict_file_permissions(log_path)
        payload = json.dumps(
            entry,
            separators=(",", ":"),
        ).encode("utf-8")
        token = self._fernet.encrypt(payload)
        with open(
            log_path,
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                token.decode("ascii") + "\n"
            )
        # Re-apply permissions after writing in case the filesystem
        # or platform altered them.
        self._restrict_file_permissions(log_path)

    def read_json(self, log_path: Path) -> list:
        log_path = Path(log_path)
        entries = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = self._fernet.decrypt(line.encode("ascii")).decode("utf-8")
                        entries.append(json.loads(payload))
                    except (InvalidToken, UnicodeError, json.JSONDecodeError):
                        # Legacy compatibility: allow old plaintext JSONL lines.
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        return entries
