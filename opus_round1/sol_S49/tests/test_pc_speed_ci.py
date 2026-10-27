#!/usr/bin/env python3
"""Tests for pc_speed_ci_20261027.ps1 (needs pwsh 7 on PATH). No engine is run:
  * the script's own -SelfTest (pure functions + the static affinity check);
  * -PlanOnly with fixtures (-FixtureLiveMask / -FixtureCoreCount, fixture manifest and RUN_INFO dirs) for the core
    choice and every refusal path;
  * static checks on the script text: one ProcessorAffinity assignment (from the validated mask), no kill/delete
    commands, every write goes under -OutDir.

  python -I -B tests/test_pc_speed_ci.py        (PS49_SCRIPT=<path> tests another copy; used by the mutation check)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(os.environ.get("PS49_SCRIPT", Path(__file__).resolve().parents[1] / "pc_speed_ci_20261027.ps1"))
PWSH = os.environ.get("PWSH", "pwsh")


def run(*args: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(SCRIPT), *args], capture_output=True,
                          text=True, timeout=timeout)


class SelfTest(unittest.TestCase):
    def test_selftest_passes(self):
        r = run("-SelfTest")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m = re.search(r"SELFTEST checks=(\d+) failures=(\d+)", r.stdout)
        self.assertIsNotNone(m, r.stdout)
        self.assertGreaterEqual(int(m.group(1)), 20)
        self.assertEqual(int(m.group(2)), 0)


class Plan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.empty_runinfo = self.root / "runinfo_empty"
        self.empty_runinfo.mkdir()
        self.no_manifest = str(self.root / "no_manifest.json")
        self.n = 0

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, live: str, *extra: str, runinfo: Path | None = None, manifest: str | None = None, cores: int = 16):
        self.n += 1
        out = self.root / f"out{self.n}"
        r = run("-PlanOnly", "-OutDir", str(out), "-FixtureLiveMask", live, "-FixtureCoreCount", str(cores),
                "-RunInfoRoot", str(runinfo or self.empty_runinfo), "-Manifest", manifest or self.no_manifest,
                "-TempCsv", str(self.root / "no.csv"), *extra)
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8-sig")) if (out / "plan.json").exists() else None
        return r, plan

    def assert_safe(self, plan: dict):
        c = plan["chosen_core"]
        self.assertGreaterEqual(c, 4)
        self.assertNotIn(c, plan["used"])
        self.assertNotIn(c, plan["reserved"])

    def test_pc_like_gate_on_4_15_refuses(self):
        r, plan = self.plan("0xFFF0")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("REFUSED", r.stdout)
        self.assertEqual(plan["chosen_core"], -1)

    def test_gate_on_4_13_picks_15(self):
        r, plan = self.plan("0x3FF0")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(plan["chosen_core"], 15)
        self.assert_safe(plan)

    def test_manifest_affinity_field_is_honoured(self):
        man = self.root / "manifest.json"
        man.write_text(json.dumps({"base": {}, "gates": [{"gate": 1, "affinity": "0x8000"}]}), encoding="utf-8-sig")
        r, plan = self.plan("0x3FF0", manifest=str(man))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(plan["manifest_cores"], [15])
        self.assertEqual(plan["chosen_core"], 14)
        self.assert_safe(plan)

    def test_recent_runinfo_affinity_blocks_and_old_runinfo_is_ignored(self):
        ri = self.root / "runinfo"
        (ri / "gate1_x").mkdir(parents=True)
        f = ri / "gate1_x" / "RUN_INFO.json"
        f.write_text(json.dumps({"affinity": "0xFFF0 (CPUs 4-15)"}), encoding="utf-8")
        r, plan = self.plan("0x0", runinfo=ri)
        self.assertEqual(r.returncode, 3, r.stdout)
        old = time.time() - 72 * 3600
        os.utime(f, (old, old))
        r, plan = self.plan("0x0", runinfo=ri)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(plan["runinfo_cores"], [])
        self.assertEqual(plan["chosen_core"], 15)

    def test_requested_core(self):
        r, plan = self.plan("0x3FF0", "-Core", "5")
        self.assertEqual(r.returncode, 3, r.stdout)
        r, plan = self.plan("0x3FF0", "-Core", "2")
        self.assertEqual(r.returncode, 3, r.stdout)
        r, plan = self.plan("0x3FF0", "-Core", "14")
        self.assertEqual((r.returncode, plan["chosen_core"]), (0, 14), r.stdout)

    def test_list_parameters_under_pwsh_file(self):
        # 'pwsh -File' passes "13,16" as one string; it must mean depths 13 and 16 (not 1316 -> engine depth 64).
        r, plan = self.plan("0x3FF0", "-Depths", "13,16")
        self.assertEqual(r.returncode, 0, r.stdout)
        for bad in ("30", "0", "13,64", "1316"):
            r, _ = self.plan("0x3FF0", "-Depths", bad)
            self.assertEqual(r.returncode, 2, bad + ": " + r.stdout)
            self.assertIn("-Depths must be 1..24", r.stdout)
        r, plan = self.plan("0x3FF0", "-ReservedCores", "0,1,2,3,15")
        self.assertEqual((r.returncode, plan["chosen_core"], plan["reserved"]), (0, 14, [0, 1, 2, 3, 15]), r.stdout)

    def test_cores_0_3_must_stay_reserved_without_boxonly(self):
        r, _ = self.plan("0x0", "-ReservedCores", "4,5")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("cores 0-3 must stay reserved", r.stdout)

    def test_boxonly_refuses_where_gates_run(self):
        r, _ = self.plan("0x3FF0", "-BoxOnly", "-ReservedCores", "0")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("-BoxOnly but this machine runs gates", r.stdout)

    def test_small_box_without_gates(self):
        # A 4-core quiet runner: -BoxOnly with core 0 reserved picks core 3 (live mask empty, no RUN_INFO).
        self.n += 1
        out = self.root / f"out{self.n}"
        r = run("-PlanOnly", "-BoxOnly", "-ReservedCores", "0", "-OutDir", str(out), "-FixtureCoreCount", "4",
                "-RunInfoRoot", str(self.empty_runinfo), "-Manifest", self.no_manifest, "-TempCsv", str(self.root / "no.csv"))
        # -FixtureLiveMask not given: the real live scan runs; on a machine with a gate this refuses (also correct).
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8-sig")) if (out / "plan.json").exists() else None
        if "machine runs gates" in r.stdout:
            self.assertEqual(r.returncode, 3)
        else:
            self.assertEqual((r.returncode, plan["chosen_core"]), (0, 3), r.stdout)

    def test_protected_and_nonempty_outdirs(self):
        bad = self.root / "forge_push" / "x"
        r = run("-PlanOnly", "-OutDir", str(bad), "-FixtureLiveMask", "0x0", "-FixtureCoreCount", "16")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertFalse(bad.exists(), "nothing may be created under a protected path")
        full = self.root / "full"
        full.mkdir()
        (full / "x.txt").write_text("x")
        r = run("-PlanOnly", "-OutDir", str(full), "-FixtureLiveMask", "0x0", "-FixtureCoreCount", "16")
        self.assertEqual(r.returncode, 2, r.stdout)

    def test_fixtures_only_with_planonly(self):
        r = run("-OutDir", str(self.root / "o"), "-FixtureLiveMask", "0x0", "-ExeA", "a", "-ExeB", "b")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("fixtures are allowed with -PlanOnly only", r.stdout)


class Static(unittest.TestCase):
    src = SCRIPT.read_text(encoding="utf-8")

    def code_lines(self):
        out = []
        in_help = False
        for line in self.src.splitlines():
            s = line.strip()
            if s.startswith("<#"):
                in_help = True
            if in_help:
                if s.endswith("#>"):
                    in_help = False
                continue
            if s.startswith("#"):
                continue
            out.append(line)
        return out

    def test_single_affinity_assignment_from_validated_mask(self):
        assigns = [l for l in self.code_lines() if re.search(r"ProcessorAffinity\s*=", l) and "regex" not in l]
        self.assertEqual(len(assigns), 1, assigns)
        self.assertIn("[IntPtr]$script:ChosenMask", assigns[0])
        sets = [l.strip() for l in self.code_lines() if re.search(r"\$script:ChosenMask\s*=", l) and "regex" not in l]
        self.assertEqual(sets, ["$script:ChosenMask = [int64]0", "$script:ChosenMask = [int64]1 -shl $sel.Core"])
        # the mask is set only after the refusal exit for a negative core
        i_refuse = self.src.index("if ($sel.Core -lt 0) { exit 3 }")
        i_set = self.src.index("$script:ChosenMask = [int64]1 -shl $sel.Core")
        self.assertLess(i_refuse, i_set)

    def test_no_kill_or_delete(self):
        code = "\n".join(self.code_lines())
        for bad in ("Stop-Process", "taskkill", "Remove-Item", "Move-Item", ".Kill(", "Rename-Item", "Clear-Content"):
            self.assertNotIn(bad, code, bad)

    def test_every_write_targets_outdir(self):
        writers = ("Set-Content", "Out-File", "Add-Content", "Export-Csv", "Copy-Item", "New-Item")
        for l in self.code_lines():
            if any(w in l for w in writers):
                self.assertTrue(any(v in l for v in ("$OutDir", "$bin", "$csv", "$exes")), l.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
