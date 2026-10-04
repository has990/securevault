"""
Decoy Vault Setup Dialog — Create and configure the decoy vault.
"""
import customtkinter as ctk
from gui.animations import BounceAnimations, FadeAnimations
from gui.components.toast_notification import ToastNotification


class DecoySetupView(ctk.CTkToplevel):
    """Modal dialog for creating a decoy vault."""

    def __init__(self, parent, colors, decoy_manager):
        super().__init__(parent)
        self.colors = colors
        self.decoy_manager = decoy_manager

        self.title("🎭 Decoy Vault Setup")
        self.geometry("520x580")
        self.resizable(False, False)
        self.configure(fg_color=colors["bg_dark"])
        self.transient(parent)
        self.grab_set()

        FadeAnimations.fade_in_window(self, duration_ms=300)

        # ── Header ──
        ctk.CTkLabel(
            self, text="🎭", font=("Segoe UI Emoji", 48)
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self, text="Create Decoy Vault",
            font=("Segoe UI", 22, "bold"),
            text_color=colors["text_primary"]
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self,
            text="This creates a fake vault with dummy passwords.\n"
                 "A different master password will open it instead of your real vault.\n"
                 "An adversary cannot prove the real vault exists.",
            font=("Segoe UI", 12),
            text_color=colors["text_secondary"],
            justify="center"
        ).pack(pady=(0, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=40)

        # Decoy password
        ctk.CTkLabel(
            form, text="Decoy Master Password",
            font=("Segoe UI", 13), text_color=colors["text_secondary"]
        ).pack(anchor="w", pady=(0, 3))

        self.decoy_pass = ctk.CTkEntry(
            form, placeholder_text="Password to open decoy vault...",
            height=42, corner_radius=10, show="•",
            fg_color=colors["bg_card"], border_color=colors["border"],
            text_color=colors["text_primary"], font=("Segoe UI", 13)
        )
        self.decoy_pass.pack(fill="x")

        # Confirm
        ctk.CTkLabel(
            form, text="Confirm Decoy Password",
            font=("Segoe UI", 13), text_color=colors["text_secondary"]
        ).pack(anchor="w", pady=(10, 3))

        self.decoy_confirm = ctk.CTkEntry(
            form, placeholder_text="Confirm password...",
            height=42, corner_radius=10, show="•",
            fg_color=colors["bg_card"], border_color=colors["border"],
            text_color=colors["text_primary"], font=("Segoe UI", 13)
        )
        self.decoy_confirm.pack(fill="x")

        # Number of fake entries
        ctk.CTkLabel(
            form, text="Number of fake entries to generate",
            font=("Segoe UI", 13), text_color=colors["text_secondary"]
        ).pack(anchor="w", pady=(10, 3))

        self.count_var = ctk.IntVar(value=5)
        count_frame = ctk.CTkFrame(form, fg_color="transparent")
        count_frame.pack(fill="x")

        self.count_label = ctk.CTkLabel(
            count_frame, text="5",
            font=("Segoe UI", 14, "bold"), text_color=colors["accent"]
        )
        self.count_label.pack(side="right")

        ctk.CTkSlider(
            count_frame, from_=1, to=8,
            variable=self.count_var,
            command=lambda v: self.count_label.configure(text=str(int(v))),
            button_color=colors["accent"],
            progress_color=colors["accent"],
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Error label
        self.error_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11),
            text_color=colors["danger"]
        )
        self.error_label.pack(pady=(10, 0))

        # Create button
        ctk.CTkButton(
            self, text="🎭  Create Decoy Vault",
            width=250, height=48,
            font=("Segoe UI", 15, "bold"),
            corner_radius=12,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            command=self._create_decoy
        ).pack(pady=(10, 20))

    def _create_decoy(self):
        password = self.decoy_pass.get()
        confirm = self.decoy_confirm.get()

        if not password or len(password) < 8:
            self.error_label.configure(text="Password must be at least 8 characters.")
            BounceAnimations.shake(self.decoy_pass, intensity=6)
            return

        if password != confirm:
            self.error_label.configure(text="Passwords don't match.")
            BounceAnimations.shake(self.decoy_confirm, intensity=6)
            return

        try:
            fake_entries = self.decoy_manager.generate_plausible_entries(
                count=self.count_var.get()
            )
            self.decoy_manager.create_decoy_vault(password, fake_entries)
            ToastNotification.show(
                self.master, "🎭 Decoy vault created successfully!", "success"
            )
            self.destroy()
        except Exception as e:
            self.error_label.configure(text=f"Error: {str(e)}")