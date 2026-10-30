#!/usr/bin/env python3
"""PORTABLE STATIC GUARDS ONLY: does not execute PowerShell or qualify Windows.

IDEA_SOURCE: item 7A review of PowerShell 5.1 NativeCommandError conversion.
Behavioral validation lives in test_idle_launcher.ps1 and requires Windows.
"""
from pathlib import Path
import re
import unittest


LAUNCHER = Path(__file__).resolve().parents[2] / "tools/data/run_idle_spare.ps1"


class IdleLauncherStaticGuards(unittest.TestCase):
    """Structural safety guards; passing is not Windows runtime evidence."""

    def test_static_native_stderr_does_not_enter_powershell_error_stream(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?m)^\s*&\s*\$Python\b")
        self.assertRegex(source, r"RedirectStandardOutput\s*=\s*\$true")
        self.assertRegex(source, r"RedirectStandardError\s*=\s*\$true")
        self.assertRegex(source, r"UseShellExecute\s*=\s*\$false")

    def test_static_both_async_stream_copies_start_before_waiting_for_exit(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        stdout = re.search(r"DrainAsync\(\$Child\.StandardOutput\.BaseStream,", source)
        stderr = re.search(r"DrainAsync\(\$Child\.StandardError\.BaseStream,", source)
        wait = re.search(r"\.WaitForExit\(\)", source)
        self.assertIsNotNone(stdout, "stdout must drain asynchronously")
        self.assertIsNotNone(stderr, "stderr must drain asynchronously")
        self.assertIsNotNone(wait, "native exit must be observed")
        self.assertLess(max(stdout.start(), stderr.start()), wait.start())

    def test_static_capture_fault_is_recorded_after_child_exit(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertRegex(source, r"if \(captureError == null\)")
        self.assertRegex(source, r"catch \(Exception error\) \{ captureError = error\.ToString\(\); \}")
        self.assertRegex(source, r"capture_errors\s*=\s*@\(\$CaptureErrors\)")
        self.assertRegex(source, r"if \(\$CaptureErrors\.Count -ne 0\)")
        self.assertLess(source.index("$Child.WaitForExit()"), source.index("capture_errors="))

    def test_static_no_process_termination_or_evidence_deletion(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?i)\b(?:Stop-Process|taskkill|Remove-Item)\b|\.Kill\(")


if __name__ == "__main__":
    print("PORTABLE STATIC GUARDS ONLY; Windows/PowerShell runtime remains UNVERIFIED.")
    unittest.main()
