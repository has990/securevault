"""
CYBERPUNK Vault View — Neon cards, glitch animations on add,
hologram scan effects, terminal-style search.
"""
import base64
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from gui.add_entry_dialog import AddEntryDialog
from gui.animations import (
    FadeAnimations, BounceAnimations, PulseAnimations,
    GlitchAnimation, NeonFlickerAnimation, HologramAnimation,
)
from core.clipboard import ClipboardManager
from core.crypto_context import CryptoContext
from core.per_password_lock import PerPasswordLock


class VaultView(ctk.CTkFrame):
    def __init__(self, parent, colors, encryption_engine, vault_id,
                 is_decoy, per_password_lock, db):
        super().__init__(parent, fg_color=colors["bg_dark"])
        self.colors = colors
        self.engine = encryption_engine
        self.vault_id = vault_id
        self.is_decoy = is_decoy
        self.ppl = per_password_lock
        self.db = db
        self.parent_app = parent
        self._card_widgets = []

        # ── SIDEBAR ──
        sidebar = ctk.CTkFrame(self, width=230, fg_color=colors["bg_sidebar"],
                                corner_radius=0, border_width=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Neon header
        header_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        header_frame.pack(pady=(20, 5), padx=15, anchor="w")

        header = ctk.CTkLabel(
            header_frame, text="⟨ VAULT ⟩",
            font=("Consolas", 18, "bold"),
            text_color=colors["accent"]
        )
        header.pack(anchor="w")

        # Glitch the header on load
        self.after(300, lambda: GlitchAnimation.glitch_text(
            header, "⟨ VAULT ⟩", duration_ms=600
        ))

        # Status line
        entry_count = self.db.get_entry_count(vault_id)
        status = "DECOY" if is_decoy else "SECURE"
        ctk.CTkLabel(
            sidebar,
            text=f"[{status}] {entry_count} entries",
            font=("Consolas", 9),
            text_color=colors["text_secondary"]
        ).pack(padx=15, anchor="w", pady=(0, 20))

        # Separator line
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=colors["border"])
        sep.pack(fill="x", padx=15, pady=(0, 10))

        # Navigation
        nav_items = [
            ("◈  ALL ITEMS",       self.show_all),
            ("★  FAVORITES",       self.show_favorites),
            ("◆  PASSWORDS",       self.show_passwords),
            ("◇  CARDS",           self.show_cards),
            ("◈  NOTES",           self.show_notes),
            ("⚡ GENERATOR",       lambda: self.parent_app.show_generator()),
            ("◈  2FA / TOTP",      lambda: self.parent_app.show_totp()),
            ("⊕  SEC SCORE",       lambda: self.parent_app.show_security_dashboard()),
            ("⊞  CONFIG",          lambda: self.parent_app.show_settings()),
        ]

        self._nav_buttons = []
        for i, (text, command) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar, text=text, anchor="w",
                font=("Consolas", 12), height=38,
                fg_color="transparent",
                hover_color=colors["bg_hover"],
                text_color=colors["text_secondary"],
                corner_radius=4,
                command=command
            )
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_buttons.append(btn)

        # Bottom buttons
        ctk.CTkButton(
            sidebar, text="◈ STEALTH",
            font=("Consolas", 11),
            fg_color=colors["border"],
            hover_color=colors["cyan_dim"],
            text_color=colors["cyan"],
            height=34, corner_radius=4,
            command=lambda: self.parent_app.toggle_stealth()
        ).pack(side="bottom", fill="x", padx=12, pady=(0, 8))

        ctk.CTkButton(
            sidebar, text="⊗ LOCK",
            font=("Consolas", 11, "bold"),
            fg_color=colors["danger_dim"],
            hover_color=colors["danger"],
            text_color=colors["danger"],
            height=34, corner_radius=4,
            command=self.lock_vault
        ).pack(side="bottom", fill="x", padx=12, pady=(0, 5))

        # ── MAIN CONTENT ──
        main = ctk.CTkFrame(self, fg_color=colors["bg_dark"])
        main.pack(side="right", fill="both", expand=True)

        # Top bar
        topbar = ctk.CTkFrame(main, fg_color="transparent", height=65)
        topbar.pack(fill="x", padx=25, pady=(15, 8))
        topbar.pack_propagate(False)

        # Terminal-style search
        search_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        search_frame.pack(side="left", fill="y")

        ctk.CTkLabel(
            search_frame, text="grep:",
            font=("Consolas", 13),
            text_color=colors["text_terminal"]
        ).pack(side="left", padx=(0, 5))

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="search_vault >>",
            width=350, height=40,
            font=("Consolas", 13),
            corner_radius=4,
            border_color=colors["border"],
            border_width=1,
            fg_color=colors["bg_input"],
            text_color=colors["text_terminal"],
            placeholder_text_color=colors["text_dim"],
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Add button — neon style
        self.add_btn = ctk.CTkButton(
            topbar, text="+ NEW ENTRY",
            font=("Consolas", 13, "bold"),
            width=150, height=40,
            corner_radius=4,
            fg_color=colors["accent_dim"],
            hover_color=colors["accent"],
            text_color=colors["accent"],
            border_width=1,
            border_color=colors["accent"],
            command=self.add_new_entry
        )
        self.add_btn.pack(side="right")

        # Scrollable cards area
        self.cards_frame = ctk.CTkScrollableFrame(
            main, fg_color="transparent",
            scrollbar_button_color=colors["border"]
        )
        self.cards_frame.pack(fill="both", expand=True, padx=25, pady=(5, 15))

        # Load entries
        self.after(200, self.load_entries)
        self.parent_app.intruder_log.record_vault_access(
            "open_vault",
            vault_id=self.vault_id,
        )

    # ─────────────────────────────────────────────
    #  ENTRY LOADING
    # ─────────────────────────────────────────────

    def load_entries(self, filter_text: str = None, category: str = None):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        self._card_widgets = []

        raw_entries = self.db.get_entries_by_vault(self.vault_id)

        for raw in raw_entries:
            try:
                entry = self._decrypt_entry(raw)
            except Exception:
                continue

            if filter_text:
                sl = filter_text.lower()
                if (sl not in entry.get("service", "").lower()
                        and sl not in entry.get("username", "").lower()):
                    continue

            if category and entry.get("category", "password") != category:
                continue

            card = self._create_cyber_card(entry, raw["id"])
            self._card_widgets.append(card)

        if not self._card_widgets:
            empty = ctk.CTkLabel(
                self.cards_frame,
                text="[ NO ENTRIES FOUND ]\n\nPress + NEW ENTRY to initialize",
                font=("Consolas", 14),
                text_color=self.colors["text_secondary"],
                justify="center"
            )
            empty.pack(expand=True, pady=50)
            return

        # Staggered cyber reveal
        for i, card in enumerate(self._card_widgets):
            card.configure(fg_color=self.colors["bg_dark"])
            def reveal(c, idx):
                def do_it():
                    FadeAnimations.fade_in_widget(
                        c, duration_ms=300,
                        start_color=self.colors["bg_dark"],
                        end_color=self.colors["bg_card"]
                    )
                    HologramAnimation.scan_reveal(c, duration_ms=400,
                                                   scan_color=self.colors["accent"])
                self.after(idx * 100, do_it)
            reveal(card, i)

    def _decrypt_entry(self, raw: dict) -> dict:
        """
        Decrypt entry metadata while supporting legacy and context-bound
        ciphertext. Password ciphertext is retained for explicit reveal/copy.
        """
        entry_uuid = raw.get("entry_uuid")

        def decrypt_field(field_name, value):
            if not value:
                return ""
            if not isinstance(value, bytes):
                raise TypeError(
                    f"{field_name} ciphertext must be bytes"
                )
            if value.startswith(self.engine.V2_PREFIX):
                if not entry_uuid:
                    raise ValueError(
                        f"V2 {field_name} is missing its entry UUID"
                    )
                aad = CryptoContext.entry(
                    self.vault_id,
                    entry_uuid,
                    field_name,
                )
                return self.engine.decrypt(value, aad=aad)
            return self.engine.decrypt(value)

        return {
            "service": decrypt_field("service", raw["service"]),
            "username": decrypt_field("username", raw["username"]),
            "url": decrypt_field("url", raw.get("url")),
            "notes": decrypt_field("notes", raw.get("notes")),
            "category": raw.get("category", "password"),
            "favorite": raw.get("favorite", 0),
            "_raw_password": raw["password"],
            "_entry_uuid": raw.get("entry_uuid"),
            "_per_pass_salt": raw.get("per_pass_salt"),
            "_per_pass_hash": raw.get("per_pass_hash"),
            "_per_pass_version": raw.get("per_pass_version", 1),
            "_has_secret": raw.get("per_pass_salt") is not None,
        }

    def _decrypt_normal_password(self, entry: dict):
        """
        Decrypt a normal password while supporting legacy V1 and
        context-bound V2 ciphertext.
        """
        encrypted_password = entry["_raw_password"]
        if not isinstance(encrypted_password, bytes):
            raise TypeError("Password ciphertext must be bytes")

        if encrypted_password.startswith(self.engine.V2_PREFIX):
            entry_uuid = entry.get("_entry_uuid")
            if not entry_uuid:
                raise ValueError("V2 password is missing its entry UUID")
            aad = CryptoContext.entry(
                self.vault_id,
                entry_uuid,
                "password",
            )
            return self.engine.decrypt(
                encrypted_password,
                aad=aad,
            )

        return self.engine.decrypt(encrypted_password)

    def _create_cyber_card(self, entry: dict, entry_id: int) -> ctk.CTkFrame:
        """Create a cyberpunk-styled entry card with neon accents."""
        card = ctk.CTkFrame(
            self.cards_frame, fg_color=self.colors["bg_card"],
            corner_radius=6, height=75,
            border_width=1, border_color=self.colors["border"]
        )
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        # Left: neon icon + info
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        # Category icon with neon glow
        cat = entry.get("category", "password")
        icons = {"card": "◇", "note": "◈", "password": "◆"}
        icon_colors = {"card": self.colors["cyan"], "note": self.colors["neon_purple"],
                        "password": self.colors["accent"]}

        icon_text = icons.get(cat, "◆")
        icon_color = icon_colors.get(cat, self.colors["accent"])

        icon_label = ctk.CTkLabel(
            left, text=icon_text,
            width=40, height=40, corner_radius=4,
            fg_color=self.colors["bg_dark"],
            font=("Consolas", 20, "bold"),
            text_color=icon_color,
        )
        icon_label.pack(side="left", padx=(0, 12))

        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left")

        ctk.CTkLabel(
            info, text=entry.get("service", "UNKNOWN").upper(),
            font=("Consolas", 13, "bold"),
            text_color=self.colors["text_primary"], anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=entry.get("username", ""),
            font=("Consolas", 10),
            text_color=self.colors["text_secondary"], anchor="w"
        ).pack(anchor="w")

        if entry.get("_has_secret"):
            ctk.CTkLabel(
                info, text="◈ SECRET-LOCKED",
                font=("Consolas", 9, "bold"),
                text_color=self.colors["neon_yellow"]
            ).pack(anchor="w")

        # Right: action buttons
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        btn_config = [
            ("ENC", lambda: self._show_encrypted_password_popup(entry, entry_id),
             self.colors["border"], self.colors["neon_yellow"]),
            ("⊙", lambda: self._reveal_password(entry, entry_id),
             self.colors["border"], self.colors["accent"]),
            ("⊕", lambda: self._copy_password(entry, entry_id),
             self.colors["border"], self.colors["cyan"]),
            ("⊗", lambda: self._delete_entry(entry_id),
             self.colors["border"], self.colors["danger"]),
        ]

        for text, cmd, fg, hover in btn_config:
            ctk.CTkButton(
                actions, text=text, width=36, height=36,
                corner_radius=4, fg_color=fg,
                hover_color=hover,
                text_color=self.colors["text_primary"],
                font=("Consolas", 16, "bold"),
                command=cmd
            ).pack(side="left", padx=2)

        return card

    # ─────────────────────────────────────────────
    #  ENTRY ADDED ANIMATION (the cool part!)
    # ─────────────────────────────────────────────

    def _on_entry_added(self):
        """
        Called after a new entry is saved.
        Plays a full cyberpunk entry-added sequence.
        """
        # 1. Flash the entire cards area green
        GlitchAnimation.glitch_flicker(
            self.cards_frame,
            base_color="transparent",
            glitch_color=self.colors["accent_dim"],
            duration_ms=300, flashes=2
        )

        # 2. Reload entries
        self.after(350, self.load_entries)

        # 3. Show a cyber toast
        self.after(500, lambda: self._show_cyber_toast("◈ ENTRY ENCRYPTED & STORED"))

        # 4. Glitch the add button
        self.after(200, lambda: GlitchAnimation.glitch_text(
            self.add_btn, "+ NEW ENTRY", duration_ms=500
        ))

    def _show_cyber_toast(self, message: str):
        """Show a cyberpunk-styled toast notification."""
        from gui.components.toast_notification import ToastNotification
        ToastNotification.show(self, message, "success", duration_ms=3000)

    # ─────────────────────────────────────────────
    #  PER-PASSWORD REVEAL
    # ─────────────────────────────────────────────

    def _show_encrypted_password_popup(self, entry: dict, entry_id: int):
        self.parent_app.intruder_log.record_vault_access(
            "view_encrypted_password",
            vault_id=self.vault_id,
            entry_id=entry_id,
            service=entry.get("service"),
        )

        encrypted_bytes = entry.get("_raw_password", b"")
        if isinstance(encrypted_bytes, memoryview):
            encrypted_bytes = encrypted_bytes.tobytes()

        popup = ctk.CTkToplevel(self)
        popup.title(f"⟨ {entry.get('service', '').upper()} ENC ⟩")
        popup.geometry("520x320")
        popup.resizable(False, False)
        popup.configure(fg_color=self.colors["bg_dark"])
        popup.transient(self)
        popup.grab_set()

        ctk.CTkLabel(
            popup, text=f"◈ ENCRYPTED BLOB: {entry.get('service', '').upper()}",
            font=("Consolas", 15, "bold"),
            text_color=self.colors["neon_yellow"]
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            popup, text="[ STORED CIPHERTEXT ONLY - NO PLAINTEXT ]",
            font=("Consolas", 10),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 10))

        display = ctk.CTkTextbox(
            popup, width=460, height=150,
            font=("Consolas", 11),
            corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            border_width=1,
            text_color=self.colors["text_terminal"],
            wrap="word",
        )
        display.pack(pady=(0, 10), padx=20, fill="both", expand=True)
        display.insert("1.0", f"HEX:\n{encrypted_bytes.hex()}\n\nBASE64:\n{base64.b64encode(encrypted_bytes).decode('ascii')}")
        display.configure(state="disabled")

        button_row = ctk.CTkFrame(popup, fg_color="transparent")
        button_row.pack(pady=(0, 18))

        ctk.CTkButton(
            button_row, text="EXPORT",
            width=160, height=36,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            corner_radius=4,
            font=("Consolas", 11, "bold"),
            command=lambda: self._export_encrypted_password(entry, entry_id, encrypted_bytes, popup),
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            button_row, text="CLOSE",
            width=160, height=36,
            fg_color=self.colors["border"],
            hover_color=self.colors["bg_hover"],
            text_color=self.colors["text_secondary"],
            corner_radius=4,
            font=("Consolas", 11, "bold"),
            command=popup.destroy,
        ).pack(side="left", padx=6)

    def _export_encrypted_password(self, entry: dict, entry_id: int, encrypted_bytes: bytes, popup):
        self.parent_app.intruder_log.record_vault_access(
            "export_encrypted_password",
            vault_id=self.vault_id,
            entry_id=entry_id,
            service=entry.get("service"),
        )

        export_dir = Path.home() / ".securevault" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_service = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in entry.get("service", "entry").lower())
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = export_dir / f"{safe_service}_{entry_id}_{stamp}_encrypted.txt"

        content = (
            f"Service: {entry.get('service', '')}\n"
            f"Username: {entry.get('username', '')}\n"
            f"Vault ID: {self.vault_id}\n"
            f"Entry ID: {entry_id}\n"
            f"Exported At: {datetime.now().isoformat()}\n\n"
            f"HEX:\n{encrypted_bytes.hex()}\n\n"
            f"BASE64:\n{base64.b64encode(encrypted_bytes).decode('ascii')}\n"
        )
        export_path.write_text(content, encoding="utf-8")

        popup.destroy()
        self._show_cyber_toast(f"⊕ EXPORTED TO {export_path}")

    def _reveal_password(self, entry: dict, entry_id: int):
        self.parent_app.intruder_log.record_vault_access(
            "reveal_password",
            vault_id=self.vault_id,
            entry_id=entry_id,
            service=entry.get("service"),
        )
        if entry.get("_has_secret"):
            self._show_secret_prompt(entry, entry_id, mode="reveal")
        else:
            try:
                password = self._decrypt_normal_password(entry)
                self._show_password_popup(
                    entry.get("service", ""),
                    password,
                )
            except Exception:
                self._show_password_popup(
                    entry.get("service", ""),
                    "[DECRYPT ERROR]",
                )

    def _copy_password(self, entry: dict, entry_id: int):
        self.parent_app.intruder_log.record_vault_access(
            "copy_password",
            vault_id=self.vault_id,
            entry_id=entry_id,
            service=entry.get("service"),
        )
        if entry.get("_has_secret"):
            self._show_secret_prompt(entry, entry_id, mode="copy")
        else:
            try:
                password = self._decrypt_normal_password(entry)
                ClipboardManager.copy_and_clear(
                    password
                )
                self._show_cyber_toast("⊕ COPIED — AUTO-CLEAR 15s")
            except Exception:
                pass

    def _show_secret_prompt(self, entry: dict, entry_id: int, mode="reveal"):
        dialog = ctk.CTkToplevel(self)
        dialog.title("⟨ SECRET KEY ⟩")
        dialog.geometry("430x280")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.colors["bg_dark"])
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text=f"◈ UNLOCK: {entry.get('service', '').upper()}",
            font=("Consolas", 16, "bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            dialog, text="[ ENTER SECRET DECRYPTION KEY ]",
            font=("Consolas", 10),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 15))

        secret_entry = ctk.CTkEntry(
            dialog, placeholder_text="secret_key >>>",
            width=300, height=42, show="•",
            font=("Consolas", 13),
            corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text_terminal"]
        )
        secret_entry.pack(pady=(0, 8))

        error_label = ctk.CTkLabel(
            dialog, text="", font=("Consolas", 10),
            text_color=self.colors["danger"]
        )
        error_label.pack(pady=(0, 8))

        def attempt():
            secret = secret_entry.get()
            if not secret:
                error_label.configure(text="[ERR] No input.")
                return
            try:
                encrypted_data = {
                    "encrypted_password": entry["_raw_password"],
                    "salt": entry["_per_pass_salt"],
                    "verify_hash": entry["_per_pass_hash"],
                    "encryption_version": entry.get(
                        "_per_pass_version",
                        1,
                    ),
                }
                password = self.ppl.decrypt_with_secret(
                    encrypted_data,
                    secret,
                    entry_id=str(entry_id),
                    vault_id=self.vault_id,
                    entry_uuid=entry.get("_entry_uuid"),
                )
                dialog.destroy()

                if mode == "reveal":
                    self._show_password_popup(entry.get("service", ""), password)
                elif mode == "copy":
                    ClipboardManager.copy_and_clear(password)
                    self._show_cyber_toast("⊕ COPIED — AUTO-CLEAR 15s")

            except PermissionError as e:
                error_label.configure(text=str(e))
                GlitchAnimation.glitch_flicker(
                    secret_entry, base_color=self.colors["bg_input"],
                    glitch_color=self.colors["danger_dim"],
                    duration_ms=300, flashes=3
                )
            except ValueError:
                error_label.configure(text="[ACCESS DENIED] Wrong key.")
                GlitchAnimation.glitch_flicker(
                    secret_entry, base_color=self.colors["bg_input"],
                    glitch_color=self.colors["danger_dim"],
                    duration_ms=300, flashes=3
                )
                secret_entry.delete(0, "end")

        secret_entry.bind("<Return>", lambda e: attempt())

        ctk.CTkButton(
            dialog, text="⟨ DECRYPT ⟩",
            width=200, height=40,
            font=("Consolas", 13, "bold"),
            corner_radius=4,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            border_width=1, border_color=self.colors["accent"],
            command=attempt
        ).pack(pady=(0, 15))

        secret_entry.focus()

    def _show_password_popup(self, service: str, password: str):
        popup = ctk.CTkToplevel(self)
        popup.title(f"⟨ {service.upper()} ⟩")
        popup.geometry("460x230")
        popup.resizable(False, False)
        popup.configure(fg_color=self.colors["bg_dark"])
        popup.transient(self)
        popup.grab_set()

        ctk.CTkLabel(
            popup, text=f"◈ DECRYPTED: {service.upper()}",
            font=("Consolas", 15, "bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        pass_display = ctk.CTkEntry(
            popup, width=380, height=45,
            font=("Consolas", 16),
            corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["accent"],
            border_width=1,
            text_color=self.colors["accent"],
            justify="center"
        )
        pass_display.pack(pady=(0, 5))
        pass_display.insert(0, password)
        pass_display.configure(state="readonly")

        timer_label = ctk.CTkLabel(
            popup, text="[ AUTO-HIDE: 30s ]",
            font=("Consolas", 10),
            text_color=self.colors["text_secondary"]
        )
        timer_label.pack(pady=(0, 10))

        ctk.CTkButton(
            popup, text="⊕ COPY & CLOSE",
            width=180, height=38, corner_radius=4,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            border_width=1, border_color=self.colors["accent"],
            font=("Consolas", 12, "bold"),
            command=lambda: (ClipboardManager.copy_and_clear(password), popup.destroy())
        ).pack(pady=(0, 10))

        remaining = [30]
        def countdown():
            remaining[0] -= 1
            if remaining[0] <= 0:
                try: popup.destroy()
                except: pass
                return
            try: timer_label.configure(text=f"[ AUTO-HIDE: {remaining[0]}s ]")
            except: return
            popup.after(1000, countdown)
        popup.after(1000, countdown)

    # ─────────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────────

    def add_new_entry(self):
        AddEntryDialog(
            self, self.colors, self.engine,
            vault_id=self.vault_id,
            per_password_lock=self.ppl,
            db=self.db,
            on_save=self._on_entry_added
        )

    def _delete_entry(self, entry_id: int):
        """Delete an entry with confirmation."""
        confirm = ctk.CTkToplevel(self)
        confirm.title("⟨ CONFIRM DELETE ⟩")
        confirm.geometry("380x200")
        confirm.configure(fg_color=self.colors["bg_dark"])
        confirm.transient(self)
        confirm.grab_set()

        ctk.CTkLabel(
            confirm, text="⊗ DELETE ENTRY?",
            font=("Consolas", 18, "bold"),
            text_color=self.colors["danger"]
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            confirm, text="[ THIS ACTION CANNOT BE UNDONE ]",
            font=("Consolas", 10),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame, text="CANCEL", width=120, height=36,
            fg_color=self.colors["border"],
            hover_color=self.colors["bg_hover"],
            text_color=self.colors["text_secondary"],
            corner_radius=4, font=("Consolas", 11),
            command=confirm.destroy
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="DELETE", width=120, height=36,
            fg_color=self.colors["danger_dim"],
            hover_color=self.colors["danger"],
            text_color=self.colors["danger"],
            corner_radius=4, font=("Consolas", 11, "bold"),
            command=lambda: (
                self.parent_app.intruder_log.record_security_event(
                    "entry_deleted",
                    vault_id=self.vault_id,
                    entry_id=entry_id,
                ),
                self.db.delete_entry(
                    entry_id,
                    self.vault_id,
                ),
                confirm.destroy(),
                self._on_entry_added()
            )
        ).pack(side="left", padx=5)

    # ─────────────────────────────────────────────
    #  SIDEBAR FILTERS
    # ─────────────────────────────────────────────

    def on_search(self, event=None):
        self.load_entries(filter_text=self.search_entry.get())

    def show_all(self):
        self.load_entries()

    def show_favorites(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        self._card_widgets = []

        raw_entries = self.db.get_entries_by_vault(self.vault_id)
        for raw in raw_entries:
            if raw.get("favorite", 0) != 1:
                continue
            try:
                entry = self._decrypt_entry(raw)
                card = self._create_cyber_card(entry, raw["id"])
                self._card_widgets.append(card)
            except Exception:
                continue

        if not self._card_widgets:
            ctk.CTkLabel(
                self.cards_frame,
                text="[ NO FAVORITES ]\n\nStar entries to see them here.",
                font=("Consolas", 14),
                text_color=self.colors["text_secondary"],
                justify="center"
            ).pack(expand=True, pady=50)

    def show_passwords(self):
        self.load_entries(category="password")

    def show_cards(self):
        self.load_entries(category="card")

    def show_notes(self):
        self.load_entries(category="note")

    def lock_vault(self):
        self.engine = None
        self.parent_app.lock_vault()