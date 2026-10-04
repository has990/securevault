"""
Animated Password Strength Meter — Visual strength bar with color transitions.
"""
import customtkinter as ctk
from gui.animations.engine import AnimationController, Easing


class StrengthMeter(ctk.CTkFrame):
    """Animated password strength indicator bar."""

    COLORS = {
        "Weak":        "#e74c3c",
        "Fair":        "#f39c12",
        "Strong":      "#6c5ce7",
        "Very Strong": "#00b894",
    }

    def __init__(self, parent, width=300, height=8, **kwargs):
        # Strip out any custom kwargs before passing to CTkFrame
        kwargs.pop("colors", None)
        super().__init__(parent, fg_color="#2a2a3a", corner_radius=4,
                         height=height, width=width)
        self.pack_propagate(False)

        self._bar = ctk.CTkFrame(
            self, fg_color="#2a2a3a", corner_radius=4,
            height=height, width=0
        )
        self._bar.place(x=0, y=0, relheight=1.0)

        self._label = ctk.CTkLabel(
            parent, text="", font=("Segoe UI", 11),
            text_color="#a0a0b0"
        )

        self._total_width = width

    def update_strength(self, strength_result: dict):
        label = strength_result.get("label", "Weak")
        score = strength_result.get("score", 0)
        max_score = strength_result.get("max_score", 8)
        feedback = strength_result.get("feedback", [])

        target_width = int((score / max_score) * self._total_width)
        color = self.COLORS.get(label, "#e74c3c")

        current_width = [self._bar.cget("width") if self._bar.cget("width") else 0]
        controller = AnimationController(self._bar, duration_ms=500)

        def update(progress):
            new_width = int(current_width[0] + (target_width - current_width[0]) * progress)
            try:
                self._bar.configure(width=max(1, new_width), fg_color=color)
            except Exception:
                pass

        controller.animate(update, Easing.ease_out_cubic)

        feedback_text = "  •  ".join(feedback[:2]) if feedback else ""
        self._label.configure(
            text=f"{label}  {feedback_text}",
            text_color=color
        )

    def get_label_widget(self):
        return self._label

    def reset(self):
        self._bar.configure(width=0, fg_color="#2a2a3a")
        self._label.configure(text="")