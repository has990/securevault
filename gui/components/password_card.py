"""
Reusable Password Card Component
Standalone card widget for displaying a single vault entry.
"""
import customtkinter as ctk


class PasswordCard(ctk.CTkFrame):
    """A single password entry card with icon, info, and action buttons."""

    def __init__(self, parent, entry: dict, colors: dict,
                 on_reveal=None, on_copy=None, on_delete=None,
                 on_favorite=None, **kwargs):
        super().__init__(parent, fg_color=colors["bg_card"],
                         corner_radius=15, height=80, **kwargs)
        self.pack_propagate(False)
        self.colors = colors
        self.entry = entry

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=12)

        # Left: icon + info
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        icon_text = entry.get("service", "?")[0].upper()
        ctk.CTkLabel(
            left, text=icon_text,
            width=45, height=45, corner_radius=10,
            fg_color=colors["accent"],
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        ).pack(side="left", padx=(0, 15))

        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left")

        ctk.CTkLabel(
            info, text=entry.get("service", "Unknown"),
            font=("Segoe UI", 15, "bold"),
            text_color=colors["text_primary"], anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=entry.get("username", ""),
            font=("Segoe UI", 12),
            text_color=colors["text_secondary"], anchor="w"
        ).pack(anchor="w")

        if entry.get("_has_secret"):
            ctk.CTkLabel(
                info, text="🔑 Secret-protected",
                font=("Segoe UI", 10),
                text_color=colors["warning"]
            ).pack(anchor="w")

        # Right: actions
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        buttons = [
            ("⭐" if entry.get("favorite") else "☆", on_favorite, colors["border"], colors["warning"]),
            ("👁", on_reveal, colors["border"], colors["accent"]),
            ("📋", on_copy, colors["border"], colors["accent"]),
            ("🗑", on_delete, colors["border"], colors["danger"]),
        ]

        for text, cmd, fg, hover in buttons:
            if cmd:
                ctk.CTkButton(
                    actions, text=text, width=40, height=40,
                    corner_radius=10, fg_color=fg,
                    hover_color=hover, font=("Segoe UI", 14),
                    command=cmd
                ).pack(side="left", padx=2)