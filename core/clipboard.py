"""
Secure Clipboard Manager — Auto-clears after timeout
"""
import threading
import pyperclip

class ClipboardManager:
    _clear_timer = None
    CLEAR_TIMEOUT = 15  # seconds

    @classmethod
    def copy_and_clear(cls, text: str, timeout: int = None):
        """Copy text to clipboard and auto-clear after timeout."""
        pyperclip.copy(text)

        if cls._clear_timer:
            cls._clear_timer.cancel()

        cls._clear_timer = threading.Timer(
            timeout or cls.CLEAR_TIMEOUT, cls._clear_clipboard
        )
        cls._clear_timer.daemon = True
        cls._clear_timer.start()

    @staticmethod
    def _clear_clipboard():
        pyperclip.copy("")