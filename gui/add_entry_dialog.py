"""
Add/Edit Entry Dialog — With category selector and per-password secret phrase.
"""
import uuid
import customtkinter as ctk
from core.crypto_context import CryptoContext
from core.password_generator import PasswordGenerator
from gui.animations import BounceAnimations, FadeAnimations


class AddEntryDialog(ctk.CTkToplevel):
    def __init__(self, parent, colors, encryption_engine, vault_id,
                 per_password_lock, db, on_save=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = encryption_engine
        self.vault_id = vault_id
        self.ppl = per_password_lock
        self.db = db
        self.on_save = on_save

        self.title("Add New Entry")
        self.geometry("520x750")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg_dark"])
        self.transient(parent)
        self.grab_set()

        # ── Fade In ──
        FadeAnimations.fade_in_window(self, duration_ms=300)

        # ── Header ──
        ctk.CTkLabel(
            self, text="➕ Add New Entry",
            font=("Segoe UI", 22, "bold"),
            text_color=colors["text_primary"]
        ).pack(pady=(25, 15))

        # ── Form ──
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=35)

        # ── Category Selector ──
        self._add_field_label(form, "Category")

        category_frame = ctk.CTkFrame(form, fg_color="transparent")
        category_frame.pack(fill="x", pady=(0, 5))

        self.category_var = ctk.StringVar(value="password")
        self._category_buttons = {}

        categories = [
            ("🔑 Password", "password"),
            ("💳 Card", "card"),
            ("📝 Note", "note"),
        ]

        for text, value in categories:
            btn = ctk.CTkButton(
                category_frame, text=text,
                width=130, height=38, corner_radius=10,
                fg_color=colors["accent"] if value == "password" else colors["border"],
                hover_color=colors["accent_hover"],
                font=("Segoe UI", 12, "bold"),
                command=lambda v=value: self._select_category(v)
            )
            btn.pack(side="left", padx=(0, 8))
            self._category_buttons[value] = btn

        # ── Dynamic Labels (change based on category) ──
        # Service
        self.service_label = self._add_field_label(form, "Service / Website")
        self.service_entry = self._add_field_input(form, "e.g., GitHub")

        # Username
        self.username_label_widget = self._add_field_label(form, "Username / Email")
        self.username_entry = self._add_field_input(form, "e.g., user@email.com")

        # Password
        self.password_label_widget = self._add_field_label(form, "Password")
        self.password_entry = self._add_field_input(form, "Enter or generate", show="•")

        self.password_meter_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.password_meter_frame.pack(fill="x", pady=(6, 0))

        self.password_strength_bar = ctk.CTkProgressBar(
            self.password_meter_frame,
            height=10,
            corner_radius=8,
            fg_color=colors["bg_card"],
            progress_color=colors["danger"],
        )
        self.password_strength_bar.pack(fill="x")
        self.password_strength_bar.set(0)

        self.password_strength_label = ctk.CTkLabel(
            self.password_meter_frame,
            text="Strength: not set yet | Risk: high",
            font=("Segoe UI", 10),
            text_color=colors["text_secondary"],
            justify="left",
        )
        self.password_strength_label.pack(anchor="w", pady=(4, 0))

        self.password_entry.bind("<KeyRelease>", self._update_password_meter)

        ctk.CTkLabel(
            form,
            text="Optional: add a secret key below to require extra unlock protection.",
            font=("Segoe UI", 10),
            text_color=colors["text_secondary"],
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # Generate button
        self.gen_btn = ctk.CTkButton(
            form, text="🎲 Generate Strong Password",
            height=35, corner_radius=10,
            fg_color=colors["border"],
            hover_color=colors["accent"],
            font=("Segoe UI", 12),
            command=self.generate_password
        )
        self.gen_btn.pack(fill="x", pady=(5, 0))

        self._update_password_meter()

        # URL
        self.url_label_widget = self._add_field_label(form, "URL (optional)")
        self.url_entry = self._add_field_input(form, "https://...")

        # Notes
        self._add_field_label(form, "Notes (optional)")
        self.notes_entry = self._add_field_input(form, "Any notes...")

        # ── Per-Password Secret Section ──
        secret_frame = ctk.CTkFrame(form, fg_color=colors["bg_card"], corner_radius=12)
        secret_frame.pack(fill="x", pady=(15, 5))

        ctk.CTkLabel(
            secret_frame, text="🔐 Secret Key Protection",
            font=("Segoe UI", 14, "bold"),
            text_color=colors["warning"]
        ).pack(pady=(12, 2), padx=15, anchor="w")

        ctk.CTkLabel(
            secret_frame,
            text="Enable this if the entry needs a separate secret key to reveal or copy.\n"
                 "Even with the vault unlocked, this password stays hidden until the secret is entered.",
            font=("Segoe UI", 11),
            text_color=colors["text_secondary"],
            justify="left"
        ).pack(padx=15, anchor="w")

        self.enable_secret_var = ctk.BooleanVar(value=False)
        self.secret_toggle = ctk.CTkSwitch(
            secret_frame, text="Protect with secret key",
            variable=self.enable_secret_var,
            font=("Segoe UI", 12),
            text_color=colors["text_secondary"],
            command=self._toggle_secret_fields
        )
        self.secret_toggle.pack(padx=15, pady=(8, 5), anchor="w")

        self.secret_phrase_entry = ctk.CTkEntry(
            secret_frame, placeholder_text="Enter secret phrase...",
            height=40, corner_radius=10, show="•",
            fg_color=colors["bg_dark"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            font=("Segoe UI", 13),
            state="disabled"
        )
        self.secret_phrase_entry.pack(fill="x", padx=15, pady=(0, 5))

        self.secret_confirm_entry = ctk.CTkEntry(
            secret_frame, placeholder_text="Confirm secret phrase...",
            height=40, corner_radius=10, show="•",
            fg_color=colors["bg_dark"],
            border_color=colors["border"],
            text_color=colors["text_primary"],
            font=("Segoe UI", 13),
            state="disabled"
        )
        self.secret_confirm_entry.pack(fill="x", padx=15, pady=(0, 12))

        # ── Error Label ──
        self.error_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11),
            text_color=colors["danger"]
        )
        self.error_label.pack(pady=(5, 0))

        # ── Save Button ──
        self.save_btn = ctk.CTkButton(
            self, text="💾  Save Entry",
            width=220, height=48,
            font=("Segoe UI", 15, "bold"),
            corner_radius=12,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self.save_entry
        )
        self.save_btn.pack(pady=(5, 25))

    def _select_category(self, category: str):
        """Switch category and update form labels dynamically."""
        self.category_var.set(category)

        # Update button styles
        for value, btn in self._category_buttons.items():
            if value == category:
                btn.configure(fg_color=self.colors["accent"])
            else:
                btn.configure(fg_color=self.colors["border"])

        # Update placeholders based on category
        if category == "card":
            self.service_label.configure(text="Card Name")
            self.service_entry.configure(placeholder_text="e.g., Visa Credit Card")
            self.username_label_widget.configure(text="Card Number")
            self.username_entry.configure(placeholder_text="e.g., 4532-XXXX-XXXX-1234")
            self.password_label_widget.configure(text="CVV / PIN")
            self.password_entry.configure(placeholder_text="e.g., 123")
            self.url_label_widget.configure(text="Bank (optional)")
            self.url_entry.configure(placeholder_text="e.g., Chase, HSBC")
            self.notes_entry.configure(placeholder_text="Expiry date, billing address...")
        elif category == "note":
            self.service_label.configure(text="Note Title")
            self.service_entry.configure(placeholder_text="e.g., Recovery Phrase")
            self.username_label_widget.configure(text="Label (optional)")
            self.username_entry.configure(placeholder_text="e.g., Wallet #1")
            self.password_label_widget.configure(text="Secret Content")
            self.password_entry.configure(placeholder_text="Your secret note content...")
            self.url_label_widget.configure(text="Reference (optional)")
            self.url_entry.configure(placeholder_text="Any reference link...")
            self.notes_entry.configure(placeholder_text="Additional details...")
        else:  # password
            self.service_label.configure(text="Service / Website")
            self.service_entry.configure(placeholder_text="e.g., GitHub")
            self.username_label_widget.configure(text="Username / Email")
            self.username_entry.configure(placeholder_text="e.g., user@email.com")
            self.password_label_widget.configure(text="Password")
            self.password_entry.configure(placeholder_text="Enter or generate")
            self.url_label_widget.configure(text="URL (optional)")
            self.url_entry.configure(placeholder_text="https://...")
            self.notes_entry.configure(placeholder_text="Any notes...")

    def _add_field_label(self, parent, text) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent, text=text,
            font=("Segoe UI", 13),
            text_color=self.colors["text_secondary"]
        )
        label.pack(anchor="w", pady=(10, 3))
        return label

    def _add_field_input(self, parent, placeholder, show=""):
        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder,
            height=42, corner_radius=10,
            fg_color=self.colors["bg_card"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            font=("Segoe UI", 13),
            show=show
        )
        entry.pack(fill="x")
        return entry

    def _toggle_secret_fields(self):
        state = "normal" if self.enable_secret_var.get() else "disabled"
        self.secret_phrase_entry.configure(state=state)
        self.secret_confirm_entry.configure(state=state)

    def generate_password(self):
        password = PasswordGenerator.generate(length=20)
        self.password_entry.delete(0, "end")
        self.password_entry.configure(show="")
        self.password_entry.insert(0, password)
        self._update_password_meter()

    def _update_password_meter(self, event=None):
        password = self.password_entry.get().strip()

        if not password:
            self.password_strength_bar.set(0)
            self.password_strength_bar.configure(progress_color=self.colors["danger"])
            self.password_strength_label.configure(text="Strength: not set yet | Risk: high")
            return

        analysis = PasswordGenerator.check_strength(password)
        score = analysis["score"]
        max_score = max(1, analysis.get("max_score", 8))
        strength_ratio = min(max(score / max_score, 0), 1)
        risk_ratio = 1 - strength_ratio

        if strength_ratio >= 0.85:
            label = "Very Strong"
            color = self.colors["success"]
            risk_text = "very low"
        elif strength_ratio >= 0.65:
            label = "Strong"
            color = self.colors["accent"]
            risk_text = "low"
        elif strength_ratio >= 0.4:
            label = "Fair"
            color = self.colors["warning"]
            risk_text = "moderate"
        else:
            label = "Weak"
            color = self.colors["danger"]
            risk_text = "high"

        self.password_strength_bar.set(strength_ratio)
        self.password_strength_bar.configure(progress_color=color)
        self.password_strength_label.configure(
            text=f"Strength: {label} ({score}/{max_score}) | Risk: {risk_text} ({round(risk_ratio * 100)}%)"
        )

    def save_entry(self):
        """Validate, encrypt, and save the entry."""
        # Generate the immutable identifier BEFORE any encryption.
        # The UUID will later be included in AES-GCM AAD.
        entry_uuid = str(uuid.uuid4())
        service = self.service_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        url = self.url_entry.get().strip()
        notes = self.notes_entry.get().strip()
        category = self.category_var.get()

        # Validation
        if not service:
            self.error_label.configure(text="Service/Name is required.")
            BounceAnimations.shake(self.service_entry, intensity=6)
            return
        if not password:
            self.error_label.configure(text="Password/Secret content is required.")
            BounceAnimations.shake(self.password_entry, intensity=6)
            return

        # ---------------------------------------------------------
        # Password protection
        # ---------------------------------------------------------
        per_pass_salt = None
        per_pass_hash = None
        per_pass_version = 1

        if self.enable_secret_var.get():
            secret_phrase = self.secret_phrase_entry.get()
            secret_confirm = self.secret_confirm_entry.get()

            if not secret_phrase:
                self.error_label.configure(
                    text="[ERROR] Secret phrase cannot be empty."
                )
                return

            if secret_phrase != secret_confirm:
                self.error_label.configure(
                    text="[ERROR] Secret phrases do not match."
                )
                return

            try:
                protected = self.ppl.encrypt_with_secret(
                    password,
                    secret_phrase,
                    vault_id=self.vault_id,
                    entry_uuid=entry_uuid,
                )
            except ValueError as exc:
                self.error_label.configure(text=f"[ERROR] {exc}")
                return

            encrypted_password = protected["encrypted_password"]
            per_pass_salt = protected["salt"]
            per_pass_hash = protected["verify_hash"]
            per_pass_version = protected.get(
                "version",
                protected.get("encryption_version", 2),
            )
        else:
            # Bind the password ciphertext to this specific vault entry.
            # The entry UUID must exist before encryption so it can be
            # included in the AES-GCM authenticated context.
            password_aad = CryptoContext.entry(
                self.vault_id,
                entry_uuid,
                "password",
            )
            encrypted_password = self.engine.encrypt(
                password,
                aad=password_aad,
            )

        # Encrypt metadata with field-specific authenticated contexts.
        try:
            service_aad = CryptoContext.entry(
                self.vault_id,
                entry_uuid,
                "service",
            )
            username_aad = CryptoContext.entry(
                self.vault_id,
                entry_uuid,
                "username",
            )
            url_aad = CryptoContext.entry(
                self.vault_id,
                entry_uuid,
                "url",
            )
            notes_aad = CryptoContext.entry(
                self.vault_id,
                entry_uuid,
                "notes",
            )
            self.db.add_entry(
                service=self.engine.encrypt(
                    service,
                    aad=service_aad,
                ),
                username=self.engine.encrypt(
                    username,
                    aad=username_aad,
                ),
                password=encrypted_password,
                url=(
                    self.engine.encrypt(
                        url,
                        aad=url_aad,
                    )
                    if url
                    else None
                ),
                notes=(
                    self.engine.encrypt(
                        notes,
                        aad=notes_aad,
                    )
                    if notes
                    else None
                ),
                vault_id=self.vault_id,
                category=category,
                per_pass_salt=per_pass_salt,
                per_pass_hash=per_pass_hash,
                entry_uuid=entry_uuid,
                per_pass_version=per_pass_version,
            )
            if self.on_save:
                self.on_save()
            self.destroy()

        except Exception as e:
            self.error_label.configure(text=f"Save failed: {str(e)}")
