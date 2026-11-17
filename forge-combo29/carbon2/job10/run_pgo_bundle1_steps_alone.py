#!/usr/bin/env python3
"""
Job 10 Standalone Isolation of Each Step of `bundle 1` (`S1..S7`) Alone on `r15d`
Built with Clang 18.1.3 + libstdc++ + ThinLTO + PGO (-march=sapphirerapids), `Hash 16`.
Runs 6 palindromic rounds of 60 games (`54` runs total):
  Odd  round r: r15d_1, S1, S2, S3, S4, S5, S6, S7, r15d_2
  Even round r: r15d_2, S7, S6, S5, S4, S3, S2, S1, r15d_1
Every step S_k is paired in round r against 0.5 * (r15d_1[r] + r15d_2[r]).
"""
from __future__ import annotations

import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "job8"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "job2"))
from run_selfplay_hash16_abba import run_60_game_hash16  # noqa: E402
from selfplay_driver_v2 import select_book_fens  # noqa: E402


def main() -> int:
    work = pathlib.Path("/tmp/carbon2_job10")
    repo = pathlib.Path("/agent/repos/dwqww")
    net768 = "/tmp/carbon2_work/net768.fnn3"
    fens_60 = select_book_fens(str(repo / "forge-combo29/carbon2/positions_250.txt"), 60)
    out_path = repo / "forge-combo29/carbon2/job10/pgo_bundle1_steps_alone_6x60_hash16_raw.txt"

    bins = {
        "r15d_1": str(work / "bld_r15d_1/forge"),
        "r15d_2": str(work / "bld_r15d_2/forge"),
        "S1": str(work / "bld_alone_s1/forge"),
        "S2": str(work / "bld_alone_s2/forge"),
        "S3": str(work / "bld_alone_s3/forge"),
        "S4": str(work / "bld_alone_s4/forge"),
        "S5": str(work / "bld_alone_s5/forge"),
        "S6": str(work / "bld_alone_s6/forge"),
        "S7": str(work / "bld_alone_s7/forge"),
    }
    fwd_order = ["r15d_1", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "r15d_2"]
    rev_order = list(reversed(fwd_order))

    lines: list[str] = []

    def emit(s: str) -> None:
        print(s, flush=True)
        lines.append(s)
        out_path.write_text("\n".join(lines) + "\n")

    emit("=== JOB 10 CLANG-18 ThinLTO+PGO (-march=sapphirerapids): BUNDLE 1 STEPS (S1..S7) ALONE ON r15d ===")
    emit("6 palindromic rounds x 9 builds x 60 games at Hash 16 (54 runs = 414,180 searches)")
    emit("")

    _ = run_60_game_hash16(bins["r15d_1"], net768, fens_60[:2])

    cpu = {k: [] for k in bins}
    wall = {k: [] for k in bins}
    exp_trace = None

    n_rounds = 6
    for r in range(1, n_rounds + 1):
        order = fwd_order if (r % 2 == 1) else rev_order
        round_cpu = {}
        round_wall = {}
        for tag in order:
            res = run_60_game_hash16(bins[tag], net768, fens_60)
            if exp_trace is None:
                exp_trace = res["trace_fnv1a64"]
            elif res["trace_fnv1a64"] != exp_trace or res["searches"] != 7670 or res["nodes"] != 25641316:
                raise RuntimeError(f"TRACE DIVERGENCE on {tag} round {r}: {res}")
            round_cpu[tag] = res["cpu_sps"]
            round_wall[tag] = res["wall_sps"]
            emit(
                f"  round {r:02d} {tag:6s}: searches={res['searches']} nodes={res['nodes']} "
                f"wall_ns={res['wall_ns']} wall_sps={res['wall_sps']:6.2f} "
                f"rusage_cpu_ns={res['rusage_cpu_ns']} cpu_sps={res['cpu_sps']:6.2f} trace={res['trace_fnv1a64']}"
            )
        for k in bins:
            cpu[k].append(round_cpu[k])
            wall[k].append(round_wall[k])

    emit("")
    emit(f"=== TRACE INVARIANCE VERIFIED ACROSS ALL {n_rounds * len(bins)} RUNS: fnv1a64={exp_trace} ===")
    aa_cpu = [cpu["r15d_2"][i] / cpu["r15d_1"][i] for i in range(n_rounds)]
    aa_wall = [wall["r15d_2"][i] / wall["r15d_1"][i] for i in range(n_rounds)]
    emit(
        f"  [A/A r15d_2/r15d_1] CPU median={statistics.median(aa_cpu):.4f} range=[{min(aa_cpu):.4f}, {max(aa_cpu):.4f}] | "
        f"Wall median={statistics.median(aa_wall):.4f} range=[{min(aa_wall):.4f}, {max(aa_wall):.4f}]"
    )
    emit("")
    for step in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
        c_ratios = [cpu[step][i] / (0.5 * (cpu["r15d_1"][i] + cpu["r15d_2"][i])) for i in range(n_rounds)]
        w_ratios = [wall[step][i] / (0.5 * (wall["r15d_1"][i] + wall["r15d_2"][i])) for i in range(n_rounds)]
        c_med = statistics.median(c_ratios)
        w_med = statistics.median(w_ratios)
        c_fast = sum(1 for x in c_ratios if x > 1.0)
        w_fast = sum(1 for x in w_ratios if x > 1.0)
        emit(
            f"  [{step} vs r15d] CPU paired=[{', '.join(f'{x:.4f}' for x in c_ratios)}] "
            f"median={c_med:.4f}x ({(c_med - 1)*100:+.2f}%, {c_fast}/{n_rounds} faster) | "
            f"Wall median={w_med:.4f}x ({(w_med - 1)*100:+.2f}%, {w_fast}/{n_rounds} faster)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
