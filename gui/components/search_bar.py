"""
Animated Search Bar — Expands on focus with glow effect.
"""
import customtkinter as ctk
from gui.animations.engine import AnimationController, Easing


class AnimatedSearchBar(ctk.CTkFrame):
    """Search bar that expands and glows on focus."""

    def __init__(self, parent, colors, on_search=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.colors = colors
        self.on_search = on_search

        self.entry = ctk.CTkEntry(
            self, placeholder_text="🔍  Search vault...",
            width=350, height=45,
            font=("Segoe UI", 14),
            corner_radius=12,
            border_color=colors["border"],
            fg_color=colors["bg_card"],
            text_color=colors["text_primary"],
        )
        self.entry.pack(fill="x")

        # Bind events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_key_release)

    def _on_focus_in(self, event=None):
        """Expand and glow on focus."""
        controller = AnimationController(self.entry, duration_ms=300)

        def expand(progress):
            new_width = int(350 + (450 - 350) * progress)
            try:
                self.entry.configure(width=new_width,
                                     border_color=self.colors["accent"])
            except Exception:
                pass

        controller.animate(expand, Easing.ease_out_cubic)

    def _on_focus_out(self, event=None):
        """Shrink and remove glow on blur."""
        controller = AnimationController(self.entry, duration_ms=300)

        def shrink(progress):
            new_width = int(450 + (350 - 450) * progress)
            try:
                self.entry.configure(width=new_width,
                                     border_color=self.colors["border"])
            except Exception:
                pass

        controller.animate(shrink, Easing.ease_out_cubic)

    def _on_key_release(self, event=None):
        if self.on_search:
            self.on_search(self.entry.get())

    def get(self):
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, "end")