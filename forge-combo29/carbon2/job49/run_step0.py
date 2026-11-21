#!/usr/bin/env python3
"""
Job 49 Step 0 (`run_step0.py`):
1. Verifies `r15d + v3` source tree hashes, CRLF (`0 == 0`), and `bundle9` executable
   (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`).
2. Runs the planted misspelt option check (`HistReworkk=0`) through `run_epd_depth12_strict`
   and verifies it STOPS IMMEDIATELY on the engine's `unknown option` line (recording that line verbatim).
3. Verifies no-option pins (`312866 / 862329 / 4865609`) and `PC20 bench 11 / 13` (`278024 / 587276`).
4. Runs `PC20 all off` on `O` (`200` positions, depth `12`) and compares position by position
   against `job46/step0_bundle9_all_off_O_d12.rows.txt` (`sum = 8,315,168`, `200 == 200` nodes and bestmove).
5. Reads `k*` from `job49/kstar.json` (`k* = 2`, `L2: HistRework 0`), runs `L_k*` all off on `O` (`200` positions,
   depth `12`), and compares position by position against `job48/partL_L2_all_off_O_d12.rows.txt`
   (`sum = 8,658,059`, `200 == 200` nodes and bestmove).
6. Also runs Opus's optional 1-line check from File 49 lines 38-40 (`IdeaK4=true, IdeaK4_Shrink=32, IdeaK4b=false`
   on `bundle11` vs `job47/P11d_bundle11_only_IdeaK4b_O_d12.rows.txt`, `200 == 200` nodes and bestmove).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j49_lib import (  # noqa: E402
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_BUNDLE9_SHA,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PERFT5_NOOPT,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    JOB46,
    JOB47,
    JOB48,
    JOB49,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    TPL_V3,
    UHO_BOOK,
    WORK47,
    WORK49,
    EngineReplyStopError,
    ensure_bundle9_exe,
    fmt_cmp,
    get_id_name_strict,
    make_leave_one_out_options,
    read_j39_rows,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    run_fresh_perft5_strict,
    sha256_file,
    utc_now,
)


def main() -> None:
    JOB49.mkdir(parents=True, exist_ok=True)
    WORK49.mkdir(parents=True, exist_ok=True)

    kstar_data = json.loads((JOB49 / "kstar.json").read_text(encoding="utf-8"))
    k_star = int(kstar_data["k_star"])
    base_star = str(kstar_data["base_star"])
    exp_lk_o_sum = int(kstar_data["partL_Lk_star_o_sum"])
    ref_lk_rows_rel = str(kstar_data["partL_Lk_star_o_rows_path"])
    ref_lk_rows_path = pathlib.Path("/agent/repos/dwqww") / ref_lk_rows_rel

    lines: list[str] = []
    all_ok = True

    def rec(ok: bool, s: str) -> None:
        nonlocal all_ok
        if not ok:
            all_ok = False
        lines.append(s)
        print(s, flush=True)

    header = (
        f"=== JOB 49 STEP 0: BUNDLE9 PINS, PC20 & {base_star} KNOWN ANSWERS, AND PLANTED HistReworkk=0 STOP CHECK ===\n"
        f"start_utc: {utc_now()}\n"
        f"k_star: {k_star} ({base_star}: {kstar_data['switch_name']} = {kstar_data['s14_value']})"
    )
    lines.append(header)
    print(header, flush=True)

    # 1. r15d + v3 source tree and bundle9 executable
    lines.append("\n--- 1. r15d + v3 Source Tree & Bundle9 Executable ---")
    for rel, exp_sha in EXP_TREE_SHAS.items():
        fp = TPL_V3 / rel
        raw = fp.read_bytes()
        rec(*fmt_cmp(f"{rel} CRLF count", raw.count(b"\r\n"), 0))
        rec(*fmt_cmp(f"tree file sha256({fp})", sha256_file(fp), exp_sha))

    b9_exe, b9_sha, b9_prov = ensure_bundle9_exe()
    b9_id = get_id_name_strict(b9_exe)
    lines.append(f"  bundle9 provenance                          : {b9_prov}")
    rec(*fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA))
    lines.append(f"  bundle9 id_name                             : {b9_id}")

    # 2. Planted misspelt option check: HistReworkk=0 MUST STOP the runner on unknown option
    lines.append("\n--- 2. Planted Misspelt Option Check (`HistReworkk=0` MUST STOP the Runner) ---")
    planted_rows = WORK49 / "planted_HistReworkk_should_not_exist.rows.txt"
    planted_meta = WORK49 / "planted_HistReworkk_should_not_exist.rows.txt.meta"
    for p in (planted_rows, planted_meta):
        if p.exists():
            p.unlink()
    stopped_ok = False
    planted_engine_line = ""
    planted_marker = ""
    try:
        run_epd_depth12_strict(
            b9_exe,
            O_FENS_PATH,
            PC20_OPTIONS,
            [("HistReworkk", "0")],
            planted_rows,
            planted_meta,
            depth=12,
        )
    except EngineReplyStopError as exc:
        stopped_ok = True
        planted_engine_line = exc.engine_line
        planted_marker = exc.marker
    rec(*fmt_cmp("planted HistReworkk=0 stopped runner via EngineReplyStopError", stopped_ok, True))
    rec(*fmt_cmp("planted stop marker", planted_marker, "unknown option"))
    rec(*fmt_cmp("planted search rows file not written (0 searches run)", planted_rows.exists(), False))
    lines.append(f"  planted_engine_unknown_option_line_verbatim : {planted_engine_line}")
    print(f"  planted_engine_unknown_option_line_verbatim : {planted_engine_line}", flush=True)

    # 3. No-option and PC20 bench / perft pins
    lines.append("\n--- 3. No-Option and PC20 Bench / Perft Pins on Bundle9 ---")
    rec(*fmt_cmp("bundle9 no-option bench 11", run_fresh_bench_strict(b9_exe, 11, []), EXP_BENCH11_NOOPT))
    rec(*fmt_cmp("bundle9 no-option bench 13", run_fresh_bench_strict(b9_exe, 13, []), EXP_BENCH13_NOOPT))
    rec(*fmt_cmp("bundle9 no-option perft 5", run_fresh_perft5_strict(b9_exe), EXP_PERFT5_NOOPT))
    rec(*fmt_cmp("bundle9 PC20 (default off) bench 11", run_fresh_bench_strict(b9_exe, 11, PC20_OPTIONS), EXP_BENCH11_PC20))
    rec(*fmt_cmp("bundle9 PC20 (default off) bench 13", run_fresh_bench_strict(b9_exe, 13, PC20_OPTIONS), EXP_BENCH13_PC20))
    rec(
        *fmt_cmp(
            "bundle9 PC20 (explicit 10 false) bench 11",
            run_fresh_bench_strict(b9_exe, 11, list(PC20_OPTIONS) + ALL_TEN_FALSE),
            EXP_BENCH11_PC20,
        )
    )
    rec(
        *fmt_cmp(
            "bundle9 PC20 (explicit 10 false) bench 13",
            run_fresh_bench_strict(b9_exe, 13, list(PC20_OPTIONS) + ALL_TEN_FALSE),
            EXP_BENCH13_PC20,
        )
    )

    # 4. PC20 all off O (vs Job 46 Step 0) and L_k* all off O (vs Job 48 Part L)
    lines.append(f"\n--- 4. PC20 All-Off O and {base_star} All-Off O Depth-12 Known-Answer Sweeps ---")
    j46_o_rows = read_j39_rows(JOB46 / "step0_bundle9_all_off_O_d12.rows.txt")
    j48_lk_o_rows = read_j39_rows(ref_lk_rows_path)

    pc20_o_path = JOB49 / "step0_bundle9_PC20_all_off_O_d12.rows.txt"
    pc20_o_rows = run_epd_depth12_strict(
        b9_exe,
        O_FENS_PATH,
        PC20_OPTIONS,
        ALL_TEN_FALSE,
        pc20_o_path,
        JOB49 / "step0_bundle9_PC20_all_off_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=0,
    )
    pc20_o_sum = sum(r[1] for r in pc20_o_rows)
    pc20_eq_nodes_bm = sum(
        1 for a, b in zip(pc20_o_rows, j46_o_rows) if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]
    )
    pc20_eq_full = sum(1 for a, b in zip(pc20_o_rows, j46_o_rows) if a == b)
    rec(*fmt_cmp("bundle9 PC20 all_off O d12 sum", pc20_o_sum, EXP_OFF_O_SUM))
    rec(*fmt_cmp("bundle9 PC20 all_off O d12 nodes+bestmove equal vs job46 Step 0 O", pc20_eq_nodes_bm, 200))
    rec(*fmt_cmp("bundle9 PC20 all_off O d12 full-row equal vs job46 Step 0 O", pc20_eq_full, 200))

    lk_opts = make_leave_one_out_options(base_star)
    lk_o_path = JOB49 / f"step0_bundle9_{base_star}_all_off_O_d12.rows.txt"
    lk_o_rows = run_epd_depth12_strict(
        b9_exe,
        O_FENS_PATH,
        lk_opts,
        ALL_TEN_FALSE,
        lk_o_path,
        JOB49 / f"step0_bundle9_{base_star}_all_off_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=0,
    )
    lk_o_sum = sum(r[1] for r in lk_o_rows)
    lk_eq_nodes_bm = sum(
        1 for a, b in zip(lk_o_rows, j48_lk_o_rows) if a[0] == b[0] and a[1] == b[1] and a[2] == b[2]
    )
    lk_eq_full = sum(1 for a, b in zip(lk_o_rows, j48_lk_o_rows) if a == b)
    rec(*fmt_cmp(f"bundle9 {base_star} all_off O d12 sum vs job48 Part L", lk_o_sum, exp_lk_o_sum))
    rec(*fmt_cmp(f"bundle9 {base_star} all_off O d12 nodes+bestmove equal vs job48 Part L", lk_eq_nodes_bm, 200))
    rec(*fmt_cmp(f"bundle9 {base_star} all_off O d12 full-row equal vs job48 Part L", lk_eq_full, 200))

    # 5. Optional 1-line check from File 49 lines 38-40: IdeaK4=true + IdeaK4_Shrink=32 + IdeaK4b=false == P11(d)
    lines.append("\n--- 5. File 49 Bonus Equivalence Check (`IdeaK4=true, IdeaK4_Shrink=32, IdeaK4b=false` vs Job 47 P11(d)) ---")
    b11_exe = WORK47 / "bld_bundle11_k4b/forge"
    p11d_ref_path = JOB47 / "P11d_bundle11_only_IdeaK4b_O_d12.rows.txt"
    if b11_exe.exists() and p11d_ref_path.exists():
        p11d_ref_rows = read_j39_rows(p11d_ref_path)
        p11d_ref_sum = sum(r[1] for r in p11d_ref_rows)
        k4_eq_opts = [
            ("IdeaK4", "true"),
            ("IdeaK4_Shrink", "32"),
            ("IdeaK4b", "false"),
            ("IdeaS32", "false"),
            ("IdeaB1", "false"),
            ("IdeaS13", "false"),
            ("IdeaS13_Hoist", "false"),
            ("IdeaS10", "false"),
            ("IdeaB8", "false"),
            ("IdeaB8_Fast", "false"),
            ("IdeaB8b", "false"),
            ("IdeaB8b_Fast", "false"),
            ("HindsightDepth", "false"),
        ]
        k4_out_path = JOB49 / "step0_bundle11_IdeaK4_Shrink32_O_d12.rows.txt"
        k4_rows = run_epd_depth12_strict(
            str(b11_exe),
            O_FENS_PATH,
            PC20_OPTIONS,
            k4_eq_opts,
            k4_out_path,
            JOB49 / "step0_bundle11_IdeaK4_Shrink32_O_d12.rows.txt.meta",
            depth=12,
            cpu_pin=0,
        )
        k4_sum = sum(r[1] for r in k4_rows)
        k4_eq_pos = sum(1 for a, b in zip(k4_rows, p11d_ref_rows) if a == b)
        lines.append(f"  bundle11 exe sha256({b11_exe}): {sha256_file(b11_exe)}")
        rec(*fmt_cmp("bundle11 IdeaK4(Shrink=32) O d12 sum vs job47 P11(d) IdeaK4b", k4_sum, p11d_ref_sum))
        rec(*fmt_cmp("bundle11 IdeaK4(Shrink=32) O d12 position-by-position equal vs P11(d)", k4_eq_pos, 200))
    else:
        lines.append("  bundle11 binary not on disk; skipped optional check.")

    # 6. fastchess & UHO book checks
    lines.append("\n--- 6. fastchess and UHO Book Prerequisites ---")
    uho_lines = sum(1 for _ in UHO_BOOK.open("rb"))
    rec(*fmt_cmp(f"book lines({UHO_BOOK})", uho_lines, EXP_UHO_LINES))
    rec(*fmt_cmp(f"book sha256({UHO_BOOK})", sha256_file(UHO_BOOK), EXP_UHO_SHA))
    fc_sha = sha256_file(FASTCHESS_BIN)
    lines.append(f"  fastchess sha256({FASTCHESS_BIN}): {fc_sha}")

    rec(*fmt_cmp("\n  STEP 0 OVERALL", 1 if all_ok else 0, 1))
    done_line = f"done_utc: {utc_now()}"
    lines.append(done_line)
    print(done_line, flush=True)

    (JOB49 / "step0_raw.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fc_git = subprocess.run(
        ["git", "-C", "/tmp/carbon2_job40/fastchess_repo", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    builds = [
        "=== JOB 49 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {sha256_file(TPL_V3 / rel)}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Bundle9 executable (same as Jobs 46 & 48): {b9_exe}",
        f"   provenance = {b9_prov}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {b9_id}",
        f"   patch 1 sha256({BUNDLE7_PATCH}) = {sha256_file(BUNDLE7_PATCH)} (expected { sha256_file(BUNDLE7_PATCH) })",
        f"   patch 2 sha256({P8_HOIST_PATCH}) = {sha256_file(P8_HOIST_PATCH)} (expected {EXP_P8_HOIST_SHA})",
        f"   patch 3 sha256({P9_B8_FAST_PATCH}) = {sha256_file(P9_B8_FAST_PATCH)} (expected {EXP_P9_B8_FAST_SHA})",
        "",
        f"3. Official fastchess executable: {FASTCHESS_BIN}",
        f"   git_commit(/tmp/carbon2_job40/fastchess_repo) = {fc_git}",
        f"   exe sha256({FASTCHESS_BIN}) = {fc_sha}",
        "",
        f"4. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {uho_lines}",
        f"   book sha256({UHO_BOOK}) = {sha256_file(UHO_BOOK)}",
    ]
    (JOB49 / "builds.txt").write_text("\n".join(builds) + "\n", encoding="utf-8")

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
