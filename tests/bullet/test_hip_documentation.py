"""Portable documentation/source checks only; they do not execute PowerShell."""
from pathlib import Path
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
