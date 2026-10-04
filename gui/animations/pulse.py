"""
Pulse & Glow Animations — Attention-grabbing effects.
"""
import math
from gui.animations.engine import AnimationController, Easing

class PulseAnimations:
    """Pulsing glow and breathing effects."""

    @staticmethod
    def pulse_glow(widget, base_color="#6c5ce7", glow_color="#a29bfe",
                   duration_ms=1500, loops=-1):
        """
        Pulse a widget's color between base and glow.
        loops=-1 means infinite.
        """
        base_rgb = PulseAnimations._hex_to_rgb(base_color)
        glow_rgb = PulseAnimations._hex_to_rgb(glow_color)

        loop_count = [0]
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            # Sine wave for smooth back-and-forth
            wave = (math.sin(progress * math.pi * 2 - math.pi / 2) + 1) / 2
            r = int(base_rgb[0] + (glow_rgb[0] - base_rgb[0]) * wave)
            g = int(base_rgb[1] + (glow_rgb[1] - base_rgb[1]) * wave)
            b = int(base_rgb[2] + (glow_rgb[2] - base_rgb[2]) * wave)
            color = f"#{r:02x}{g:02x}{b:02x}"
            try:
                widget.configure(fg_color=color)
            except Exception:
                pass

        def on_done():
            loop_count[0] += 1
            if loops == -1 or loop_count[0] < loops:
                controller.animate(update, Easing.linear, on_done)

        controller.animate(update, Easing.linear, on_done)
        return controller  # return so caller can stop it

    @staticmethod
    def pulse_border(widget, base_color="#2a2a3a", glow_color="#6c5ce7",
                     duration_ms=1200, loops=3):
        """Pulse the border color of a widget."""
        base_rgb = PulseAnimations._hex_to_rgb(base_color)
        glow_rgb = PulseAnimations._hex_to_rgb(glow_color)

        loop_count = [0]
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            wave = (math.sin(progress * math.pi * 2 - math.pi / 2) + 1) / 2
            r = int(base_rgb[0] + (glow_rgb[0] - base_rgb[0]) * wave)
            g = int(base_rgb[1] + (glow_rgb[1] - base_rgb[1]) * wave)
            b = int(base_rgb[2] + (glow_rgb[2] - base_rgb[2]) * wave)
            color = f"#{r:02x}{g:02x}{b:02x}"
            try:
                widget.configure(border_color=color)
            except Exception:
                pass

        def on_done():
            loop_count[0] += 1
            if loops == -1 or loop_count[0] < loops:
                controller.animate(update, Easing.linear, on_done)

        controller.animate(update, Easing.linear, on_done)
        return controller

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))