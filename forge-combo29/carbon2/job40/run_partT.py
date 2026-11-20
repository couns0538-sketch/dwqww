#!/usr/bin/env python3
"""
Job 40 Part T: THE COST PER NODE (`run_partT.py`, no games).
- O set (200 positions) at depth 12, PC20, built-in evaluation, Threads 1, Hash 16,
  `ucinewgame` + `isready` (and `position fen <fen>` + `isready`) before every search;
  per position records exact `perf_counter_ns()` wall time from `go depth 12` write to
  `bestmove` line receipt and the `nodes` of the last `info` line.
- Runs the 9 settings in forward order:
    1) all_off_1, 2) all_off_2, 3) only_K4, 4) only_S32, 5) only_B1,
    6) only_S13, 7) only_S10, 8) only_B8, 9) all_on
  followed immediately by all 9 in REVERSE order (`10..18`).
- Writes raw per-position rows + `.meta` for every one of the 18 runs and `partT_summary.txt`.
"""
from __future__ import annotations

import pathlib
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j40_lib import (  # noqa: E402
    ALL_SIX_FALSE,
    ALL_SIX_TRUE,
    JOB40,
    O_FENS_PATH,
    SIX_SWITCHES,
    WORK40,
    fmt_cmp,
    load_fens,
    pc20_option_lines,
    sha256_file,
    utc_now,
)

EXE_PATH = str(WORK40 / "bld_bundle/forge")
CPU_PIN = 2

EXP_NODE_SUMS = {
    "all_off_1": 8315168,
    "all_off_2": 8315168,
    "only_K4": 8080229,
    "only_S32": 8339315,
    "only_B1": 8548042,
    "only_S13": 8077984,
    "only_S10": 8314153,
    "only_B8": 8262696,
    "all_on": 8035170,
}


def build_setting_list() -> list[tuple[str, list[tuple[str, str]]]]:
    fwd: list[tuple[str, list[tuple[str, str]]]] = [
        ("all_off_1", list(ALL_SIX_FALSE)),
        ("all_off_2", list(ALL_SIX_FALSE)),
    ]
    for short, opt_name in SIX_SWITCHES:
        opts = [(o, "true" if o == opt_name else "false") for _, o in SIX_SWITCHES]
        fwd.append((f"only_{short}", opts))
    fwd.append(("all_on", list(ALL_SIX_TRUE)))
    return fwd


def run_timed_o_d12(
    run_idx: int,
    pass_tag: str,
    setting_name: str,
    extra_opts: list[tuple[str, str]],
    fens: list[str],
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
    for idx, fen in enumerate(fens, start=1):
        # Complete ucinewgame + isready AND position + isready BEFORE starting the `go` wall timer
        proc.stdin.write(f"ucinewgame\nisready\n")
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

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Engine exited rc={rc} stderr={stderr_txt!r}")

    node_sum = sum(r[1] for r in rows)
    wall_ns_sum = sum(r[2] for r in rows)
    wall_s = wall_ns_sum / 1e9
    wall_ms = wall_ns_sum / 1e6
    us_per_1k = (wall_ns_sum / 1e3) / (node_sum / 1000.0)  # microseconds per 1,000 nodes == ns per node
    ms_per_1k = wall_ms / (node_sum / 1000.0)

    stem = f"partT_{run_idx:02d}_{pass_tag}_{setting_name}"
    rows_path = JOB40 / f"{stem}.rows.txt"
    meta_path = JOB40 / f"{stem}.rows.txt.meta"

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
        f"exe_sha256: {sha256_file(EXE_PATH)}",
        f"id_name: {id_name}",
        f"cpu_pin: {CPU_PIN}",
        f"set_path: {O_FENS_PATH}",
        f"set_sha256: {sha256_file(O_FENS_PATH)}",
        f"positions: {len(rows)}",
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
        "wall_ns": wall_ns_sum,
        "wall_s": wall_s,
        "wall_ms": wall_ms,
        "ms_per_1k": ms_per_1k,
        "us_per_1k": us_per_1k,
    }


def main() -> int:
    fens = load_fens(O_FENS_PATH)
    assert len(fens) == 200
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

    # Short 1-second CPU frequency warm-up on CPU_PIN (discarded, before Run 01) so Run 01 isn't turbo-cold
    subprocess.run(
        ["taskset", "-c", str(CPU_PIN), EXE_PATH],
        input="uci\nisready\nbench 12\nquit\n",
        text=True,
        capture_output=True,
        check=True,
    )

    for idx, (ptag, sname, sopts) in enumerate(schedule, start=1):
        r = run_timed_o_d12(idx, ptag, sname, sopts, fens)
        results.append(r)
        exp_nd = EXP_NODE_SUMS[sname]
        ok, s = fmt_cmp(f"{r['stem']} node_sum", r["node_sum"], exp_nd)
        all_ok = all_ok and ok
        node_checks.append(s)
        print(
            f"[{idx:02d}/18] {r['stem']:<26s} nodes={r['node_sum']:>8d} "
            f"wall={r['wall_s']:.4f}s ({r['us_per_1k']:.2f} us/1k nodes)",
            flush=True,
        )

    # All-off runs: 4 runs total (fwd all_off_1, fwd all_off_2, rev all_off_2, rev all_off_1)
    all_off_runs = [r for r in results if r["setting"].startswith("all_off")]
    fwd_off_runs = [r for r in results if r["pass"] == "fwd" and r["setting"].startswith("all_off")]
    rev_off_runs = [r for r in results if r["pass"] == "rev" and r["setting"].startswith("all_off")]

    mean_off_4_ms1k = statistics.mean(r["ms_per_1k"] for r in all_off_runs)
    mean_off_4_us1k = statistics.mean(r["us_per_1k"] for r in all_off_runs)
    mean_off_fwd_ms1k = statistics.mean(r["ms_per_1k"] for r in fwd_off_runs)
    mean_off_rev_ms1k = statistics.mean(r["ms_per_1k"] for r in rev_off_runs)

    lines = [
        "=== JOB 40 PART T: THE COST PER NODE (O Set, 200 FENs, Depth 12, PC20, Built-in Eval) ===",
        f"start_utc: {start_u}",
        f"exe_path: {EXE_PATH}",
        f"exe_sha256({EXE_PATH}): {sha256_file(EXE_PATH)}",
        f"set_path: {O_FENS_PATH} | set_sha256({O_FENS_PATH}): {sha256_file(O_FENS_PATH)}",
        f"cpu_pin: {CPU_PIN}",
        "",
        "--- 1. Deterministic Node-Sum Checks Across All 18 Runs ---",
        *node_checks,
        "",
        "--- 2. All Four All-Off Runs Side by Side (Noise & Drift Check) ---",
        f"  mean_all_off_4_runs  : {mean_off_4_ms1k:.6f} ms / 1,000 nodes ({mean_off_4_us1k:.3f} us / 1,000 nodes)",
        f"  mean_all_off_forward : {mean_off_fwd_ms1k:.6f} ms / 1,000 nodes",
        f"  mean_all_off_reverse : {mean_off_rev_ms1k:.6f} ms / 1,000 nodes",
        f"  drift (rev / fwd)    : {mean_off_rev_ms1k / mean_off_fwd_ms1k:.6f}",
        "",
        "  run_id                     | pass | setting   | node_sum | wall_s   | ms/1k_nodes | us/1k_nodes | ratio_vs_mean4",
        "  ---------------------------+------+-----------+----------+----------+-------------+-------------+---------------",
    ]
    for r in all_off_runs:
        rat4 = r["ms_per_1k"] / mean_off_4_ms1k
        lines.append(
            f"  {r['stem']:<26s} | {r['pass']:<4s} | {r['setting']:<9s} | {r['node_sum']:>8d} | "
            f"{r['wall_s']:>8.4f} | {r['ms_per_1k']:>11.6f} | {r['us_per_1k']:>11.3f} | {rat4:>13.6f}"
        )

    lines.extend(
        [
            "",
            "--- 3. All 18 Runs in Execution Order (Forward 01..09, Then Reverse 10..18) ---",
            "  run_id                     | pass | setting   | node_sum | wall_s   | ms/1k_nodes | us/1k_nodes | ratio_vs_mean4 | ratio_vs_pass_off",
            "  ---------------------------+------+-----------+----------+----------+-------------+-------------+----------------+------------------",
        ]
    )
    for r in results:
        rat4 = r["ms_per_1k"] / mean_off_4_ms1k
        pass_ref = mean_off_fwd_ms1k if r["pass"] == "fwd" else mean_off_rev_ms1k
        rat_p = r["ms_per_1k"] / pass_ref
        lines.append(
            f"  {r['stem']:<26s} | {r['pass']:<4s} | {r['setting']:<9s} | {r['node_sum']:>8d} | "
            f"{r['wall_s']:>8.4f} | {r['ms_per_1k']:>11.6f} | {r['us_per_1k']:>11.3f} | {rat4:>14.6f} | {rat_p:>16.6f}"
        )

    lines.extend(
        [
            "",
            "--- 4. Forward + Reverse Paired Means per Setting (Ratio to Mean of All 4 All-Off Runs) ---",
            "  setting   | node_sum | fwd_wall_s | rev_wall_s | mean_wall_s | fwd_ms/1k  | rev_ms/1k  | mean_ms/1k | mean_us/1k | ratio_vs_all_off",
            "  ----------+----------+------------+------------+-------------+------------+------------+------------+------------+-----------------",
        ]
    )
    setting_order = [s for s, _ in fwd_settings]
    for sname in setting_order:
        rf = next(r for r in results if r["pass"] == "fwd" and r["setting"] == sname)
        rr = next(r for r in results if r["pass"] == "rev" and r["setting"] == sname)
        m_wall = 0.5 * (rf["wall_s"] + rr["wall_s"])
        m_ms1k = 0.5 * (rf["ms_per_1k"] + rr["ms_per_1k"])
        m_us1k = 0.5 * (rf["us_per_1k"] + rr["us_per_1k"])
        rat = m_ms1k / mean_off_4_ms1k
        lines.append(
            f"  {sname:<9s} | {rf['node_sum']:>8d} | {rf['wall_s']:>10.4f} | {rr['wall_s']:>10.4f} | "
            f"{m_wall:>11.4f} | {rf['ms_per_1k']:>10.6f} | {rr['ms_per_1k']:>10.6f} | "
            f"{m_ms1k:>10.6f} | {m_us1k:>10.3f} | {rat:>15.6f}"
        )

    rf_on = next(r for r in results if r["pass"] == "fwd" and r["setting"] == "all_on")
    rr_on = next(r for r in results if r["pass"] == "rev" and r["setting"] == "all_on")
    mean_all_on_ms1k = 0.5 * (rf_on["ms_per_1k"] + rr_on["ms_per_1k"])
    all_on_ratio = mean_all_on_ms1k / mean_off_4_ms1k

    lines.extend(
        [
            "",
            f"  SUMMARY all_on / all_off time-per-1000-nodes ratio (mean of 2 all_on / mean of 4 all_off): {all_on_ratio:.6f}",
            f"  (forward all_on / forward all_off = {rf_on['ms_per_1k'] / mean_off_fwd_ms1k:.6f}; "
            f"reverse all_on / reverse all_off = {rr_on['ms_per_1k'] / mean_off_rev_ms1k:.6f})",
        ]
    )
    ok_ov, s_ov = fmt_cmp("PART T OVERALL", 1 if all_ok else 0, 1)
    lines.append(s_ov)
    lines.append(f"done_utc: {utc_now()}")

    (JOB40 / "partT_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines[-28:]))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
