"""Fail-before / pass-after verification test for Round 12 SF34 and SF36 under live FULL 45-param Big Tune config."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
CFG = tomllib.loads((LAB / "pipeline/config.forge.toml").read_text(encoding="utf-8"))["engine"]["v3_uci_options"]


def full_bench13(exe: Path) -> int:
    opts = "\n".join(
        f"setoption name {k} value {str(v).lower() if isinstance(v, bool) else v}"
        for k, v in CFG.items()
    )
    inp = (
        f"uci\nsetoption name NNUEArchFile value {str(R0067).replace(chr(92), '/')}\n"
        f"setoption name NNUEArch value true\n{opts}\nisready\nbench 13\nquit\n"
    )
    r = subprocess.run([str(exe)], input=inp, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    m = re.findall(r"nodes\s+(\d+)\s+time\s+(\d+)\s+nps\s+(\d+)", r.stdout)
    assert m, r.stdout[-200:]
    return int(m[-1][0])


def main() -> int:
    base_nodes = full_bench13(FIX / "builds/base_r15dsg.exe")
    override = os.environ.get("FORGE_TEST_EXE", "").strip()
    if override:
        exe = Path(override)
        nd = full_bench13(exe)
        # Fail-before: base binary has identical node count (576,063), whereas SF34/SF36 cut nodes by >=10%
        assert nd < int(base_nodes * 0.90), f"Expected >=10% FULL bench13 reduction vs {base_nodes}, got {nd}"
        print(f"OVERRIDE PASS: {exe.name} nodes={nd} vs base={base_nodes}")
        return 0

    for nm in ("SF34_tactical_cutoff_quiet_malus_and_prior_refute.exe", "SF36_threat_quiet_move_ordering.exe"):
        nd = full_bench13(FIX / "builds" / nm)
        assert nd < int(base_nodes * 0.90), f"{nm} failed >=10% FULL bench13 reduction: {nd} vs {base_nodes}"
        print(f"PASS {nm}: nodes={nd:,} vs base={base_nodes:,} ({100*(nd-base_nodes)/base_nodes:+.2f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
