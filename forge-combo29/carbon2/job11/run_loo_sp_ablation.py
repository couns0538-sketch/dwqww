#!/usr/bin/env python3
"""
Job 11 Leave-One-Out SP-Profile Ablation of `bundle 5` (`bundle 5 minus X` on SP-profile builds)
Runs 6 palindromic rounds of 60 games at `Hash 16` (`60` runs = `460,200` searches):
  Odd  round r: sp_r15d_1, sp_b5_1, L_s1236, L_s45, L_s7, L_g14, L_w12, L_p1, sp_b5_2, sp_r15d_2
  Even round r: reversed
For each removed component X, computes:
  - Marginal contribution inside bundle 5: `b5_mean[r] / L_X[r]` (>1.000x means removing X hurt bundle 5 -> X carries gain)
  - Remaining bundle vs r15d:              `L_X[r] / r15d_mean[r]`
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
    work = pathlib.Path("/tmp/carbon2_job11")
    repo = pathlib.Path("/agent/repos/dwqww")
    net768 = "/tmp/carbon2_work/net768.fnn3"
    fens_60 = select_book_fens(str(repo / "forge-combo29/carbon2/positions_250.txt"), 60)
    out_path = repo / "forge-combo29/carbon2/job11/ablation_loo_sp_6x60_hash16_raw.txt"

    bins = {
        "sp_r15d_1": str(work / "bld_sp_r15d_1/forge"),
        "sp_r15d_2": str(work / "bld_sp_r15d_2/forge"),
        "sp_b5_1": str(work / "bld_sp_b5_1/forge"),
        "sp_b5_2": str(work / "bld_sp_b5_2/forge"),
        "L_s1236": str(work / "bld_loo_s1236/forge"),
        "L_s45": str(work / "bld_loo_s45/forge"),
        "L_s7": str(work / "bld_loo_s7/forge"),
        "L_g14": str(work / "bld_loo_g14/forge"),
        "L_w12": str(work / "bld_loo_w12/forge"),
        "L_p1": str(work / "bld_loo_p1/forge"),
    }
    fwd_order = [
        "sp_r15d_1",
        "sp_b5_1",
        "L_s1236",
        "L_s45",
        "L_s7",
        "L_g14",
        "L_w12",
        "L_p1",
        "sp_b5_2",
        "sp_r15d_2",
    ]
    rev_order = list(reversed(fwd_order))

    lines: list[str] = []

    def emit(s: str) -> None:
        print(s, flush=True)
        lines.append(s)
        out_path.write_text("\n".join(lines) + "\n")

    emit("=== JOB 11 LEAVE-ONE-OUT SP-PROFILE ABLATION OF BUNDLE 5 (CLANG-18 ThinLTO+PGO sapphirerapids, HASH 16) ===")
    emit("6 palindromic rounds x 10 SP-profile builds x 60 games (60 runs = 460,200 searches)")
    emit("")

    _ = run_60_game_hash16(bins["sp_r15d_1"], net768, fens_60[:2])

    cpu = {k: [] for k in bins}
    wall = {k: [] for k in bins}
    exp_trace = None
    n_rounds = 6

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
                f"  round {r:02d} {tag:9s}: searches={res['searches']} nodes={res['nodes']} "
                f"wall_ns={res['wall_ns']} wall_sps={res['wall_sps']:6.2f} "
                f"rusage_cpu_ns={res['rusage_cpu_ns']} cpu_sps={res['cpu_sps']:6.2f} trace={res['trace_fnv1a64']}"
            )
        for k in bins:
            cpu[k].append(rc[k])
            wall[k].append(rw[k])

    emit("")
    emit(f"=== TRACE INVARIANCE VERIFIED ACROSS ALL {n_rounds * len(bins)} RUNS: fnv1a64={exp_trace} ===")
    aa_r15d = [cpu["sp_r15d_2"][i] / cpu["sp_r15d_1"][i] for i in range(n_rounds)]
    bb_b5 = [cpu["sp_b5_2"][i] / cpu["sp_b5_1"][i] for i in range(n_rounds)]
    b5_vs_r15d = [
        (0.5 * (cpu["sp_b5_1"][i] + cpu["sp_b5_2"][i])) / (0.5 * (cpu["sp_r15d_1"][i] + cpu["sp_r15d_2"][i]))
        for i in range(n_rounds)
    ]
    emit(
        f"  [Controls] A/A r15d CPU median={statistics.median(aa_r15d):.4f} range=[{min(aa_r15d):.4f}, {max(aa_r15d):.4f}] | "
        f"B/B b5 CPU median={statistics.median(bb_b5):.4f} range=[{min(bb_b5):.4f}, {max(bb_b5):.4f}]"
    )
    emit(
        f"  [Full bundle5 / r15d] CPU paired=[{', '.join(f'{x:.4f}' for x in b5_vs_r15d)}] "
        f"median={statistics.median(b5_vs_r15d):.4f}x ({sum(1 for x in b5_vs_r15d if x > 1.0)}/{n_rounds} faster)"
    )
    emit("")
    for tag, desc in [
        ("L_s1236", "S1_nnue+S2+S3+S6"),
        ("L_s45", "S4+S5"),
        ("L_s7", "S7_uci_clear"),
        ("L_g14", "G1..G4"),
        ("L_w12", "W1+W2"),
        ("L_p1", "P1"),
    ]:
        marg_c = [(0.5 * (cpu["sp_b5_1"][i] + cpu["sp_b5_2"][i])) / cpu[tag][i] for i in range(n_rounds)]
        vs_r15d_c = [cpu[tag][i] / (0.5 * (cpu["sp_r15d_1"][i] + cpu["sp_r15d_2"][i])) for i in range(n_rounds)]
        m_med = statistics.median(marg_c)
        r_med = statistics.median(vs_r15d_c)
        m_fast = sum(1 for x in marg_c if x > 1.0)
        gate = "KEPT" if (m_med >= 1.0035 and m_fast >= 4) else "DROPPED"
        emit(
            f"  [Marginal {desc:16s} = b5/{tag:7s}] CPU paired=[{', '.join(f'{x:.4f}' for x in marg_c)}] "
            f"median={m_med:.4f}x ({(m_med - 1)*100:+.2f}%, {m_fast}/{n_rounds} b5>LOO) | "
            f"{tag}/r15d median={r_med:.4f}x ({(r_med - 1)*100:+.2f}%) -> {gate}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
