#!/usr/bin/env python3
"""
Job 47 Part T3 (`run_partT3.py`): THE BUNDLE'S SELF-PLAY COST WITH THE FAST IdeaB8b.
Runs Set A line L (`seed='carbon2-job33-a'`, `attempts=200`, `PC20`, built-in evaluation) on
`/tmp/carbon2_job47/bld_bundle10/forge` pinned to CPU core 1 in the exact 12-run rotation of T2:
  Forward (01..06): A B A B A B
  Reverse (07..12): B A B A B A
where:
  - A = `all_off` (all 10 `bundle10` `Idea*` switches + `HindsightDepth` explicitly `false`)
  - B = `bundle_fast` (`IdeaB8b=true`, `IdeaB8b_Fast=true`, `HindsightDepth=true`, other 8 `Idea*` switches `false`)
Verifies known answers BEFORE any time counts:
  - Every A run equals T2's A (`26,741` records, `26,867` searches, `107,124,743` nodes, `d5b52710...`)
  - Every B run equals T2's B (`27,817` records, `27,939` searches, `112,503,041` nodes, `bd9112cd...`)
"""
from __future__ import annotations

import pathlib
import re
import statistics
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j47_lib import (  # noqa: E402
    ALL_ELEVEN_FALSE,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SEARCHES,
    EXP_SETA_L_SHA,
    EXP_T2_B_NODES,
    EXP_T2_B_RECORDS,
    EXP_T2_B_SEARCHES,
    EXP_T2_B_SHA,
    JOB44,
    JOB47,
    PC20_OPTIONS,
    TEN_BUNDLE10_IDEA_NAMES,
    WORK47,
    fmt_cmp,
    get_id_name_strict,
    run_fresh_bench_strict,
    run_selfgame_set_strict,
    sha256_file,
    utc_now,
    write_v2_v3_rows,
)


def read_t2_summary_ratios(t2_summary_path: pathlib.Path) -> tuple[float, float, float]:
    txt = t2_summary_path.read_text(encoding="utf-8")
    m_wall = re.search(r"OVERALL WALL-TIME RATIO \(B / A, all 12\)\s*:\s*([0-9.]+)", txt)
    m_rps = re.search(r"OVERALL RECORDS/SEC RATIO \(B / A, all 12\)\s*:\s*([0-9.]+)", txt)
    m_tpn = re.search(r"IMPLIED TIME PER 1,000 NODES RATIO \(B / A\):\s*([0-9.]+)", txt)
    if not (m_wall and m_rps and m_tpn):
        raise RuntimeError(f"Could not parse T2 ratios from {t2_summary_path}")
    return float(m_wall.group(1)), float(m_rps.group(1)), float(m_tpn.group(1))


def write_t3_meta(
    meta_path: pathlib.Path,
    run_id: str,
    pass_tag: str,
    arm: str,
    exe_path: str,
    extra_opts: list[tuple[str, str]],
    sg_run,
    pre_readyok_lines: list[str],
    verified_opt_count: int,
    wall_ns: int,
    cpu_pin: int,
) -> None:
    wall_s = wall_ns / 1e9
    rec_per_s = sg_run.total_records / wall_s
    rec_per_h = rec_per_s * 3600.0
    opt_lines = [f"setoption name {k} value {v}" for k, v in list(PC20_OPTIONS) + list(extra_opts)]
    lines = [
        f"run_id: {run_id}",
        f"pass: {pass_tag}",
        f"arm: {arm}",
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(pathlib.Path(exe_path))}",
        f"id_name: {get_id_name_strict(exe_path)}",
        f"cpu_pin: {cpu_pin}",
        "suite: Set A (seed='carbon2-job33-a', attempts=200, built-in evaluation)",
        "selfgame_line: selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8",
        f"records: {sg_run.total_records}",
        f"searches: {sg_run.total_searches}",
        f"nodes: {sg_run.total_nodes}",
        f"record_text_sha256: {sg_run.full_sha256}",
        f"options_verified_in_uci_list: {verified_opt_count}/{len(opt_lines)}",
        f"pre_readyok_lines_count: {len(pre_readyok_lines)}",
        "pre_readyok_lines_begin:",
        *[f"  {pln}" for pln in pre_readyok_lines],
        "pre_readyok_lines_end",
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
    b10_exe = str(WORK47 / "bld_bundle10/forge")
    b10_sha = sha256_file(pathlib.Path(b10_exe))
    cpu_pin = 1

    t2_wall_ratio, t2_rps_ratio, t2_tpn_ratio = read_t2_summary_ratios(JOB44 / "partT2_summary.txt")
    t2_b_rows_ref = (JOB44 / "T2_02_fwd_B_bundle_SetA_L.rows.txt").read_text(encoding="utf-8").splitlines()[1:]

    opts_a = list(ALL_ELEVEN_FALSE)
    opts_b = [
        (o, "true" if o in ("IdeaB8b", "IdeaB8b_Fast") else "false")
        for o in TEN_BUNDLE10_IDEA_NAMES
    ] + [("HindsightDepth", "true")]

    # Warm-up on pinned CPU 1 before Run 01 (strict bench 12, matching T2's warm-up)
    _ = run_fresh_bench_strict(b10_exe, 12, opts_a)

    schedule = [
        ("fwd", "A", "all_off", opts_a),
        ("fwd", "B", "bundle_fast", opts_b),
        ("fwd", "A", "all_off", opts_a),
        ("fwd", "B", "bundle_fast", opts_b),
        ("fwd", "A", "all_off", opts_a),
        ("fwd", "B", "bundle_fast", opts_b),
        ("rev", "B", "bundle_fast", opts_b),
        ("rev", "A", "all_off", opts_a),
        ("rev", "B", "bundle_fast", opts_b),
        ("rev", "A", "all_off", opts_a),
        ("rev", "B", "bundle_fast", opts_b),
        ("rev", "A", "all_off", opts_a),
    ]

    start_u = utc_now()
    runs: list[dict] = []
    checks: list[str] = []
    all_ok = True

    for idx, (ptag, arm, label, opts) in enumerate(schedule, start=1):
        run_id = f"T3_{idx:02d}_{ptag}_{arm}_{label}"
        t0_ns = time.perf_counter_ns()
        sg_res, pre_lines, ver_cnt = run_selfgame_set_strict(
            b10_exe, "carbon2-job33-a", 200, None, extra_opts=opts, cpu_pin=cpu_pin
        )
        t1_ns = time.perf_counter_ns()
        wall_ns = t1_ns - t0_ns
        wall_s = wall_ns / 1e9
        rec_per_s = sg_res.total_records / wall_s
        rec_per_h = rec_per_s * 3600.0

        rows_p = JOB47 / f"{run_id}_SetA_L.rows.txt"
        meta_p = JOB47 / f"{run_id}_SetA_L.rows.txt.meta"
        write_v2_v3_rows(rows_p, f"Job 47 Part T3 {run_id} Set A line L (built-in eval, PC20)", sg_res)
        write_t3_meta(meta_p, run_id, ptag, arm, b10_exe, opts, sg_res, pre_lines, ver_cnt, wall_ns, cpu_pin)

        # Known-answer check IMMEDIATELY after each run ("Known answers before any time counts ... If they differ, say so with your numbers and stop T3")
        if arm == "A":
            run_checks = [
                fmt_cmp(f"{run_id} records vs T2 A", sg_res.total_records, EXP_SETA_L_RECORDS),
                fmt_cmp(f"{run_id} searches vs T2 A", sg_res.total_searches, EXP_SETA_L_SEARCHES),
                fmt_cmp(f"{run_id} nodes vs T2 A", sg_res.total_nodes, EXP_SETA_L_NODES),
                fmt_cmp(f"{run_id} sha256 vs T2 A", sg_res.full_sha256, EXP_SETA_L_SHA),
                fmt_cmp(f"{run_id} pre-readyok lines", len(pre_lines), 0),
            ]
        else:
            cur_b_rows = rows_p.read_text(encoding="utf-8").splitlines()[1:]
            eq_200 = sum(1 for x, y in zip(cur_b_rows, t2_b_rows_ref) if x == y)
            run_checks = [
                fmt_cmp(f"{run_id} records vs T2 B", sg_res.total_records, EXP_T2_B_RECORDS),
                fmt_cmp(f"{run_id} searches vs T2 B", sg_res.total_searches, EXP_T2_B_SEARCHES),
                fmt_cmp(f"{run_id} nodes vs T2 B", sg_res.total_nodes, EXP_T2_B_NODES),
                fmt_cmp(f"{run_id} sha256 vs T2 B", sg_res.full_sha256, EXP_T2_B_SHA),
                fmt_cmp(f"{run_id} attempt rows equal vs T2_02_fwd_B", eq_200, len(t2_b_rows_ref)),
                fmt_cmp(f"{run_id} pre-readyok lines", len(pre_lines), 0),
            ]

        for ok_c, s_c in run_checks:
            all_ok = all_ok and ok_c
            checks.append(s_c)
        if not all_ok:
            stop_msg = (
                f"STOP_T3 at {run_id}: known-answer mismatch! "
                f"got records={sg_res.total_records} searches={sg_res.total_searches} "
                f"nodes={sg_res.total_nodes} sha256={sg_res.full_sha256}"
            )
            (JOB47 / "partT3_summary.txt").write_text("\n".join(checks + [stop_msg]) + "\n", encoding="utf-8")
            print(stop_msg, flush=True)
            return 1

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
            f"records={sg_res.total_records} searches={sg_res.total_searches} nodes={sg_res.total_nodes} sha256={sg_res.full_sha256[:16]}...",
            flush=True,
        )

    a_runs = [r for r in runs if r["arm"] == "A"]
    b_runs = [r for r in runs if r["arm"] == "B"]
    a_ref = a_runs[0]
    b_ref = b_runs[0]

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

    mean_a_odd_wall = statistics.mean(a_runs[i]["wall_s"] for i in (0, 2, 4))
    mean_a_even_wall = statistics.mean(a_runs[i]["wall_s"] for i in (1, 3, 5))

    ratio_ba_wall_all = mean_b_wall / mean_a_wall
    ratio_ba_wall_fwd = mean_b_fwd_wall / mean_a_fwd_wall
    ratio_ba_wall_rev = mean_b_rev_wall / mean_a_rev_wall

    ratio_ba_rps_all = mean_b_rps / mean_a_rps
    ratio_ba_rps_fwd = mean_b_fwd_rps / mean_a_fwd_rps
    ratio_ba_rps_rev = mean_b_rev_rps / mean_a_rev_rps

    nodes_ratio = b_ref["nodes"] / a_ref["nodes"]
    records_ratio = b_ref["records"] / a_ref["records"]
    tpn_a_ms = (mean_a_wall * 1000.0) / (a_ref["nodes"] / 1000.0)
    tpn_b_ms = (mean_b_wall * 1000.0) / (b_ref["nodes"] / 1000.0)
    tpn_ratio = tpn_b_ms / tpn_a_ms

    a_spread_fwd_rev_s = abs(mean_a_rev_wall - mean_a_fwd_wall)
    a_spread_fwd_rev_pct = 100.0 * a_spread_fwd_rev_s / mean_a_wall
    a_spread_interleaved_s = abs(mean_a_even_wall - mean_a_odd_wall)
    a_spread_interleaved_pct = 100.0 * a_spread_interleaved_s / mean_a_wall

    pred_ok = 1.068 <= ratio_ba_wall_all <= 1.115

    out = [
        "=== JOB 47 PART T3: SELF-PLAY COST WITH FAST IdeaB8b ON SET A LINE L (12 Runs: A B A B A B, then B A B A B A, Pinned Core 1) ===",
        f"start_utc: {start_u}",
        f"exe_path: {b10_exe}",
        f"exe_sha256({b10_exe}): {b10_sha}",
        "",
        "--- 1. Known Answers Checked Before Any Time Counts ---",
        f"A (all_off)     invariant across all 6 runs: records={a_ref['records']}, searches={a_ref['searches']}, nodes={a_ref['nodes']}, record_text_sha256={a_ref['sha256']}",
        f"B (bundle_fast) invariant across all 6 runs: records={b_ref['records']}, searches={b_ref['searches']}, nodes={b_ref['nodes']}, record_text_sha256={b_ref['sha256']}",
        f"B / A deterministic structural ratios: records={records_ratio:.6f}, nodes={nodes_ratio:.6f}",
        *checks,
        "",
        "--- 2. All 12 Runs in Execution Order ---",
        "  run_id                    | pass | arm | records | searches |     nodes | wall_s  | records/s | records/hour | record_text_sha256",
        "  --------------------------+------+-----+---------+----------+-----------+---------+-----------+--------------+-----------------------------------------------------------------",
    ]
    for r in runs:
        out.append(
            f"  {r['run_id']:<25s} | {r['pass']:<4s} |  {r['arm']}  | {r['records']:>7d} | {r['searches']:>8d} | {r['nodes']:>9d} | "
            f"{r['wall_s']:>7.4f} | {r['rec_per_s']:>9.2f} | {r['rec_per_h']:>12.1f} | {r['sha256']}"
        )

    out.extend(
        [
            "",
            "--- 3. Means, Direction in Words, Split Into Nodes * Time-Per-Node, Beside Job 44 T2 ---",
            f"  A (all_off)     mean wall_s (all 6 runs)  : {mean_a_wall:.4f} s (SD={statistics.stdev(r['wall_s'] for r in a_runs):.4f} s) | mean records/s = {mean_a_rps:.2f} ({mean_a_rps*3600.0:.1f} / hr) | {tpn_a_ms:.6f} ms / 1k nodes",
            f"  B (bundle_fast) mean wall_s (all 6 runs)  : {mean_b_wall:.4f} s (SD={statistics.stdev(r['wall_s'] for r in b_runs):.4f} s) | mean records/s = {mean_b_rps:.2f} ({mean_b_rps*3600.0:.1f} / hr) | {tpn_b_ms:.6f} ms / 1k nodes",
            f"  DIRECTION IN WORDS (wall time)            : B takes {ratio_ba_wall_all:.6f} times A's wall time (beside T2's {t2_wall_ratio:.6f} without IdeaB8b_Fast).",
            f"  DIRECTION IN WORDS (records per second)   : B produces {ratio_ba_rps_all:.6f} times A's records per second (beside T2's {t2_rps_ratio:.6f} without IdeaB8b_Fast).",
            f"  DECOMPOSITION (nodes * time_per_node)     : B / A wall time = {nodes_ratio:.6f} (nodes_B / nodes_A) * {tpn_ratio:.6f} (time_per_node_B / time_per_node_A) = {nodes_ratio * tpn_ratio:.6f} (beside T2's {nodes_ratio:.6f} * {t2_tpn_ratio:.6f} = {t2_wall_ratio:.6f}).",
            f"  FORWARD WALL-TIME RATIO (B / A, runs 1..6): {ratio_ba_wall_fwd:.6f} (B_fwd={mean_b_fwd_wall:.4f} s / A_fwd={mean_a_fwd_wall:.4f} s; {(ratio_ba_wall_fwd - 1.0)*100.0:+.2f}%)",
            f"  REVERSE WALL-TIME RATIO (B / A, runs 7..12): {ratio_ba_wall_rev:.6f} (B_rev={mean_b_rev_wall:.4f} s / A_rev={mean_a_rev_wall:.4f} s; {(ratio_ba_wall_rev - 1.0)*100.0:+.2f}%)",
            f"  FORWARD RECORDS/SEC RATIO (B / A, runs 1..6): {ratio_ba_rps_fwd:.6f} (B_fwd={mean_b_fwd_rps:.2f} / A_fwd={mean_a_fwd_rps:.2f})",
            f"  REVERSE RECORDS/SEC RATIO (B / A, runs 7..12): {ratio_ba_rps_rev:.6f} (B_rev={mean_b_rev_rps:.2f} / A_rev={mean_a_rev_rps:.2f})",
            f"  NOISE LINE (two A means: A_fwd={mean_a_fwd_wall:.4f}s vs A_rev={mean_a_rev_wall:.4f}s): diff={a_spread_fwd_rev_s:.4f} s ({a_spread_fwd_rev_pct:.3f}% of A mean; ratio A_rev/A_fwd={mean_a_rev_wall/mean_a_fwd_wall:.6f})",
            f"  NOISE LINE (interleaved A[1,3,5]={mean_a_odd_wall:.4f}s vs A[2,4,6]={mean_a_even_wall:.4f}s): diff={a_spread_interleaved_s:.4f} s ({a_spread_interleaved_pct:.3f}% of A mean; ratio={mean_a_even_wall/mean_a_odd_wall:.6f})",
            "",
            f"  PREDICTION (3) CHECK: B / A wall-time ratio = {ratio_ba_wall_all:.6f} (predicted 1.090, falsification range outside [1.068, 1.115] -> {'TRUE' if pred_ok else 'FALSE'})",
        ]
    )
    ok_ov, s_ov = fmt_cmp("PART T3 OVERALL", 1 if all_ok else 0, 1)
    out.append(s_ov)
    out.append(f"done_utc: {utc_now()}")

    (JOB47 / "partT3_summary.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
