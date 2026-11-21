"""AC-5: the build runs with the network blocked and never imports anthropic or yaml."""
import subprocess
import sys
import tempfile
import unittest

from .helpers import ROOT

GUARDED_BUILD = r"""
import socket, sys

def refuse(*args, **kwargs):
    raise OSError("network access is blocked in this test")

socket.socket.connect = refuse
socket.socket.connect_ex = refuse
socket.create_connection = refuse
socket.getaddrinfo = refuse

from akg.__main__ import main
code = main(sys.argv[1:])
loaded = [m for m in ("anthropic", "yaml") if m in sys.modules]
if loaded:
    print("loaded: " + ", ".join(loaded))
    sys.exit(3)
sys.exit(code)
"""


class OfflineTests(unittest.TestCase):
    def run_guarded(self, *args: str, size: str = "sample") -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as out:
            return subprocess.run([sys.executable, "-c", GUARDED_BUILD, "build", "--seed", "42", "--size", size, "--out", out, *args],
                                  cwd=ROOT, capture_output=True, text=True)

    def test_ac5_build_is_offline_and_never_imports_anthropic(self):
        for size in ("sample", "full"):  # full size with AI text since 010 (AC-6)
            for text in ("templated", "ai"):
                with self.subTest(size=size, text=text):
                    result = self.run_guarded("--text", text, size=size)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
