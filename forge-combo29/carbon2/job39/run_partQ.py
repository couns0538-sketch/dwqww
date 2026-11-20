#!/usr/bin/env python3
"""
Job 39 Part Q Runner (`run_partQ.py`):
- Q1: Generates `bundle_grok.patch.txt` (`diff -u`, LF) against `r15d + v3` (`TPL_V3`) and applies cleanly to fresh `TPL_V3`.
- Q2: Release build:
  * All switches off -> proves every Step 0 OFF number (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`,
    `Set A line L 26,741 / 107,124,743 / d5b52710...`, `n[1..60] line L 8,449 / 8,482 / 36,688,357 / b6bf7600...`).
  * Each switch ON ALONE -> proves `O` d12 rows equal its single-port `Pk_on_O_d12.rows.txt` position by position (`200/200`).
  * All SIX switches ON -> records `O` d12, `G` d12, and `Set A line L` rows + `.meta` + `all_on_O_sum / all_off_O_sum` ratio.
- Q3: Checking build (`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`) using Job 37's
  `run_partA_checking.py` harness (`CheckingEngine` + `run_v3_with_stderr`) unchanged:
  * First `bench 11 = 312866` and `perft 5 = 4865609` with no option (`stderr_bytes == 0`).
  * `Set C line L` (100 attempts) and `n[1..20] line L` (20 attempts, `net768.fnn3`) with all 6 switches ON (`PC20`),
    recording `.rows.txt`, `.meta`, `stderr_bytes`, and side-by-side Release sha256 match.
"""
from __future__ import annotations

import concurrent.futures
import dataclasses
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True

THIS_DIR = pathlib.Path(__file__).resolve().parent
JOB37_DIR = THIS_DIR.parent / "job37"
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(JOB37_DIR))

from j39_lib import (
    EXP_BENCH11_NOOPT,
    EXP_PERFT5_NOOPT,
    G_EPD_PATH,
    JOB39,
    LINE_L_CMD,
    NET768,
    O_FENS_PATH,
    PC20_OPTIONS,
    RunSettings,
    TPL_V3,
    WORK39,
    apply_patch_to_fresh_v3,
    build_checking_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name,
    pc20_option_lines,
    run_epd_depth12,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    write_seta_meta,
    write_v2_v3_rows,
)
import run_partA_checking as j37_chk

PORTS = [
    ("P1_K4_093", "IdeaK4"),
    ("P2_S32_074", "IdeaS32"),
    ("P3_B1_030", "IdeaB1"),
    ("P4_S13_016", "IdeaS13"),
    ("P5_S10_081", "IdeaS10"),
    ("P6_B8_078", "IdeaB8"),
]

ALL_OFF_OPTS = [(opt, "false") for _, opt in PORTS]
ALL_ON_OPTS = [(opt, "true") for _, opt in PORTS]


def load_saved_rows(path: pathlib.Path) -> list[tuple[int, int, str, str]]:
    rows: list[tuple[int, int, str, str]] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln or ln.startswith("#") or ln.startswith("position\t"):
            continue
        pos_s, nd_s, bm, sc = ln.split("\t")
        rows.append((int(pos_s), int(nd_s), bm, sc))
    return rows


def normalize_thrown_labels(run):
    fixed = []
    for d in run.details:
        if d.end_reason.startswith("err_noscore@"):
            d = dataclasses.replace(d, end_reason=d.end_reason.replace("err_noscore@", "thrown@", 1))
        elif d.end_reason.startswith("err_maxsims@"):
            d = dataclasses.replace(d, end_reason=d.end_reason.replace("err_maxsims@", "maxsims@", 1))
        fixed.append(d)
    return dataclasses.replace(run, details=fixed)


def chk_noopt_pins(exe: str) -> tuple[int, int, int]:
    env = {"UBSAN_OPTIONS": "print_stacktrace=1:report_error_type=1"}
    r1 = subprocess.run([exe], input="uci\nisready\nbench 11\nisready\nquit\n", text=True, capture_output=True, env=env, check=True)
    b11 = -1
    prefix = "info string bench depth 11 nodes "
    for ln in r1.stdout.splitlines():
        if ln.startswith(prefix):
            b11 = int(ln[len(prefix) :].split()[0])
    r2 = subprocess.run([exe], input="uci\nisready\nposition startpos\ngo perft 5\nisready\nquit\n", text=True, capture_output=True, env=env, check=True)
    p5 = -1
    for ln in reversed(r2.stdout.splitlines()):
        if ln.startswith("nodes "):
            p5 = int(ln.split()[1])
            break
    stderr_bytes = len(r1.stderr.encode("utf-8")) + len(r2.stderr.encode("utf-8"))
    return b11, p5, stderr_bytes


def write_chk_meta(
    out_meta: pathlib.Path,
    exe_path: str,
    suite_desc: str,
    opt_lines: list[str],
    run,
    stderr_bytes: int,
    exit_code: int,
) -> None:
    meta = [
        f"exe_path: {exe_path}",
        f"exe_sha256: {sha256_file(exe_path)}",
        f"id_name: {get_id_name(exe_path)}",
        "checking_harness: forge-combo29/carbon2/job37/run_partA_checking.py (CheckingEngine + run_v3_with_stderr used unchanged)",
        f"suite: {suite_desc}",
        f"selfgame_line: {LINE_L_CMD}",
        f"attempts: {run.attempts}",
        f"finished: {run.finished}",
        f"thrown: {run.thrown_away}",
        f"records: {run.total_records}",
        f"searches: {run.total_searches}",
        f"nodes: {run.total_nodes}",
        f"record_text_sha256: {run.full_sha256}",
        f"stderr_bytes: {stderr_bytes}",
        f"exit_code: {exit_code}",
        "options_sent_begin:",
        *[f"  {o}" for o in opt_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    out_meta.write_text("\n".join(meta) + "\n", encoding="utf-8")


def main() -> None:
    all_ok = True
    out: list[str] = [
        "=== JOB 39 PART Q: THE SIX-PORT BUNDLE (`bundle_grok.patch.txt`) ===",
        f"start_utc: {utc_now()}",
    ]

    # --- Q1: Generate bundle_grok.patch.txt and apply cleanly to fresh TPL_V3 ---
    bundle_patch = JOB39 / "bundle_grok.patch.txt"
    generate_diff_u_patch(TPL_V3, WORK39 / "edit_BUNDLE", bundle_patch)
    patch_sha = sha256_file(bundle_patch)
    patch_lines = len(bundle_patch.read_text(encoding="utf-8").splitlines())

    src_bundle = WORK39 / "src_BUNDLE"
    ok_apply, apply_msg = apply_patch_to_fresh_v3(bundle_patch, src_bundle)
    all_ok = all_ok and ok_apply
    out.append(f"Q1 bundle_patch: {bundle_patch.name} | lines={patch_lines} | sha256={patch_sha}")
    out.append(f"  apply_against_r15d_v3                       : {apply_msg}")
    if not ok_apply:
        raise RuntimeError(apply_msg)

    # Build Release and Checking executables
    rel_exe, rel_sha, rel_cflags, rel_lflags = build_release_v3(src_bundle, WORK39 / "bld_BUNDLE_rel")
    chk_exe, chk_sha, chk_cflags, chk_lflags = build_checking_v3(src_bundle, WORK39 / "bld_BUNDLE_chk")
    rel_id = get_id_name(rel_exe)
    chk_id = get_id_name(chk_exe)

    out.append(f"  rel_exe: {rel_exe} | sha256={rel_sha} | {rel_id}")
    out.append(f"  chk_exe: {chk_exe} | sha256={chk_sha} | {chk_id}")

    with (JOB39 / "builds.txt").open("a", encoding="utf-8") as bf:
        bf.write(f"\n[BUNDLE_rel] patch={bundle_patch.name} ({patch_sha})\n")
        bf.write(f"  exe={rel_exe} | sha256={rel_sha} | {rel_id}\n")
        bf.write(f"  cflags={rel_cflags}\n")
        bf.write(f"  lflags={rel_lflags}\n")
        bf.write(f"\n[BUNDLE_chk] patch={bundle_patch.name} ({patch_sha})\n")
        bf.write(f"  exe={chk_exe} | sha256={chk_sha} | {chk_id}\n")
        bf.write(f"  cflags={chk_cflags}\n")
        bf.write(f"  lflags={chk_lflags}\n")

    # --- Q2a: All switches OFF -> every OFF number + O d12 off match ---
    out.append("")
    out.append("--- Q2a. All Six Switches OFF: Every Step 0 OFF Number ---")
    ok_off, off_lines = verify_all_off_numbers("BUNDLE_all_off", rel_exe, ALL_OFF_OPTS)
    all_ok = all_ok and ok_off
    out.extend(off_lines)

    off_o_ref = load_saved_rows(JOB39 / "OFF_O_d12.rows.txt")
    off_g_ref = load_saved_rows(JOB39 / "OFF_G_d12.rows.txt")
    off_o_sum = sum(r[1] for r in off_o_ref)
    off_g_sum = sum(r[1] for r in off_g_ref)

    bundle_off_o = run_epd_depth12(
        rel_exe,
        O_FENS_PATH,
        ALL_OFF_OPTS,
        WORK39 / "BUNDLE_off_O_d12.rows.txt",
        WORK39 / "BUNDLE_off_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=0,
    )
    bo_diff, _ = diff_rows(bundle_off_o, off_o_ref)
    ok_bo_sum, s_bo_sum = fmt_cmp("BUNDLE_all_off O d12 sum vs Step0 OFF", sum(r[1] for r in bundle_off_o), off_o_sum)
    ok_bo_dif, s_bo_dif = fmt_cmp("BUNDLE_all_off O d12 differing positions", bo_diff, 0)
    all_ok = all_ok and ok_bo_sum and ok_bo_dif
    out.extend([s_bo_sum, s_bo_dif])

    # --- Q2b: Each switch ON ALONE -> 200/200 position-by-position equality with P-c ---
    out.append("")
    out.append("--- Q2b. Each Switch ON Alone vs Single Port P-c on O Set (200 FENs, Depth 12) ---")
    alone_results: dict[str, list[tuple[int, int, str, str]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futs = {}
        for idx, (pid, opt) in enumerate(PORTS):
            opts = [(o, "true" if o == opt else "false") for _, o in PORTS]
            futs[
                pool.submit(
                    run_epd_depth12,
                    rel_exe,
                    O_FENS_PATH,
                    opts,
                    JOB39 / f"BUNDLE_ONLY_{opt}_O_d12.rows.txt",
                    JOB39 / f"BUNDLE_ONLY_{opt}_O_d12.rows.txt.meta",
                    12,
                    idx % 4,
                )
            ] = (pid, opt)
        for fut in concurrent.futures.as_completed(futs):
            pid, opt = futs[fut]
            alone_results[pid] = fut.result()

    for pid, opt in PORTS:
        single_rows = load_saved_rows(JOB39 / f"{pid}_on_O_d12.rows.txt")
        bund_rows = alone_results[pid]
        any_diff, nd_diff = diff_rows(bund_rows, single_rows)
        s_sum = sum(r[1] for r in single_rows)
        b_sum = sum(r[1] for r in bund_rows)
        ok_eq, s_eq = fmt_cmp(f"BUNDLE only {opt} O d12 equal positions", 200 - any_diff, 200)
        ok_sm, s_sm = fmt_cmp(f"BUNDLE only {opt} O d12 sum vs {pid}", b_sum, s_sum)
        all_ok = all_ok and ok_eq and ok_sm
        out.extend([s_eq, s_sm])

    # --- Q2c: All SIX switches ON together (O d12, G d12, Set A line L) ---
    out.append("")
    out.append("--- Q2c. All Six Switches ON Together (PC20, Built-in Evaluation) ---")
    all_on_o_rows = JOB39 / "BUNDLE_ALL_ON_O_d12.rows.txt"
    all_on_o_meta = JOB39 / "BUNDLE_ALL_ON_O_d12.rows.txt.meta"
    all_on_g_rows = JOB39 / "BUNDLE_ALL_ON_G_d12.rows.txt"
    all_on_g_meta = JOB39 / "BUNDLE_ALL_ON_G_d12.rows.txt.meta"
    all_on_a_rows = JOB39 / "BUNDLE_ALL_ON_SetA_L.rows.txt"
    all_on_a_meta = JOB39 / "BUNDLE_ALL_ON_SetA_L.rows.txt.meta"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fut_o = pool.submit(run_epd_depth12, rel_exe, O_FENS_PATH, ALL_ON_OPTS, all_on_o_rows, all_on_o_meta, 12, 1)
        fut_g = pool.submit(run_epd_depth12, rel_exe, G_EPD_PATH, ALL_ON_OPTS, all_on_g_rows, all_on_g_meta, 12, 2)
        fut_a = pool.submit(run_selfgame_set_with_options, rel_exe, "carbon2-job33-a", 200, None, ALL_ON_OPTS, 3)
        on_o = fut_o.result()
        on_g = fut_g.result()
        on_a = fut_a.result()

    write_v2_v3_rows(all_on_a_rows, "BUNDLE ALL SIX ON Set A line L", on_a)
    write_seta_meta(all_on_a_meta, rel_exe, ALL_ON_OPTS, on_a)

    all_on_o_sum = sum(r[1] for r in on_o)
    all_on_g_sum = sum(r[1] for r in on_g)
    o_any_diff, o_nd_diff = diff_rows(on_o, off_o_ref)
    g_any_diff, g_nd_diff = diff_rows(on_g, off_g_ref)
    ratio_o = all_on_o_sum / off_o_sum

    out.append(
        f"  BUNDLE ALL ON O d12 (200 FENs)  : sum_nodes={all_on_o_sum} (off={off_o_sum}, delta={all_on_o_sum - off_o_sum:+d}, "
        f"ratio={ratio_o:.6f}) | positions_differ={o_any_diff}/200 (nodes_differ={o_nd_diff}/200)"
    )
    out.append(
        f"  BUNDLE ALL ON G d12 (353 FENs)  : sum_nodes={all_on_g_sum} (off={off_g_sum}, delta={all_on_g_sum - off_g_sum:+d}, "
        f"ratio={all_on_g_sum / off_g_sum:.6f}) | positions_differ={g_any_diff}/353 (nodes_differ={g_nd_diff}/353)"
    )
    out.append(
        f"  BUNDLE ALL ON Set A line L      : attempts={on_a.attempts} finished={on_a.finished} thrown={on_a.thrown_away} "
        f"records={on_a.total_records} searches={on_a.total_searches} nodes={on_a.total_nodes}"
    )
    out.append(f"  BUNDLE ALL ON Set A line L sha256: {on_a.full_sha256}")

    # --- Q3: Checking build (ASan + UBSan + _GLIBCXX_ASSERTIONS) with Job 37 harness unchanged ---
    out.append("")
    out.append("--- Q3. Checking Build (`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`) ---")
    out.append("  Harness: forge-combo29/carbon2/job37/run_partA_checking.py (`CheckingEngine` + `run_v3_with_stderr` used unchanged; no new control needed).")

    chk_b11, chk_p5, chk_pin_stderr = chk_noopt_pins(chk_exe)
    ok_cb11, s_cb11 = fmt_cmp("BUNDLE_chk no-option bench 11", chk_b11, EXP_BENCH11_NOOPT)
    ok_cp5, s_cp5 = fmt_cmp("BUNDLE_chk no-option perft 5", chk_p5, EXP_PERFT5_NOOPT)
    ok_cpe, s_cpe = fmt_cmp("BUNDLE_chk no-option pins stderr_bytes", chk_pin_stderr, 0)
    all_ok = all_ok and ok_cb11 and ok_cp5 and ok_cpe
    out.extend([s_cb11, s_cp5, s_cpe])

    # Inject ALL_ON_OPTS into j37_chk.PC20_OPTIONS so CheckingEngine sends PC20 + all 6 Idea switches = true
    orig_pc20 = list(j37_chk.PC20_OPTIONS)
    j37_chk.PC20_OPTIONS = orig_pc20 + ALL_ON_OPTS
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            fut_chk_c = pool.submit(j37_chk.run_v3_with_stderr, chk_exe, "carbon2-job33-c", 100, RunSettings(), 0, LINE_L_CMD)
            fut_chk_n = pool.submit(j37_chk.run_v3_with_stderr, chk_exe, "carbon2-job33-n", 20, RunSettings(net_path=NET768), 1, LINE_L_CMD)
            fut_rel_c = pool.submit(run_selfgame_set_with_options, rel_exe, "carbon2-job33-c", 100, None, ALL_ON_OPTS, 2)
            fut_rel_n = pool.submit(run_selfgame_set_with_options, rel_exe, "carbon2-job33-n", 20, NET768, ALL_ON_OPTS, 3)

            chk_c_raw, err_c, rc_c = fut_chk_c.result()
            chk_n_raw, err_n, rc_n = fut_chk_n.result()
            rel_c = fut_rel_c.result()
            rel_n = fut_rel_n.result()
    finally:
        j37_chk.PC20_OPTIONS = orig_pc20

    chk_c = normalize_thrown_labels(chk_c_raw)
    chk_n = normalize_thrown_labels(chk_n_raw)

    write_v2_v3_rows(JOB39 / "BUNDLE_CHK_ALL_ON_SetC_L.rows.txt", "BUNDLE CHK ALL ON Set C line L", chk_c)
    write_chk_meta(
        JOB39 / "BUNDLE_CHK_ALL_ON_SetC_L.rows.txt.meta",
        chk_exe,
        "Set C (seed='carbon2-job33-c', attempts=100, built-in evaluation, all 6 switches true)",
        pc20_option_lines(ALL_ON_OPTS),
        chk_c,
        len(err_c),
        rc_c,
    )

    n_opt_lines = pc20_option_lines(ALL_ON_OPTS + [("NNUEArchFile", NET768), ("NNUEArch", "true")])
    write_v2_v3_rows(JOB39 / "BUNDLE_CHK_ALL_ON_n20_L.rows.txt", "BUNDLE CHK ALL ON n[1..20] line L", chk_n)
    write_chk_meta(
        JOB39 / "BUNDLE_CHK_ALL_ON_n20_L.rows.txt.meta",
        chk_exe,
        "Set n[1..20] (seed='carbon2-job33-n', attempts=20, net768.fnn3, all 6 switches true)",
        n_opt_lines,
        chk_n,
        len(err_n),
        rc_n,
    )

    out.append(
        f"  [Set C line L, ALL ON] attempts={chk_c.attempts} finished={chk_c.finished} thrown={chk_c.thrown_away} "
        f"records={chk_c.total_records} searches={chk_c.total_searches} nodes={chk_c.total_nodes} sha256={chk_c.full_sha256}"
    )
    for lbl, got, exp in [
        ("BUNDLE_chk ALL_ON Set C stderr_bytes", len(err_c), 0),
        ("BUNDLE_chk ALL_ON Set C exit_code", rc_c, 0),
        ("BUNDLE_chk vs rel ALL_ON Set C records", chk_c.total_records, rel_c.total_records),
        ("BUNDLE_chk vs rel ALL_ON Set C nodes", chk_c.total_nodes, rel_c.total_nodes),
        ("BUNDLE_chk vs rel ALL_ON Set C sha256", chk_c.full_sha256, rel_c.full_sha256),
    ]:
        ok_i, s_i = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok_i
        out.append(s_i)

    out.append(
        f"  [n[1..20] line L, ALL ON] attempts={chk_n.attempts} finished={chk_n.finished} thrown={chk_n.thrown_away} "
        f"records={chk_n.total_records} searches={chk_n.total_searches} nodes={chk_n.total_nodes} sha256={chk_n.full_sha256}"
    )
    for lbl, got, exp in [
        ("BUNDLE_chk ALL_ON n[1..20] stderr_bytes", len(err_n), 0),
        ("BUNDLE_chk ALL_ON n[1..20] exit_code", rc_n, 0),
        ("BUNDLE_chk vs rel ALL_ON n[1..20] records", chk_n.total_records, rel_n.total_records),
        ("BUNDLE_chk vs rel ALL_ON n[1..20] nodes", chk_n.total_nodes, rel_n.total_nodes),
        ("BUNDLE_chk vs rel ALL_ON n[1..20] sha256", chk_n.full_sha256, rel_n.full_sha256),
    ]:
        ok_i, s_i = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok_i
        out.append(s_i)

    out.append("")
    out.append(f"PART Q OVERALL: {'PASS (1 == 1)' if all_ok else 'FAIL (0 != 1)'}")
    out.append(f"done_utc: {utc_now()}")

    summary_txt = "\n".join(out) + "\n"
    (JOB39 / "partQ_summary.txt").write_text(summary_txt, encoding="utf-8")
    print(summary_txt)
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
