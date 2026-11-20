#!/usr/bin/env python3
"""
Job 47 Part M14 (`run_partM14.py`): IdeaK4b ON TOP OF THE BUNDLE (`PC20`).
- Executable: `/tmp/carbon2_job47/bld_bundle11_k4b/forge` (`bundle10 + P11_K4b.patch.txt`).
- Both sides have `IdeaB8b=true`, `IdeaB8b_Fast=true`, `HindsightDepth=true`, `IdeaK4b_Shrink=32`,
  and every other `Idea*` switch (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS13_Hoist`,
  `IdeaS10`, `IdeaB8`, `IdeaB8_Fast`) explicitly `false`.
- Side A (`bundle_plus_IdeaK4b`): `IdeaK4b=true`.
- Side B (`bundle_only`): `IdeaK4b=false`.
- Pre-match liveness & bundle fast-path check on `O` depth 12 (`PC20`):
  * Verifies `Side B` (`bundle_only` with `IdeaB8b_Fast=true`) equals `job46/M11_liveness_bundle_only_O_d12.rows.txt`
    on `200 == 200` positions (`8,481,645` nodes).
  * Verifies `Side A` (`bundle_plus_IdeaK4b`) differs from `Side B` on `>= 1` position.
- Match: `3,000` games (`1,500` pairs) at `nodes=20000`, `PC20`, UHO book lines `2,022,501..2,024,000`.
"""
from __future__ import annotations

import argparse
import calendar
import concurrent.futures
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j47_lib import (  # noqa: E402
    ELEVEN_BUNDLE11_IDEA_NAMES,
    JOB46,
    JOB47,
    O_FENS_PATH,
    PC20_OPTIONS,
    WORK47,
    fmt_cmp,
    read_j39_rows,
    run_epd_depth12_strict,
    run_match_strict,
    utc_now,
)

EXE_PATH = WORK47 / "bld_bundle11_k4b/forge"
CLAIM_EPOCH = calendar.timegm((2026, 11, 20, 21, 45, 39, 0, 0, 0))
DEFAULT_CUTOFF_EPOCH = float(CLAIM_EPOCH + 64 * 60)  # Minute 64, leaving >15m for T3 + Report before Minute 80


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-epoch", type=float, default=DEFAULT_CUTOFF_EPOCH)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    e1_switches = [
        (o, "true" if o in ("IdeaB8b", "IdeaB8b_Fast", "IdeaK4b") else "false")
        for o in ELEVEN_BUNDLE11_IDEA_NAMES
    ] + [("HindsightDepth", "true"), ("IdeaK4b_Shrink", "32")]

    e2_switches = [
        (o, "true" if o in ("IdeaB8b", "IdeaB8b_Fast") else "false")
        for o in ELEVEN_BUNDLE11_IDEA_NAMES
    ] + [("HindsightDepth", "true"), ("IdeaK4b_Shrink", "32")]

    a_rows_path = JOB47 / "M14_liveness_bundle_plus_IdeaK4b_O_d12.rows.txt"
    b_rows_path = JOB47 / "M14_liveness_bundle_only_O_d12.rows.txt"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(
            run_epd_depth12_strict,
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
            run_epd_depth12_strict,
            str(EXE_PATH),
            O_FENS_PATH,
            PC20_OPTIONS,
            e2_switches,
            b_rows_path,
            pathlib.Path(str(b_rows_path) + ".meta"),
            12,
            2,
        )
        rows_a = fut_a.result()
        rows_b = fut_b.result()

    ref_m11_bundle = read_j39_rows(JOB46 / "M11_liveness_bundle_only_O_d12.rows.txt")
    sum_a = sum(r[1] for r in rows_a)
    sum_b = sum(r[1] for r in rows_b)
    eq_b_vs_j46 = sum(1 for a, b in zip(rows_b, ref_m11_bundle) if a == b)
    eq_ab = sum(1 for a, b in zip(rows_a, rows_b) if a == b)
    nd_diff = sum(1 for a, b in zip(rows_a, rows_b) if a[1] != b[1])
    bm_diff = sum(1 for a, b in zip(rows_a, rows_b) if a[2] != b[2])
    sc_diff = sum(1 for a, b in zip(rows_a, rows_b) if a[3] != b[3])

    ok_id, s_id = fmt_cmp("M14 SideB (bundle+IdeaB8b_Fast) O d12 sum vs J46 bundle_only", sum_b, 8481645)
    ok_id2, s_id2 = fmt_cmp("M14 SideB equal positions vs J46 M11_liveness_bundle_only", eq_b_vs_j46, 200)
    ok_liv, s_liv = fmt_cmp("M14 liveness (bundle+K4b vs bundle nodes_diff >= 1)", nd_diff >= 1, True)

    liv_lines = [
        "=== JOB 47 PART M14 LIVENESS (PC20, O depth 12: bundle+IdeaK4b vs bundle, IdeaB8b_Fast=true on both) ===",
        f"exe_path: {EXE_PATH}",
        s_id,
        s_id2,
        f"  sideA_rows_file                             : {a_rows_path}",
        f"  sideB_rows_file                             : {b_rows_path}",
        f"  bundle_plus_IdeaK4b_O_d12_sum_nodes         : {sum_a}",
        f"  bundle_only_O_d12_sum_nodes                 : {sum_b}",
        f"  node_sum_delta ((bundle+IdeaK4b) - bundle)  : {sum_a - sum_b:+d}",
        f"  equal_positions_of_200                      : {eq_ab}",
        f"  nodes_diff_positions_of_200                 : {nd_diff}",
        f"  bestmove_diff_positions_of_200              : {bm_diff}",
        f"  score_diff_positions_of_200                 : {sc_diff}",
        s_liv,
        f"liveness_done_utc: {utc_now()}",
    ]
    (JOB47 / "M14_liveness.txt").write_text("\n".join(liv_lines) + "\n", encoding="utf-8")
    print("\n".join(liv_lines), flush=True)

    if not (ok_id and ok_id2 and ok_liv):
        raise RuntimeError("M14 pre-match bundle identity or liveness check failed!")

    rec = run_match_strict(
        tag="M14",
        out_dir=JOB47,
        exe_path=EXE_PATH,
        eng1_name="bundle_plus_IdeaK4b",
        eng2_name="bundle_only",
        e1_switches=e1_switches,
        e2_switches=e2_switches,
        each_base_opts=PC20_OPTIONS,
        nodes=20000,
        start_line=2022501,
        rounds=1500,
        cutoff_epoch=args.cutoff_epoch,
        concurrency=args.concurrency,
    )
    if not rec["all_ok"]:
        raise RuntimeError("M14 recount verification failed!")
    elo = float(rec["elo"])
    pred_ok = -14.0 <= elo <= 4.0
    pred_line = (
        f"PREDICTION (2) CHECK: M14 Elo = {elo:+.2f} "
        f"(predicted -5.0, falsification range outside [-14.0, +4.0] -> {'TRUE' if pred_ok else 'FALSE'})"
    )
    with open(JOB47 / "M14_recount.txt", "a", encoding="utf-8") as rf:
        rf.write(pred_line + "\n")
    print(pred_line, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
