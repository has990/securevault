"""
SecureVault v2.0 — CYBERPUNK EDITION
Neon-infused, hacker-themed password manager with glitch animations.
"""
import time
import customtkinter as ctk
from gui.login_view import LoginView
from gui.vault_view import VaultView
from gui.generator_view import GeneratorView
from gui.settings_view import SettingsView
from gui.security_dashboard import SecurityDashboard
from gui.animations import FadeAnimations
from core.database import VaultDatabase
from core.decoy_vault import DecoyVaultManager
from core.duress_handler import DuressHandler
from core.stealth_mode import StealthMode
from core.intruder_log import IntruderLog
from core.tamper_detection import TamperDetection
from core.per_password_lock import PerPasswordLock


class SecureVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("⟨ SECUREVAULT ⟩")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── CYBERPUNK COLOR PALETTE ──
        self.colors = {
            # Backgrounds
            "bg_dark":        "#0a0a0f",       # Near-black with blue tint
            "bg_card":        "#0f1923",       # Dark navy card
            "bg_sidebar":     "#070b10",       # Darkest sidebar
            "bg_input":       "#0c1219",       # Input field bg
            "bg_hover":       "#131f2e",       # Hover state

            # Neon accents
            "accent":         "#00ff9f",       # Neon green (primary)
            "accent_hover":   "#00cc7f",       # Darker green
            "accent_dim":     "#004d30",       # Dimmed green
            "cyan":           "#00f0ff",       # Cyan accent
            "cyan_dim":       "#003844",       # Dimmed cyan
            "neon_pink":      "#ff0080",       # Hot pink
            "neon_purple":    "#bf00ff",       # Purple accent
            "neon_yellow":    "#ffff00",       # Warning yellow
            "neon_orange":    "#ff6600",       # Orange accent

            # Status
            "success":        "#00ff9f",       # Same as accent
            "warning":        "#ffff00",       # Neon yellow
            "danger":         "#ff0040",       # Neon red
            "danger_dim":     "#4d0013",       # Dimmed red

            # Text
            "text_primary":   "#e0ffe0",       # Light green-tinted white
            "text_secondary": "#4a7a5a",       # Muted green
            "text_terminal":  "#00ff9f",       # Terminal green
            "text_cyan":      "#00f0ff",       # Cyan text
            "text_dim":       "#1a3a2a",       # Very dim

            # Borders & effects
            "border":         "#0d3320",       # Dark green border
            "border_glow":    "#00ff9f",       # Glowing border
            "glow":           "#00ff9f",       # Glow effect color
            "scanline":       "#00ff9f08",     # Subtle scanline overlay
        }

        self.configure(fg_color=self.colors["bg_dark"])

        # ── Core Systems ──
        self.db = VaultDatabase()
        self.decoy_manager = DecoyVaultManager(self.db)
        self.duress_handler = DuressHandler(self.db)
        self.stealth_mode = StealthMode(self)
        self.intruder_log = IntruderLog()
        self.per_password_lock = PerPasswordLock()

        # ── State ──
        self.encryption_engine = None
        self._vault_key = None
        self.current_vault_id = None
        self.current_view = None
        self.is_decoy_active = False
        self._last_activity = time.time()
        self._auto_lock_seconds = 300
        self._auto_lock_enabled = True

        # ── Auto-Lock ──
        self.bind_all("<Key>", self._on_activity)
        self.bind_all("<Motion>", self._on_activity)
        self.bind_all("<Button>", self._on_activity)

        # ── Global Stealth Hotkeys ──
        self.bind_all("<Control-Shift-s>", self._hotkey_toggle_stealth)
        self.bind_all("<Control-Shift-S>", self._hotkey_toggle_stealth)
        self.bind_all("<Control-Shift-x>", self._hotkey_force_exit_stealth)
        self.bind_all("<Control-Shift-X>", self._hotkey_force_exit_stealth)

        # ── Startup ──
        self._start_auto_lock_monitor()
        self.show_login()

        # ── Fade In ──
        FadeAnimations.fade_in_window(self, duration_ms=700)

    # ─────────────────────────────────────────────
    #  VIEW MANAGEMENT
    # ─────────────────────────────────────────────

    def show_login(self):
        self._clear_view()
        self.encryption_engine = None
        self.current_vault_id = None
        self.is_decoy_active = False

        self.current_view = LoginView(
            self, self.colors,
            on_login_success=self._handle_login_success,
            db=self.db,
            decoy_manager=self.decoy_manager,
            duress_handler=self.duress_handler,
            intruder_log=self.intruder_log,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_vault(self):
        self._clear_view()
        self.current_view = VaultView(
            self, self.colors, self.encryption_engine,
            vault_id=self.current_vault_id,
            is_decoy=self.is_decoy_active,
            per_password_lock=self.per_password_lock,
            db=self.db,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_generator(self):
        self._clear_view()
        self.current_view = GeneratorView(self, self.colors)
        self.current_view.pack(fill="both", expand=True)

    def show_security_dashboard(self):
        self._clear_view()
        self.current_view = SecurityDashboard(
            self, self.colors, self.encryption_engine,
            vault_id=self.current_vault_id, db=self.db,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_settings(self):
        self._clear_view()
        self.current_view = SettingsView(
            self, self.colors,
            stealth_mode=self.stealth_mode,
            duress_handler=self.duress_handler,
            decoy_manager=self.decoy_manager,
            auto_lock_seconds=self._auto_lock_seconds,
            on_auto_lock_changed=self._set_auto_lock_timeout,
            db=self.db,
            vault_id=self.current_vault_id,
            encryption_engine=self.encryption_engine,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_totp(self):
        """Display the TOTP authenticator view."""
        self._clear_view()
        from gui.totp_view import TOTPView
        self.current_view = TOTPView(
            self, self.colors, self.encryption_engine,
            vault_id=self.current_vault_id, db=self.db,
        )
        self.current_view.pack(fill="both", expand=True)

    def _clear_view(self):
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    # ─────────────────────────────────────────────
    #  LOGIN HANDLING
    # ─────────────────────────────────────────────

    def _handle_login_success(
        self,
        engine,
        vault_id,
        is_decoy=False,
        vault_key=None,
        is_new_vault=False,
    ):
        """Complete authentication and initialize the active vault session."""

        self.encryption_engine = engine
        self._vault_key = (
            vault_key
            if vault_key is not None
            else engine._key
        )
        self.current_vault_id = vault_id
        self.is_decoy_active = is_decoy
        self._last_activity = time.time()

        # Verify the database integrity before allowing access.
        integrity_ok = self._update_tamper_baseline(
            is_new_vault=is_new_vault,
        )
        if not integrity_ok:
            self.intruder_log.record_security_event(
                "login_blocked_tamper",
                vault_id=vault_id,
                is_decoy=is_decoy,
            )
            # Do not leave the authenticated encryption context
            # active after a failed integrity check.
            self.encryption_engine = None
            self._vault_key = None
            self.current_vault_id = None
            self.is_decoy_active = False
            return False

        self.intruder_log.record_successful_login(
            vault_id=vault_id,
            is_decoy=is_decoy,
        )
        self.show_vault()
        return True

    def _update_tamper_baseline(self, is_new_vault=False):
        """
        Verify the existing integrity baseline before replacing it.

        A missing baseline is treated as a first-run condition.
        An existing baseline that fails verification is treated as
        possible tampering and is never silently overwritten.
        """

        if not self.current_vault_id or not self._vault_key:
            return False

        try:
            td = TamperDetection(
                str(self.db.DB_PATH),
                self._vault_key,
                self.current_vault_id,
            )

            result = td.verify_integrity()
            warnings = result.get("warnings", [])

            # A missing baseline is trusted only during new-vault setup.
            if warnings == ["No integrity baseline found"]:
                if is_new_vault:
                    td.create_integrity_record()
                    return True
                self.intruder_log.record_security_event(
                    "integrity_baseline_missing",
                    vault_id=self.current_vault_id,
                )
                self._show_tamper_warning(
                    [
                        "Integrity baseline is missing for this existing vault.",
                        "Vault access has been blocked.",
                    ]
                )
                return False

            # Existing baseline failed verification.
            if not result.get("intact", False):
                self.intruder_log.record_security_event(
                    "tamper_detected",
                    vault_id=self.current_vault_id,
                    warnings=warnings,
                )

                self._show_tamper_warning(warnings)
                return False

            # Existing baseline is valid, so it is safe to refresh it.
            td.create_integrity_record()
            return True
        except Exception as exc:
            self.intruder_log.record_security_event(
                "tamper_baseline_error",
                vault_id=self.current_vault_id,
                error=str(exc),
            )

            return False

    def _check_tamper(self):
        """Run tamper detection using the authenticated vault key."""

        if not self.current_vault_id or not self.encryption_engine or not self._vault_key:
            return {
                "intact": True,
                "warnings": [],
                "details": {},
            }

        try:
            td = TamperDetection(
                str(self.db.DB_PATH),
                self._vault_key,
                self.current_vault_id,
            )

            result = td.verify_integrity()

            warnings = result.get("warnings", [])

            if warnings and warnings != ["No integrity baseline found"]:
                self.intruder_log.record_security_event(
                    "tamper_check_warning",
                    vault_id=self.current_vault_id,
                    warnings=warnings,
                )
                self._show_tamper_warning(warnings)

            return result
        except Exception as exc:
            self.intruder_log.record_security_event(
                "tamper_check_error",
                vault_id=self.current_vault_id,
                error=str(exc),
            )
            return {
                "intact": False,
                "warnings": [f"Tamper check failed: {exc}"],
                "details": {},
            }

    def _show_tamper_warning(self, warnings):
        from gui.components.toast_notification import ToastNotification
        for warning in warnings[:3]:
            ToastNotification.show(self, warning, toast_type="warning", duration_ms=5000)

    # ─────────────────────────────────────────────
    #  AUTO-LOCK
    # ─────────────────────────────────────────────

    def _on_activity(self, event=None):
        self._last_activity = time.time()

    def _start_auto_lock_monitor(self):
        def _check():
            if (self._auto_lock_enabled
                    and self.encryption_engine is not None
                    and time.time() - self._last_activity > self._auto_lock_seconds):
                self.lock_vault()
            self.after(5000, _check)
        self.after(5000, _check)

    def _set_auto_lock_timeout(self, seconds: int):
        self._auto_lock_seconds = max(30, seconds)

    def lock_vault(self):
        if self.current_vault_id:
            self.intruder_log.record_security_event(
                "vault_locked",
                vault_id=self.current_vault_id,
                is_decoy=self.is_decoy_active,
            )
        self.encryption_engine = None
        self.current_vault_id = None
        self.is_decoy_active = False
        self.show_login()

    def toggle_stealth(self, disguise: str = "calculator"):
        self.stealth_mode.toggle(disguise)

    def _hotkey_toggle_stealth(self, event=None):
        self._on_activity()
        self.toggle_stealth("calculator")
        return "break"

    def _hotkey_force_exit_stealth(self, event=None):
        self._on_activity()
        if self.stealth_mode.is_stealth:
            self.stealth_mode.deactivate()
        return "break"