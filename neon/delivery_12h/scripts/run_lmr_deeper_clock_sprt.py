"""Declared Clean Equal-Time SPRT [0, 10] (cap 4,000g @ 6+0.06, concurrency=7) for LmrDeeperShallower=true.

Aligned with OPUS-2811-ARM-B-RECOUNTED (05:57 PC):
  - Zero C++ changes (live PGO forge.exe + r0067 on both sides; ONLY LmrDeeperShallower=true differs!).
  - Normalized SPRT [0, 10] (alpha=0.05, beta=0.05), hard cap 4,000 games, 6+0.06, concurrency=7.
  - Cap reached without decision => inconclusive. Never pooled with prior 50k runs.
  - MUST ONLY RUN ON 100% IDLE GPU + 100% IDLE CPU (run_net_match.py sets CLOCK_MATCH_RUNNING).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
PY = str(LAB / "venv/Scripts/python.exe")
RUNNER = str(FIX / "run_net_match.py")
LIVE_PGO_EXE = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
BOOK = LAB / "tools/book/UHO_Lichess_4852_v1.epd"
DECL_PATH = FIX / "LMR_DEEPER_CLOCK_DECLARATION.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    name = "CLK_LmrDeeperShallower_SPRT_0_10_6p006"
    decl = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S PC"),
        "request_ref": "OPUS-2811-ARM-B-RECOUNTED Point 3 (05:57 PC)",
        "name": name,
        "exe_both": str(LIVE_PGO_EXE),
        "exe_sha256": sha256_file(LIVE_PGO_EXE),
        "net_both": str(R0067),
        "net_sha256": sha256_file(R0067),
        "book": str(BOOK),
        "book_sha256": sha256_file(BOOK),
        "single_option_diff": {"cand": {"LmrDeeperShallower": True}, "base": {"LmrDeeperShallower": False}},
        "tc": "6+0.06",
        "concurrency": 7,
        "seed": 202611971,
        "sprt": {"elo0": 0, "elo1": 10, "alpha": 0.05, "beta": 0.05, "model": "normalized"},
        "max_games": 4000,
        "prior_50k_disclosure": "LmrDeeper_alone_vs_base_1000g_50k scored +8.34 [-4.06, +20.76]; NEVER pooled with this clock SPRT.",
        "decision_rule": "H1 accepted => eligible for lab-place-a-change 1-line config.forge.toml:214 placement; H0 accepted => reject; cap (4,000g) without decision => inconclusive.",
    }
    DECL_PATH.write_text(json.dumps(decl, indent=2), encoding="utf-8")
    print("WROTE DECLARATION:", DECL_PATH, flush=True)

    cmd = [
        PY, RUNNER,
        "--name", name,
        "--cand-exe", str(LIVE_PGO_EXE), "--base-exe", str(LIVE_PGO_EXE),
        "--cand-net", str(R0067), "--base-net", str(R0067),
        "--games", "4000", "--nodes", "0", "--tc", "6+0.06",
        "--concurrency", "7", "--seed", "202611971",
        "--sprt", "0,10",
        "--cand-opt", "LmrDeeperShallower=true",
        "--rule", decl["decision_rule"],
    ]
    r = subprocess.run(cmd, text=True)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
