"""GPU-Idle Clock Time-Management Screen Runner (6+0.06, 600g each, neon/CLOCK_MATCH_RUNNING enforced!).

Run ONLY when GPU is 100% idle and no other heavy CPU jobs are running!
Screens:
  1. SF17_tm_bestmove_avg_eval vs base_r15dsg (r0067, 6+0.06)
  2. SF18_tm_ply_curve vs base_r15dsg (r0067, 6+0.06)
  3. TmNodeShare=true alone vs base_r15dsg (6+0.06) — explicitly noting Opus Point 4 prior result:
     Task 2D S7 (TmNodeShare+TmFinishIteration+AspCappedReopen+AspArmLate) scored -32.2 [-49.0, -15.6] Elo.
  4. TmFinishIteration=true alone vs base_r15dsg (6+0.06) — same prior disclosure.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
PY = str(LAB / "venv/Scripts/python.exe")
FIX = LAB / "neon/forge_fixes"
RUNNER = str(FIX / "run_net_match.py")
BASE_EXE = str(FIX / "builds/base_r15dsg.exe")
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3")
MATCHES = FIX / "matches"

PRIOR_S7_NOTE = (
    "Prior result disclosure (Opus 20:05 PC Point 4): Task 2D S7 bundled TmNodeShare+TmFinishIteration"
    "+AspCappedReopen+AspArmLate at 6+0.06 and scored -32.2 [-49.0, -15.6] Elo. This is an isolated screen."
)


def run_clock(name: str, cand_exe: str, games: int, tc: str, conc: int, seed: int, rule: str,
              cand_opts: list[str] | None = None) -> None:
    if (MATCHES / name / "summary.json").exists():
        print(f"SKIP (already done): {name}", flush=True)
        return
    cmd = [
        PY, RUNNER, "--name", name,
        "--cand-exe", cand_exe, "--base-exe", BASE_EXE,
        "--cand-net", R0067, "--base-net", R0067,
        "--games", str(games), "--nodes", "0", "--tc", tc,
        "--concurrency", str(conc), "--seed", str(seed), "--rule", rule,
    ]
    for opt in (cand_opts or []):
        cmd += ["--cand-opt", opt]
    print(f"=== CLOCK SCREEN: {name} ({games}g @ {tc}) ===", flush=True)
    subprocess.run(cmd, check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=600)
    ap.add_argument("--tc", default="6+0.06")
    ap.add_argument("--concurrency", type=int, default=7)
    args = ap.parse_args()

    run_clock(
        f"CLK_SF17_tm_bestmove_avg_{args.games}g", str(FIX / "builds/SF17_tm_bestmove_avg_eval.exe"),
        args.games, args.tc, args.concurrency, 202611601,
        "Clean-room Stockfish/Viridithas decaying bestmove instability + running-avg falling eval TM screen",
    )
    run_clock(
        f"CLK_SF18_tm_ply_curve_{args.games}g", str(FIX / "builds/SF18_tm_ply_curve.exe"),
        args.games, args.tc, args.concurrency, 202611602,
        "Clean-room Stockfish/Stormphrax move-number ply-adaptive sudden-death budget curve TM screen",
    )
    run_clock(
        f"CLK_SF37_tm_combined_{args.games}g", str(FIX / "builds/SF37_tm_combined_SF17_plus_SF18.exe"),
        args.games, args.tc, args.concurrency, 202611605,
        "Clean-room combined TM (SF17 decaying instability+avg eval + SF18 ply-adaptive sudden-death curve)",
    )
    run_clock(
        f"CLK_TmNodeShare_alone_{args.games}g", BASE_EXE,
        args.games, args.tc, args.concurrency, 202611603,
        f"Isolated TmNodeShare=true screen. {PRIOR_S7_NOTE}",
        cand_opts=["TmNodeShare=true"],
    )
    run_clock(
        f"CLK_TmFinishIteration_alone_{args.games}g", BASE_EXE,
        args.games, args.tc, args.concurrency, 202611604,
        f"Isolated TmFinishIteration=true screen. {PRIOR_S7_NOTE}",
        cand_opts=["TmFinishIteration=true"],
    )
    print("CLOCK TM SCREEN QUEUE COMPLETE.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
