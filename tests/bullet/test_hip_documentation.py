"""Portable documentation/source checks only; they do not execute PowerShell."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HipDocumentationTests(unittest.TestCase):
    def test_current_recipe_states_minimum_and_runtime_boundary(self):
        readme = (ROOT / "tools/bullet/README.md").read_text()
        self.assertIn("Rust **1.87 or newer**", readme)
        self.assertIn("run_hip_smoke.ps1", readme)
        self.assertIn("GPU-free scheduled slot", readme)
        self.assertIn("never alongside the live AMD trainer", readme)
        self.assertNotIn("2>&1 | Tee-Object", readme)
        self.assertIn("UNVERIFIED", readme)

    def test_process_source_no_longer_rejects_all_python_or_compilers(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        self.assertNotIn("Production/build process present", source)
        self.assertIn("[string[]]$GateExeNames", source)
        self.assertIn("[string[]]$GateExePaths", source)
        self.assertIn("Get-PythonScriptArgument", source)

    def test_gpu_source_has_engine_aggregation_and_five_snapshots(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        self.assertIn("$engineTotals[$engineKey] += $util", source)
        self.assertIn("$engineTotals[$engineKey] -gt 2", source)
        self.assertIn("$sampleIndex -lt 5", source)
        self.assertIn("$sampleIndex -lt 4", source)
        self.assertNotIn("$util -gt 0", source)

    def test_production_basename_pattern_covers_final2_regressions(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        patterns = re.findall(r"\$basename -match '([^']+)'", source)
        # Exercise the literal source regex portably; PowerShell behavior is
        # covered by the separately shipped, Windows-only regression script.
        pattern = next((p for p in patterns if "train_resid" in p), "(?!)")
        for name in ("train_resid_v2.py", "TRAIN_RESID_V3B.PY",
                     "r11_train_entry.py", "R11_TRAIN_ENTRY", "selfplay.py"):
            with self.subTest(name=name):
                self.assertRegex(name.lower(), pattern)
        for name in ("README_train_resid_v2.py", "inspect.py", "train_metrics.py"):
            self.assertIsNone(re.search(pattern, name, re.IGNORECASE))

    def test_unknown_process_metadata_and_guard_tag_refuse(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        behavior = (ROOT / "tests/bullet/test_hip_launcher.ps1").read_text()
        self.assertIn("Production status unknown: unreadable command line", source)
        self.assertIn("$commandLine -match '--guard-tag'", source)
        self.assertIn("UnauthorizedAccessException", behavior)
        self.assertIn("New-TestProcess 'python.exe' 'python.exe'", behavior)

    def test_wddm_source_patterns_allow_spaces_and_graphics_indices(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        identity = re.search(r"\$sample.Name -notmatch '([^']+)'", source).group(1)
        identity = re.sub(r"\(\?<([a-z]+)>", r"(?P<\1>", identity)
        busy = re.search(r"\$kind -notmatch '([^']+)'", source).group(1)
        for kind in ("3D", "Compute", "Compute_1", "Compute 1", "Graphics_1", "Graphics_99"):
            self.assertIsNotNone(re.fullmatch(busy, kind, re.IGNORECASE), kind)
        for kind in ("Video Decode", "Video Processing", "Graphics_1", "Compute 1"):
            name = "pid_1_luid_0x0_0x1_phys_0_eng_1_engtype_" + kind
            self.assertIsNotNone(re.fullmatch(identity, name, re.IGNORECASE), name)
        for kind in ("Copy", "Video Decode"):
            self.assertIsNone(re.fullmatch(busy, kind, re.IGNORECASE))
        key = next(line for line in source.splitlines() if "$engineKey =" in line)
        self.assertNotIn("$Matches.kind", key)

    def test_gate_names_support_comma_separated_cli(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        readme = (ROOT / "tools/bullet/README.md").read_text()
        self.assertIn("function ConvertTo-GateExeNames", source)
        self.assertIn("$value -split ','", source)
        self.assertIn("$name = $entry.Trim()", source)
        self.assertEqual(source.count("$GateExeNames = @(ConvertTo-GateExeNames $GateExeNames)"), 2)
        self.assertIn("-GateExeNames 'forge_gate_candidate.exe,stockfish_gate.exe'", readme)

    def test_scratch_drive_is_explicit_throughout_launcher(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        readme = (ROOT / "tools/bullet/README.md").read_text()
        self.assertIn("[string]$ScratchDrive", source)
        self.assertNotIn("F:", source)
        self.assertIn("[IO.DriveInfo]::new($scratchRoot)", source)
        self.assertIn("Join-Path $ScratchDrive 'astra_bullet_smoke'", source)
        self.assertIn("Join-Path $ScratchDrive 'astra_bullet_cargo_target'", source)
        calls = [line.strip() for line in source.splitlines()
                 if line.strip().startswith(("Assert-HipSlot ", "Assert-HipDiskSpace ", "Assert-ScratchPath "))]
        self.assertTrue(calls)
        for call in calls:
            self.assertIn("-ScratchDrive $ScratchDrive", call)
        self.assertIn("scratch_drive=$ScratchDrive", source)
        self.assertIn("-ScratchDrive '<APPROVED_DRIVE_LETTER>:'", readme)

    def test_gate_basename_pattern_rejects_drive_relative_paths(self):
        source = (ROOT / "tools/bullet/run_hip_smoke.ps1").read_text()
        forbidden = re.search(r"\$name -match '([^']+)' -or \$name -notmatch", source).group(1)
        for name in ("R:forge.exe", r"R:\gates\forge.exe", "forge*.exe", "gates/forge.exe"):
            self.assertIsNotNone(re.search(forbidden, name), name)
        self.assertIsNone(re.search(forbidden, "forge_gate.exe"))

    def test_current_recipe_describes_refined_policy_and_runtime_limit(self):
        readme = (ROOT / "tools/bullet/README.md").read_text()
        for text in ("five valid snapshots", "strictly greater than 2%",
                     "same physical GPU and engine", "GateExeNames", "GateExePaths",
                     "Unrelated Python", "compiler processes", "Compute_0",
                     "qa_policy_refinement"):
            self.assertIn(text, readme)

    def test_launcher_and_behavioral_regressions_are_shipped(self):
        self.assertTrue((ROOT / "tools/bullet/run_hip_smoke.ps1").is_file())
        self.assertTrue((ROOT / "tests/bullet/test_hip_launcher.ps1").is_file())


if __name__ == "__main__":
    unittest.main()
