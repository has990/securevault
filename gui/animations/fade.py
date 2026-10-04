"""
Fade Animations — Smooth opacity transitions for widgets and windows.
"""
from gui.animations.engine import AnimationController, Easing

class FadeAnimations:
    """Collection of fade effects."""

    @staticmethod
    def fade_in_window(window, duration_ms=600):
        """Fade the entire window from transparent to opaque."""
        window.attributes("-alpha", 0.0)
        controller = AnimationController(window, duration_ms)

        def update(progress):
            window.attributes("-alpha", progress)

        controller.animate(update, Easing.ease_out_cubic)

    @staticmethod
    def fade_in_widget(widget, duration_ms=400, start_color="#0f0f14", end_color=None):
        """Simulate fade-in by transitioning widget fg_color from bg to actual."""
        if end_color is None:
            end_color = "#1a1a24"

        start_rgb = FadeAnimations._hex_to_rgb(start_color)
        end_rgb = FadeAnimations._hex_to_rgb(end_color)
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
            color = f"#{r:02x}{g:02x}{b:02x}"
            try:
                widget.configure(fg_color=color)
            except Exception:
                pass

        controller.animate(update, Easing.ease_in_out_cubic)

    @staticmethod
    def fade_in_text(label, duration_ms=500, start_color="#0f0f14", end_color="#ffffff"):
        """Fade label text from invisible to visible."""
        start_rgb = FadeAnimations._hex_to_rgb(start_color)
        end_rgb = FadeAnimations._hex_to_rgb(end_color)
        controller = AnimationController(label, duration_ms)

        def update(progress):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
            color = f"#{r:02x}{g:02x}{b:02x}"
            try:
                label.configure(text_color=color)
            except Exception:
                pass

        controller.animate(update, Easing.ease_out_cubic)

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))