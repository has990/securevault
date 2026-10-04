"""
CYBERPUNK TOTP Authenticator View
Built-in 2FA code generator with animated countdown.
"""
import time
import customtkinter as ctk
from gui.animations import GlitchAnimation, NeonFlickerAnimation
from gui.components.toast_notification import ToastNotification


class TOTPView(ctk.CTkFrame):
    """Built-in TOTP authenticator with live countdown."""

    def __init__(self, parent, colors, encryption_engine, vault_id, db):
        super().__init__(parent, fg_color=colors["bg_dark"])
        self.colors = colors
        self.parent_app = parent
        self.engine = encryption_engine
        self.vault_id = vault_id
        self.db = db
        self._totp_managers = {}
        self._code_labels = {}
        self._timer_labels = {}
        self._running = True

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
            header, text="⟨ AUTHENTICATOR ⟩",
            font=("Consolas", 22, "bold"),
            text_color=colors["accent"]
        )
        title.pack(side="left", padx=20)
        self.after(200, lambda: GlitchAnimation.glitch_text(
            title, "⟨ AUTHENTICATOR ⟩", duration_ms=600
        ))

        ctk.CTkButton(
            header, text="+ ADD 2FA",
            font=("Consolas", 12, "bold"),
            width=120, height=32,
            corner_radius=4,
            fg_color=colors["accent_dim"],
            hover_color=colors["accent"],
            text_color=colors["accent"],
            border_width=1, border_color=colors["accent"],
            command=self._show_add_dialog
        ).pack(side="right")

        # ── TOTP Cards ──
        self.cards_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors["border"]
        )
        self.cards_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._load_totp_entries()
        self._update_codes()

    def _load_totp_entries(self):
        """Load and display all TOTP entries."""
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        self._totp_managers = {}
        self._code_labels = {}
        self._timer_labels = {}

        entries = self.db.get_totp_entries(self.vault_id)

        if not entries:
            ctk.CTkLabel(
                self.cards_frame,
                text="[ NO 2FA ENTRIES ]\n\nPress + ADD 2FA to add an authenticator",
                font=("Consolas", 14),
                text_color=self.colors["text_secondary"],
                justify="center"
            ).pack(expand=True, pady=50)
            return

        for entry in entries:
            try:
                label = self.engine.decrypt(entry["label"])
                secret = self.engine.decrypt(entry["secret"])
                issuer = self.engine.decrypt(entry["issuer"]) if entry.get("issuer") else ""
                digits = entry.get("digits", 6)
                period = entry.get("period", 30)
                entry_id = entry["id"]

                # Create TOTP generator
                totp = SimpleTOTP(secret, digits=digits, period=period)
                self._totp_managers[entry_id] = totp

                self._create_totp_card(entry_id, label, issuer, totp)
            except Exception:
                continue

    def _create_totp_card(self, entry_id, label, issuer, totp):
        """Create a cyberpunk TOTP card with live code display."""
        card = ctk.CTkFrame(
            self.cards_frame, fg_color=self.colors["bg_card"],
            corner_radius=6, height=90,
            border_width=1, border_color=self.colors["border"]
        )
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=12)

        # Left: label + issuer
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left, text="◈",
            font=("Consolas", 20, "bold"),
            text_color=self.colors["neon_purple"]
        ).pack(side="left", padx=(0, 12))

        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left")

        display_name = issuer if issuer else label
        ctk.CTkLabel(
            info, text=display_name.upper(),
            font=("Consolas", 13, "bold"),
            text_color=self.colors["text_primary"]
        ).pack(anchor="w")

        if issuer and label != issuer:
            ctk.CTkLabel(
                info, text=label,
                font=("Consolas", 10),
                text_color=self.colors["text_secondary"]
            ).pack(anchor="w")

        # Center: large code display
        code = totp.generate()
        formatted_code = f"{code[:3]} {code[3:]}" if len(code) == 6 else code

        code_label = ctk.CTkLabel(
            inner, text=formatted_code,
            font=("Consolas", 28, "bold"),
            text_color=self.colors["accent"]
        )
        code_label.pack(side="left", expand=True)
        self._code_labels[entry_id] = code_label

        # Right: timer + actions
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        remaining = totp.remaining()
        timer_label = ctk.CTkLabel(
            right, text=f"{remaining}s",
            font=("Consolas", 14, "bold"),
            text_color=self.colors["cyan"] if remaining > 10 else self.colors["danger"]
        )
        timer_label.pack()
        self._timer_labels[entry_id] = timer_label

        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(pady=(5, 0))

        ctk.CTkButton(
            btn_frame, text="⊕", width=32, height=28,
            corner_radius=4, fg_color=self.colors["border"],
            hover_color=self.colors["accent"],
            font=("Consolas", 14),
            command=lambda: self._copy_code(totp.generate())
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame, text="⊗", width=32, height=28,
            corner_radius=4, fg_color=self.colors["border"],
            hover_color=self.colors["danger"],
            font=("Consolas", 14),
            command=lambda eid=entry_id: self._delete_totp(eid)
        ).pack(side="left", padx=2)

    def _update_codes(self):
        """Live-update all TOTP codes every second."""
        if not self._running:
            return

        for entry_id, totp in self._totp_managers.items():
            try:
                code = totp.generate()
                formatted = f"{code[:3]} {code[3:]}" if len(code) == 6 else code
                if entry_id in self._code_labels:
                    self._code_labels[entry_id].configure(text=formatted)

                remaining = totp.remaining()
                if entry_id in self._timer_labels:
                    color = self.colors["cyan"] if remaining > 10 else self.colors["danger"]
                    self._timer_labels[entry_id].configure(
                        text=f"{remaining}s", text_color=color
                    )

                    if remaining <= 3:
                        NeonFlickerAnimation.flicker_text(
                            self._code_labels[entry_id],
                            text_color=self.colors["accent"],
                            dim_color=self.colors["accent_dim"],
                            duration_ms=300, flicker_count=1
                        )
            except Exception:
                continue

        self.after(1000, self._update_codes)

    def _copy_code(self, code):
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
            ToastNotification.show(self, "⊕ CODE COPIED", "success")

            # Auto-clear clipboard after 30s
            self.after(30000, lambda: self._clear_clipboard())
        except Exception:
            pass

    def _clear_clipboard(self):
        try:
            self.clipboard_clear()
            self.clipboard_append("")
        except Exception:
            pass

    def _delete_totp(self, entry_id):
        self.db.delete_totp_entry(entry_id)
        self._load_totp_entries()
        ToastNotification.show(self, "⊗ 2FA ENTRY DELETED", "warning")

    def _show_add_dialog(self):
        """Show dialog to add a new TOTP entry."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("⟨ ADD 2FA ⟩")
        dialog.geometry("480x500")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.colors["bg_dark"])
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="⟨ ADD AUTHENTICATOR ⟩",
            font=("Consolas", 18, "bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(25, 15))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=35)

        # Service name
        ctk.CTkLabel(form, text="SERVICE NAME",
                     font=("Consolas", 11), text_color=self.colors["text_secondary"]
                     ).pack(anchor="w", pady=(10, 3))
        issuer_entry = ctk.CTkEntry(
            form, placeholder_text="e.g., GitHub",
            height=40, corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text_terminal"],
            font=("Consolas", 12)
        )
        issuer_entry.pack(fill="x")

        # Account / Label
        ctk.CTkLabel(form, text="ACCOUNT / EMAIL",
                     font=("Consolas", 11), text_color=self.colors["text_secondary"]
                     ).pack(anchor="w", pady=(10, 3))
        label_entry = ctk.CTkEntry(
            form, placeholder_text="e.g., user@email.com",
            height=40, corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text_terminal"],
            font=("Consolas", 12)
        )
        label_entry.pack(fill="x")

        # Secret key
        ctk.CTkLabel(form, text="SECRET KEY (BASE32)",
                     font=("Consolas", 11), text_color=self.colors["text_secondary"]
                     ).pack(anchor="w", pady=(10, 3))
        secret_entry = ctk.CTkEntry(
            form, placeholder_text="e.g., JBSWY3DPEHPK3PXP",
            height=40, corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text_terminal"],
            font=("Consolas", 12)
        )
        secret_entry.pack(fill="x")

        # OR paste URI
        ctk.CTkLabel(form, text="─── OR PASTE otpauth:// URI ───",
                     font=("Consolas", 9), text_color=self.colors["text_dim"]
                     ).pack(pady=(15, 3))
        uri_entry = ctk.CTkEntry(
            form, placeholder_text="otpauth://totp/...",
            height=40, corner_radius=4,
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text_terminal"],
            font=("Consolas", 11)
        )
        uri_entry.pack(fill="x")

        # Error label
        error_label = ctk.CTkLabel(
            dialog, text="", font=("Consolas", 10),
            text_color=self.colors["danger"]
        )
        error_label.pack(pady=(10, 0))

        def save_totp():
            uri = uri_entry.get().strip()

            if uri and uri.startswith("otpauth://"):
                try:
                    parsed = self._parse_otpauth_uri(uri)
                    label_val = parsed["label"]
                    secret_val = parsed["secret"]
                    issuer_val = parsed.get("issuer", "")
                    digits = parsed.get("digits", 6)
                    period = parsed.get("period", 30)
                    algorithm = parsed.get("algorithm", "sha1")
                except Exception as e:
                    error_label.configure(text=f"[ERR] Invalid URI: {e}")
                    return
            else:
                label_val = label_entry.get().strip()
                secret_val = secret_entry.get().strip().replace(" ", "")
                issuer_val = issuer_entry.get().strip()
                digits = 6
                period = 30
                algorithm = "sha1"

            if not label_val:
                error_label.configure(text="[ERR] Account/label required.")
                return
            if not secret_val:
                error_label.configure(text="[ERR] Secret key required.")
                return

            # Validate the secret
            try:
                test = SimpleTOTP(secret_val)
                test.generate()
            except Exception:
                error_label.configure(text="[ERR] Invalid secret key (must be base32).")
                return

            # Encrypt and store
            try:
                self.db.add_totp_entry(
                    label=self.engine.encrypt(label_val),
                    secret=self.engine.encrypt(secret_val),
                    vault_id=self.vault_id,
                    issuer=self.engine.encrypt(issuer_val) if issuer_val else None,
                    digits=digits,
                    period=period,
                    algorithm=algorithm,
                )
                dialog.destroy()
                self._load_totp_entries()
                ToastNotification.show(self, "◈ 2FA ENTRY ADDED", "success")
            except Exception as e:
                error_label.configure(text=f"[ERR] Save failed: {e}")

        ctk.CTkButton(
            dialog, text="⟨ ADD AUTHENTICATOR ⟩",
            width=220, height=42,
            font=("Consolas", 13, "bold"),
            corner_radius=4,
            fg_color=self.colors["accent_dim"],
            hover_color=self.colors["accent"],
            text_color=self.colors["accent"],
            border_width=1, border_color=self.colors["accent"],
            command=save_totp
        ).pack(pady=(10, 20))

    def _parse_otpauth_uri(self, uri):
        """Parse an otpauth:// URI into components."""
        from urllib.parse import urlparse, parse_qs, unquote

        parsed = urlparse(uri)
        params = parse_qs(parsed.query)

        # Label is the path (after /totp/)
        label = unquote(parsed.path.lstrip("/"))
        if ":" in label:
            label = label.split(":", 1)[1].strip()

        return {
            "label": label,
            "secret": params.get("secret", [""])[0],
            "issuer": params.get("issuer", [""])[0],
            "digits": int(params.get("digits", [6])[0]),
            "period": int(params.get("period", [30])[0]),
            "algorithm": params.get("algorithm", ["sha1"])[0],
        }

    def destroy(self):
        self._running = False
        super().destroy()


class SimpleTOTP:
    """
    Simple TOTP implementation — no external dependencies.
    Generates RFC 6238 compliant time-based one-time passwords.
    """

    def __init__(self, secret, digits=6, period=30, algorithm="sha1"):
        self.secret = secret
        self.digits = digits
        self.period = period
        self.algorithm = algorithm

    def generate(self):
        """Generate the current TOTP code."""
        import hmac
        import hashlib
        import struct
        import base64

        # Decode base32 secret
        key = base64.b32decode(self._normalize_secret(self.secret), casefold=True)

        # Get current time step
        now = int(time.time())
        time_step = now // self.period

        # Pack time step as big-endian 8 bytes
        time_bytes = struct.pack(">Q", time_step)

        # HMAC-SHA1
        if self.algorithm == "sha256":
            h = hmac.new(key, time_bytes, hashlib.sha256).digest()
        elif self.algorithm == "sha512":
            h = hmac.new(key, time_bytes, hashlib.sha512).digest()
        else:
            h = hmac.new(key, time_bytes, hashlib.sha1).digest()

        # Dynamic truncation
        offset = h[-1] & 0x0F
        truncated = struct.unpack(">I", h[offset:offset + 4])[0]
        truncated &= 0x7FFFFFFF

        # Generate code with correct number of digits
        code = truncated % (10 ** self.digits)
        return str(code).zfill(self.digits)

    def remaining(self):
        """Seconds remaining until code changes."""
        now = int(time.time())
        return self.period - (now % self.period)

    def _normalize_secret(self, secret):
        """Normalize base32 secret (remove spaces, add padding)."""
        secret = secret.replace(" ", "").replace("-", "").upper()
        # Add padding if needed
        padding = 8 - (len(secret) % 8)
        if padding != 8:
            secret += "=" * padding
        return secret