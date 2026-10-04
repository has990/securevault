"""
Audit log for SecureVault.

Tracks failed login attempts, successful logins, vault access,
and security-relevant events in JSONL format.
"""
import json
import time
from pathlib import Path

from core.secure_log_store import SecureLogStore


class IntruderLog:
    """Tracks suspicious activity and audit events."""

    LOG_PATH = Path.home() / ".securevault" / ".audit_log.enc"
    MAX_ATTEMPTS = 10
    LOCKOUT_SECONDS = 300  # 5 minutes

    def __init__(self):
        self._store = SecureLogStore()
        self.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not self.LOG_PATH.exists():
            self.LOG_PATH.write_text("")

    def log_event(self, event_type: str, **details):
        """Write a structured audit event."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "epoch": time.time(),
            "type": event_type,
            "details": details,
        }
        self._store.append_json(self.LOG_PATH, entry)

    def record_failed_attempt(self, reason: str = "invalid_credentials"):
        """Log a failed login attempt."""
        self.log_event("failed_login", reason=reason)

    def record_successful_login(self, vault_id: str = None, is_decoy: bool = False):
        """Log a successful login."""
        self.log_event("successful_login", vault_id=vault_id, is_decoy=is_decoy)

    def record_vault_access(self, action: str, vault_id: str = None, entry_id: int = None, service: str = None):
        """Log vault access and content interactions."""
        self.log_event(
            "vault_access",
            action=action,
            vault_id=vault_id,
            entry_id=entry_id,
            service=service,
        )

    def record_security_event(self, event: str, **details):
        """Log a security-relevant event."""
        self.log_event("security_event", event=event, **details)

    def get_recent_attempts(self, within_seconds=3600):
        """Get failed attempts within the time window."""
        entries = self._read_all()
        cutoff = time.time() - within_seconds
        return [
            e for e in entries
            if e.get("epoch", 0) > cutoff and e.get("type") == "failed_login"
        ]

    def get_attempt_count(self):
        """Get number of recent failed attempts."""
        return len(self.get_recent_attempts(within_seconds=3600))

    def get_recent_events(self, within_seconds=86400, event_type: str = None):
        """Return recent audit events."""
        entries = self._read_all()
        cutoff = time.time() - within_seconds
        filtered = [e for e in entries if e.get("epoch", 0) > cutoff]
        if event_type is not None:
            filtered = [e for e in filtered if e.get("type") == event_type]
        return filtered

    def get_recent_summary(self, within_seconds=86400):
        """Summarize recent audit activity."""
        summary = {}
        for entry in self.get_recent_events(within_seconds=within_seconds):
            event_type = entry.get("type", "unknown")
            summary[event_type] = summary.get(event_type, 0) + 1
        return summary

    def is_locked_out(self):
        """Check if user is locked out due to too many failed attempts."""
        recent = self.get_recent_attempts(within_seconds=self.LOCKOUT_SECONDS)
        if len(recent) >= self.MAX_ATTEMPTS:
            last_attempt = max(e.get("epoch", 0) for e in recent)
            remaining = self.LOCKOUT_SECONDS - (time.time() - last_attempt)
            if remaining > 0:
                return True, remaining
        return False, 0

    def _read_all(self):
        """Read all log entries."""
        return self._store.read_json(self.LOG_PATH)