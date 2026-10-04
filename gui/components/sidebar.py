"""
Animated Sidebar — Navigation panel with hover effects and active state.
"""
import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    """Reusable animated sidebar navigation component."""

    def __init__(self, parent, colors, nav_items: list,
                 header_text="🔐 SecureVault",
                 on_lock=None, on_stealth=None, **kwargs):
        super().__init__(parent, width=220, fg_color=colors["bg_sidebar"],
                         corner_radius=0, **kwargs)
        self.pack_propagate(False)
        self.colors = colors
        self._buttons = []
        self._active_index = 0

        # Header
        ctk.CTkLabel(
            self, text=header_text,
            font=("Segoe UI", 18, "bold"),
            text_color=colors["text_primary"]
        ).pack(pady=(25, 30), padx=15, anchor="w")

        # Navigation buttons
        for i, (text, command) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self, text=text, anchor="w",
                font=("Segoe UI", 14), height=42,
                fg_color=colors["accent"] if i == 0 else "transparent",
                hover_color=colors["bg_card"],
                text_color=colors["text_primary"] if i == 0 else colors["text_secondary"],
                corner_radius=10,
                command=lambda idx=i, cmd=command: self._on_nav(idx, cmd)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._buttons.append(btn)

        # Bottom buttons
        if on_stealth:
            ctk.CTkButton(
                self, text="👻  Stealth Mode",
                font=("Segoe UI", 13),
                fg_color=colors["border"],
                hover_color=colors["accent"],
                height=38, corner_radius=10,
                command=on_stealth
            ).pack(side="bottom", fill="x", padx=15, pady=(0, 10))

        if on_lock:
            ctk.CTkButton(
                self, text="🔒  Lock Vault",
                font=("Segoe UI", 13),
                fg_color=colors["danger"],
                hover_color="#c0392b",
                height=40, corner_radius=10,
                command=on_lock
            ).pack(side="bottom", fill="x", padx=15, pady=(0, 8))

    def _on_nav(self, index: int, command):
        """Update active state and execute command."""
        for i, btn in enumerate(self._buttons):
            if i == index:
                btn.configure(
                    fg_color=self.colors["accent"],
                    text_color=self.colors["text_primary"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.colors["text_secondary"]
                )
        self._active_index = index
        if command:
            command()