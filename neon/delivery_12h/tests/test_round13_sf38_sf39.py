"""Fail-before / pass-after verification test for Round 13 SF38 (major corrhist) and SF39 (minor+major corrhist)."""
from __future__ import annotations

import os
import re
import subprocess
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
    base_nd = full_bench13(FIX / "builds/base_r15dsg.exe")
    ov = os.environ.get("FORGE_TEST_EXE", "").strip()
    if ov:
        nd = full_bench13(Path(ov))
        assert nd < int(base_nd * 0.95), f"Expected >=5% FULL bench13 reduction vs {base_nd}, got {nd}"
        print(f"OVERRIDE PASS: {ov} nodes={nd:,} vs base={base_nd:,}")
        return 0
    for nm in ("SF38_corrhist_major.exe", "SF39_corrhist_minor_plus_major.exe"):
        nd = full_bench13(FIX / "builds" / nm)
        assert nd < int(base_nd * 0.95), f"{nm} expected >=5% FULL bench13 reduction vs {base_nd}, got {nd}"
        print(f"PASS {nm}: nodes={nd:,} vs base={base_nd:,} ({100*(nd-base_nd)/base_nd:+.2f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
