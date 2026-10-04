"""
Bounce & Elastic Animations — Playful micro-interactions.
"""
import math
from gui.animations.engine import AnimationController, Easing

class BounceAnimations:
    """Bounce and elastic effects for interactive elements."""

    @staticmethod
    def bounce_in(widget, target_y, drop_height=60, duration_ms=700):
        """Drop a widget from above with a bouncing landing."""
        start_y = target_y - drop_height
        widget.place_configure(y=start_y)
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            current_y = int(start_y + (target_y - start_y) * Easing.ease_out_bounce(progress))
            widget.place_configure(y=current_y)

        controller.animate(update, Easing.linear)

    @staticmethod
    def elastic_scale(widget, duration_ms=600):
        """
        Simulate elastic scaling by quickly changing widget size.
        Works with widgets using .place() with width/height.
        """
        try:
            original_width = widget.cget("width")
            original_height = widget.cget("height")
        except Exception:
            return

        controller = AnimationController(widget, duration_ms)

        def update(progress):
            scale = Easing.ease_out_elastic(progress)
            new_w = int(original_width * scale)
            new_h = int(original_height * scale)
            try:
                widget.configure(width=max(1, new_w), height=max(1, new_h))
            except Exception:
                pass

        controller.animate(update, Easing.linear)

    @staticmethod
    def shake(widget, intensity=8, duration_ms=400):
        """Shake a widget horizontally — great for wrong password feedback."""
        try:
            original_x = widget.winfo_x()
        except Exception:
            return

        controller = AnimationController(widget, duration_ms)

        def update(progress):
            remaining = 1 - progress
            offset = int(math.sin(progress * math.pi * 6) * intensity * remaining)
            try:
                widget.place_configure(x=original_x + offset)
            except Exception:
                pass

        controller.animate(update, Easing.linear)

    @staticmethod
    def jelly_click(button, duration_ms=300):
        """Jelly-like squish effect on button click."""
        try:
            original_width = button.cget("width")
            original_height = button.cget("height")
        except Exception:
            return

        controller = AnimationController(button, duration_ms)

        def update(progress):
            if progress < 0.3:
                # Squish
                sx = 1 + 0.1 * (progress / 0.3)
                sy = 1 - 0.08 * (progress / 0.3)
            else:
                # Bounce back
                t = (progress - 0.3) / 0.7
                sx = 1.1 - 0.1 * Easing.ease_out_elastic(t)
                sy = 0.92 + 0.08 * Easing.ease_out_elastic(t)
            try:
                button.configure(
                    width=max(1, int(original_width * sx)),
                    height=max(1, int(original_height * sy))
                )
            except Exception:
                pass

        controller.animate(update, Easing.linear)