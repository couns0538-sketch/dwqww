#!/usr/bin/env python3
"""
Job 46 Part M13 (`run_partM13.py`): THE BUNDLE UNDER S14.
- Uses Job 44's `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`).
- Options as in M9 (`PC20_OPTIONS`) except five sent explicitly:
  `CuckooRep=false`, `HistRework=0`, `TtPruneV2=false`, `CorrHistV2=false`, `MateAlphaGuard=false`.
- Step 1: Verify UCI handshake accepts every option on both sides with zero `unknown option` / `invalid value`.
- Step 2: Liveness on `O` at depth 12 (`200` rows): `all_off` under `S14` must differ from `all_off` under `PC20`
  (read from `step0_bundle9_all_off_O_d12.rows.txt`) on at least 1 position (`nodes_diff >= 1`, `equal < 200`).
- Step 3: Match `8,000` games (`4,000` pairs) at `nodes=2000`, UHO book lines `2,015,501..2,019,500`:
  Side A = `IdeaB8b=true + HindsightDepth=true` (other 8 `Idea*` off), Side B = all 9 `Idea*` + `HindsightDepth` off.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j46_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    FIVE_S14_OVERRIDES,
    JOB46,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    S14_EXPLICIT_OPTIONS,
    WORK44,
    count_row_diffs,
    fmt_cmp,
    read_j39_rows,
    run_epd_depth12_custom,
    run_match_generic,
    utc_now,
    verify_options_accepted_cleanly,
)

EXE_PATH = WORK44 / "bld_bundle9/forge"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-epoch", type=float, default=None)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    e1_switches = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "true")]
    e2_switches = ALL_TEN_FALSE

    liv_lines: list[str] = [
        "=== JOB 46 PART M13 LIVENESS & OPTION CHECK (S14 EXPLICIT 5 SWITCHES) ===",
        f"start_utc: {utc_now()}",
        f"exe_path: {EXE_PATH}",
        "five_s14_overrides_sent_explicitly: "
        + ", ".join(f"{k}={v}" for k, v in FIVE_S14_OVERRIDES.items()),
    ]

    ok_opt_a, opt_a_lines = verify_options_accepted_cleanly(str(EXE_PATH), S14_EXPLICIT_OPTIONS + e1_switches)
    ok_opt_b, opt_b_lines = verify_options_accepted_cleanly(str(EXE_PATH), S14_EXPLICIT_OPTIONS + e2_switches)
    liv_lines.append("--- 1. Explicit Option Acceptance Check (Side A and Side B) ---")
    liv_lines.extend([f"  [SideA] {ln.strip()}" for ln in opt_a_lines])
    liv_lines.extend([f"  [SideB] {ln.strip()}" for ln in opt_b_lines])

    if not (ok_opt_a and ok_opt_b):
        liv_lines.append("STOP_M13: unknown option or invalid value detected during UCI option handshake.")
        (JOB46 / "M13_liveness.txt").write_text("\n".join(liv_lines) + "\n", encoding="utf-8")
        print("\n".join(liv_lines), flush=True)
        return 0

    liv_lines.append("")
    liv_lines.append("--- 2. Liveness on O at Depth 12: S14 all_off vs PC20 all_off ---")
    s14_off_rows_path = JOB46 / "M13_liveness_S14_all_off_O_d12.rows.txt"
    s14_off_meta_path = JOB46 / "M13_liveness_S14_all_off_O_d12.rows.txt.meta"
    s14_rows, bad_liv_opts = run_epd_depth12_custom(
        str(EXE_PATH),
        O_FENS_PATH,
        S14_EXPLICIT_OPTIONS,
        ALL_TEN_FALSE,
        s14_off_rows_path,
        s14_off_meta_path,
        depth=12,
        cpu_pin=1,
    )
    ok_bad_liv, s_bad_liv = fmt_cmp("S14 liveness unknown/invalid option lines", len(bad_liv_opts), 0)
    liv_lines.append(s_bad_liv)
    if not ok_bad_liv:
        liv_lines.append("STOP_M13: unknown option or invalid value during S14 liveness search.")
        (JOB46 / "M13_liveness.txt").write_text("\n".join(liv_lines) + "\n", encoding="utf-8")
        print("\n".join(liv_lines), flush=True)
        return 0

    pc20_off_path = JOB46 / "step0_bundle9_all_off_O_d12.rows.txt"
    pc20_rows = read_j39_rows(pc20_off_path)
    cmp_stats = count_row_diffs(s14_rows, pc20_rows)

    liv_ok = cmp_stats["any_diff"] >= 1 and cmp_stats["nodes_diff"] >= 1
    ok_l, s_l = fmt_cmp("M13 liveness (S14 vs PC20 nodes_diff >= 1)", cmp_stats["nodes_diff"] >= 1, True)
    liv_lines.extend(
        [
            f"  S14_all_off_rows_file                       : {s14_off_rows_path}",
            f"  PC20_all_off_rows_file                      : {pc20_off_path}",
            f"  positions_compared                          : {cmp_stats['positions']}",
            f"  S14_all_off_O_d12_sum_nodes                 : {cmp_stats['sum_a']}",
            f"  PC20_all_off_O_d12_sum_nodes (from Step 0)  : {cmp_stats['sum_b']}",
            f"  node_sum_delta (S14 - PC20)                 : {cmp_stats['sum_a'] - cmp_stats['sum_b']:+d}",
            f"  equal_positions_of_{cmp_stats['positions']}                     : {cmp_stats['equal']}",
            f"  any_field_diff_positions_of_{cmp_stats['positions']}            : {cmp_stats['any_diff']}",
            f"  nodes_diff_positions_of_{cmp_stats['positions']}                : {cmp_stats['nodes_diff']}",
            f"  bestmove_diff_positions_of_{cmp_stats['positions']}             : {cmp_stats['bestmove_diff']}",
            f"  score_diff_positions_of_{cmp_stats['positions']}                : {cmp_stats['score_diff']}",
            s_l,
            f"liveness_done_utc: {utc_now()}",
        ]
    )
    (JOB46 / "M13_liveness.txt").write_text("\n".join(liv_lines) + "\n", encoding="utf-8")
    print("\n".join(liv_lines), flush=True)

    if not liv_ok:
        with open(JOB46 / "M13_liveness.txt", "a", encoding="utf-8") as lf:
            lf.write("STOP_M13: S14 all_off equaled PC20 all_off on all positions; skipping M13 match.\n")
        return 0

    rec = run_match_generic(
        tag="M13",
        exe_path=EXE_PATH,
        eng1_name="B8b_HindsightDepth_on_S14",
        eng2_name="all_off_S14",
        e1_switches=e1_switches,
        e2_switches=e2_switches,
        each_base_opts=S14_EXPLICIT_OPTIONS,
        nodes=2000,
        start_line=2015501,
        rounds=4000,
        cutoff_epoch=args.cutoff_epoch,
        concurrency=args.concurrency,
    )
    if not rec["ok_bad_options"]:
        raise RuntimeError(f"M13 fastchess output contained bad option lines: {rec['bad_option_lines']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
