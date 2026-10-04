"""
Cyberpunk Animations — Glitch, Matrix Rain, Scanlines, Neon Flicker,
Terminal Boot, Hologram effects.
"""
import math
import secrets
import string
from gui.animations.engine import AnimationController, Easing


class GlitchAnimation:
    """Digital glitch/corruption effect on text widgets."""

    GLITCH_CHARS = "█▓▒░╔╗╚╝║═╠╣╦╩╬▲▼◄►◊○●"

    @staticmethod
    def glitch_text(label, final_text: str, duration_ms=800, intensity=0.7):
        """
        Scramble text with random characters before resolving to final text.
        Like a Hollywood hacking scene.
        """
        controller = AnimationController(label, duration_ms)
        text_len = len(final_text)

        def update(progress):
            result = []
            for i, char in enumerate(final_text):
                # Each character "resolves" at a different time
                char_threshold = (i / text_len) * 0.7 + 0.1
                if progress >= char_threshold:
                    result.append(char)
                else:
                    # Random glitch character
                    if secrets.randbelow(100) < intensity * 100:
                        result.append(secrets.choice(GlitchAnimation.GLITCH_CHARS))
                    else:
                        result.append(secrets.choice(string.ascii_uppercase + "0123456789"))
            try:
                label.configure(text="".join(result))
            except Exception:
                pass

        controller.animate(update, Easing.linear)

    @staticmethod
    def glitch_flicker(widget, base_color="#0f1923", glitch_color="#00ff9f",
                       duration_ms=200, flashes=3):
        """Quick color flicker — like a CRT monitor glitch."""
        flash_count = [0]
        total_flashes = flashes * 2  # on + off = 1 flash

        def _flash():
            if flash_count[0] >= total_flashes:
                try:
                    widget.configure(fg_color=base_color)
                except Exception:
                    pass
                return

            if flash_count[0] % 2 == 0:
                try:
                    widget.configure(fg_color=glitch_color)
                except Exception:
                    pass
            else:
                try:
                    widget.configure(fg_color=base_color)
                except Exception:
                    pass

            flash_count[0] += 1
            widget.after(duration_ms // total_flashes, _flash)

        _flash()

    @staticmethod
    def glitch_offset(widget, intensity=5, duration_ms=300):
        """Briefly offset the widget position like a digital glitch."""
        try:
            orig_x = widget.winfo_x()
            orig_y = widget.winfo_y()
        except Exception:
            return

        controller = AnimationController(widget, duration_ms)

        def update(progress):
            if progress < 0.8:
                ox = secrets.randbelow(intensity * 2) - intensity
                oy = secrets.randbelow(intensity // 2 + 1)
                try:
                    widget.place_configure(x=orig_x + ox, y=orig_y + oy)
                except Exception:
                    pass
            else:
                try:
                    widget.place_configure(x=orig_x, y=orig_y)
                except Exception:
                    pass

        controller.animate(update, Easing.linear)


class MatrixRainAnimation:
    """Matrix-style falling character rain on a Canvas."""

    CHARS = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモ" \
            "ヤユヨラリルレロワヲン0123456789ABCDEF"

    @staticmethod
    def start_rain(canvas, width, height, color="#00ff9f", density=25,
                   speed_ms=50):
        """
        Start matrix rain on a tkinter Canvas.
        Returns a stop function to halt the animation.
        """
        import tkinter as tk

        columns = width // 14  # character width approx 14px
        drops = [secrets.randbelow(height // 14) for _ in range(columns)]
        running = [True]

        def _draw():
            if not running[0]:
                return
            try:
                canvas.delete("rain")
            except Exception:
                return

            for i in range(columns):
                char = secrets.choice(MatrixRainAnimation.CHARS)
                x = i * 14
                y = drops[i] * 14

                # Bright head character
                try:
                    canvas.create_text(
                        x, y, text=char, fill="#ffffff",
                        font=("Consolas", 11, "bold"),
                        anchor="nw", tags="rain"
                    )
                except Exception:
                    return

                # Trailing characters (dimmer)
                for trail in range(1, 8):
                    trail_y = y - trail * 14
                    if trail_y < 0:
                        continue
                    trail_char = secrets.choice(MatrixRainAnimation.CHARS)
                    # Fade from green to dark
                    brightness = max(0, 255 - trail * 35)
                    trail_color = f"#00{brightness:02x}00"
                    try:
                        canvas.create_text(
                            x, trail_y, text=trail_char, fill=trail_color,
                            font=("Consolas", 10),
                            anchor="nw", tags="rain"
                        )
                    except Exception:
                        return

                drops[i] += 1
                if drops[i] * 14 > height or secrets.randbelow(100) > 95:
                    drops[i] = 0

            try:
                canvas.after(speed_ms, _draw)
            except Exception:
                pass

        _draw()

        def stop():
            running[0] = False
            try:
                canvas.delete("rain")
            except Exception:
                pass

        return stop


class NeonFlickerAnimation:
    """Neon sign flicker effect — like a broken neon tube."""

    @staticmethod
    def flicker_text(label, text_color="#00ff9f", dim_color="#004d30",
                     duration_ms=2000, flicker_count=8):
        """Make text flicker like a neon sign."""
        step = [0]
        total_steps = flicker_count * 2

        def _flicker():
            if step[0] >= total_steps:
                try:
                    label.configure(text_color=text_color)
                except Exception:
                    pass
                return

            if step[0] % 2 == 0:
                # Dim
                try:
                    label.configure(text_color=dim_color)
                except Exception:
                    pass
                delay = secrets.randbelow(80) + 30
            else:
                # Bright
                try:
                    label.configure(text_color=text_color)
                except Exception:
                    pass
                delay = secrets.randbelow(200) + 50

            step[0] += 1
            label.after(delay, _flicker)

        _flicker()


class TerminalBootAnimation:
    """Simulates a terminal boot sequence with scrolling text."""

    BOOT_LINES = [
        "[SYS] Initializing SecureVault v2.0...",
        "[SYS] Loading cryptographic modules... OK",
        "[SEC] AES-256-GCM cipher initialized",
        "[SEC] Argon2id KDF parameters loaded",
        "[SEC] Memory: 64MB | Iterations: 3 | Threads: 4",
        "[NET] Network isolation: ENABLED",
        "[SEC] Zero-knowledge architecture: ACTIVE",
        "[SYS] Checking vault integrity...",
        "[SYS] Vault status: ENCRYPTED ✓",
        "[SEC] Anti-tamper watchdog: ONLINE",
        "[SYS] Clipboard auto-clear: 15s",
        "[SYS] Boot complete. Awaiting authentication.",
        "",
        ">> ENTER MASTER PASSWORD TO DECRYPT VAULT",
    ]

    @staticmethod
    def play_boot(textbox, lines=None, line_delay_ms=80, char_delay_ms=15,
                  text_color="#00ff9f", on_complete=None):
        """Play a terminal boot sequence in a text widget."""
        if lines is None:
            lines = TerminalBootAnimation.BOOT_LINES

        line_idx = [0]
        char_idx = [0]

        def _type_next():
            if line_idx[0] >= len(lines):
                if on_complete:
                    on_complete()
                return

            current_line = lines[line_idx[0]]

            if char_idx[0] <= len(current_line):
                try:
                    # Clear current line and retype
                    textbox.configure(state="normal")
                    # Build full text so far
                    completed_lines = "\n".join(lines[:line_idx[0]])
                    current_partial = current_line[:char_idx[0]]
                    if completed_lines:
                        full_text = completed_lines + "\n" + current_partial + "█"
                    else:
                        full_text = current_partial + "█"

                    textbox.delete("1.0", "end")
                    textbox.insert("1.0", full_text)
                    textbox.see("end")
                    textbox.configure(state="disabled")
                except Exception:
                    pass

                char_idx[0] += 1
                textbox.after(char_delay_ms, _type_next)
            else:
                char_idx[0] = 0
                line_idx[0] += 1
                textbox.after(line_delay_ms, _type_next)

        _type_next()


class HologramAnimation:
    """Hologram scan-line effect on widgets."""

    @staticmethod
    def scan_reveal(widget, duration_ms=600, scan_color="#00ff9f"):
        """Reveal a widget with a horizontal scan line effect."""
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            # Simulate by cycling through border colors
            if progress < 0.3:
                try:
                    widget.configure(border_color=scan_color, border_width=2)
                except Exception:
                    pass
            elif progress < 0.6:
                try:
                    widget.configure(border_color=scan_color, border_width=1)
                except Exception:
                    pass
            else:
                try:
                    widget.configure(border_color="#0d3320", border_width=1)
                except Exception:
                    pass

        controller.animate(update, Easing.linear)


class DataStreamAnimation:
    """Streaming data/hex effect for backgrounds."""

    @staticmethod
    def hex_stream(label, length=32, duration_ms=3000, on_complete=None):
        """Display rapidly changing hex data like a data stream."""
        controller = AnimationController(label, duration_ms)

        def update(progress):
            hex_data = ''.join(secrets.choice('0123456789ABCDEF') for _ in range(length))
            # Insert spaces every 4 chars
            formatted = ' '.join(hex_data[i:i+4] for i in range(0, len(hex_data), 4))
            try:
                label.configure(text=formatted)
            except Exception:
                pass

        controller.animate(update, Easing.linear, on_complete)