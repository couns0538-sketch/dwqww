#!/usr/bin/env python3
"""
Job 12 12-Round x 60-Game Two-Build Symmetric ABBA Leave-One-Out Benchmark of `PGO1` on SP-Profile Builds
=========================================================================================================
- 2 SP-profile builds of `r15d + PGO1` (`pgo1_1`, `pgo1_2`) and 2 SP-profile builds each of:
    loo1 = PGO1 minus S4
    loo2 = PGO1 minus S5
    loo3 = PGO1 minus S7
    loo4 = PGO1 minus TT part
    loo5 = PGO1 minus legal-move part
    loo6 = PGO1 minus stop & hot-attribute part
- 12 symmetric palindromic rounds x 14 builds x 60 games at `Hash 16` (`168` runs = `1,288,560` searches):
    Odd  r: pgo1_1, loo1_1..loo6_1, loo6_2..loo1_2, pgo1_2
    Even r: pgo1_2, loo1_2..loo6_2, loo6_1..loo1_1, pgo1_1
  Every `loo_k` has exact `A1 ... B1 ... B2 ... A2` symmetry around the round midpoint in all 12 rounds.
"""
from __future__ import annotations

import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "job8"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "job2"))
from run_selfplay_hash16_abba import run_60_game_hash16, summarize_abba_j8  # noqa: E402
from selfplay_driver_v2 import select_book_fens  # noqa: E402


def main() -> int:
    work = pathlib.Path("/tmp/carbon2_job12")
    repo = pathlib.Path("/agent/repos/dwqww")
    net768 = "/tmp/carbon2_work/net768.fnn3"
    fens_60 = select_book_fens(str(repo / "forge-combo29/carbon2/positions_250.txt"), 60)
    out_path = repo / "forge-combo29/carbon2/job12/pgo1_loo6_12x60_hash16_raw.txt"

    bins = {
        "pgo1_1": str(work / "bld_sp_pgo1_1/forge"),
        "pgo1_2": str(work / "bld_sp_pgo1_2/forge"),
    }
    for k in range(1, 7):
        bins[f"loo{k}_1"] = str(work / f"bld_sp_loo{k}_1/forge")
        bins[f"loo{k}_2"] = str(work / f"bld_sp_loo{k}_2/forge")

    fwd_order = [
        "pgo1_1",
        "loo1_1", "loo2_1", "loo3_1", "loo4_1", "loo5_1", "loo6_1",
        "loo6_2", "loo5_2", "loo4_2", "loo3_2", "loo2_2", "loo1_2",
        "pgo1_2",
    ]
    rev_order = [
        "pgo1_2",
        "loo1_2", "loo2_2", "loo3_2", "loo4_2", "loo5_2", "loo6_2",
        "loo6_1", "loo5_1", "loo4_1", "loo3_1", "loo2_1", "loo1_1",
        "pgo1_1",
    ]

    lines: list[str] = []

    def emit(s: str) -> None:
        print(s, flush=True)
        lines.append(s)
        out_path.write_text("\n".join(lines) + "\n")

    emit("=== JOB 12 SP-PROFILE 12-ROUND TWO-BUILD LEAVE-ONE-OUT TIMING OF PGO1's 6 PARTS (HASH 16) ===")
    emit("12 symmetric palindromic rounds x 14 SP-profile builds x 60 games (168 runs = 1,288,560 searches)")
    emit("")

    _ = run_60_game_hash16(bins["pgo1_1"], net768, fens_60[:2])

    cpu = {k: [] for k in bins}
    wall = {k: [] for k in bins}
    exp_trace = None
    n_rounds = 12

    for r in range(1, n_rounds + 1):
        order = fwd_order if (r % 2 == 1) else rev_order
        rc, rw = {}, {}
        for tag in order:
            res = run_60_game_hash16(bins[tag], net768, fens_60)
            if exp_trace is None:
                exp_trace = res["trace_fnv1a64"]
            elif res["trace_fnv1a64"] != exp_trace or res["searches"] != 7670 or res["nodes"] != 25641316:
                raise RuntimeError(f"TRACE DIVERGENCE on {tag} round {r}: {res}")
            rc[tag] = res["cpu_sps"]
            rw[tag] = res["wall_sps"]
            emit(
                f"  round {r:02d} {tag:7s}: searches={res['searches']} nodes={res['nodes']} "
                f"wall_ns={res['wall_ns']} wall_sps={res['wall_sps']:6.2f} "
                f"rusage_cpu_ns={res['rusage_cpu_ns']} cpu_sps={res['cpu_sps']:6.2f} trace={res['trace_fnv1a64']}"
            )
        for k in bins:
            cpu[k].append(rc[k])
            wall[k].append(rw[k])

    emit("")
    emit(f"=== TRACE INVARIANCE VERIFIED ACROSS ALL {n_rounds * len(bins)} RUNS: fnv1a64={exp_trace} searches=7670 nodes=25641316 ===")
    emit("")

    names = [
        (1, "S4_slim_movepicker"),
        (2, "S5_make_move_key_undo"),
        (3, "S7_uci_clear"),
        (4, "TT_miss_fastpath"),
        (5, "Legal_move_checks"),
        (6, "Stop_inline_and_hot_attr"),
    ]
    for k, desc in names:
        emit(f"--- Part {k} ({desc}): Marginal Carrier Ratio B=PGO1 over A=loo{k} (PGO1 / [PGO1 minus {desc}]) ---")
        for ln in summarize_abba_j8(
            f"marginal_cpu_PGO1_over_loo{k}",
            cpu[f"loo{k}_1"], cpu[f"loo{k}_2"],
            cpu["pgo1_1"], cpu["pgo1_2"],
        ):
            emit(ln)
        for ln in summarize_abba_j8(
            f"marginal_wall_PGO1_over_loo{k}",
            wall[f"loo{k}_1"], wall[f"loo{k}_2"],
            wall["pgo1_1"], wall["pgo1_2"],
        ):
            emit(ln)
        paired_c = [
            (0.5 * (cpu["pgo1_1"][i] + cpu["pgo1_2"][i])) / (0.5 * (cpu[f"loo{k}_1"][i] + cpu[f"loo{k}_2"][i]))
            for i in range(n_rounds)
        ]
        med_c = statistics.median(paired_c)
        fast_c = sum(1 for x in paired_c if x > 1.0)
        verdict = "KEPT" if (med_c >= 1.0035 and fast_c >= 8) else "DROPPED"
        emit(f"  => CARRIER GATE VERDICT for Part {k} ({desc}): median={med_c:.4f}x, rounds PGO1>loo{k}={fast_c}/12 -> {verdict}")
        emit("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
