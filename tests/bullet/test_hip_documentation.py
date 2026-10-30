"""Portable documentation regression; native behavior has a separate PS5.1 test."""
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

    def test_launcher_and_behavioral_regressions_are_shipped(self):
        self.assertTrue((ROOT / "tools/bullet/run_hip_smoke.ps1").is_file())
        self.assertTrue((ROOT / "tests/bullet/test_hip_launcher.ps1").is_file())


if __name__ == "__main__":
    unittest.main()
