"""
CYBERPUNK Login Screen
Features: Matrix rain background, terminal boot sequence,
glitch text title, neon flicker, hex data stream.
"""
import tkinter as tk
import customtkinter as ctk
from gui.animations import (
    FadeAnimations, BounceAnimations, PulseAnimations,
    GlitchAnimation, MatrixRainAnimation, NeonFlickerAnimation,
    TerminalBootAnimation, DataStreamAnimation,
)
from core.key_derivation import KeyDerivation
from core.encryption import EncryptionEngine
from core.decoy_vault import DecoyVaultManager
from core.totp_manager import TOTPManager


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, colors, on_login_success, db,
                 decoy_manager, duress_handler, intruder_log):
        super().__init__(parent, fg_color=colors["bg_dark"])
        self.colors = colors
        self.on_login_success = on_login_success
        self.db = db
        self.decoy_manager = decoy_manager
        self.duress_handler = duress_handler
        self.intruder_log = intruder_log
        self._rain_stop = None
        self.is_first_run = not self.db.vault_exists()
        self.is_create_mode = self.is_first_run

        # Check lockout
        is_locked, remaining = self.intruder_log.is_locked_out()
        if is_locked:
            self._show_lockout_screen(remaining)
            return

        # ── Matrix Rain Background ──
        self.rain_canvas = tk.Canvas(
            self, bg="#0a0a0f", highlightthickness=0
        )
        self.rain_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Start rain after widget is rendered
        self.after(100, self._start_matrix_rain)

        # ── Center Container (over the rain) ──
        self.center = ctk.CTkFrame(self, fg_color="#0d0d14", corner_radius=20,
                                    border_width=1, border_color=colors["border"])
        self.center.place(relx=0.5, rely=0.5, anchor="center",
                          relwidth=0.45, relheight=0.75)

        # ── Neon Lock Icon ──
        self.logo_label = ctk.CTkLabel(
            self.center, text="⟨ 🔐 ⟩",
            font=("Consolas", 48, "bold"),
            text_color=colors["accent"]
        )
        self.logo_label.pack(pady=(30, 5))

        # Neon flicker on the lock icon
        self.after(500, lambda: NeonFlickerAnimation.flicker_text(
            self.logo_label,
            text_color=colors["accent"],
            dim_color=colors["accent_dim"],
            duration_ms=1500, flicker_count=6
        ))

        # ── Glitch Title ──
        self.title_label = ctk.CTkLabel(
            self.center, text="████████████",
            font=("Consolas", 32, "bold"),
            text_color=colors["accent"]
        )
        self.title_label.pack(pady=(0, 2))

        # Glitch-resolve the title
        self.after(800, lambda: GlitchAnimation.glitch_text(
            self.title_label, "SECUREVAULT", duration_ms=1000
        ))

        # ── Hex Data Stream Subtitle ──
        self.subtitle_label = ctk.CTkLabel(
            self.center, text="",
            font=("Consolas", 10),
            text_color=colors["text_secondary"]
        )
        self.subtitle_label.pack(pady=(0, 5))

        self.after(1800, lambda: DataStreamAnimation.hex_stream(
            self.subtitle_label, length=24, duration_ms=2000,
            on_complete=lambda: self.subtitle_label.configure(
                text="[ ENCRYPTED · LOCAL-FIRST · AUTHENTICATED ]"
            )
        ))

        self.onboarding_label = ctk.CTkLabel(
            self.center,
            text=self._get_onboarding_text(),
            font=("Consolas", 10),
            text_color=colors["text_secondary"],
            justify="left",
            wraplength=450,
        )
        self.onboarding_label.pack(fill="x", padx=25, pady=(4, 6))

        # ── Terminal Boot Text ──
        self.boot_text = ctk.CTkTextbox(
            self.center, height=100,
            font=("Consolas", 9),
            fg_color="#050810",
            text_color=colors["text_terminal"],
            border_color=colors["border"],
            border_width=1,
            corner_radius=8,
            activate_scrollbars=False,
        )
        self.boot_text.pack(fill="x", padx=25, pady=(10, 10))

        # Play boot sequence
        self.after(600, lambda: TerminalBootAnimation.play_boot(
            self.boot_text, line_delay_ms=60, char_delay_ms=8,
            on_complete=self._show_login_fields
        ))

        # ── Login fields (initially hidden, shown after boot) ──
        self.login_frame = ctk.CTkFrame(self.center, fg_color="transparent")

        # Pre-build login fields
        self._build_login_fields()

        # Failed attempts warning
        recent = self.intruder_log.get_recent_attempts(within_seconds=3600)
        if len(recent) > 0:
            self.warn_label = ctk.CTkLabel(
                self.center,
                text=f"⚠ {len(recent)} FAILED ATTEMPT(S) DETECTED",
                font=("Consolas", 10, "bold"),
                text_color=colors["danger"]
            )
            self.warn_label.pack(pady=(5, 0))
            NeonFlickerAnimation.flicker_text(
                self.warn_label,
                text_color=colors["danger"],
                dim_color=colors["danger_dim"],
                duration_ms=1500, flicker_count=4
            )

    def _build_login_fields(self):
        """Pre-build login fields (shown after boot animation)."""
        self.password_var = tk.StringVar(value="")
        self.confirm_var = tk.StringVar(value="")

        # Terminal-style prompt
        self.prompt_label = ctk.CTkLabel(
            self.login_frame, text="root@securevault:~$ ",
            font=("Consolas", 12),
            text_color=self.colors["text_terminal"]
        )
        self.prompt_label.pack(anchor="w", padx=25, pady=(5, 0))

        # Password Entry — terminal style
        self.password_entry = ctk.CTkEntry(
            self.login_frame, placeholder_text="enter_master_key >>>",
            width=350, height=45, show="•",
            textvariable=self.password_var,
            font=("Consolas", 14),
            corner_radius=4,
            border_color=self.colors["border"],
            border_width=1,
            fg_color=self.colors["bg_input"],
            text_color=self.colors["text_terminal"],
            placeholder_text_color=self.colors["text_dim"],
        )
        self.password_entry.pack(fill="x", padx=25, pady=(2, 8))
        self.password_entry.bind("<Return>", lambda e: self._handle_primary_action())

        self.confirm_entry = ctk.CTkEntry(
            self.login_frame, placeholder_text="confirm_master_key >>>",
            width=350, height=45, show="•",
            textvariable=self.confirm_var,
            font=("Consolas", 14),
            corner_radius=4,
            border_color=self.colors["border"],
            border_width=1,
            fg_color=self.colors["bg_input"],
            text_color=self.colors["text_terminal"],
            placeholder_text_color=self.colors["text_dim"],
        )
        self.confirm_entry.bind("<Return>", lambda e: self._handle_primary_action())

        self.mode_hint_label = ctk.CTkLabel(
            self.login_frame,
            text="",
            font=("Consolas", 9),
            text_color=self.colors["text_secondary"],
            justify="left",
            wraplength=450,
        )
        self.mode_hint_label.pack(fill="x", padx=25, pady=(0, 6))

        # Error Label
        self.error_label = ctk.CTkLabel(
            self.login_frame, text="", font=("Consolas", 11),
            text_color=self.colors["danger"]
        )
        self.error_label.pack(pady=(0, 5))

        # Unlock Button — neon style
        self.unlock_btn = ctk.CTkButton(
            self.login_frame, text="⟨ DECRYPT VAULT ⟩",
            width=350, height=45,
            font=("Consolas", 14, "bold"),
            corner_radius=4,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            border_width=1,
            border_color=self.colors["accent"],
            command=self._handle_primary_action
        )
        self.unlock_btn.pack(fill="x", padx=25, pady=(0, 10))

        self.mode_switch_btn = ctk.CTkButton(
            self.login_frame,
            text="",
            width=350,
            height=36,
            font=("Consolas", 11, "bold"),
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.colors["bg_hover"],
            text_color=self.colors["cyan"],
            border_width=1,
            border_color=self.colors["cyan_dim"],
            command=self._toggle_mode,
        )
        self.mode_switch_btn.pack(fill="x", padx=25, pady=(0, 5))

        self._refresh_mode_ui()

    def _get_onboarding_text(self) -> str:
        if self.is_first_run:
            return (
                "[ FIRST RUN ] 1) Create your first vault. 2) Set a strong master password "
                "(8+ chars). 3) Use the same password to unlock this vault later."
            )
        return (
            "Use your master password to unlock an existing vault. "
            "If another person needs their own vault on this device, click CREATE NEW VAULT."
        )

    def _handle_primary_action(self):
        if self.is_create_mode:
            # In create mode, pressing Enter in the first field should move to confirmation.
            focused = self.focus_get()
            if focused == self.password_entry and not self.confirm_var.get().strip():
                self.confirm_entry.focus_set()
                return
            self.create_new_vault()
            return
        self.attempt_login()

    def _toggle_mode(self):
        if self.is_first_run:
            return
        self.is_create_mode = not self.is_create_mode
        self.password_var.set("")
        self.confirm_var.set("")
        self._show_error("")
        self._refresh_mode_ui()

    def _refresh_mode_ui(self):
        if self.is_create_mode:
            self.prompt_label.configure(text="create@securevault:~$ ")
            self.password_entry.configure(placeholder_text="new_master_key >>>")
            if not self.confirm_entry.winfo_ismapped():
                self.confirm_entry.pack(fill="x", padx=25, pady=(0, 8))
            self.mode_hint_label.configure(
                text="[ CREATE MODE ] This master password opens a separate vault for this user."
            )
            self.unlock_btn.configure(
                text="⟨ INITIALIZE FIRST VAULT ⟩" if self.is_first_run else "⟨ CREATE NEW VAULT ⟩"
            )
            if self.is_first_run:
                self.mode_switch_btn.configure(
                    text="[ FIRST-RUN SETUP REQUIRED ]",
                    state="disabled",
                    text_color=self.colors["text_secondary"],
                    border_color=self.colors["border"],
                )
            else:
                self.mode_switch_btn.configure(
                    text="⟨ BACK TO LOGIN ⟩",
                    state="normal",
                    text_color=self.colors["cyan"],
                    border_color=self.colors["cyan_dim"],
                )
        else:
            self.prompt_label.configure(text="root@securevault:~$ ")
            self.password_entry.configure(placeholder_text="enter_master_key >>>")
            if self.confirm_entry.winfo_ismapped():
                self.confirm_entry.pack_forget()
            self.mode_hint_label.configure(
                text="[ LOGIN MODE ] Enter an existing vault master password to decrypt."
            )
            self.unlock_btn.configure(text="⟨ DECRYPT VAULT ⟩")
            self.mode_switch_btn.configure(
                text="⟨ CREATE NEW VAULT ⟩",
                state="normal",
                text_color=self.colors["cyan"],
                border_color=self.colors["cyan_dim"],
            )

    def create_new_vault(self):
        master_password = self.password_var.get().strip()
        confirm_password = self.confirm_var.get().strip()

        if not master_password:
            self._show_error("[ERR] Enter a new master key first.")
            return

        if len(master_password) < 8:
            self._show_error("[ERR] Key must be ≥ 8 characters.")
            return

        if not confirm_password:
            self._show_error("[ERR] Confirm your master key.")
            self.confirm_entry.focus_set()
            return

        if master_password != confirm_password:
            self._show_error("[ERR] Key confirmation mismatch.")
            return

        # Avoid creating duplicate vault credentials for an existing master password.
        if self.decoy_manager.identify_vault(master_password):
            self._show_error("[ERR] This master key is already linked to a vault.")
            return

        try:
            key, salt = KeyDerivation.derive_key(master_password)
            verify_hash = KeyDerivation.create_verification_hash(key)
            vault_id = DecoyVaultManager._derive_vault_id(key)

            if not self.db.vault_exists():
                self.db.create_vault(salt, verify_hash)

            self.db.add_vault_credentials(salt, verify_hash, vault_id)
            engine = EncryptionEngine(key)
            self.intruder_log.record_security_event("vault_initialized", vault_id=vault_id)
            self._stop_rain()
            self.on_login_success(
                engine,
                vault_id,
                is_decoy=False,
                vault_key=key,
                is_new_vault=True,
            )
        except Exception as e:
            self._show_error(f"[ERR] Init failed: {str(e)}")

    def _show_login_fields(self):
        """Reveal login fields after boot sequence completes."""
        self.login_frame.pack(fill="x", pady=(5, 15))

        # Glow pulse on password entry
        self.after(200, lambda: PulseAnimations.pulse_border(
            self.password_entry,
            base_color=self.colors["border"],
            glow_color=self.colors["accent"],
            duration_ms=2000, loops=2
        ))

        self.after(300, self.password_entry.focus)

    def _start_matrix_rain(self):
        """Start the matrix rain background."""
        try:
            self.update_idletasks()
            w = self.winfo_width() or 1100
            h = self.winfo_height() or 700
            self._rain_stop = MatrixRainAnimation.start_rain(
                self.rain_canvas, w, h,
                color=self.colors["accent"],
                density=20, speed_ms=60
            )
        except Exception:
            pass

    def attempt_login(self):
        # Re-check lockout every time the user submits credentials.
        if self._enforce_lockout_if_needed():
            return

        master_password = self.password_var.get().strip()

        if not master_password:
            self._show_error("[ERR] No input detected.")
            return

        if len(master_password) < 8:
            self._show_error("[ERR] Key must be ≥ 8 characters.")
            return

        # ── 1. CHECK DURESS PASSWORD ──
        if self.duress_handler.is_duress_password(master_password):
            # Silently trigger duress actions (wipe, log)
            self.duress_handler.trigger_duress(master_password)

            # Recover the decoy vault using the duress-decoy key link
            decoy_info = self.duress_handler.get_decoy_vault_from_duress(master_password)
            if decoy_info:
                self.intruder_log.record_security_event("duress_password_used")
                self._stop_rain()
                self.on_login_success(
                    decoy_info["engine"],
                    decoy_info["vault_id"],
                    is_decoy=True,
                    vault_key=decoy_info["key"],
                )
                return
            else:
                self._show_error("[ERR] Decryption failed.")
                self.password_entry.delete(0, "end")
                return

        # 2. Try All Vaults
        vault_info = self.decoy_manager.identify_vault(master_password)
        if vault_info:
            is_decoy = self._check_if_decoy(vault_info["vault_id"])
            self._handle_vault_login(vault_info, is_decoy=is_decoy)
            return

        # 3. First-Time Setup
        if not self.db.vault_exists():
            try:
                key, salt = KeyDerivation.derive_key(master_password)
                verify_hash = KeyDerivation.create_verification_hash(key)
                vault_id = DecoyVaultManager._derive_vault_id(key)
                self.db.create_vault(salt, verify_hash)
                self.db.add_vault_credentials(salt, verify_hash, vault_id)
                engine = EncryptionEngine(key)
                self.intruder_log.record_security_event("vault_initialized", vault_id=vault_id)
                self._stop_rain()
                self.on_login_success(
                    engine,
                    vault_id,
                    is_decoy=False,
                    vault_key=key,
                    is_new_vault=True,
                )
                return
            except Exception as e:
                self._show_error(f"[ERR] Init failed: {str(e)}")
                return

        # 4. Wrong Password
        self.intruder_log.record_failed_attempt()
        # Enforce lockout immediately after recording the failure.
        if self._enforce_lockout_if_needed():
            return
        self._show_error("[ACCESS DENIED] Invalid decryption key.")
        self.password_entry.delete(0, "end")

        # Glitch effect on wrong password
        GlitchAnimation.glitch_flicker(
            self.center,
            base_color="",
            glitch_color=self.colors["danger_dim"],
            duration_ms=400, flashes=4
        )

    def _handle_vault_login(self, vault_info, is_decoy=False):
        """Handle an authenticated vault, including optional OTP verification."""

        otp_settings = self.db.get_otp_settings(vault_info["vault_id"])

        if otp_settings and otp_settings.get("enabled"):
            self._show_otp_prompt(
                vault_info,
                is_decoy=is_decoy,
            )
            return

        self._complete_login(
            vault_info["engine"],
            vault_info["vault_id"],
            is_decoy=is_decoy,
            vault_key=vault_info["key"],
        )

    def _decode_otp_secret(self, secret_value: str, engine: EncryptionEngine) -> str:
        if not secret_value:
            return ""
        if secret_value.startswith("enc:"):
            try:
                encrypted_secret = bytes.fromhex(secret_value[4:])
                return engine.decrypt(encrypted_secret)
            except Exception:
                return ""
        return secret_value

    def _show_otp_prompt(self, vault_info, is_decoy=False):
        dialog = ctk.CTkToplevel(self)
        dialog.title("⟨ OTP VERIFY ⟩")
        dialog.geometry("400x260")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.colors["bg_dark"])
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="◈ ENTER 2FA CODE",
            font=("Consolas", 16, "bold"), text_color=self.colors["accent"]
        ).pack(pady=(25, 8))

        ctk.CTkLabel(
            dialog, text="This vault requires a one-time code before unlock.",
            font=("Consolas", 10), text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 15))

        otp_entry = ctk.CTkEntry(
            dialog, placeholder_text="123456",
            width=260, height=42,
            font=("Consolas", 13), corner_radius=4,
            fg_color=self.colors["bg_input"], border_color=self.colors["border"],
            text_color=self.colors["text_terminal"]
        )
        otp_entry.pack(pady=(0, 8))

        error_label = ctk.CTkLabel(
            dialog, text="", font=("Consolas", 10), text_color=self.colors["danger"]
        )
        error_label.pack(pady=(0, 8))

        def submit():
            otp_settings = self.db.get_otp_settings(vault_info["vault_id"])
            if not otp_settings or not otp_settings.get("enabled"):
                dialog.destroy()
                self._complete_login(
                    vault_info["engine"],
                    vault_info["vault_id"],
                    is_decoy=is_decoy,
                    vault_key=vault_info["key"],
                )
                return

            code = otp_entry.get().strip()
            try:
                otp_secret = self._decode_otp_secret(
                    otp_settings.get("secret", ""),
                    vault_info["engine"],
                )
                if not otp_secret:
                    error_label.configure(text="[ERR] OTP secret could not be loaded.")
                    self.intruder_log.record_security_event(
                        "otp_secret_load_failed",
                        vault_id=vault_info["vault_id"],
                    )
                    return

                manager = TOTPManager(
                    otp_secret,
                    digits=otp_settings.get("digits", 6),
                    interval=otp_settings.get("interval", 30),
                    algorithm=otp_settings.get("algorithm", "sha1"),
                )
                if manager.verify_code(code):
                    dialog.destroy()
                    self._complete_login(
                        vault_info["engine"],
                        vault_info["vault_id"],
                        is_decoy=is_decoy,
                        vault_key=vault_info["key"],
                    )
                else:
                    self.intruder_log.record_security_event(
                        "otp_failed",
                        vault_id=vault_info["vault_id"],
                    )
                    error_label.configure(text="[ERR] Code rejected. Try again.")
                    otp_entry.delete(0, "end")
                    GlitchAnimation.glitch_flicker(
                        otp_entry, base_color=self.colors["bg_input"],
                        glitch_color=self.colors["danger_dim"], duration_ms=250, flashes=2
                    )
            except Exception as exc:
                error_label.configure(text=f"[ERR] {exc}")

        otp_entry.bind("<Return>", lambda _event: submit())
        ctk.CTkButton(
            dialog, text="⟨ VERIFY ⟩",
            width=200, height=40, corner_radius=4,
            fg_color=self.colors["accent_dim"], hover_color=self.colors["accent"],
            text_color=self.colors["accent"], border_width=1, border_color=self.colors["accent"],
            font=("Consolas", 13, "bold"), command=submit
        ).pack(pady=(0, 15))
        otp_entry.focus()

    def _complete_login(self, engine, vault_id, is_decoy=False, vault_key=None):
        """Finish login and pass the authenticated vault key to the app."""

        self._stop_rain()

        self.on_login_success(
            engine,
            vault_id,
            is_decoy=is_decoy,
            vault_key=vault_key,
        )

    def _show_error(self, message: str):
        self.error_label.configure(text=message)
        NeonFlickerAnimation.flicker_text(
            self.error_label,
            text_color=self.colors["danger"],
            dim_color=self.colors["danger_dim"],
            duration_ms=800, flicker_count=3
        )

    def _check_if_decoy(self, vault_id: str) -> bool:
        all_creds = self.db.get_all_vault_credentials()
        if all_creds and len(all_creds) > 0:
            return vault_id != all_creds[0][2]
        return False

    def _stop_rain(self):
        if self._rain_stop:
            self._rain_stop()

    def destroy(self):
        self._stop_rain()
        super().destroy()

    def _enforce_lockout_if_needed(self):
        """
        Check whether the failed-attempt threshold has been reached.
        Returns True when the login interface has been locked out.
        """
        is_locked, remaining = self.intruder_log.is_locked_out()
        if not is_locked:
            return False
        self._stop_rain()
        # Remove the current login interface before displaying
        # the lockout screen.
        for widget in self.winfo_children():
            widget.destroy()
        self._show_lockout_screen(remaining)
        return True

    def _show_lockout_screen(self, remaining: float):
        center = ctk.CTkFrame(self, fg_color="", corner_radius=20)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center, text="⟨ ⛔ ⟩",
            font=("Consolas", 48, "bold"),
            text_color=self.colors["danger"]
        ).pack(pady=(30, 10))

        title = ctk.CTkLabel(
            center, text="LOCKOUT ENGAGED",
            font=("Consolas", 24, "bold"),
            text_color=self.colors["danger"]
        )
        title.pack(pady=(0, 10))
        NeonFlickerAnimation.flicker_text(
            title, text_color=self.colors["danger"],
            dim_color=self.colors["danger_dim"],
            duration_ms=2000, flicker_count=6
        )

        self.lockout_timer = ctk.CTkLabel(
            center, text="",
            font=("Consolas", 16),
            text_color=self.colors["text_secondary"]
        )
        self.lockout_timer.pack(pady=(0, 30), padx=40)
        self._update_lockout_timer(remaining)

    def _update_lockout_timer(self, remaining: float):
        if remaining <= 0:
            for widget in self.winfo_children():
                widget.destroy()
            self.__init__(
                self.master, self.colors, self.on_login_success,
                self.db, self.decoy_manager, self.duress_handler, self.intruder_log
            )
            return
        mins, secs = divmod(int(remaining), 60)
        self.lockout_timer.configure(text=f"RETRY IN {mins:02d}:{secs:02d}")
        self.after(1000, self._update_lockout_timer, remaining - 1)
           