"""
Typewriter Animation — Character-by-character text reveal.
"""

class TypewriterAnimation:
    """Reveals text one character at a time with optional cursor blink."""

    @staticmethod
    def type_text(label, full_text: str, char_delay_ms=45, cursor="▌",
                  on_complete=None):
        """Type text into a label one character at a time."""
        index = [0]
        blink_state = [True]

        def _type_next():
            if index[0] <= len(full_text):
                displayed = full_text[:index[0]]
                cursor_char = cursor if blink_state[0] else " "
                try:
                    label.configure(text=displayed + cursor_char)
                except Exception:
                    return
                index[0] += 1
                blink_state[0] = not blink_state[0]
                label.after(char_delay_ms, _type_next)
            else:
                # Remove cursor when done
                try:
                    label.configure(text=full_text)
                except Exception:
                    pass
                if on_complete:
                    on_complete()

        _type_next()

    @staticmethod
    def type_text_with_sound(label, full_text: str, char_delay_ms=45):
        """Type text with simulated keystroke timing variation."""
        import secrets
        index = [0]

        def _type_next():
            if index[0] <= len(full_text):
                displayed = full_text[:index[0]]
                try:
                    label.configure(text=displayed + "▌")
                except Exception:
                    return
                index[0] += 1
                # Randomize delay slightly for natural feel
                jitter = secrets.randbelow(30) - 15
                delay = max(20, char_delay_ms + jitter)
                label.after(delay, _type_next)
            else:
                try:
                    label.configure(text=full_text)
                except Exception:
                    pass

        _type_next()