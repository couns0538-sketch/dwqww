#!/usr/bin/env python3
"""
Job 44 Part T2 (`run_partT2.py`): WHAT THE BUNDLE COSTS IN SELF-PLAY POSITIONS.
Runs Set A line L (`seed='carbon2-job33-a'`, `attempts=200`, `PC20`, built-in evaluation) on
`/tmp/carbon2_job44/bld_bundle9/forge` pinned to CPU core 1 in the 12-run rotation:
  Forward (01..06): A B A B A B
  Reverse (07..12): B A B A B A
where:
  - A = `all_off` (all 9 `Idea*` switches + `HindsightDepth` explicitly `false`)
  - B = `bundle` (`IdeaB8b=true`, `HindsightDepth=true`, all other 8 `Idea*` switches explicitly `false`)
Note on C: Job 43's `IdeaB8_Fast` met every identity row on O, G, and Set A line L, and covers `IdeaB8` (078)
only (not `IdeaB8b` [028]), so C is not added per File 44 lines 103-104.
"""
from __future__ import annotations

import pathlib
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j44_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    JOB44,
    NINE_SWITCH_NAMES,
    WORK44,
    fmt_cmp,
    get_id_name,
    pc20_option_lines,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    write_v2_v3_rows,
)


def write_t2_meta(
    meta_path: pathlib.Path,
    run_id: str,
    pass_tag: str,
    arm: str,
    exe_path: str,
    extra_opts: list[tuple[str, str]],
    sg_run,
    wall_ns: int,
    cpu_pin: int,
) -> None:
    wall_s = wall_ns / 1e9
    rec_per_s = sg_run.total_records / wall_s
    rec_per_h = rec_per_s * 3600.0
    opt_lines = pc20_option_lines(extra_opts)
    lines = [
        f"run_id: {run_id}",
        f"pass: {pass_tag}",
        f"arm: {arm}",
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(pathlib.Path(exe_path))}",
        f"id_name: {get_id_name(exe_path)}",
        f"cpu_pin: {cpu_pin}",
        "suite: Set A (seed='carbon2-job33-a', attempts=200, built-in evaluation)",
        "selfgame_line: selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8",
        f"records: {sg_run.total_records}",
        f"searches: {sg_run.total_searches}",
        f"nodes: {sg_run.total_nodes}",
        f"record_text_sha256: {sg_run.full_sha256}",
        f"wall_ns: {wall_ns}",
        f"wall_s: {wall_s:.6f}",
        f"records_per_sec: {rec_per_s:.3f}",
        f"records_per_hour: {rec_per_h:.1f}",
        "options_sent_begin:",
        *[f"  {o}" for o in opt_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    meta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    b9_exe = str(WORK44 / "bld_bundle9/forge")
    b9_sha = sha256_file(pathlib.Path(b9_exe))
    cpu_pin = 1

    opts_a = ALL_TEN_FALSE
    opts_b = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "true")]

    # 1s warm-up on pinned CPU 1 before Run 01
    subprocess.run(
        ["taskset", "-c", str(cpu_pin), b9_exe],
        input="uci\nisready\nbench 12\nquit\n",
        text=True,
        capture_output=True,
        check=True,
    )

    schedule = [
        ("fwd", "A", "all_off", opts_a),
        ("fwd", "B", "bundle", opts_b),
        ("fwd", "A", "all_off", opts_a),
        ("fwd", "B", "bundle", opts_b),
        ("fwd", "A", "all_off", opts_a),
        ("fwd", "B", "bundle", opts_b),
        ("rev", "B", "bundle", opts_b),
        ("rev", "A", "all_off", opts_a),
        ("rev", "B", "bundle", opts_b),
        ("rev", "A", "all_off", opts_a),
        ("rev", "B", "bundle", opts_b),
        ("rev", "A", "all_off", opts_a),
    ]

    start_u = utc_now()
    runs: list[dict] = []
    for idx, (ptag, arm, label, opts) in enumerate(schedule, start=1):
        run_id = f"T2_{idx:02d}_{ptag}_{arm}_{label}"
        t0_ns = time.perf_counter_ns()
        sg_res = run_selfgame_set_with_options(b9_exe, "carbon2-job33-a", 200, None, extra_opts=opts, cpu_pin=cpu_pin)
        t1_ns = time.perf_counter_ns()
        wall_ns = t1_ns - t0_ns
        wall_s = wall_ns / 1e9
        rec_per_s = sg_res.total_records / wall_s
        rec_per_h = rec_per_s * 3600.0

        rows_p = JOB44 / f"{run_id}_SetA_L.rows.txt"
        meta_p = JOB44 / f"{run_id}_SetA_L.rows.txt.meta"
        write_v2_v3_rows(rows_p, f"Job 44 Part T2 {run_id} Set A line L (built-in eval, PC20)", sg_res)
        write_t2_meta(meta_p, run_id, ptag, arm, b9_exe, opts, sg_res, wall_ns, cpu_pin)

        runs.append(
            {
                "idx": idx,
                "run_id": run_id,
                "pass": ptag,
                "arm": arm,
                "label": label,
                "records": sg_res.total_records,
                "searches": sg_res.total_searches,
                "nodes": sg_res.total_nodes,
                "sha256": sg_res.full_sha256,
                "wall_s": wall_s,
                "rec_per_s": rec_per_s,
                "rec_per_h": rec_per_h,
            }
        )
        print(
            f"[{utc_now()}] {run_id}: wall_s={wall_s:.4f}s rec/s={rec_per_s:.2f} "
            f"records={sg_res.total_records} nodes={sg_res.total_nodes} sha256={sg_res.full_sha256[:16]}...",
            flush=True,
        )

    a_runs = [r for r in runs if r["arm"] == "A"]
    b_runs = [r for r in runs if r["arm"] == "B"]
    b_ref = b_runs[0]

    checks: list[str] = []
    all_ok = True
    for r in a_runs:
        for lbl, got, exp in [
            (f"{r['run_id']} records vs OFF known answer", r["records"], EXP_SETA_L_RECORDS),
            (f"{r['run_id']} nodes vs OFF known answer", r["nodes"], EXP_SETA_L_NODES),
            (f"{r['run_id']} sha256 vs OFF known answer", r["sha256"], EXP_SETA_L_SHA),
        ]:
            ok, s = fmt_cmp(lbl, got, exp)
            all_ok = all_ok and ok
            checks.append(s)

    for r in b_runs:
        for lbl, got, exp in [
            (f"{r['run_id']} records vs B[0]", r["records"], b_ref["records"]),
            (f"{r['run_id']} searches vs B[0]", r["searches"], b_ref["searches"]),
            (f"{r['run_id']} nodes vs B[0]", r["nodes"], b_ref["nodes"]),
            (f"{r['run_id']} sha256 vs B[0]", r["sha256"], b_ref["sha256"]),
        ]:
            ok, s = fmt_cmp(lbl, got, exp)
            all_ok = all_ok and ok
            checks.append(s)

    a_fwd = [r for r in a_runs if r["pass"] == "fwd"]
    a_rev = [r for r in a_runs if r["pass"] == "rev"]
    b_fwd = [r for r in b_runs if r["pass"] == "fwd"]
    b_rev = [r for r in b_runs if r["pass"] == "rev"]

    mean_a_wall = statistics.mean(r["wall_s"] for r in a_runs)
    mean_b_wall = statistics.mean(r["wall_s"] for r in b_runs)
    mean_a_rps = statistics.mean(r["rec_per_s"] for r in a_runs)
    mean_b_rps = statistics.mean(r["rec_per_s"] for r in b_runs)

    mean_a_fwd_wall = statistics.mean(r["wall_s"] for r in a_fwd)
    mean_a_rev_wall = statistics.mean(r["wall_s"] for r in a_rev)
    mean_b_fwd_wall = statistics.mean(r["wall_s"] for r in b_fwd)
    mean_b_rev_wall = statistics.mean(r["wall_s"] for r in b_rev)

    mean_a_fwd_rps = statistics.mean(r["rec_per_s"] for r in a_fwd)
    mean_a_rev_rps = statistics.mean(r["rec_per_s"] for r in a_rev)
    mean_b_fwd_rps = statistics.mean(r["rec_per_s"] for r in b_fwd)
    mean_b_rev_rps = statistics.mean(r["rec_per_s"] for r in b_rev)

    # Interleaved odd-vs-even A pairs (A[0,2,4] vs A[1,3,5]) for additional noise diagnostic
    mean_a_odd_wall = statistics.mean(a_runs[i]["wall_s"] for i in (0, 2, 4))
    mean_a_even_wall = statistics.mean(a_runs[i]["wall_s"] for i in (1, 3, 5))

    ratio_ba_wall_all = mean_b_wall / mean_a_wall
    ratio_ba_wall_fwd = mean_b_fwd_wall / mean_a_fwd_wall
    ratio_ba_wall_rev = mean_b_rev_wall / mean_a_rev_wall

    ratio_ba_rps_all = mean_b_rps / mean_a_rps
    ratio_ba_rps_fwd = mean_b_fwd_rps / mean_a_fwd_rps
    ratio_ba_rps_rev = mean_b_rev_rps / mean_a_rev_rps

    a_spread_fwd_rev_s = abs(mean_a_rev_wall - mean_a_fwd_wall)
    a_spread_fwd_rev_pct = 100.0 * a_spread_fwd_rev_s / mean_a_wall
    a_spread_interleaved_s = abs(mean_a_even_wall - mean_a_odd_wall)
    a_spread_interleaved_pct = 100.0 * a_spread_interleaved_s / mean_a_wall

    out = [
        "=== JOB 44 PART T2: SELF-PLAY COST ON SET A LINE L (12 Runs: A B A B A B, then B A B A B A, Pinned Core 1) ===",
        f"start_utc: {start_u}",
        f"exe_path: {b9_exe}",
        f"exe_sha256({b9_exe}): {b9_sha}",
        "arm_C_note: Job 43's IdeaB8_Fast met every identity row (O, G, Set A line L) and covers IdeaB8 (078) only, NOT IdeaB8b (028); therefore arm C is not added.",
        "",
        f"A (all_off) invariant across all 6 runs: records={EXP_SETA_L_RECORDS}, searches=26856, nodes={EXP_SETA_L_NODES}, record_text_sha256={EXP_SETA_L_SHA}",
        f"B (bundle)  invariant across all 6 runs: records={b_ref['records']}, searches={b_ref['searches']}, nodes={b_ref['nodes']}, record_text_sha256={b_ref['sha256']}",
        f"B / A structural ratios (deterministic): records={b_ref['records']/EXP_SETA_L_RECORDS:.6f}, nodes={b_ref['nodes']/EXP_SETA_L_NODES:.6f}",
        "",
        "--- All 12 Runs in Execution Order ---",
        "  run_id                | pass | arm | records |     nodes | wall_s  | records/s | records/hour | record_text_sha256",
        "  ----------------------+------+-----+---------+-----------+---------+-----------+--------------+-----------------------------------------------------------------",
    ]
    for r in runs:
        out.append(
            f"  {r['run_id']:<21s} | {r['pass']:<4s} |  {r['arm']}  | {r['records']:>7d} | {r['nodes']:>9d} | "
            f"{r['wall_s']:>7.4f} | {r['rec_per_s']:>9.2f} | {r['rec_per_h']:>12.1f} | {r['sha256']}"
        )

    out.extend(
        [
            "",
            "--- Means, B / A Ratios, Forward vs Reverse Ratios, and Two-A-Means Noise Spread ---",
            f"  A (all_off) mean wall_s (all 6 runs)      : {mean_a_wall:.4f} s (SD={statistics.stdev(r['wall_s'] for r in a_runs):.4f} s) | mean records/s = {mean_a_rps:.2f} ({mean_a_rps*3600.0:.1f} / hr)",
            f"  B (bundle)  mean wall_s (all 6 runs)      : {mean_b_wall:.4f} s (SD={statistics.stdev(r['wall_s'] for r in b_runs):.4f} s) | mean records/s = {mean_b_rps:.2f} ({mean_b_rps*3600.0:.1f} / hr)",
            f"  OVERALL WALL-TIME RATIO (B / A, all 12)   : {ratio_ba_wall_all:.6f} ({(ratio_ba_wall_all - 1.0)*100.0:+.2f}%)",
            f"  FORWARD WALL-TIME RATIO (B / A, runs 1..6): {ratio_ba_wall_fwd:.6f} (B_fwd={mean_b_fwd_wall:.4f} s / A_fwd={mean_a_fwd_wall:.4f} s; {(ratio_ba_wall_fwd - 1.0)*100.0:+.2f}%)",
            f"  REVERSE WALL-TIME RATIO (B / A, runs 7..12): {ratio_ba_wall_rev:.6f} (B_rev={mean_b_rev_wall:.4f} s / A_rev={mean_a_rev_wall:.4f} s; {(ratio_ba_wall_rev - 1.0)*100.0:+.2f}%)",
            f"  OVERALL RECORDS/SEC RATIO (B / A, all 12) : {ratio_ba_rps_all:.6f} ({(ratio_ba_rps_all - 1.0)*100.0:+.2f}%)",
            f"  FORWARD RECORDS/SEC RATIO (B / A, runs 1..6): {ratio_ba_rps_fwd:.6f} (B_fwd={mean_b_fwd_rps:.2f} / A_fwd={mean_a_fwd_rps:.2f})",
            f"  REVERSE RECORDS/SEC RATIO (B / A, runs 7..12): {ratio_ba_rps_rev:.6f} (B_rev={mean_b_rev_rps:.2f} / A_rev={mean_a_rev_rps:.2f})",
            f"  NOISE LINE (two A means: A_fwd={mean_a_fwd_wall:.4f}s vs A_rev={mean_a_rev_wall:.4f}s): diff={a_spread_fwd_rev_s:.4f} s ({a_spread_fwd_rev_pct:.3f}% of A mean; ratio A_rev/A_fwd={mean_a_rev_wall/mean_a_fwd_wall:.6f})",
            f"  NOISE LINE (interleaved A[1,3,5]={mean_a_odd_wall:.4f}s vs A[2,4,6]={mean_a_even_wall:.4f}s): diff={a_spread_interleaved_s:.4f} s ({a_spread_interleaved_pct:.3f}% of A mean; ratio={mean_a_even_wall/mean_a_odd_wall:.6f})",
            f"  IMPLIED TIME PER 1,000 NODES RATIO (B / A): {(mean_b_wall / b_ref['nodes']) / (mean_a_wall / EXP_SETA_L_NODES):.6f}",
            "",
            "--- Determinism & Known-Answer Checks ---",
            *checks,
            "",
            f"  PREDICTION (3) CHECK: B / A wall-time ratio = {ratio_ba_wall_all:.6f} (predicted 1.065, range [1.020, 1.115] -> {'TRUE' if 1.020 <= ratio_ba_wall_all <= 1.115 else 'FALSE'})",
        ]
    )
    ok_ov, s_ov = fmt_cmp("PART T2 OVERALL", 1 if all_ok else 0, 1)
    out.append(s_ov)
    out.append(f"done_utc: {utc_now()}")

    (JOB44 / "partT2_summary.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
