"""
Password Generator View — Interactive generator with animated strength meter.
"""
import customtkinter as ctk
from core.password_generator import PasswordGenerator
from core.clipboard import ClipboardManager
from gui.components.strength_meter import StrengthMeter
from gui.animations import FadeAnimations, BounceAnimations
from gui.components.toast_notification import ToastNotification


class GeneratorView(ctk.CTkFrame):
    """Full-screen password generator with live strength preview."""

    def __init__(self, parent, colors):
        super().__init__(parent, fg_color=colors["bg_dark"])
        self.colors = colors
        self.parent_app = parent

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 20))

        ctk.CTkButton(
            header, text="← Back", width=80, height=35,
            fg_color=colors["border"], hover_color=colors["bg_card"],
            corner_radius=10, font=("Segoe UI", 12),
            command=lambda: parent.show_vault()
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="🎲  Password Generator",
            font=("Segoe UI", 24, "bold"),
            text_color=colors["text_primary"]
        ).pack(side="left", padx=20)

        # ── Main Card ──
        card = ctk.CTkFrame(self, fg_color=colors["bg_card"], corner_radius=20)
        card.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        center = ctk.CTkFrame(card, fg_color="transparent")
        center.pack(expand=True, fill="x", padx=50)

        # Generated password display
        self.password_display = ctk.CTkEntry(
            center, height=60, font=("Consolas", 22),
            corner_radius=15, fg_color=colors["bg_dark"],
            border_color=colors["accent"], text_color=colors["success"],
            justify="center"
        )
        self.password_display.pack(fill="x", pady=(30, 5))

        # Strength meter (no colors kwarg)
        self.strength_meter = StrengthMeter(center, width=500)
        self.strength_meter.pack(fill="x", pady=(5, 2))
        self.strength_label = self.strength_meter.get_label_widget()
        self.strength_label.pack(anchor="w", pady=(0, 15))

        # ── Controls ──
        controls = ctk.CTkFrame(center, fg_color="transparent")
        controls.pack(fill="x", pady=10)

        # Length slider
        ctk.CTkLabel(
            controls, text="Length", font=("Segoe UI", 13),
            text_color=colors["text_secondary"]
        ).pack(anchor="w")

        length_frame = ctk.CTkFrame(controls, fg_color="transparent")
        length_frame.pack(fill="x", pady=(0, 15))

        self.length_var = ctk.IntVar(value=20)
        self.length_label = ctk.CTkLabel(
            length_frame, text="20", width=40,
            font=("Segoe UI", 14, "bold"),
            text_color=colors["accent"]
        )
        self.length_label.pack(side="right")

        self.length_slider = ctk.CTkSlider(
            length_frame, from_=8, to=64,
            variable=self.length_var,
            command=self._on_length_change,
            button_color=colors["accent"],
            button_hover_color=colors["accent_hover"],
            progress_color=colors["accent"],
        )
        self.length_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Character options
        options_frame = ctk.CTkFrame(controls, fg_color="transparent")
        options_frame.pack(fill="x", pady=5)

        self.uppercase_var = ctk.BooleanVar(value=True)
        self.digits_var = ctk.BooleanVar(value=True)
        self.symbols_var = ctk.BooleanVar(value=True)
        self.ambiguous_var = ctk.BooleanVar(value=False)

        toggles = [
            ("ABC  Uppercase", self.uppercase_var),
            ("123  Digits", self.digits_var),
            ("!@#  Symbols", self.symbols_var),
            ("🚫  No Ambiguous", self.ambiguous_var),
        ]

        for text, var in toggles:
            ctk.CTkSwitch(
                options_frame, text=text, variable=var,
                font=("Segoe UI", 12),
                text_color=colors["text_secondary"],
                command=self._generate,
                button_color=colors["accent"],
                button_hover_color=colors["accent_hover"],
                progress_color=colors["accent"],
            ).pack(side="left", padx=(0, 20), pady=5)

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(center, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 30))

        ctk.CTkButton(
            btn_frame, text="🔄  Regenerate",
            width=180, height=48,
            font=("Segoe UI", 14, "bold"),
            corner_radius=12,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._generate
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="📋  Copy",
            width=140, height=48,
            font=("Segoe UI", 14, "bold"),
            corner_radius=12,
            fg_color=colors["success"],
            hover_color="#00a884",
            command=self._copy
        ).pack(side="left")

        # Generate initial password
        self.after(300, self._generate)

    def _on_length_change(self, value):
        self.length_label.configure(text=str(int(value)))
        self._generate()

    def _generate(self):
        """Generate a new password and update the display."""
        try:
            password = PasswordGenerator.generate(
                length=self.length_var.get(),
                use_uppercase=self.uppercase_var.get(),
                use_digits=self.digits_var.get(),
                use_symbols=self.symbols_var.get(),
                exclude_ambiguous=self.ambiguous_var.get(),
            )
        except ValueError:
            password = PasswordGenerator.generate(length=12)

        self.password_display.configure(state="normal")
        self.password_display.delete(0, "end")
        self.password_display.insert(0, password)

        # Update strength meter
        strength = PasswordGenerator.check_strength(password)
        self.strength_meter.update_strength(strength)

    def _copy(self):
        password = self.password_display.get()
        if password:
            ClipboardManager.copy_and_clear(password)
            ToastNotification.show(self, "📋 Copied! Auto-clears in 15s", "success")