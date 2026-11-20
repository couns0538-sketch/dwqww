#!/usr/bin/env python3
"""
Job 41 Part T (`run_partT.py`):
- Same `O` set (200 positions) at depth 12, `PC20`, built-in evaluation, `Threads 1`, `Hash 16`,
  on `/tmp/carbon2_job41/bld_bundle7/forge` (`bundle_grok7`):
    (1) all_off_1, (2) all_off_2, (3) only_B8b, (4) only_HindsightDepth, (5) only_B8;
  followed immediately by all five in reverse order (`06..10`).
- Same table format as Job 40's Part T (`partT_summary.txt`), plus exact 200/200 row checks.
"""
from __future__ import annotations

import pathlib
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j41_lib import (  # noqa: E402
    ALL_SEVEN_FALSE,
    EXP_HINDSIGHT_O_SUM,
    EXP_OFF_O_SUM,
    JOB39,
    JOB41,
    O_FENS_PATH,
    SEVEN_SWITCH_NAMES,
    WORK41,
    diff_rows,
    fmt_cmp,
    load_fens,
    pc20_option_lines,
    read_j39_rows,
    sha256_file,
    utc_now,
)

EXE_PATH = str(WORK41 / "bld_bundle7/forge")
CPU_PIN = 1

EXP_NODE_SUMS = {
    "all_off_1": EXP_OFF_O_SUM,
    "all_off_2": EXP_OFF_O_SUM,
    "only_B8b": 8483711,
    "only_HindsightDepth": EXP_HINDSIGHT_O_SUM,
    "only_B8": 8262696,
}


def build_setting_list() -> list[tuple[str, list[tuple[str, str]]]]:
    off_all = ALL_SEVEN_FALSE + [("HindsightDepth", "false")]
    only_b8b = [(o, "true" if o == "IdeaB8b" else "false") for o in SEVEN_SWITCH_NAMES] + [("HindsightDepth", "false")]
    only_hd = ALL_SEVEN_FALSE + [("HindsightDepth", "true")]
    only_b8 = [(o, "true" if o == "IdeaB8" else "false") for o in SEVEN_SWITCH_NAMES] + [("HindsightDepth", "false")]
    return [
        ("all_off_1", off_all),
        ("all_off_2", off_all),
        ("only_B8b", only_b8b),
        ("only_HindsightDepth", only_hd),
        ("only_B8", only_b8),
    ]


def run_timed_o_d12(
    run_idx: int,
    pass_tag: str,
    setting_name: str,
    extra_opts: list[tuple[str, str]],
    fens: list[str],
    ref_rows: list[tuple[int, int, str, str]],
) -> dict:
    opt_lines = pc20_option_lines(extra_opts)
    cmd = ["taskset", "-c", str(CPU_PIN), EXE_PATH]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline()
        if ln == "":
            raise RuntimeError("EOF waiting for uciok")
        ln = ln.rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    rows: list[tuple[int, int, int, str, str]] = []
    cmp_rows: list[tuple[int, int, str, str]] = []
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write("ucinewgame\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass
        proc.stdin.write(f"position fen {fen}\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass

        last_nodes = None
        last_score = ""
        bestmove = None

        t0_ns = time.perf_counter_ns()
        proc.stdin.write("go depth 12\n")
        proc.stdin.flush()
        while True:
            ln = proc.stdout.readline()
            if ln == "":
                raise RuntimeError(f"EOF during go depth 12 at pos {idx}")
            if ln.startswith("bestmove "):
                t1_ns = time.perf_counter_ns()
                bestmove = ln.split()[1]
                break
            if ln.startswith("info ") and " nodes " in ln:
                toks = ln.split()
                ni = toks.index("nodes")
                last_nodes = int(toks[ni + 1])
                if "score" in toks:
                    si = toks.index("score")
                    last_score = f"{toks[si + 1]} {toks[si + 2]}"

        assert last_nodes is not None and bestmove is not None
        rows.append((idx, last_nodes, t1_ns - t0_ns, bestmove, last_score))
        cmp_rows.append((idx, last_nodes, bestmove, last_score))

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Engine exited rc={rc} stderr={stderr_txt!r}")

    any_diff, _ = diff_rows(cmp_rows, ref_rows)
    node_sum = sum(r[1] for r in rows)
    wall_ns_sum = sum(r[2] for r in rows)
    wall_s = wall_ns_sum / 1e9
    wall_ms = wall_ns_sum / 1e6
    us_per_1k = (wall_ns_sum / 1e3) / (node_sum / 1000.0)
    ms_per_1k = wall_ms / (node_sum / 1000.0)

    stem = f"partT_{run_idx:02d}_{pass_tag}_{setting_name}"
    rows_path = JOB41 / f"{stem}.rows.txt"
    meta_path = JOB41 / f"{stem}.rows.txt.meta"

    hdr = [
        f"# run={run_idx:02d} pass={pass_tag} setting={setting_name} positions={len(rows)} depth=12 "
        f"node_sum={node_sum} wall_ns_sum={wall_ns_sum} wall_ms={wall_ms:.3f} ms_per_1000_nodes={ms_per_1k:.6f}",
        "position\tnodes\twall_ns\tbestmove\tscore",
    ]
    body = [f"{p}\t{nd}\t{wns}\t{bm}\t{sc}" for p, nd, wns, bm, sc in rows]
    rows_path.write_text("\n".join(hdr + body) + "\n", encoding="utf-8")

    meta = [
        f"run_id: {stem}",
        f"exe_path: {EXE_PATH}",
        f"exe_sha256: {sha256_file(pathlib.Path(EXE_PATH))}",
        f"id_name: {id_name}",
        f"cpu_pin: {CPU_PIN}",
        f"set_path: {O_FENS_PATH}",
        f"set_sha256: {sha256_file(O_FENS_PATH)}",
        f"positions: {len(rows)}",
        f"equal_positions_vs_ref: {200 - any_diff}",
        "depth: 12",
        f"node_sum: {node_sum}",
        f"wall_ns_sum: {wall_ns_sum}",
        f"wall_s: {wall_s:.6f}",
        f"ms_per_1000_nodes: {ms_per_1k:.6f}",
        f"us_per_1000_nodes: {us_per_1k:.3f}",
        "options_sent_begin:",
        *[f"  {o}" for o in opt_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    meta_path.write_text("\n".join(meta) + "\n", encoding="utf-8")

    return {
        "run_idx": run_idx,
        "stem": stem,
        "pass": pass_tag,
        "setting": setting_name,
        "node_sum": node_sum,
        "equal_pos": 200 - any_diff,
        "wall_ns": wall_ns_sum,
        "wall_s": wall_s,
        "wall_ms": wall_ms,
        "ms_per_1k": ms_per_1k,
        "us_per_1k": us_per_1k,
    }


def main() -> int:
    fens = load_fens(O_FENS_PATH)
    assert len(fens) == 200

    refs = {
        "all_off_1": read_j39_rows(JOB39 / "OFF_O_d12.rows.txt"),
        "all_off_2": read_j39_rows(JOB39 / "OFF_O_d12.rows.txt"),
        "only_B8b": read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt"),
        "only_HindsightDepth": read_j39_rows(JOB41 / "partK_HindsightDepth_O_d12.rows.txt"),
        "only_B8": read_j39_rows(JOB41 / "P7_bundle7_only_B8_O_d12.rows.txt"),
    }

    fwd_settings = build_setting_list()
    rev_settings = list(reversed(fwd_settings))

    schedule: list[tuple[str, str, list[tuple[str, str]]]] = []
    for sname, sopts in fwd_settings:
        schedule.append(("fwd", sname, sopts))
    for sname, sopts in rev_settings:
        schedule.append(("rev", sname, sopts))

    start_u = utc_now()
    results: list[dict] = []
    all_ok = True
    node_checks: list[str] = []

    # Short 1-second CPU warm-up on CPU_PIN (discarded before Run 01)
    subprocess.run(
        ["taskset", "-c", str(CPU_PIN), EXE_PATH],
        input="uci\nisready\nbench 12\nquit\n",
        text=True,
        capture_output=True,
        check=True,
    )

    for idx, (ptag, sname, sopts) in enumerate(schedule, start=1):
        r = run_timed_o_d12(idx, ptag, sname, sopts, fens, refs[sname])
        results.append(r)
        ok_n, s_n = fmt_cmp(f"{r['stem']} node_sum", r["node_sum"], EXP_NODE_SUMS[sname])
        ok_p, s_p = fmt_cmp(f"{r['stem']} equal_pos", r["equal_pos"], 200)
        all_ok = all_ok and ok_n and ok_p
        node_checks.extend([s_n, s_p])
        print(
            f"[{idx:02d}/10] {r['stem']:<34s} nodes={r['node_sum']:>8d} eq={r['equal_pos']}/200 "
            f"wall={r['wall_s']:.4f}s ({r['us_per_1k']:.2f} us/1k nodes)",
            flush=True,
        )

    all_off_runs = [r for r in results if r["setting"].startswith("all_off")]
    fwd_off_runs = [r for r in results if r["pass"] == "fwd" and r["setting"].startswith("all_off")]
    rev_off_runs = [r for r in results if r["pass"] == "rev" and r["setting"].startswith("all_off")]

    mean_off_4_ms1k = statistics.mean(r["ms_per_1k"] for r in all_off_runs)
    mean_off_4_us1k = statistics.mean(r["us_per_1k"] for r in all_off_runs)
    mean_off_fwd_ms1k = statistics.mean(r["ms_per_1k"] for r in fwd_off_runs)
    mean_off_rev_ms1k = statistics.mean(r["ms_per_1k"] for r in rev_off_runs)

    lines = [
        "=== JOB 41 PART T: THE COST PER NODE (O Set, 200 FENs, Depth 12, PC20, Built-in Eval, bundle_grok7) ===",
        f"start_utc: {start_u}",
        f"exe_path: {EXE_PATH}",
        f"exe_sha256({EXE_PATH}): {sha256_file(pathlib.Path(EXE_PATH))}",
        f"set_path: {O_FENS_PATH} | set_sha256({O_FENS_PATH}): {sha256_file(O_FENS_PATH)}",
        f"cpu_pin: {CPU_PIN}",
        "",
        "--- 1. Deterministic Node-Sum & Row-Identity Checks Across All 10 Runs ---",
        *node_checks,
        "",
        "--- 2. All Four All-Off Runs Side by Side (Noise & Drift Check) ---",
        f"  mean_all_off_4_runs  : {mean_off_4_ms1k:.6f} ms / 1,000 nodes ({mean_off_4_us1k:.3f} us / 1,000 nodes)",
        f"  mean_all_off_forward : {mean_off_fwd_ms1k:.6f} ms / 1,000 nodes",
        f"  mean_all_off_reverse : {mean_off_rev_ms1k:.6f} ms / 1,000 nodes",
        f"  drift (rev / fwd)    : {mean_off_rev_ms1k / mean_off_fwd_ms1k:.6f}",
        "",
        "  run_id                             | pass | setting             | node_sum | wall_s   | ms/1k_nodes | us/1k_nodes | ratio_vs_mean4",
        "  -----------------------------------+------+---------------------+----------+----------+-------------+-------------+---------------",
    ]
    for r in all_off_runs:
        rat4 = r["ms_per_1k"] / mean_off_4_ms1k
        lines.append(
            f"  {r['stem']:<34s} | {r['pass']:<4s} | {r['setting']:<19s} | {r['node_sum']:>8d} | "
            f"{r['wall_s']:>8.4f} | {r['ms_per_1k']:>11.6f} | {r['us_per_1k']:>11.3f} | {rat4:>13.6f}"
        )

    lines.extend(
        [
            "",
            "--- 3. All 10 Runs in Execution Order (Forward 01..05, Then Reverse 06..10) ---",
            "  run_id                             | pass | setting             | node_sum | wall_s   | ms/1k_nodes | us/1k_nodes | ratio_vs_mean4 | ratio_vs_pass_off",
            "  -----------------------------------+------+---------------------+----------+----------+-------------+-------------+----------------+------------------",
        ]
    )
    for r in results:
        rat4 = r["ms_per_1k"] / mean_off_4_ms1k
        pass_ref = mean_off_fwd_ms1k if r["pass"] == "fwd" else mean_off_rev_ms1k
        rat_p = r["ms_per_1k"] / pass_ref
        lines.append(
            f"  {r['stem']:<34s} | {r['pass']:<4s} | {r['setting']:<19s} | {r['node_sum']:>8d} | "
            f"{r['wall_s']:>8.4f} | {r['ms_per_1k']:>11.6f} | {r['us_per_1k']:>11.3f} | {rat4:>14.6f} | {rat_p:>16.6f}"
        )

    lines.extend(
        [
            "",
            "--- 4. Forward + Reverse Paired Means per Setting (Ratio to Mean of All 4 All-Off Runs) ---",
            "  setting             | node_sum | fwd_wall_s | rev_wall_s | mean_wall_s | fwd_ms/1k  | rev_ms/1k  | mean_ms/1k | mean_us/1k | ratio_vs_all_off",
            "  --------------------+----------+------------+------------+-------------+------------+------------+------------+------------+-----------------",
        ]
    )
    for sname, _ in fwd_settings:
        rf = next(r for r in results if r["pass"] == "fwd" and r["setting"] == sname)
        rr = next(r for r in results if r["pass"] == "rev" and r["setting"] == sname)
        m_wall = 0.5 * (rf["wall_s"] + rr["wall_s"])
        m_ms1k = 0.5 * (rf["ms_per_1k"] + rr["ms_per_1k"])
        m_us1k = 0.5 * (rf["us_per_1k"] + rr["us_per_1k"])
        rat = m_ms1k / mean_off_4_ms1k
        lines.append(
            f"  {sname:<19s} | {rf['node_sum']:>8d} | {rf['wall_s']:>10.4f} | {rr['wall_s']:>10.4f} | "
            f"{m_wall:>11.4f} | {rf['ms_per_1k']:>10.6f} | {rr['ms_per_1k']:>10.6f} | "
            f"{m_ms1k:>10.6f} | {m_us1k:>10.3f} | {rat:>15.6f}"
        )

    lines.append("")
    ok_ov, s_ov = fmt_cmp("PART T OVERALL", 1 if all_ok else 0, 1)
    lines.append(s_ov)
    lines.append(f"done_utc: {utc_now()}")

    (JOB41 / "partT_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines[-22:]))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
