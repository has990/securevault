#!/usr/bin/env python3
"""
SecureVault v2.0 — Ultimate High-Security Password Manager
Run this file to launch the application.

Features:
- AES-256-GCM encryption with Argon2id key derivation
- Decoy vault with plausible deniability
- Per-password secret keys
- Duress/panic password system
- Stealth mode disguise
- Animated GUI with smooth transitions
- Breach detection, TOTP, tamper detection
"""
import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import SecureVaultApp


def main():
    # Pre-flight checks
    _check_dependencies()
    _ensure_data_directory()

    # Launch
    app = SecureVaultApp()
    app.mainloop()


def _check_dependencies():
    """Verify all required packages are installed."""
    required = {
        "customtkinter": "customtkinter",
        "cryptography": "cryptography",
        "argon2": "argon2-cffi",
        "pyperclip": "pyperclip",
    }
    missing = []
    for import_name, pip_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("❌ Missing dependencies detected!")
        print(f"   Run: pip install {' '.join(missing)}")
        sys.exit(1)


def _ensure_data_directory():
    """Create the SecureVault data directory if it doesn't exist."""
    from pathlib import Path
    data_dir = Path.home() / ".securevault"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Set restrictive permissions (owner-only on Unix)
    try:
        os.chmod(data_dir, 0o700)
    except OSError:
        pass  # Windows doesn't support Unix permissions


if __name__ == "__main__":
    main()