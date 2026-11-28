"""Opus High-Value Request (OPUS-2711-GATE-DEPTH, 23:24 PC):
Declared 1,000g @ 250,000 nodes: live-loop r0202 vs live best r0067,
BOTH on base_r15dsg.exe with identical 45 live Big Tune v3_uci_options (concurrency=8).
Tests Opus's hypothesis that part of the 134-round loop stall is stronger nets rejected at 50k!
"""
from __future__ import annotations

import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
PY = str(LAB / "venv/Scripts/python.exe")
RUNNER = str(FIX / "run_net_match.py")
BASE_EXE = str(FIX / "builds/base_r15dsg.exe")
R0202 = str(LAB / "runs/forge/r0202/train/cand.fnn3")
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3")


def main() -> int:
    name = "OPUS_r0202_vs_r0067_1000g_250k"
    if (FIX / "matches" / name / "summary.json").exists():
        print(f"SKIP (done): {name}", flush=True)
        return 0
    print(f"=== LAUNCH {name} (1000g @ 250k, base_r15dsg both sides, concurrency=8) ===", flush=True)
    r = subprocess.run([
        PY, RUNNER,
        "--name", name,
        "--cand-exe", BASE_EXE, "--base-exe", BASE_EXE,
        "--cand-net", R0202, "--base-net", R0067,
        "--games", "1000", "--nodes", "250000", "--concurrency", "8", "--seed", "202611750",
        "--rule", "Opus high-value gate-depth hypothesis test (OPUS-2711-GATE-DEPTH): live-loop r0202 vs live best r0067, 1000g @ 250,000 nodes, identical base_r15dsg.exe & 45 Big Tune options",
    ])
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
