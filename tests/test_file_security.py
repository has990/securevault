import platform
import subprocess
import tempfile
import unittest
from pathlib import Path


class FileSecurityTests(unittest.TestCase):

    @unittest.skipUnless(
        platform.system() == "Windows",
        "Windows ACL test requires Windows",
    )
    def test_windows_acl_removes_inherited_permissions(self):
        """Sensitive files should not inherit the parent ACL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "secret.db"
            path.write_bytes(b"test")

            sid_result = subprocess.run(
                [
                    "whoami",
                    "/user",
                    "/fo",
                    "csv",
                    "/nh",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            line = sid_result.stdout.strip()
            parts = line.split(",")
            self.assertGreaterEqual(len(parts), 2)
            sid = parts[1].strip().strip('"')
            self.assertTrue(sid.startswith("S-1-"))

            subprocess.run(
                [
                    "icacls",
                    str(path),
                    "/inheritance:r",
                    "/grant:r",
                    f"*{sid}:F",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )

            acl_result = subprocess.run(
                ["icacls", str(path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            acl_lines = acl_result.stdout.splitlines()
            permission_lines = [
                item for item in acl_lines
                if ":" in item and not item.rstrip().endswith(":")
            ]
            self.assertTrue(permission_lines)
            self.assertFalse(
                any("(I)" in item for item in permission_lines)
            )
