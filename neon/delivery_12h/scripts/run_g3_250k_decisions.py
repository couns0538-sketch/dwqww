"""Opus Point 3 Decision Matches (OPUS-2711-G3-READINGS, 22:40 PC):
Lab's own 15-Nov rule: nets are DECIDED at 250,000 nodes; 50k is only a filter.
Runs sequentially with concurrency=8 (<= 8 cores / 16 threads, zero other engine games!):
  1. G3_FULL25_vs_r0067_600g_250k (pre-declared, fresh seed 202611701)
  2. G3_FULL25_vs_r0202_600g_250k (pre-declared, fresh seed 202611702)
"""
from __future__ import annotations

import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
PY = str(LAB / "venv/Scripts/python.exe")
RUNNER = str(FIX / "run_net_match.py")
V3P_EXE = str(FIX / "builds/v3p_fused_v3_engine.exe")
BASE_EXE = str(FIX / "builds/base_r15dsg.exe")
G3_NET = str(FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/cand.fnn3")
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3")
R0202 = str(LAB / "runs/forge/r0202/train/cand.fnn3")


def main() -> int:
    jobs = [
        (
            "G3_FULL25_vs_r0067_600g_250k",
            R0067,
            202611701,
            "Opus Point 3 250k decision match: G3_FULL25 (1024w Pairwise+PSQT) vs live best r0067 (768w SCReLU), 600g @ 250,000 nodes",
        ),
        (
            "G3_FULL25_vs_r0202_600g_250k",
            R0202,
            202611702,
            "Opus Point 3 250k decision match (exact same r0178..r0202 25r window): G3_FULL25 vs r0202 (768w SCReLU), 600g @ 250,000 nodes",
        ),
    ]
    for name, base_net, seed, rule in jobs:
        if (FIX / "matches" / name / "summary.json").exists():
            print(f"SKIP (done): {name}", flush=True)
            continue
        print(f"=== LAUNCH {name} (600g @ 250k, concurrency=8) ===", flush=True)
        r = subprocess.run([
            PY, RUNNER,
            "--name", name,
            "--cand-exe", V3P_EXE, "--base-exe", BASE_EXE,
            "--cand-net", G3_NET, "--base-net", base_net,
            "--games", "600", "--nodes", "250000", "--concurrency", "8", "--seed", str(seed),
            "--rule", rule,
        ])
        if r.returncode != 0:
            return r.returncode
    print("G3_250K_DECISION_MATCHES_COMPLETE.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
