"""
Encrypted SQLite Vault Database — v2.0
Supports: multiple vaults, per-password secrets, duress credentials,
          vault-scoped entries, TOTP storage, and tamper-aware storage.
"""
import os
import platform
import sqlite3
import subprocess
import uuid
from pathlib import Path


class VaultDatabase:
    @staticmethod
    def _restrict_file_permissions(path: Path):
        """
        Restrict a sensitive database file to the current user where
        POSIX-style permissions are supported.
        """
        try:
            if path.exists():
                os.chmod(path, 0o600)
        except OSError:
            # chmod is advisory on some platforms, especially Windows.
            # Windows ACL hardening will be handled separately.
            pass

    @staticmethod
    def _restrict_windows_acl(path: Path):
        path = Path(path)
        if not path.exists() or platform.system() != "Windows":
            return
        try:
            sid_result = subprocess.run(
                [
                    "whoami",
                    "/user",
                    "/fo",
                    "csv",
                    "/nh",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            line = sid_result.stdout.strip()
            if not line:
                return
            parts = line.split(",")
            if len(parts) < 2:
                return
            sid = parts[1].strip().strip('"')
            if not sid.startswith("S-1-"):
                return
            subprocess.run(
                [
                    "icacls",
                    str(path),
                    "/inheritance:r",
                    "/grant:r",
                    f"*{sid}:F",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            # ACL hardening must not make the vault unusable.
            # Higher-level security diagnostics can surface failures.
            return

    def _harden_database_files(self):
        """
        Apply restrictive permissions to the SQLite database and
        any SQLite sidecar files currently present.
        """
        database_path = Path(self.DB_PATH)
        sensitive_files = (
            database_path,
            Path(f"{database_path}-wal"),
            Path(f"{database_path}-shm"),
        )
        for path in sensitive_files:
            self._restrict_file_permissions(path)
            self._restrict_windows_acl(path)

    DB_PATH = Path.home() / ".securevault" / "vault.db"

    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA secure_delete = ON")
        self._init_tables()
        self._harden_database_files()

    def _init_tables(self):
        """Create all required tables."""

        # Master credentials (supports multiple vaults)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vault_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salt BLOB NOT NULL,
                verify_hash TEXT NOT NULL,
                vault_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Legacy master table (backward compat)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS master (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                salt BLOB NOT NULL,
                verify_hash TEXT NOT NULL
            )
        """)

        # Duress credentials
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS duress (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                salt BLOB NOT NULL,
                verify_hash TEXT NOT NULL
            )
        """)

        # Password entries — vault-scoped with per-password secrets
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_uuid TEXT,
                service BLOB NOT NULL,
                username BLOB NOT NULL,
                password BLOB NOT NULL,
                url BLOB,
                notes BLOB,
                category TEXT DEFAULT 'password',
                favorite INTEGER DEFAULT 0,
                vault_id TEXT NOT NULL,
                per_pass_salt BLOB,
                per_pass_hash TEXT,
                per_pass_version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---------------------------------------------------------
        # Entry UUID migration
        # ---------------------------------------------------------
        # Existing databases were created before entry_uuid existed.
        # Add the column when necessary and assign every existing entry
        # a stable UUID.
        entry_columns = {
            row["name"]
            for row in self.conn.execute(
                "PRAGMA table_info(entries)"
            ).fetchall()
        }
        if "entry_uuid" not in entry_columns:
            self.conn.execute(
                "ALTER TABLE entries ADD COLUMN entry_uuid TEXT"
            )

        existing_entries = self.conn.execute(
            """
            SELECT id
            FROM entries
            WHERE entry_uuid IS NULL
            ORDER BY id
            """
        ).fetchall()
        for row in existing_entries:
            self.conn.execute(
                """
                UPDATE entries
                SET entry_uuid = ?
                WHERE id = ?
                """,
                (str(uuid.uuid4()), row["id"]),
            )

        # ---------------------------------------------------------
        # Per-password encryption version migration
        # ---------------------------------------------------------
        # Existing protected passwords use the legacy V1 format.
        # New protected passwords may use V2 with entry-specific AAD.
        # ---------------------------------------------------------
        entry_columns = {
            row["name"]
            for row in self.conn.execute(
                "PRAGMA table_info(entries)"
            ).fetchall()
        }
        if "per_pass_version" not in entry_columns:
            self.conn.execute(
                """
                ALTER TABLE entries
                ADD COLUMN per_pass_version INTEGER DEFAULT 1
                """
            )
            self.conn.execute(
                """
                UPDATE entries
                SET per_pass_version = 1
                WHERE per_pass_salt IS NOT NULL
                """
            )

        # TOTP secrets
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS totp_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label BLOB NOT NULL,
                secret BLOB NOT NULL,
                issuer BLOB,
                digits INTEGER DEFAULT 6,
                period INTEGER DEFAULT 30,
                algorithm TEXT DEFAULT 'sha1',
                vault_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS duress_decoy_link (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                encrypted_decoy_key BLOB NOT NULL,
                decoy_vault_id TEXT NOT NULL,
                decoy_key_nonce BLOB NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS otp_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vault_id TEXT NOT NULL UNIQUE,
                enabled INTEGER DEFAULT 0,
                secret TEXT,
                issuer TEXT,
                digits INTEGER DEFAULT 6,
                interval INTEGER DEFAULT 30,
                algorithm TEXT DEFAULT 'sha1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    # ─────────────────────────────────────────────
    #  VAULT CREDENTIALS (Multi-Vault)
    # ─────────────────────────────────────────────

    def vault_exists(self) -> bool:
        cur = self.conn.execute("SELECT COUNT(*) as cnt FROM vault_credentials")
        return cur.fetchone()["cnt"] > 0

    def create_vault(self, salt: bytes, verify_hash: str):
        """Legacy: create master table entry."""
        self.conn.execute(
            "INSERT OR REPLACE INTO master (id, salt, verify_hash) VALUES (1, ?, ?)",
            (salt, verify_hash)
        )
        self.conn.commit()

    def add_vault_credentials(self, salt: bytes, verify_hash: str, vault_id: str):
        """Add credentials for a vault (real or decoy)."""
        self.conn.execute(
            "INSERT OR REPLACE INTO vault_credentials (salt, verify_hash, vault_id) VALUES (?, ?, ?)",
            (salt, verify_hash, vault_id)
        )
        self.conn.commit()

    def get_all_vault_credentials(self) -> list:
        """Get all vault credentials (for multi-vault unlock)."""
        cur = self.conn.execute(
            "SELECT salt, verify_hash, vault_id FROM vault_credentials ORDER BY created_at ASC"
        )
        return [(row["salt"], row["verify_hash"], row["vault_id"]) for row in cur.fetchall()]

    def get_master_credentials(self) -> tuple:
        cur = self.conn.execute("SELECT salt, verify_hash FROM master WHERE id = 1")
        row = cur.fetchone()
        return row["salt"], row["verify_hash"]

    # ─────────────────────────────────────────────
    #  DURESS CREDENTIALS
    # ─────────────────────────────────────────────

    def set_duress_credentials(self, salt: bytes, verify_hash: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO duress (id, salt, verify_hash) VALUES (1, ?, ?)",
            (salt, verify_hash)
        )
        self.conn.commit()

    def get_duress_credentials(self):
        cur = self.conn.execute("SELECT salt, verify_hash FROM duress WHERE id = 1")
        row = cur.fetchone()
        return (row["salt"], row["verify_hash"]) if row else None

    # ─────────────────────────────────────────────
    #  ENTRIES (Vault-Scoped)
    # ─────────────────────────────────────────────

    def add_entry(self, service: bytes, username: bytes, password: bytes,
                  vault_id: str, url: bytes = None, notes: bytes = None,
                  category: str = "password", per_pass_salt: bytes = None,
                  per_pass_hash: str = None, entry_uuid: str = None,
                  per_pass_version: int = 1):
        if not vault_id:
            raise ValueError("vault_id is required")
        if entry_uuid is None:
            entry_uuid = str(uuid.uuid4())
        try:
            uuid.UUID(str(entry_uuid))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(
                "entry_uuid must be a valid UUID"
            ) from exc
        entry_uuid = str(entry_uuid)

        self.conn.execute(
            """
            INSERT INTO entries
                (
                    entry_uuid,
                    service,
                    username,
                    password,
                    url,
                    notes,
                    category,
                    vault_id,
                    per_pass_salt,
                    per_pass_hash,
                    per_pass_version
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_uuid,
                service,
                username,
                password,
                url,
                notes,
                category,
                vault_id,
                per_pass_salt,
                per_pass_hash,
                per_pass_version,
            ),
        )
        self.conn.commit()
        return entry_uuid

    def get_entries_by_vault(self, vault_id: str) -> list:
        """Get all entries belonging to a specific vault."""
        cur = self.conn.execute(
            "SELECT * FROM entries WHERE vault_id = ? ORDER BY updated_at DESC",
            (vault_id,)
        )
        return [dict(row) for row in cur.fetchall()]

    def get_all_entries(self) -> list:
        cur = self.conn.execute("SELECT * FROM entries ORDER BY updated_at DESC")
        return [dict(row) for row in cur.fetchall()]

    def delete_entry(self, entry_id: int, vault_id: str):
        """
        Delete an entry only when it belongs to the specified vault.
        This prevents an authenticated session from deleting an entry
        belonging to another vault by supplying its database ID.
        """
        if not vault_id:
            raise ValueError("vault_id is required")
        cursor = self.conn.execute(
            """
            DELETE FROM entries
            WHERE id = ? AND vault_id = ?
            """,
            (entry_id, vault_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def update_entry(self, entry_id: int, vault_id: str, **fields):
        """
        Update an entry only when it belongs to the specified vault.
        The vault boundary is enforced directly in the SQL WHERE clause
        so callers cannot modify another vault's entry by ID alone.
        """
        if not vault_id:
            raise ValueError("vault_id is required")

        allowed = {
            "service",
            "username",
            "password",
            "url",
            "notes",
            "category",
            "favorite",
            "per_pass_salt",
            "per_pass_hash",
            "per_pass_version",
        }
        filtered = {
            key: value
            for key, value in fields.items()
            if key in allowed
        }
        if not filtered:
            return False

        set_clause = ", ".join(
            f"{key} = ?"
            for key in filtered.keys()
        )
        values = list(filtered.values()) + [entry_id, vault_id]
        cursor = self.conn.execute(
            f"""
            UPDATE entries
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND vault_id = ?
            """,
            values,
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def wipe_vault_entries(self, keep_decoy: bool = False):
        """
        Wipe vault entries.
        If keep_decoy=True, only wipe the FIRST (real) vault's entries.
        """
        if keep_decoy:
            all_creds = self.get_all_vault_credentials()
            if all_creds:
                real_vault_id = all_creds[0][2]
                self.conn.execute(
                    "DELETE FROM entries WHERE vault_id = ?", (real_vault_id,)
                )
        else:
            self.conn.execute("DELETE FROM entries")
        self.conn.commit()
        self._vacuum_if_possible()

    def toggle_favorite(self, entry_id: int, vault_id: str):
        """
        Toggle an entry's favorite state only within the specified vault.
        """
        if not vault_id:
            raise ValueError("vault_id is required")

        cursor = self.conn.execute(
            """
            UPDATE entries
            SET favorite = CASE
                WHEN favorite = 1 THEN 0
                ELSE 1
            END
            WHERE id = ?
              AND vault_id = ?
            """,
            (entry_id, vault_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    # ─────────────────────────────────────────────
    #  TOTP ENTRIES
    # ─────────────────────────────────────────────

    def add_totp_entry(
        self,
        label: bytes,
        secret: bytes,
        vault_id: str,
        issuer: bytes = None,
        digits: int = 6,
        period: int = 30,
        algorithm: str = "sha1",
    ):
        """Add an encrypted TOTP entry to the specified vault."""

        self.conn.execute(
            """
            INSERT INTO totp_entries
                (label, secret, issuer, digits, period, algorithm, vault_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                label,
                secret,
                issuer,
                digits,
                period,
                algorithm,
                vault_id,
            ),
        )

        self.conn.commit()

    def get_totp_entries(self, vault_id: str) -> list:
        """Return all TOTP entries belonging to a specific vault."""

        cur = self.conn.execute(
            """
            SELECT *
            FROM totp_entries
            WHERE vault_id = ?
            ORDER BY created_at DESC
            """,
            (vault_id,),
        )

        return [dict(row) for row in cur.fetchall()]

    def delete_totp_entry(self, entry_id: int):
        """Delete a TOTP entry by ID."""

        self.conn.execute(
            "DELETE FROM totp_entries WHERE id = ?",
            (entry_id,),
        )

        self.conn.commit()

    def set_otp_settings(
        self,
        vault_id: str,
        enabled: bool,
        secret: str,
        issuer: str = None,
        digits: int = 6,
        interval: int = 30,
        algorithm: str = "sha1",
    ):
        """Create or update TOTP settings for a vault."""

        self.conn.execute(
            """
            INSERT INTO otp_settings
                (vault_id, enabled, secret, issuer, digits, interval, algorithm)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vault_id) DO UPDATE SET
                enabled=excluded.enabled,
                secret=excluded.secret,
                issuer=excluded.issuer,
                digits=excluded.digits,
                interval=excluded.interval,
                algorithm=excluded.algorithm
            """,
            (
                vault_id,
                1 if enabled else 0,
                secret,
                issuer,
                digits,
                interval,
                algorithm,
            ),
        )

        self.conn.commit()

    def get_otp_settings(self, vault_id: str):
        """Return OTP settings for a specific vault."""

        cur = self.conn.execute(
            """
            SELECT *
            FROM otp_settings
            WHERE vault_id = ?
            """,
            (vault_id,),
        )

        row = cur.fetchone()
        return dict(row) if row else None

    def disable_otp(self, vault_id: str):
        """Disable OTP for a specific vault."""

        self.conn.execute(
            """
            UPDATE otp_settings
            SET enabled = 0
            WHERE vault_id = ?
            """,
            (vault_id,),
        )

        self.conn.commit()

    # ─────────────────────────────────────────────
    #  STATS
    # ─────────────────────────────────────────────

    def get_entry_count(self, vault_id: str) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM entries WHERE vault_id = ?", (vault_id,)
        )
        return cur.fetchone()["cnt"]

    def set_duress_decoy_link(self, encrypted_decoy_key, decoy_vault_id, nonce):
        """Store the decoy vault's key encrypted by the duress key."""
        self.conn.execute(
            """INSERT OR REPLACE INTO duress_decoy_link
               (id, encrypted_decoy_key, decoy_vault_id, decoy_key_nonce)
               VALUES (1, ?, ?, ?)""",
            (encrypted_decoy_key, decoy_vault_id, nonce)
        )
        self.conn.commit()

    def get_duress_decoy_link(self):
        """Get the encrypted decoy key and vault ID."""
        cur = self.conn.execute(
            "SELECT encrypted_decoy_key, decoy_vault_id, decoy_key_nonce FROM duress_decoy_link WHERE id = 1"
        )
        row = cur.fetchone()
        if row:
            return {
                "encrypted_decoy_key": row[0],
                "decoy_vault_id": row[1],
                "nonce": row[2],
            }
        return None

    def wipe_entries_by_vault_id(self, vault_id):
        """Delete all entries for a specific vault ID."""
        self.conn.execute(
            "DELETE FROM entries WHERE vault_id = ?", (vault_id,)
        )
        self.conn.commit()
        self._vacuum_if_possible()

    def wipe_vault_secret_data(self, vault_id: str):
        """
        Remove all secret-bearing data belonging to one vault.
        This intentionally preserves:
        - the vault credential record
        - duress credentials
        - the decoy-vault link
        - data belonging to other vaults
        The goal is to wipe the real vault's contents without
        destroying the mechanism required to open the decoy vault.
        """
        if not vault_id:
            raise ValueError("vault_id is required")
        self.conn.execute(
            "DELETE FROM entries WHERE vault_id = ?",
            (vault_id,),
        )
        self.conn.execute(
            "DELETE FROM totp_entries WHERE vault_id = ?",
            (vault_id,),
        )
        self.conn.execute(
            "DELETE FROM otp_settings WHERE vault_id = ?",
            (vault_id,),
        )
        self.conn.commit()
        self._vacuum_if_possible()

    def _vacuum_if_possible(self):
        try:
            self.conn.execute("VACUUM")
        except sqlite3.OperationalError:
            pass

    def close(self):
        self.conn.close()