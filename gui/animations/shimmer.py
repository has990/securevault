"""
Shimmer & Loading Animations — Elegant loading states.
"""
import math
from gui.animations.engine import AnimationController, Easing

class ShimmerAnimations:
    """Shimmer effects for loading states and skeleton screens."""

    @staticmethod
    def shimmer_loading(widget, color1="#1a1a24", color2="#2a2a3a",
                        duration_ms=1800, loops=-1):
        """Create a shimmer loading effect across a widget."""
        rgb1 = ShimmerAnimations._hex_to_rgb(color1)
        rgb2 = ShimmerAnimations._hex_to_rgb(color2)

        loop_count = [0]
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            wave = (math.sin(progress * math.pi * 2) + 1) / 2
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * wave)
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * wave)
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * wave)
            try:
                widget.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
            except Exception:
                pass

        def on_done():
            loop_count[0] += 1
            if loops == -1 or loop_count[0] < loops:
                controller.animate(update, Easing.linear, on_done)

        controller.animate(update, Easing.linear, on_done)
        return controller

    @staticmethod
    def loading_dots(label, text="Loading", duration_ms=800, loops=-1):
        """Animate loading dots: Loading. → Loading.. → Loading..."""
        dot_count = [0]
        loop_count = [0]

        def _cycle():
            dots = "." * (dot_count[0] % 4)
            try:
                label.configure(text=f"{text}{dots}")
            except Exception:
                return
            dot_count[0] += 1

            if loops == -1 or loop_count[0] < loops * 4:
                loop_count[0] += 1
                label.after(duration_ms // 4, _cycle)

        _cycle()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))