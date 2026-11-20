#!/usr/bin/env python3
"""
Job 46 Part M11 (`run_partM11.py`): IdeaS10 ON TOP OF THE BUNDLE (`PC20`).
- Liveness first on `O` at depth 12 (`PC20`):
  `IdeaB8b + HindsightDepth + IdeaS10` vs `IdeaB8b + HindsightDepth`.
  Reports both sums (read from the runs) and how many of 200 node counts differ (`>= 1` required).
- Match: `3,000` games (`1,500` pairs) at `nodes=20000`, `PC20`, UHO book lines `2,019,501..2,021,000`:
  Side A = `IdeaB8b + HindsightDepth + IdeaS10`, Side B = `IdeaB8b + HindsightDepth`.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j46_lib import (  # noqa: E402
    JOB46,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    PC20_OPTIONS,
    WORK44,
    count_row_diffs,
    fmt_cmp,
    run_epd_depth12_custom,
    run_match_generic,
    utc_now,
)

EXE_PATH = WORK44 / "bld_bundle9/forge"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-epoch", type=float, default=None)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    if args.cutoff_epoch is not None:
        import time

        if time.time() >= args.cutoff_epoch:
            print(f"[{utc_now()}] Cutoff already reached before M11; skipping M11.", flush=True)
            return 0

    e1_switches = [
        (o, "true" if o in ("IdeaB8b", "IdeaS10") else "false") for o in NINE_SWITCH_NAMES
    ] + [("HindsightDepth", "true")]
    e2_switches = [
        (o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES
    ] + [("HindsightDepth", "true")]

    a_rows_path = JOB46 / "M11_liveness_bundle_plus_S10_O_d12.rows.txt"
    b_rows_path = JOB46 / "M11_liveness_bundle_only_O_d12.rows.txt"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(
            run_epd_depth12_custom,
            str(EXE_PATH),
            O_FENS_PATH,
            PC20_OPTIONS,
            e1_switches,
            a_rows_path,
            pathlib.Path(str(a_rows_path) + ".meta"),
            12,
            1,
        )
        fut_b = pool.submit(
            run_epd_depth12_custom,
            str(EXE_PATH),
            O_FENS_PATH,
            PC20_OPTIONS,
            e2_switches,
            b_rows_path,
            pathlib.Path(str(b_rows_path) + ".meta"),
            12,
            2,
        )
        rows_a, bad_a = fut_a.result()
        rows_b, bad_b = fut_b.result()

    cmp_stats = count_row_diffs(rows_a, rows_b)
    ok_ba, s_ba = fmt_cmp("M11 SideA liveness unknown/invalid option lines", len(bad_a), 0)
    ok_bb, s_bb = fmt_cmp("M11 SideB liveness unknown/invalid option lines", len(bad_b), 0)
    liv_ok = ok_ba and ok_bb and (cmp_stats["nodes_diff"] >= 1)
    ok_l, s_l = fmt_cmp("M11 liveness (bundle+S10 vs bundle nodes_diff >= 1)", cmp_stats["nodes_diff"] >= 1, True)

    liv_lines = [
        "=== JOB 46 PART M11 LIVENESS (PC20, O depth 12: IdeaB8b+HindsightDepth+IdeaS10 vs IdeaB8b+HindsightDepth) ===",
        f"exe_path: {EXE_PATH}",
        s_ba,
        s_bb,
        f"  sideA_rows_file                             : {a_rows_path}",
        f"  sideB_rows_file                             : {b_rows_path}",
        f"  positions_compared                          : {cmp_stats['positions']}",
        f"  bundle_plus_IdeaS10_O_d12_sum_nodes         : {cmp_stats['sum_a']}",
        f"  bundle_only_O_d12_sum_nodes                 : {cmp_stats['sum_b']}",
        f"  node_sum_delta ((bundle+S10) - bundle)      : {cmp_stats['sum_a'] - cmp_stats['sum_b']:+d}",
        f"  equal_positions_of_{cmp_stats['positions']}                     : {cmp_stats['equal']}",
        f"  nodes_diff_positions_of_{cmp_stats['positions']}                : {cmp_stats['nodes_diff']}",
        f"  bestmove_diff_positions_of_{cmp_stats['positions']}             : {cmp_stats['bestmove_diff']}",
        f"  score_diff_positions_of_{cmp_stats['positions']}                : {cmp_stats['score_diff']}",
        s_l,
        f"liveness_done_utc: {utc_now()}",
    ]
    (JOB46 / "M11_liveness.txt").write_text("\n".join(liv_lines) + "\n", encoding="utf-8")
    print("\n".join(liv_lines), flush=True)

    if not liv_ok:
        with open(JOB46 / "M11_liveness.txt", "a", encoding="utf-8") as lf:
            lf.write("STOP_M11: liveness check failed; skipping M11 match.\n")
        return 0

    rec = run_match_generic(
        tag="M11",
        exe_path=EXE_PATH,
        eng1_name="bundle_plus_IdeaS10",
        eng2_name="bundle_only",
        e1_switches=e1_switches,
        e2_switches=e2_switches,
        each_base_opts=PC20_OPTIONS,
        nodes=20000,
        start_line=2019501,
        rounds=1500,
        cutoff_epoch=args.cutoff_epoch,
        concurrency=args.concurrency,
    )
    if not rec["ok_bad_options"]:
        raise RuntimeError(f"M11 fastchess output contained bad option lines: {rec['bad_option_lines']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
