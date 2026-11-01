"""Portable package guards only. These do NOT execute PowerShell/Windows."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/grok-pc-safe-run/scripts/Invoke-GrokPcSafeRun.ps1'

class SafeRunStatic(unittest.TestCase):
    def source(self):
        self.assertTrue(SCRIPT.is_file(), 'Windows safe launcher not implemented')
        return SCRIPT.read_text()
    def test_native_stderr_is_captured_through_process_streams(self):
        text = self.source()
        self.assertIn('RedirectStandardError = $true', text)
        self.assertIn('RedirectStandardOutput = $true', text)
        self.assertNotIn('2>&1', text)
        self.assertIn('GetAwaiter().GetResult()', text)
    def test_owned_process_never_terminates_or_enumerates_other_processes(self):
        text = self.source()
        self.assertNotRegex(text, r'(?i)\b(?:Stop-Process|Get-Process|taskkill|Remove-Item)\b|\.Kill\s*\(')
        self.assertIn('GetCurrentProcess()', text)
        self.assertIn("InvocationName -ne '.'", text)
    def test_affinity_idle_and_thread_limits_are_explicit(self):
        text = self.source()
        self.assertIn('$cpus.Count -gt 2', text)
        self.assertIn('$j.worker_threads -gt 2', text)
        self.assertIn('PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle', text)
        self.assertLess(text.index('PriorityClass = [Diagnostics.ProcessPriorityClass]::Idle'), text.index('$child.Start()'))
        self.assertIn("'OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'", text)
        self.assertIn('explicit thread argument', text)
    def test_d_only_protected_roots_disk_floor_and_bound_executable(self):
        text = self.source()
        for required in ('Assert-DPath', 'ReparsePoint', 'ProtectedRoots', '32768', 'queue_state.json', 'executable_sha256', 'ReadOnly'):
            self.assertIn(required, text)
        self.assertIn('$j.minimum_free_mib -lt 32768', text)
        self.assertIn('Get-FileHash -Algorithm SHA256', text)
    def test_argument_paths_are_bound_and_relative_paths_refused(self):
        text = self.source()
        self.assertIn('Relative path-like argument refused', text)
        self.assertIn('Argument path is not within declared read_paths/write_paths', text)
        self.assertIn('Response file requires an explicitly declared existing read path', text)
        self.assertIn('Protected production root or its ancestor', text)
        self.assertIn('$blocked.StartsWith($full+', text)
    def test_failed_sink_keeps_draining_and_records_capture_failure(self):
        text = self.source()
        self.assertIn('if (failure == null)', text)
        self.assertIn('await source.ReadAsync', text)
        self.assertIn('capture_errors', text)
        self.assertIn('native_exit_code', text)
        self.assertIn('finally', text)

if __name__ == '__main__': unittest.main()
