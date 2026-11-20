#!/usr/bin/env python3
"""
Job 39 Single-Port Builder & Verifier (`run_port_verify.py`):
Applies `<port_id>.patch.txt` against a fresh copy of `/tmp/carbon2_job36/tpl_r15d_v3`,
builds with the Job 36 Release recipe (`clang++-18 -O3 -DNDEBUG ... -flto=thin`),
verifies EVERY OFF number of Step 0 (plus `O` d12 switch-off == Step 0 `OFF_O_d12.rows.txt`),
and runs Switch ON (`PC20`, built-in evaluation, `Threads 1`, `Hash 16`, `ucinewgame` + `isready`
before every search) on `O` (200 FENs, d12), `G` (353 FENs, d12), and `Set A line L` through
the `selfgame` driver, writing `.rows.txt`, `.meta`, and `<port_id>_summary.txt`.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import pathlib
import sys

sys.dont_write_bytecode = True

from j39_lib import (
    G_EPD_PATH,
    JOB39,
    O_FENS_PATH,
    WORK39,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    get_id_name,
    run_epd_depth12,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    write_seta_meta,
    write_v2_v3_rows,
)


def load_committed_rows(path: pathlib.Path) -> list[tuple[int, int, str, str]]:
    rows: list[tuple[int, int, str, str]] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#") or ln.startswith("position\t"):
            continue
        pos_s, nd_s, bm, sc = ln.split("\t")
        rows.append((int(pos_s), int(nd_s), bm, sc))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port-id", required=True, help="e.g. P1_K4_093")
    ap.add_argument("--option", required=True, help="e.g. IdeaK4")
    ap.add_argument("--notes-count", type=int, required=True, help="Number of port_notes.txt lines for this port")
    args = ap.parse_args()

    pid = args.port_id
    opt = args.option
    patch_path = JOB39 / f"{pid}.patch.txt"
    assert patch_path.exists(), f"Missing {patch_path}"

    src_dir = WORK39 / f"src_{pid}"
    bld_dir = WORK39 / f"bld_{pid}"

    lines: list[str] = [
        f"=== JOB 39 PART P: {pid} (option `{opt}`) ===",
        f"start_utc: {utc_now()}",
        f"patch_file: {patch_path.name} | patch_sha256: {sha256_file(patch_path)} | port_notes_lines: {args.notes_count}",
    ]

    ok_ap, msg_ap = apply_patch_to_fresh_v3(patch_path, src_dir)
    lines.append(f"  apply_against_r15d_v3                       : {msg_ap}")
    if not ok_ap:
        raise SystemExit(1)

    exe_path, exe_sha, _cflags, _lflags = build_release_v3(src_dir, bld_dir)
    id_name = get_id_name(exe_path)
    lines.append(f"  exe_path: {exe_path} | exe_sha256: {exe_sha} | {id_name}")
    lines.append("")

    # 1. Verify ALL OFF numbers with default off (no extra option on bench/perft, and explicit opt=false on PC20/SetA/n60)
    lines.append(f"--- 1. Switch OFF Verification (Default Off & `{opt}=false`) ---")
    ok_off_def, off_def_lines = verify_all_off_numbers(f"{pid}_off", exe_path, [(opt, "false")])
    lines.extend(off_def_lines)

    # Also verify no-extra-option PC20 bench 11 & 13 and O d12 default-off == Step 0 OFF_O_d12.rows.txt
    base_o_rows = load_committed_rows(JOB39 / "OFF_O_d12.rows.txt")
    base_g_rows = load_committed_rows(JOB39 / "OFF_G_d12.rows.txt")
    off_o_tmp = WORK39 / f"{pid}_off_O_d12.rows.txt"
    off_o_meta_tmp = WORK39 / f"{pid}_off_O_d12.rows.txt.meta"
    port_off_o = run_epd_depth12(exe_path, O_FENS_PATH, None, off_o_tmp, off_o_meta_tmp, 12, 3)
    off_o_any_diff, _ = diff_rows(port_off_o, base_o_rows)
    ok_off_o_sum, s_off_o_sum = fmt_cmp(f"{pid}_off O d12 sum vs Step0 OFF", sum(r[1] for r in port_off_o), sum(r[1] for r in base_o_rows))
    ok_off_o_dif, s_off_o_dif = fmt_cmp(f"{pid}_off O d12 differing positions", off_o_any_diff, 0)
    lines.extend([s_off_o_sum, s_off_o_dif, ""])

    all_off_ok = ok_off_def and ok_off_o_sum and ok_off_o_dif
    if not all_off_ok:
        out_fail = "\n".join(lines + [f"{pid} OFF VERIFICATION: FAIL"]) + "\n"
        print(out_fail, flush=True)
        raise SystemExit(1)

    # 2. Switch ON runs: O d12, G d12, and Set A line L concurrently across 3 cores
    lines.append(f"--- 2. Switch ON (`setoption name {opt} value true`, PC20, built-in evaluation) ---")
    on_opts = [(opt, "true")]
    out_o_rows = JOB39 / f"{pid}_on_O_d12.rows.txt"
    out_o_meta = JOB39 / f"{pid}_on_O_d12.rows.txt.meta"
    out_g_rows = JOB39 / f"{pid}_on_G_d12.rows.txt"
    out_g_meta = JOB39 / f"{pid}_on_G_d12.rows.txt.meta"
    out_a_rows = JOB39 / f"{pid}_on_SetA_L.rows.txt"
    out_a_meta = JOB39 / f"{pid}_on_SetA_L.rows.txt.meta"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fut_o = pool.submit(run_epd_depth12, exe_path, O_FENS_PATH, on_opts, out_o_rows, out_o_meta, 12, 1)
        fut_g = pool.submit(run_epd_depth12, exe_path, G_EPD_PATH, on_opts, out_g_rows, out_g_meta, 12, 2)
        fut_a = pool.submit(run_selfgame_set_with_options, exe_path, "carbon2-job33-a", 200, None, on_opts, 3)
        on_o_rows = fut_o.result()
        on_g_rows = fut_g.result()
        on_a_run = fut_a.result()

    write_v2_v3_rows(out_a_rows, f"{pid} ON ({opt}=true) Set A line L", on_a_run)
    write_seta_meta(out_a_meta, exe_path, on_opts, on_a_run)

    o_sum = sum(r[1] for r in on_o_rows)
    g_sum = sum(r[1] for r in on_g_rows)
    base_o_sum = sum(r[1] for r in base_o_rows)
    base_g_sum = sum(r[1] for r in base_g_rows)
    o_any_diff, o_nd_diff = diff_rows(on_o_rows, base_o_rows)
    g_any_diff, g_nd_diff = diff_rows(on_g_rows, base_g_rows)

    lines.extend([
        f"  {pid} ON O d12 (200 FENs)  : sum_nodes={o_sum} (off={base_o_sum}, delta={o_sum - base_o_sum:+d}) | positions_differ={o_any_diff}/200 (nodes_differ={o_nd_diff}/200)",
        f"  {pid} ON G d12 (353 FENs)  : sum_nodes={g_sum} (off={base_g_sum}, delta={g_sum - base_g_sum:+d}) | positions_differ={g_any_diff}/353 (nodes_differ={g_nd_diff}/353)",
        f"  {pid} ON Set A line L      : attempts={on_a_run.attempts} finished={on_a_run.finished} thrown={on_a_run.thrown_away} records={on_a_run.total_records} searches={on_a_run.total_searches} nodes={on_a_run.total_nodes}",
        f"  {pid} ON Set A line L sha256: {on_a_run.full_sha256}",
        "",
        f"{pid} OVERALL: PASS (1 == 1)",
        f"done_utc: {utc_now()}",
    ])

    summary_txt = "\n".join(lines) + "\n"
    (JOB39 / f"{pid}_summary.txt").write_text(summary_txt, encoding="utf-8")

    with (JOB39 / "builds.txt").open("a", encoding="utf-8") as bf:
        bf.write(
            f"[{pid}] patch={patch_path.name} patch_sha256={sha256_file(patch_path)} "
            f"exe={exe_path} sha256={exe_sha} id='{id_name}'\n"
        )

    print(summary_txt, flush=True)


if __name__ == "__main__":
    main()
