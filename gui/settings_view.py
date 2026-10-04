"""
CYBERPUNK Settings View — Decoy vault, duress password, auto-lock,
tamper detection, intruder log.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk
from gui.animations import GlitchAnimation, NeonFlickerAnimation
from gui.components.toast_notification import ToastNotification
from core.crypto_context import CryptoContext
from core.secure_log_store import SecureLogStore
from core.secure_export import SecureExport
from core.totp_manager import TOTPManager


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, colors, stealth_mode, duress_handler,
                 decoy_manager, auto_lock_seconds, on_auto_lock_changed,
                 db=None, vault_id=None, encryption_engine=None):
        super().__init__(parent, fg_color=colors["bg_dark"])
        self.colors = colors
        self.parent_app = parent
        self.stealth_mode = stealth_mode
        self.duress_handler = duress_handler
        self.decoy_manager = decoy_manager
        self.on_auto_lock_changed = on_auto_lock_changed
        self.db = db
        self.vault_id = vault_id
        self.encryption_engine = encryption_engine

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 15))

        ctk.CTkButton(
            header, text="◄ BACK", width=80, height=32,
            fg_color=colors["border"], hover_color=colors["bg_hover"],
            corner_radius=4, font=("Consolas", 11),
            text_color=colors["text_secondary"],
            command=lambda: parent.show_vault()
        ).pack(side="left")

        title = ctk.CTkLabel(
            header, text="⟨ CONFIG ⟩",
            font=("Consolas", 22, "bold"),
            text_color=colors["accent"]
        )
        title.pack(side="left", padx=20)
        self.after(200, lambda: GlitchAnimation.glitch_text(
            title, "��� CONFIG ⟩", duration_ms=600
        ))

        # ── Scrollable Content ──
        content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors["border"]
        )
        content.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # ═══════════════════════════════════════
        #  SECTION: DECOY VAULT
        # ═══════════════════════════════════════
        self._section_header(content, "◈  DECOY VAULT")
        decoy_card = self._card(content)

        ctk.CTkLabel(
            decoy_card,
            text="Create a fake vault with dummy entries.\n"
                 "If forced to reveal your password, give the decoy password.\n"
                 "The decoy vault looks identical to a real one.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        ctk.CTkLabel(
            decoy_card, text="DECOY PASSWORD",
            font=("Consolas", 10), text_color=colors["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(5, 2))

        self.decoy_pass_entry = ctk.CTkEntry(
            decoy_card, placeholder_text="set decoy password (8+ chars)",
            height=38, corner_radius=4, show="•",
            fg_color=colors["bg_input"],
            border_color=colors["border"],
            text_color=colors["text_terminal"],
            font=("Consolas", 12)
        )
        self.decoy_pass_entry.pack(fill="x", padx=15, pady=(0, 5))

        self.decoy_status = ctk.CTkLabel(
            decoy_card, text="",
            font=("Consolas", 10), text_color=colors["text_secondary"]
        )
        self.decoy_status.pack(anchor="w", padx=15)

        ctk.CTkButton(
            decoy_card, text="◈ CREATE DECOY VAULT",
            height=36, corner_radius=4,
            fg_color=colors["accent_dim"],
            hover_color=colors["accent"],
            text_color=colors["accent"],
            border_width=1, border_color=colors["accent"],
            font=("Consolas", 11, "bold"),
            command=self._create_decoy
        ).pack(padx=15, pady=(5, 12), anchor="w")

        # ═══════════════════════════════════════
        #  SECTION: DURESS PASSWORD
        # ═══════════════════════════════════════
        self._section_header(content, "⊗  DURESS / PANIC PASSWORD")
        duress_card = self._card(content)

        ctk.CTkLabel(
            duress_card,
            text="Set a panic password that silently wipes\n"
                 "the real vault and opens the decoy instead.\n"
                 "The attacker sees a normal vault — your real data is gone.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        ctk.CTkLabel(
            duress_card, text="DURESS PASSWORD",
            font=("Consolas", 10), text_color=colors["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(5, 2))

        self.duress_entry = ctk.CTkEntry(
            duress_card, placeholder_text="set panic password (8+ chars)",
            height=38, corner_radius=4, show="•",
            fg_color=colors["bg_input"],
            border_color=colors["border"],
            text_color=colors["text_terminal"],
            font=("Consolas", 12)
        )
        self.duress_entry.pack(fill="x", padx=15, pady=(0, 5))

        self.duress_status = ctk.CTkLabel(
            duress_card, text="",
            font=("Consolas", 10), text_color=colors["text_secondary"]
        )
        self.duress_status.pack(anchor="w", padx=15)

        ctk.CTkButton(
            duress_card, text="⊗ SET DURESS PASSWORD",
            height=36, corner_radius=4,
            fg_color=colors["danger_dim"],
            hover_color=colors["danger"],
            text_color=colors["danger"],
            border_width=1, border_color=colors["danger"],
            font=("Consolas", 11, "bold"),
            command=self._set_duress
        ).pack(padx=15, pady=(5, 12), anchor="w")

        # ═══════════════════════════════════════
        #  SECTION: STEALTH MODE
        # ═══════════════════════════════════════
        self._section_header(content, "◈  STEALTH MODE")
        stealth_card = self._card(content)

        ctk.CTkLabel(
            stealth_card,
            text="Disguise SecureVault as another application.\n"
                 "Double-click the disguise to return to vault.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        stealth_btns = ctk.CTkFrame(stealth_card, fg_color="transparent")
        stealth_btns.pack(fill="x", padx=15, pady=(0, 12))

        disguises = [
            ("◈ CALCULATOR", "calculator"),
            ("◈ NOTEPAD", "notepad"),
            ("◈ SYS MONITOR", "system_monitor"),
            ("◈ FILE MANAGER", "file_manager"),
        ]

        for text, disguise in disguises:
            ctk.CTkButton(
                stealth_btns, text=text,
                width=130, height=34, corner_radius=4,
                fg_color=colors["border"],
                hover_color=colors["cyan_dim"],
                text_color=colors["cyan"],
                font=("Consolas", 10, "bold"),
                command=lambda d=disguise: self.stealth_mode.activate(d)
            ).pack(side="left", padx=(0, 8))

        # ═══════════════════════════════════════
        #  SECTION: AUTO-LOCK
        # ═══════════════════════════════════════
        self._section_header(content, "◈  AUTO-LOCK")
        lock_card = self._card(content)

        ctk.CTkLabel(
            lock_card, text="Lock vault after inactivity (seconds):",
            font=("Consolas", 10), text_color=colors["text_secondary"]
        ).pack(anchor="w", padx=15, pady=(12, 5))

        lock_frame = ctk.CTkFrame(lock_card, fg_color="transparent")
        lock_frame.pack(fill="x", padx=15, pady=(0, 12))

        self.lock_var = ctk.IntVar(value=auto_lock_seconds)
        self.lock_label = ctk.CTkLabel(
            lock_frame, text=f"{auto_lock_seconds}s",
            font=("Consolas", 13, "bold"),
            text_color=colors["accent"], width=60
        )
        self.lock_label.pack(side="right")

        ctk.CTkSlider(
            lock_frame, from_=30, to=900,
            variable=self.lock_var,
            command=self._on_lock_change,
            button_color=colors["accent"],
            button_hover_color=colors["accent"],
            progress_color=colors["accent"],
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        # ═══════════════════════════════════════
        #  SECTION: TOTP / OTP
        # ═══════════════════════════════════════
        self._section_header(content, "◈  TOTP / OTP")
        otp_card = self._card(content)

        ctk.CTkLabel(
            otp_card,
            text="Require a time-based one-time password during vault unlock.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        self.otp_status_label = ctk.CTkLabel(
            otp_card, text=self._format_otp_status(),
            font=("Consolas", 10, "bold"), text_color=colors["text_terminal"]
        )
        self.otp_status_label.pack(anchor="w", padx=15, pady=(0, 6))

        self.otp_secret_entry = ctk.CTkEntry(
            otp_card, placeholder_text="leave blank to auto-generate a secret",
            height=38, corner_radius=4,
            fg_color=colors["bg_input"], border_color=colors["border"],
            text_color=colors["text_terminal"], font=("Consolas", 12)
        )
        self.otp_secret_entry.pack(fill="x", padx=15, pady=(0, 8))

        otp_btns = ctk.CTkFrame(otp_card, fg_color="transparent")
        otp_btns.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkButton(
            otp_btns, text="◈ ENABLE TOTP",
            height=36, corner_radius=4,
            fg_color=colors["accent_dim"], hover_color=colors["accent"],
            text_color=colors["accent"], border_width=1, border_color=colors["accent"],
            font=("Consolas", 11, "bold"), command=self._enable_otp
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            otp_btns, text="⊗ DISABLE",
            height=36, corner_radius=4,
            fg_color=colors["border"], hover_color=colors["bg_hover"],
            text_color=colors["text_secondary"], font=("Consolas", 11, "bold"),
            command=self._disable_otp
        ).pack(side="left")

        # ═══════════════════════════════════════
        #  SECTION: AUDIT LOG
        # ═══════════════════════════════════════
        self._section_header(content, "◈  AUDIT LOG")
        audit_card = self._card(content)

        ctk.CTkLabel(
            audit_card,
            text="Audit logs track login attempts, vault access, and security events.\n"
                 "Recent activity is summarized below.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        self.audit_summary_label = ctk.CTkLabel(
            audit_card,
            text=self._format_audit_summary(),
            font=("Consolas", 10, "bold"),
            text_color=colors["text_terminal"],
            justify="left"
        )
        self.audit_summary_label.pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkButton(
            audit_card, text="⟨ REFRESH AUDIT SUMMARY ⟩",
            height=36, corner_radius=4,
            fg_color=colors["border"],
            hover_color=colors["bg_hover"],
            text_color=colors["text_primary"],
            font=("Consolas", 11, "bold"),
            command=self._refresh_audit_summary
        ).pack(padx=15, pady=(0, 12), anchor="w")

        ctk.CTkButton(
            audit_card, text="◈ VIEW LOGS",
            height=36, corner_radius=4,
            fg_color=colors["accent_dim"],
            hover_color=colors["accent"],
            text_color=colors["accent"],
            border_width=1, border_color=colors["accent"],
            font=("Consolas", 11, "bold"),
            command=self._open_log_viewer
        ).pack(padx=15, pady=(0, 12), anchor="w")

        # ═══════════════════════════════════════
        #  SECTION: INTEGRITY CHECK
        # ═══════════════════════════════════════
        self._section_header(content, "◈  INTEGRITY CHECK")
        integrity_card = self._card(content)

        ctk.CTkLabel(
            integrity_card,
            text="Run a manual integrity check against the last saved vault baseline.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 8))

        self.integrity_status_label = ctk.CTkLabel(
            integrity_card,
            text="[INTEGRITY CHECK NOT RUN]",
            font=("Consolas", 10, "bold"),
            text_color=colors["text_terminal"],
            justify="left"
        )
        self.integrity_status_label.pack(anchor="w", padx=15, pady=(0, 10))

        ctk.CTkButton(
            integrity_card, text="◈ CHECK INTEGRITY",
            height=36, corner_radius=4,
            fg_color=colors["cyan_dim"],
            hover_color=colors["cyan"],
            text_color=colors["cyan"],
            border_width=1, border_color=colors["cyan"],
            font=("Consolas", 11, "bold"),
            command=self._check_integrity
        ).pack(padx=15, pady=(0, 12), anchor="w")

        # ═══════════════════════════════════════
        #  SECTION: EXPORT / DEMO
        # ═══════════════════════════════════════
        self._section_header(content, "◈  EXPORT / DEMO")
        export_card = self._card(content)

        ctk.CTkLabel(
            export_card,
            text="Create an encrypted .svault backup using a separate export password.\n"
                 "After export, you can open the file or its folder to demonstrate the result.",
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 10))

        self.export_status_label = ctk.CTkLabel(
            export_card,
            text="[NO EXPORT CREATED YET]",
            font=("Consolas", 10, "bold"),
            text_color=colors["text_terminal"],
            justify="left"
        )
        self.export_status_label.pack(anchor="w", padx=15, pady=(0, 10))

        export_btns = ctk.CTkFrame(export_card, fg_color="transparent")
        export_btns.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkButton(
            export_btns, text="◈ EXPORT VAULT",
            height=36, corner_radius=4,
            fg_color=colors["accent_dim"],
            hover_color=colors["accent"],
            text_color=colors["accent"],
            border_width=1, border_color=colors["accent"],
            font=("Consolas", 11, "bold"),
            command=self._export_vault
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            export_btns, text="⟲ IMPORT BACKUP",
            height=36, corner_radius=4,
            fg_color=colors["cyan_dim"],
            hover_color=colors["cyan"],
            text_color=colors["cyan"],
            border_width=1, border_color=colors["cyan"],
            font=("Consolas", 11, "bold"),
            command=self._import_vault_backup
        ).pack(side="left")

        # ═══════════════════════════════════════
        #  SECTION: THREAT MODEL
        # ═══════════════════════════════════════
        self._section_header(content, "◈  THREAT MODEL")
        threat_card = self._card(content)

        threat_text = (
            "Attack scenarios:\n"
            "• Brute-force login attempts are slowed by lockout and visible failed-attempt logging.\n"
            "• Coercion is handled by a duress password that opens a decoy vault and wipes the real one.\n"
            "• Offline database theft is limited by AES-256-GCM encryption and Argon2id key derivation.\n"
            "• Tampering is detected through integrity baselines and security warnings.\n"
            "• Secret-protected entries require an additional per-password secret before reveal or copy.\n\n"
            "Defense summary:\n"
            "SecureVault logs these events so suspicious behavior can be reviewed after the fact."
        )

        ctk.CTkLabel(
            threat_card,
            text=threat_text,
            font=("Consolas", 10), text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=15, pady=(12, 12))

        self._last_export_path = None

    # ─────────────────────────────────────────────
    #  UI HELPERS
    # ─────────────────────────────────────────────

    def _section_header(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=("Consolas", 14, "bold"),
            text_color=self.colors["accent"]
        ).pack(anchor="w", pady=(20, 5))

    def _card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.colors["bg_card"],
            corner_radius=6, border_width=1,
            border_color=self.colors["border"]
        )
        card.pack(fill="x", pady=(0, 5))
        return card

    # ─────────────────────────────────────────────
    #  DECOY VAULT
    # ─────────────────────────────────────────────

    def _create_decoy(self):
        password = self.decoy_pass_entry.get()
        if not password or len(password) < 8:
            self.decoy_status.configure(
                text="[ERR] Password must be 8+ characters.",
                text_color=self.colors["danger"]
            )
            return

        # Generate fake entries
        fake_entries = [
            {"service": "Gmail", "username": "john.doe@gmail.com",
             "password": "MyGmail2024!", "url": "https://gmail.com"},
            {"service": "Netflix", "username": "johndoe",
             "password": "NetflixPass1!", "url": "https://netflix.com"},
            {"service": "Amazon", "username": "john.doe@email.com",
             "password": "Shop@mazon99", "url": "https://amazon.com"},
            {"service": "Facebook", "username": "johndoe42",
             "password": "Fb_Secure#21", "url": "https://facebook.com"},
            {"service": "Bank of America", "username": "jdoe_banking",
             "password": "B0A_mybank!", "url": "https://bankofamerica.com"},
        ]

        try:
            result = self.decoy_manager.create_decoy_vault(password, fake_entries)
            self.decoy_status.configure(
                text="✓ DECOY VAULT CREATED — Now set a duress password below!",
                text_color=self.colors["accent"]
            )
            self.decoy_pass_entry.delete(0, "end")
            ToastNotification.show(self, "◈ DECOY VAULT CREATED", "success")
        except Exception as e:
            self.decoy_status.configure(
                text=f"[ERR] {e}",
                text_color=self.colors["danger"]
            )

    # ─────────────────────────────────────────────
    #  DURESS PASSWORD
    # ─────────────────────────────────────────────

    def _set_duress(self):
        password = self.duress_entry.get()
        if not password or len(password) < 8:
            self.duress_status.configure(
                text="[ERR] Password must be 8+ characters.",
                text_color=self.colors["danger"]
            )
            return

        # Get the decoy key from the decoy manager (must create decoy first!)
        decoy_key = self.decoy_manager._last_decoy_key
        decoy_vault_id = self.decoy_manager._last_decoy_vault_id

        if decoy_key is None or decoy_vault_id is None:
            self.duress_status.configure(
                text="[ERR] Create a decoy vault FIRST (above), then set duress.",
                text_color=self.colors["danger"]
            )
            return

        linked = self.duress_handler.set_duress_password(
            password,
            decoy_key=decoy_key,
            decoy_vault_id=decoy_vault_id
        )

        if linked:
            self.duress_entry.delete(0, "end")
            self.duress_status.configure(
                text="✓ DURESS PASSWORD SET & LINKED TO DECOY",
                text_color=self.colors["accent"]
            )
            ToastNotification.show(self, "⊗ DURESS PASSWORD ACTIVE", "warning")
        else:
            self.duress_status.configure(
                text="[ERR] Failed to link duress to decoy.",
                text_color=self.colors["danger"]
            )

    # ─────────────────────────────────────────────
    #  AUTO-LOCK
    # ───���─────────────────────────────────────────

    def _on_lock_change(self, value):
        val = int(value)
        self.lock_label.configure(text=f"{val}s")
        self.on_auto_lock_changed(val)

    def _format_otp_status(self):
        if not self.db or not self.vault_id:
            return "[OTP UNAVAILABLE]"
        settings = self.db.get_otp_settings(self.vault_id)
        if not settings or not settings.get("enabled"):
            return "[OTP DISABLED]"
        return f"[OTP ENABLED] Secret configured for vault {self.vault_id[:8]}"

    def _enable_otp(self):
        if not self.db or not self.vault_id or not self.encryption_engine:
            self.otp_status_label.configure(text="[OTP UNAVAILABLE]", text_color=self.colors["danger"])
            return

        secret = self.otp_secret_entry.get().strip().replace(" ", "")
        if not secret:
            secret = TOTPManager.generate_secret()
            self.otp_secret_entry.delete(0, "end")
            self.otp_secret_entry.insert(0, secret)

        try:
            TOTPManager(secret)
        except Exception as exc:
            self.otp_status_label.configure(text=f"[ERR] {exc}", text_color=self.colors["danger"])
            return

        encrypted_secret = f"enc:{self.encryption_engine.encrypt(secret).hex()}"

        self.db.set_otp_settings(
            self.vault_id,
            enabled=True,
            secret=encrypted_secret,
            issuer="SecureVault",
            digits=6,
            interval=30,
            algorithm="sha1",
        )
        self.otp_status_label.configure(text="[OTP ENABLED] Vault unlock now requires a code.", text_color=self.colors["accent"])
        ToastNotification.show(self, "◈ TOTP ENABLED", "success")

    def _disable_otp(self):
        if not self.db or not self.vault_id:
            self.otp_status_label.configure(text="[OTP UNAVAILABLE]", text_color=self.colors["danger"])
            return
        self.db.disable_otp(self.vault_id)
        self.otp_status_label.configure(text="[OTP DISABLED]", text_color=self.colors["text_secondary"])
        ToastNotification.show(self, "⊗ TOTP DISABLED", "warning")

    def _format_audit_summary(self):
        log = self.parent_app.intruder_log
        summary = log.get_recent_summary(within_seconds=86400)
        if not summary:
            return "[NO AUDIT EVENTS RECORDED IN THE LAST 24 HOURS]"
        lines = ["[LAST 24 HOURS]"]
        for key in sorted(summary.keys()):
            lines.append(f"{key}: {summary[key]}")
        return "\n".join(lines)

    def _refresh_audit_summary(self):
        self.audit_summary_label.configure(text=self._format_audit_summary())
        ToastNotification.show(self, "◈ AUDIT SUMMARY UPDATED", "success")

    def _open_log_viewer(self):
        viewer = ctk.CTkToplevel(self)
        viewer.title("⟨ LOG VIEWER ⟩")
        viewer.geometry("860x620")
        viewer.minsize(760, 520)
        viewer.configure(fg_color=self.colors["bg_dark"])
        viewer.transient(self)

        header = ctk.CTkFrame(viewer, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 10))

        ctk.CTkLabel(
            header,
            text="◈ ENCRYPTED LOG VIEWER",
            font=("Consolas", 18, "bold"),
            text_color=self.colors["accent"],
        ).pack(side="left")

        export_btn = ctk.CTkButton(
            header,
            text="EXPORT DECRYPTED",
            width=150,
            height=32,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            border_width=1,
            border_color=self.colors["accent"],
            font=("Consolas", 10, "bold"),
        )
        export_btn.pack(side="right")

        log_info = ctk.CTkLabel(
            viewer,
            text=(
                f"Audit log: {self.parent_app.intruder_log.LOG_PATH}\n"
                f"Duress log: {self.duress_handler.DURESS_LOG}\n"
                f"Log key: {SecureLogStore.KEY_PATH}"
            ),
            font=("Consolas", 10),
            text_color=self.colors["text_secondary"],
            justify="left",
        )
        log_info.pack(anchor="w", padx=20, pady=(0, 10))

        selector = ctk.CTkFrame(viewer, fg_color="transparent")
        selector.pack(fill="x", padx=20, pady=(0, 10))

        audit_btn = ctk.CTkButton(
            selector,
            text="AUDIT LOG",
            width=130,
            height=34,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            border_width=1,
            border_color=self.colors["accent"],
            font=("Consolas", 10, "bold"),
        )
        audit_btn.pack(side="left", padx=(0, 8))

        duress_btn = ctk.CTkButton(
            selector,
            text="DURESS LOG",
            width=130,
            height=34,
            fg_color=self.colors["cyan_dim"],
            hover_color=self.colors["cyan"],
            text_color=self.colors["cyan"],
            border_width=1,
            border_color=self.colors["cyan"],
            font=("Consolas", 10, "bold"),
        )
        duress_btn.pack(side="left")

        text_box = ctk.CTkTextbox(
            viewer,
            font=("Consolas", 11),
            fg_color=self.colors["bg_input"],
            text_color=self.colors["text_primary"],
            border_color=self.colors["border"],
            border_width=1,
            corner_radius=8,
            wrap="word",
        )
        text_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        store = SecureLogStore()
        current_state = {"path": self.parent_app.intruder_log.LOG_PATH, "title": "AUDIT LOG", "entries": []}

        def export_current_view():
            default_name = f"securevault-{current_state['title'].lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            filepath = filedialog.asksaveasfilename(
                parent=viewer,
                title="Save Decrypted Log",
                initialdir=str(Path.home()),
                initialfile=default_name,
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*")],
            )
            if not filepath:
                return

            try:
                lines = [f"{current_state['title']}", "=" * len(current_state["title"]), ""]
                for index, entry in enumerate(current_state["entries"], start=1):
                    lines.append(f"{index}. {entry}")
                    lines.append("")
                Path(filepath).write_text("\n".join(lines), encoding="utf-8")
                ToastNotification.show(self, "◈ LOG EXPORTED", "success")
            except Exception as exc:
                ToastNotification.show(self, f"[ERR] {type(exc).__name__}: {exc}", "error")

        def render_log(log_path, title):
            entries = store.read_json(log_path)
            current_state["path"] = log_path
            current_state["title"] = title
            current_state["entries"] = entries
            text_box.configure(state="normal")
            text_box.delete("1.0", "end")
            text_box.insert("end", f"{title}\n{'=' * len(title)}\n\n")
            if not entries:
                text_box.insert("end", "No entries found.\n")
            else:
                for index, entry in enumerate(entries, start=1):
                    text_box.insert("end", f"{index}. {entry}\n\n")
            text_box.configure(state="disabled")

        audit_btn.configure(command=lambda: render_log(self.parent_app.intruder_log.LOG_PATH, "AUDIT LOG"))
        duress_btn.configure(command=lambda: render_log(self.duress_handler.DURESS_LOG, "DURESS LOG"))
        export_btn.configure(command=export_current_view)

        render_log(self.parent_app.intruder_log.LOG_PATH, "AUDIT LOG")

    def _check_integrity(self):
        result = self.parent_app._check_tamper()
        if not result:
            self.integrity_status_label.configure(
                text="[ERR] Integrity check unavailable.",
                text_color=self.colors["danger"]
            )
            return

        warnings = result.get("warnings", [])
        if result.get("intact", True) and not warnings:
            self.integrity_status_label.configure(
                text="[OK] Vault integrity matches the current baseline.",
                text_color=self.colors["accent"]
            )
            ToastNotification.show(self, "◈ INTEGRITY OK", "success")
            return

        if warnings == ["No integrity baseline found"]:
            self.integrity_status_label.configure(
                text="[INFO] No baseline exists yet. It will be created after a successful unlock.",
                text_color=self.colors["text_secondary"]
            )
            return

        self.integrity_status_label.configure(
            text="[WARN] " + " | ".join(warnings[:3]),
            text_color=self.colors["danger"]
        )

    def _build_export_entries(self):
        """
        Build export records while supporting legacy and context-bound
        ciphertext without breaking per-password protection.
        """
        if (
            not self.db
            or not self.vault_id
            or not self.encryption_engine
        ):
            raise ValueError(
                "Vault export is unavailable right now."
            )

        exported_entries = []
        for raw in self.db.get_entries_by_vault(
            self.vault_id
        ):
            entry_uuid = raw.get("entry_uuid")
            if not entry_uuid:
                raise ValueError(
                    "Entry is missing its UUID and cannot be exported safely."
                )

            def decrypt_field(field_name, value):
                if not value:
                    return ""
                if not isinstance(value, bytes):
                    raise TypeError(
                        f"{field_name} ciphertext must be bytes"
                    )
                if value.startswith(self.encryption_engine.V2_PREFIX):
                    aad = CryptoContext.entry(
                        self.vault_id,
                        entry_uuid,
                        field_name,
                    )
                    return self.encryption_engine.decrypt(
                        value,
                        aad=aad,
                    )
                return self.encryption_engine.decrypt(value)

            per_pass_salt = raw.get("per_pass_salt")
            per_pass_hash = raw.get("per_pass_hash")
            is_password_protected = per_pass_salt is not None

            if is_password_protected:
                encrypted_password = raw["password"]
                if isinstance(encrypted_password, memoryview):
                    encrypted_password = encrypted_password.tobytes()
                if not isinstance(encrypted_password, bytes):
                    raise ValueError(
                        "Protected password ciphertext has an invalid format."
                    )
                password_value = encrypted_password
            else:
                password_value = decrypt_field(
                    "password",
                    raw["password"],
                )

            exported_entries.append({
                "entry_uuid": entry_uuid,
                "service": decrypt_field("service", raw["service"]),
                "username": decrypt_field("username", raw["username"]),
                "password": password_value,
                "url": decrypt_field("url", raw.get("url")),
                "notes": decrypt_field("notes", raw.get("notes")),
                "category": raw.get("category", "password"),
                "favorite": raw.get("favorite", 0),
                "per_pass_salt": per_pass_salt,
                "per_pass_hash": per_pass_hash,
                "per_pass_version": raw.get("per_pass_version", 1),
                "password_protected": is_password_protected,
            })
        return exported_entries

    def _export_vault(self):
        if not self.db or not self.vault_id or not self.encryption_engine:
            self.export_status_label.configure(
                text="[ERR] Unlock a vault before exporting.",
                text_color=self.colors["danger"]
            )
            return

        export_password = simpledialog.askstring(
            "Export Vault",
            "Enter a separate password to encrypt the export:",
            show="*",
            parent=self,
        )
        if not export_password:
            return

        default_dir = Path.home() / ".securevault" / "exports"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_name = f"securevault-{self.vault_id[:8]}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.svault"
        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Save SecureVault Export",
            initialdir=str(default_dir),
            initialfile=default_name,
            defaultextension=".svault",
            filetypes=[("SecureVault Export", "*.svault"), ("All Files", "*")],
        )
        if not filepath:
            return

        try:
            result = SecureExport.export_vault(
                self._build_export_entries(),
                export_password,
                filepath,
            )
            self._last_export_path = result["filepath"]
            self.export_status_label.configure(
                text=f"[EXPORTED] {self._last_export_path}",
                text_color=self.colors["accent"]
            )
            ToastNotification.show(self, "◈ VAULT EXPORTED", "success")
        except Exception as exc:
            error_text = f"[ERR] {type(exc).__name__}: {exc}" if str(exc) else f"[ERR] {type(exc).__name__}"
            self.export_status_label.configure(
                text=error_text,
                text_color=self.colors["danger"]
            )

    def _restore_field(self, value):
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")
        return str(value)

    def _import_vault_backup(self):
        if not self.db or not self.vault_id or not self.encryption_engine:
            self.export_status_label.configure(
                text="[ERR] Unlock a vault before importing.",
                text_color=self.colors["danger"]
            )
            return

        filepath = filedialog.askopenfilename(
            parent=self,
            title="Open SecureVault Backup",
            initialdir=str(Path.home() / ".securevault" / "exports"),
            filetypes=[("SecureVault Export", "*.svault"), ("All Files", "*")],
        )
        if not filepath:
            return

        import_password = simpledialog.askstring(
            "Import Backup",
            "Enter the backup password to decrypt the export:",
            show="*",
            parent=self,
        )
        if not import_password:
            return

        try:
            imported_entries = SecureExport.import_vault(filepath, import_password)
            if not imported_entries:
                self.export_status_label.configure(
                    text="[ERR] No entries found in backup.",
                    text_color=self.colors["danger"]
                )
                return

            if not messagebox.askyesno(
                "Restore Backup",
                f"Import {len(imported_entries)} entries into the current vault?",
                parent=self,
            ):
                return

            restored = 0
            for entry in imported_entries:
                is_password_protected = bool(
                    entry.get("password_protected", False)
                    or entry.get("per_pass_salt") is not None
                )

                # Metadata is always protected by the current vault key.
                service = self.encryption_engine.encrypt(
                    self._restore_field(entry.get("service"))
                )
                username = self.encryption_engine.encrypt(
                    self._restore_field(entry.get("username"))
                )
                url = (
                    self.encryption_engine.encrypt(
                        self._restore_field(entry.get("url"))
                    )
                    if entry.get("url")
                    else None
                )
                notes = (
                    self.encryption_engine.encrypt(
                        self._restore_field(entry.get("notes"))
                    )
                    if entry.get("notes")
                    else None
                )

                if is_password_protected:
                    # The password is already encrypted with its own
                    # per-password key. Preserve the ciphertext exactly.
                    password = entry.get("password")
                    if isinstance(password, memoryview):
                        password = password.tobytes()
                    if not isinstance(password, bytes):
                        raise ValueError(
                            "Protected password ciphertext has an invalid format."
                        )
                else:
                    password = self.encryption_engine.encrypt(
                        self._restore_field(entry.get("password"))
                    )

                # ---------------------------------------------------------
                # Validate cryptographic identity before restoring.
                # ---------------------------------------------------------
                entry_uuid = entry.get("entry_uuid")
                per_pass_version = entry.get(
                    "per_pass_version",
                    1,
                )
                password_protected = bool(
                    entry.get("password_protected", False)
                    or entry.get("per_pass_salt") is not None
                )
                if password_protected and per_pass_version >= 2:
                    if not entry_uuid:
                        raise ValueError(
                            "V2 protected entry is missing its entry UUID."
                        )
                    try:
                        uuid.UUID(str(entry_uuid))
                    except (ValueError, TypeError, AttributeError) as exc:
                        raise ValueError(
                            "V2 protected entry contains an invalid UUID."
                        ) from exc
                    existing_entry = self.db.conn.execute(
                        """
                        SELECT id
                        FROM entries
                        WHERE entry_uuid = ?
                        """,
                        (entry_uuid,),
                    ).fetchone()
                    if existing_entry:
                        raise ValueError(
                            "V2 protected entry UUID already exists."
                        )

                self.db.add_entry(
                    service=service,
                    username=username,
                    password=password,
                    url=url,
                    notes=notes,
                    category=entry.get("category", "password"),
                    vault_id=self.vault_id,
                    per_pass_salt=entry.get("per_pass_salt"),
                    per_pass_hash=entry.get("per_pass_hash"),
                    entry_uuid=entry.get("entry_uuid"),
                    per_pass_version=entry.get(
                        "per_pass_version",
                        1,
                    ),
                )
                restored += 1

            self.export_status_label.configure(
                text=f"[IMPORTED] {restored} entries restored into vault {self.vault_id[:8]}",
                text_color=self.colors["accent"]
            )
            ToastNotification.show(self, "◈ BACKUP RESTORED", "success")
            try:
                self.parent_app.show_vault()
            except Exception:
                pass
        except Exception as exc:
            error_text = f"[ERR] {type(exc).__name__}: {exc}" if str(exc) else f"[ERR] {type(exc).__name__}"
            self.export_status_label.configure(
                text=error_text,
                text_color=self.colors["danger"]
            )

    def _open_last_export(self):
        if not self._last_export_path:
            self.export_status_label.configure(
                text="[ERR] Export the vault first.",
                text_color=self.colors["danger"]
            )
            return

        export_path = Path(self._last_export_path)
        if not export_path.exists():
            self.export_status_label.configure(
                text="[ERR] Last export file no longer exists.",
                text_color=self.colors["danger"]
            )
            return

        try:
            os.startfile(str(export_path))
        except OSError:
            os.startfile(str(export_path.parent))
