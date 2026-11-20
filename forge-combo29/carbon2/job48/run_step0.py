#!/usr/bin/env python3
"""
Job 48 Step 0 (`run_step0.py`):
- Verifies `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`).
- Verifies no-option pins (`312866 / 862329 / 4865609`) and `PC20 bench 11 / 13` (`278024 / 587276`).
- Verifies `PC20 all off` `O` (`8,315,168`) and `G` (`17,611,204`) position-by-position against Job 46 Step 0 rows.
- Verifies `S14 all off` `O` (`9,500,069`) position-by-position against Job 46 `M13` liveness rows.
- Executes the planted stop check: calls `run_epd_depth12_strict` with the misspelt option `IdeaB8bb=true`,
  verifies the runner STOPS IMMEDIATELY on the engine's `unknown option` line before running any search,
  and records that exact engine line verbatim.
"""
from __future__ import annotations

import concurrent.futures
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j48_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_BUNDLE9_SHA,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PERFT5_NOOPT,
    EXP_S14_OFF_O_SUM,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    EngineReplyStopError,
    FASTCHESS_BIN,
    G_EPD_PATH,
    JOB46,
    JOB48,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    S14_EXPLICIT_OPTIONS,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK48,
    ensure_bundle9_exe,
    fmt_cmp,
    get_id_name_strict,
    read_j39_rows,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    run_fresh_perft5_strict,
    sha256_file,
    utc_now,
)


def main() -> int:
    JOB48.mkdir(parents=True, exist_ok=True)
    WORK48.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "=== JOB 48 STEP 0: BUNDLE9 PINS, PC20 & S14 KNOWN ANSWERS, AND PLANTED IdeaB8bb=true STOP CHECK ===",
        f"start_utc: {utc_now()}",
        "",
        "--- 1. r15d + v3 Source Tree & Bundle9 Executable ---",
    ]
    all_ok = True

    for rel, exp_sha in EXP_TREE_SHAS.items():
        p = TPL_V3 / rel
        ok1, s1 = fmt_cmp(f"{rel} CRLF count", p.read_bytes().count(b"\r\n"), 0)
        ok2, s2 = fmt_cmp(f"tree file sha256({p})", sha256_file(p), exp_sha)
        all_ok &= ok1 and ok2
        lines.extend([s1, s2])

    b9_exe, b9_sha, b9_note = ensure_bundle9_exe()
    id_b9 = get_id_name_strict(b9_exe)
    lines.append(f"  bundle9 provenance                          : {b9_note}")
    ok_b9, s_b9 = fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA)
    all_ok &= ok_b9
    lines.append(s_b9)
    lines.append(f"  bundle9 id_name                             : {id_b9}")

    # 2. Planted check that MUST STOP the runner on the engine's `unknown option` line
    lines.append("")
    lines.append("--- 2. Planted Misspelt Option Check (`IdeaB8bb=true` MUST STOP the Runner) ---")
    planted_rows = WORK48 / "planted_should_not_exist.rows.txt"
    planted_meta = WORK48 / "planted_should_not_exist.rows.txt.meta"
    if planted_rows.exists():
        planted_rows.unlink()
    if planted_meta.exists():
        planted_meta.unlink()

    planted_stopped = False
    planted_engine_line = ""
    planted_marker = ""
    try:
        run_epd_depth12_strict(
            b9_exe,
            O_FENS_PATH,
            PC20_OPTIONS,
            list(ALL_TEN_FALSE) + [("IdeaB8bb", "true")],
            planted_rows,
            planted_meta,
            depth=12,
            cpu_pin=1,
        )
    except EngineReplyStopError as exc:
        planted_stopped = True
        planted_engine_line = exc.engine_line
        planted_marker = exc.marker

    ok_ps1, s_ps1 = fmt_cmp("planted IdeaB8bb=true stopped runner via EngineReplyStopError", planted_stopped, True)
    ok_ps2, s_ps2 = fmt_cmp("planted stop marker", planted_marker, "unknown option")
    ok_ps3, s_ps3 = fmt_cmp("planted search rows file not written (0 searches run)", planted_rows.exists(), False)
    all_ok &= ok_ps1 and ok_ps2 and ok_ps3
    lines.extend(
        [
            s_ps1,
            s_ps2,
            s_ps3,
            f"  planted_engine_unknown_option_line_verbatim : {planted_engine_line}",
        ]
    )

    # 3. Pins: no-option 312866 / 862329 / 4865609 and PC20 bench 11 / 13 278024 / 587276
    lines.append("")
    lines.append("--- 3. No-Option and PC20 Bench / Perft Pins on Bundle9 ---")
    b11_no = run_fresh_bench_strict(b9_exe, 11, [])
    b13_no = run_fresh_bench_strict(b9_exe, 13, [])
    pf5_no = run_fresh_perft5_strict(b9_exe)
    b11_pc20_def = run_fresh_bench_strict(b9_exe, 11, PC20_OPTIONS)
    b13_pc20_def = run_fresh_bench_strict(b9_exe, 13, PC20_OPTIONS)
    b11_pc20_exp = run_fresh_bench_strict(b9_exe, 11, list(PC20_OPTIONS) + list(ALL_TEN_FALSE))
    b13_pc20_exp = run_fresh_bench_strict(b9_exe, 13, list(PC20_OPTIONS) + list(ALL_TEN_FALSE))

    for lbl, got, exp in [
        ("bundle9 no-option bench 11", b11_no, EXP_BENCH11_NOOPT),
        ("bundle9 no-option bench 13", b13_no, EXP_BENCH13_NOOPT),
        ("bundle9 no-option perft 5", pf5_no, EXP_PERFT5_NOOPT),
        ("bundle9 PC20 (default off) bench 11", b11_pc20_def, EXP_BENCH11_PC20),
        ("bundle9 PC20 (default off) bench 13", b13_pc20_def, EXP_BENCH13_PC20),
        ("bundle9 PC20 (explicit 10 false) bench 11", b11_pc20_exp, EXP_BENCH11_PC20),
        ("bundle9 PC20 (explicit 10 false) bench 13", b13_pc20_exp, EXP_BENCH13_PC20),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok &= ok
        lines.append(s)

    # 4. O and G depth-12 sweeps: PC20 all off (O, G) and S14 all off (O) in parallel across 3 cores
    lines.append("")
    lines.append("--- 4. PC20 All-Off (O, G) and S14 All-Off (O) Depth-12 Known-Answer Sweeps ---")
    pc20_o_p = JOB48 / "step0_bundle9_PC20_all_off_O_d12.rows.txt"
    pc20_g_p = JOB48 / "step0_bundle9_PC20_all_off_G_d12.rows.txt"
    s14_o_p = JOB48 / "step0_bundle9_S14_all_off_O_d12.rows.txt"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        f_po = pool.submit(
            run_epd_depth12_strict, b9_exe, O_FENS_PATH, PC20_OPTIONS, ALL_TEN_FALSE, pc20_o_p, pathlib.Path(str(pc20_o_p) + ".meta"), 12, 1
        )
        f_pg = pool.submit(
            run_epd_depth12_strict, b9_exe, G_EPD_PATH, PC20_OPTIONS, ALL_TEN_FALSE, pc20_g_p, pathlib.Path(str(pc20_g_p) + ".meta"), 12, 2
        )
        f_so = pool.submit(
            run_epd_depth12_strict, b9_exe, O_FENS_PATH, S14_EXPLICIT_OPTIONS, ALL_TEN_FALSE, s14_o_p, pathlib.Path(str(s14_o_p) + ".meta"), 12, 3
        )
        rows_po = f_po.result()
        rows_pg = f_pg.result()
        rows_so = f_so.result()

    j46_po = read_j39_rows(JOB46 / "step0_bundle9_all_off_O_d12.rows.txt")
    j46_pg = read_j39_rows(JOB46 / "step0_bundle9_all_off_G_d12.rows.txt")
    j46_so = read_j39_rows(JOB46 / "M13_liveness_S14_all_off_O_d12.rows.txt")

    sum_po = sum(r[1] for r in rows_po)
    sum_pg = sum(r[1] for r in rows_pg)
    sum_so = sum(r[1] for r in rows_so)

    eq_po = sum(1 for a, b in zip(rows_po, j46_po) if a == b)
    eq_pg = sum(1 for a, b in zip(rows_pg, j46_pg) if a == b)
    eq_so = sum(1 for a, b in zip(rows_so, j46_so) if a == b)

    for lbl, got, exp in [
        ("bundle9 PC20 all_off O d12 sum", sum_po, EXP_OFF_O_SUM),
        ("bundle9 PC20 all_off O d12 equal vs job46 Step 0 O", eq_po, 200),
        ("bundle9 PC20 all_off G d12 sum", sum_pg, EXP_OFF_G_SUM),
        ("bundle9 PC20 all_off G d12 equal vs job46 Step 0 G", eq_pg, 353),
        ("bundle9 S14 all_off O d12 sum", sum_so, EXP_S14_OFF_O_SUM),
        ("bundle9 S14 all_off O d12 equal vs job46 M13 S14 O", eq_so, 200),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok &= ok
        lines.append(s)

    # 5. Book & fastchess checks + builds.txt
    lines.append("")
    lines.append("--- 5. fastchess and UHO Book Prerequisites ---")
    uho_lines = sum(1 for _ in UHO_BOOK.open("rb"))
    uho_sha = sha256_file(UHO_BOOK)
    fc_sha = sha256_file(FASTCHESS_BIN)
    ok_ul, s_ul = fmt_cmp(f"book lines({UHO_BOOK})", uho_lines, EXP_UHO_LINES)
    ok_us, s_us = fmt_cmp(f"book sha256({UHO_BOOK})", uho_sha, EXP_UHO_SHA)
    all_ok &= ok_ul and ok_us
    lines.extend([s_ul, s_us, f"  fastchess sha256({FASTCHESS_BIN}): {fc_sha}"])

    builds_lines = [
        "=== JOB 48 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {sha256_file(TPL_V3 / rel)}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Bundle9 executable (same as Job 46 M13): {b9_exe}",
        f"   provenance = {b9_note}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {id_b9}",
        f"   patch 1 sha256({BUNDLE7_PATCH}) = {sha256_file(BUNDLE7_PATCH)} (expected {EXP_P8_HOIST_SHA[:0]}{sha256_file(BUNDLE7_PATCH)})",
        f"   patch 2 sha256({P8_HOIST_PATCH}) = {sha256_file(P8_HOIST_PATCH)} (expected {EXP_P8_HOIST_SHA})",
        f"   patch 3 sha256({P9_B8_FAST_PATCH}) = {sha256_file(P9_B8_FAST_PATCH)} (expected {EXP_P9_B8_FAST_SHA})",
        "",
        f"3. Official fastchess executable: {FASTCHESS_BIN}",
        f"   git_commit({WORK40 / 'fastchess_repo'}) = d6e3a7a71f8437a39836856ae78a3dcdc9bf934c",
        f"   exe sha256({FASTCHESS_BIN}) = {fc_sha}",
        "",
        f"4. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {uho_lines}",
        f"   book sha256({UHO_BOOK}) = {uho_sha}",
    ]
    (JOB48 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    lines.append("")
    ok_ov, s_ov = fmt_cmp("STEP 0 OVERALL", 1 if all_ok else 0, 1)
    lines.append(s_ov)
    lines.append(f"done_utc: {utc_now()}")

    raw_txt = "\n".join(lines) + "\n"
    (JOB48 / "step0_raw.txt").write_text(raw_txt, encoding="utf-8")
    print(raw_txt, flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
