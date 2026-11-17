#!/usr/bin/env python3
"""
Job 8 ABBA x 60-Game Self-Play Benchmark Driver at `Hash 16` (with Per-Round A/A Range)
======================================================================================
- Runs the exact PC option list (`Threads 1`, `Hash 16`, `OwnBook false`, `MateAlphaGuard true`,
  `PC20`, `net768.fnn3`, default `InfoOnce false` — zero move, node, score, or info-line changes).
- 12 rounds of `A1 B1 B2 A2` (`48` runs total), 60 distinct book FEN roots from `positions_250.txt`,
  `go softnodes 2000`, `ucinewgame` + `isready` before each game, zero untimed warmup inside any
  measured engine process.
- Prints per-round ratios, median (`median_of_paired_round_ratios`) + 95% CI, `ratio_of_pooled_medians`
  + 95% CI, rounds faster, and per-round A/A `[min, max]` ranges beside the median A/A ratios,
  for both wall clock and reaped-child `getrusage` engine CPU nanoseconds.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import random
import statistics
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "job2"))
from selfplay_driver_v2 import (  # noqa: E402
    PC20_OPTIONS,
    MinimalBoardTracker,
    fnv1a64_str,
    select_book_fens,
    send,
    wait_ready_collect,
)


def run_60_game_hash16(
    binary: str,
    net768: str,
    fens: list[str],
    softnodes: int = 2000,
    max_plies: int = 300,
) -> dict:
    proc = subprocess.Popen(
        [binary],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    cfg = ["uci\n"] + [f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS] + [
        f"setoption name NNUEArchFile value {net768}\n",
        "setoption name NNUEArch value true\n",
        "isready\n",
    ]
    send(proc, "".join(cfg))
    setup_lines = wait_ready_collect(proc, check_errors=True)
    v3_active_line = next((ln for ln in setup_lines if "NNUE v3 active:" in ln), "")
    if not v3_active_line or "30ab43b4ba5db5f3" not in v3_active_line:
        proc.kill()
        raise RuntimeError(f"Missing or wrong NNUE v3 active line in {binary}: {setup_lines}")

    total_searches = 0
    total_nodes = 0
    trace_hash = 14695981039346656037

    t_wall0 = time.perf_counter_ns()
    for g_idx, root_fen in enumerate(fens):
        send(proc, "ucinewgame\nisready\n")
        wait_ready_collect(proc, check_errors=True)

        moves: list[str] = []
        tracker = MinimalBoardTracker()
        tracker.load_fen(root_fen)

        for ply in range(max_plies):
            if tracker.is_draw():
                break
            pos_str = f"position fen {root_fen}" + (" moves " + " ".join(moves) if moves else "")
            send(proc, f"{pos_str}\ngo softnodes {softnodes}\n")

            last_nodes = 0
            last_score = ""
            bestmove = "0000"
            while True:
                line = proc.stdout.readline()
                if not line:
                    proc.kill()
                    raise RuntimeError(f"Engine EOF during search in {binary}")
                if "ERROR" in line or "illegal move" in line or "unknown option" in line or "invalid value" in line:
                    proc.kill()
                    raise RuntimeError(f"Engine error line in {binary}: {line.strip()}")
                if line.startswith("info depth "):
                    parts = line.split()
                    for i, tok in enumerate(parts):
                        if tok == "nodes" and i + 1 < len(parts):
                            last_nodes = int(parts[i + 1])
                        elif tok == "score" and i + 2 < len(parts):
                            last_score = f"{parts[i + 1]}:{parts[i + 2]}"
                elif line.startswith("bestmove "):
                    bestmove = line.split()[1]
                    break

            total_searches += 1
            total_nodes += last_nodes
            trace_hash = fnv1a64_str(trace_hash, f"{g_idx},{ply},{bestmove},{last_nodes},{last_score};")

            if bestmove == "0000" or last_nodes == 0:
                break
            moves.append(bestmove)
            tracker.push_uci(bestmove)

    t_wall1 = time.perf_counter_ns()
    send(proc, "quit\n")
    proc.stdin.close()
    proc.stdout.read()
    _, status, rusage = os.wait4(proc.pid, 0)
    if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        raise RuntimeError(f"Engine {binary} exited with bad status {status}")

    wall_ns = t_wall1 - t_wall0
    rusage_cpu_ns = int(round((rusage.ru_utime + rusage.ru_stime) * 1e9))
    return {
        "searches": total_searches,
        "nodes": total_nodes,
        "wall_ns": wall_ns,
        "rusage_cpu_ns": rusage_cpu_ns,
        "wall_sps": total_searches * 1e9 / wall_ns,
        "cpu_sps": total_searches * 1e9 / rusage_cpu_ns,
        "trace_fnv1a64": f"{trace_hash:016x}",
        "active_line": v3_active_line,
    }


def summarize_abba_j8(
    label: str,
    a1: list[float],
    a2: list[float],
    b1: list[float],
    b2: list[float],
    seed: int = 20261117,
) -> list[str]:
    n_rounds = len(a1)
    pooled_a = a1 + a2
    pooled_b = b1 + b2
    med_a1 = statistics.median(a1)
    med_a2 = statistics.median(a2)
    med_b1 = statistics.median(b1)
    med_b2 = statistics.median(b2)
    med_a = statistics.median(pooled_a)
    med_b = statistics.median(pooled_b)
    ratio_pooled = med_b / med_a

    paired_ratios = [
        (0.5 * (b1[r] + b2[r])) / (0.5 * (a1[r] + a2[r])) for r in range(n_rounds)
    ]
    aa_per_round = [a2[r] / a1[r] for r in range(n_rounds)]
    bb_per_round = [b2[r] / b1[r] for r in range(n_rounds)]

    med_paired = statistics.median(paired_ratios)
    rounds_faster = sum(1 for x in paired_ratios if x > 1.0)

    rng = random.Random(seed)
    boot_paired = []
    boot_pooled = []
    for _ in range(10000):
        idxs = [rng.randrange(n_rounds) for _ in range(n_rounds)]
        boot_paired.append(statistics.median([paired_ratios[i] for i in idxs]))
        sa = [a1[i] for i in idxs] + [a2[i] for i in idxs]
        sb = [b1[i] for i in idxs] + [b2[i] for i in idxs]
        boot_pooled.append(statistics.median(sb) / statistics.median(sa))
    boot_paired.sort()
    boot_pooled.sort()
    ci_paired = (boot_paired[250], boot_paired[9749])
    ci_pooled = (boot_pooled[250], boot_pooled[9749])

    aa_med_ratio = med_a2 / med_a1
    bb_med_ratio = med_b2 / med_b1
    pr_str = ", ".join(f"{x:.4f}" for x in paired_ratios)
    return [
        f"  [{label}] build medians: A1={med_a1:.2f}, A2={med_a2:.2f} (pooled A={med_a:.2f}) | B1={med_b1:.2f}, B2={med_b2:.2f} (pooled B={med_b:.2f})",
        f"  [{label}] paired ratio per round (r=1..{n_rounds}): [{pr_str}]",
        f"  [{label}] rounds faster: {rounds_faster}/{n_rounds}",
        f"  [{label}] median_of_paired_round_ratios (median_r(B_r/A_r)): {med_paired:.4f}x ({(med_paired - 1.0) * 100.0:+.2f}%), 95% CI [{ci_paired[0]:.4f}x, {ci_paired[1]:.4f}x]",
        f"  [{label}] ratio_of_pooled_medians (median(all B)/median(all A)): {ratio_pooled:.4f}x ({(ratio_pooled - 1.0) * 100.0:+.2f}%), 95% CI [{ci_pooled[0]:.4f}x, {ci_pooled[1]:.4f}x]",
        f"  [{label}] A/A control: median(A2)/median(A1)={aa_med_ratio:.4f} (per-round A2/A1 range [{min(aa_per_round):.4f}, {max(aa_per_round):.4f}]), median(B2)/median(B1)={bb_med_ratio:.4f} (per-round B2/B1 range [{min(bb_per_round):.4f}, {max(bb_per_round):.4f}])",
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="JOB 8 HASH-16 12-ROUND ABBA x 60-GAME SELF-PLAY BENCHMARK")
    ap.add_argument("--a1", required=True)
    ap.add_argument("--a2", required=True)
    ap.add_argument("--b1", required=True)
    ap.add_argument("--b2", required=True)
    ap.add_argument("--net768", required=True)
    ap.add_argument("--pos250", required=True)
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    fens_60 = select_book_fens(args.pos250, 60)
    out_path = pathlib.Path(args.out)
    lines: list[str] = []

    def emit(s: str) -> None:
        print(s, flush=True)
        lines.append(s)
        out_path.write_text("\n".join(lines) + "\n")

    emit(f"=== {args.title} ===")
    emit("CPU: Intel(R) Xeon(R) CPU @ 2.60GHz (x86_64 AVX-512), Threads 1, Hash 16, PC20 + net768.fnn3 (InfoOnce=false)")
    emit(f"Roots: {len(fens_60)} distinct FEN roots from positions_250.txt, max_plies=300, go softnodes 2000")
    emit(f"Order: A1 B1 B2 A2 x {args.rounds} rounds ({args.rounds * 4} runs total); zero untimed warmup inside any measured process")
    emit("")

    _ = run_60_game_hash16(args.a1, args.net768, fens_60[:2])

    wall_sps = {"A1": [], "A2": [], "B1": [], "B2": []}
    cpu_sps = {"A1": [], "A2": [], "B1": [], "B2": []}
    bins = {"A1": args.a1, "B1": args.b1, "B2": args.b2, "A2": args.a2}

    expected_trace: str | None = None
    expected_searches: int | None = None
    expected_nodes: int | None = None

    for r in range(1, args.rounds + 1):
        for tag in ("A1", "B1", "B2", "A2"):
            res = run_60_game_hash16(bins[tag], args.net768, fens_60)
            if expected_trace is None:
                expected_trace = res["trace_fnv1a64"]
                expected_searches = res["searches"]
                expected_nodes = res["nodes"]
            else:
                if (
                    res["trace_fnv1a64"] != expected_trace
                    or res["searches"] != expected_searches
                    or res["nodes"] != expected_nodes
                ):
                    raise RuntimeError(
                        f"TRACE DIVERGENCE at round {r} {tag}: got ({res['trace_fnv1a64']}, {res['searches']}, {res['nodes']}) "
                        f"expected ({expected_trace}, {expected_searches}, {expected_nodes})"
                    )
            wall_sps[tag].append(res["wall_sps"])
            cpu_sps[tag].append(res["cpu_sps"])
            emit(
                f"  round {r:02d} {tag}: searches={res['searches']} nodes={res['nodes']} "
                f"wall_ns={res['wall_ns']} wall_sps={res['wall_sps']:6.2f} "
                f"rusage_cpu_ns={res['rusage_cpu_ns']} cpu_sps={res['cpu_sps']:6.2f} "
                f"trace={res['trace_fnv1a64']} | {res['active_line']}"
            )

    emit("")
    emit(
        f"=== TRACE INVARIANCE VERIFIED ACROSS ALL {args.rounds * 4} RUNS: "
        f"fnv1a64={expected_trace} searches={expected_searches} nodes={expected_nodes} ==="
    )
    emit("")
    for s in summarize_abba_j8(
        "selfplay_hash16_wall_sps",
        wall_sps["A1"],
        wall_sps["A2"],
        wall_sps["B1"],
        wall_sps["B2"],
    ):
        emit(s)
    emit("")
    for s in summarize_abba_j8(
        "selfplay_hash16_rusage_cpu_sps",
        cpu_sps["A1"],
        cpu_sps["A2"],
        cpu_sps["B1"],
        cpu_sps["B2"],
    ):
        emit(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
