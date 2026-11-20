#!/usr/bin/env python3
"""
Job 42 Step 0 (`run_step0.py`):
1. `r15d + v3` source tree verification (`4` file hashes + `0 == 0` CRLF), plain Release build,
   all OFF numbers (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`, `Set A line L 26,741 / d5b52710...`,
   `n[1..60] line L b6bf7600...`).
2. Fresh copy + Job 41's `bundle_grok7.patch.txt`:
   - All 7 switches off = every OFF number
   - `IdeaB8b` alone on = Job 41 `P7_bundle7_only_B8b_O_d12.rows.txt` position by position (`200 == 200`, `8483711 == 8483711`)
3. Known answer without PC20 (`Threads 1`, `Hash 16`, `OwnBook false`, no `Idea*` switch on):
   - `HindsightDepth = false` -> `bench 13 = 862329`
   - `HindsightDepth = true`  -> `bench 13 = 840387`
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j42_lib import (  # noqa: E402
    ALL_SEVEN_FALSE,
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    JOB41,
    JOB42,
    O_FENS_PATH,
    SEVEN_SWITCH_NAMES,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK42,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    get_id_name,
    read_j39_rows,
    run_epd_depth12,
    run_fresh_bench,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    verify_uci_option_check,
)


def check_nopc20_hindsight_bench13(label: str, exe_path: str, extra_false: list[tuple[str, str]]) -> tuple[bool, list[str]]:
    base_opts = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        "setoption name OwnBook value false",
        *[f"setoption name {k} value {v}" for k, v in extra_false],
    ]
    b13_false = run_fresh_bench(exe_path, 13, base_opts + ["setoption name HindsightDepth value false"])
    b13_true = run_fresh_bench(exe_path, 13, base_opts + ["setoption name HindsightDepth value true"])
    ok1, s1 = fmt_cmp(f"{label} no-PC20 HindsightDepth=false bench 13", b13_false, EXP_NOPC20_HD_FALSE_BENCH13)
    ok2, s2 = fmt_cmp(f"{label} no-PC20 HindsightDepth=true bench 13", b13_true, EXP_NOPC20_HD_TRUE_BENCH13)
    return (ok1 and ok2), [s1, s2]


def main() -> int:
    WORK42.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 42 STEP 0: r15d + v3, Fresh bundle_grok7.patch.txt OFF & IdeaB8b O Identity, and Non-PC20 HindsightDepth bench 13 ===",
        f"start_utc: {utc_now()}",
        "",
        "--- 1. r15d + v3 Source Tree Verification (/tmp/carbon2_job36/tpl_r15d_v3, LF line endings) ---",
    ]
    all_ok = True

    for rel, exp_sha in EXP_TREE_SHAS.items():
        p = TPL_V3 / rel
        raw = p.read_bytes()
        crlf = raw.count(b"\r\n")
        sha = sha256_file(p)
        ok1, s1 = fmt_cmp(f"{rel} CRLF count", crlf, 0)
        ok2, s2 = fmt_cmp(f"tree file sha256({p})", sha, exp_sha)
        all_ok = all_ok and ok1 and ok2
        out_lines.extend([s1, s2])

    out_lines.append("")
    out_lines.append("--- 2. Plain r15d + v3 Release Build (/tmp/carbon2_job42/bld_base_v3/forge) ---")
    base_exe, base_sha, base_cf, base_lf = build_release_v3(TPL_V3, WORK42 / "bld_base_v3")
    ok_hd0, hd0_lines = verify_uci_option_check(base_exe, "HindsightDepth")
    ok_b0, b0_lines = verify_all_off_numbers("plain_r15d_v3", base_exe, None)
    ok_k0, k0_lines = check_nopc20_hindsight_bench13("plain_r15d_v3", base_exe, [])
    all_ok = all_ok and ok_hd0 and ok_b0 and ok_k0
    out_lines.extend(hd0_lines + b0_lines + k0_lines)

    out_lines.append("")
    out_lines.append("--- 3. Fresh Copy + Job 41 bundle_grok7.patch.txt (/tmp/carbon2_job42/bld_bundle7/forge) ---")
    b7_patch_sha = sha256_file(BUNDLE7_PATCH)
    ok_ps, s_ps = fmt_cmp(f"patch sha256({BUNDLE7_PATCH})", b7_patch_sha, EXP_BUNDLE7_SHA)
    all_ok = all_ok and ok_ps
    out_lines.append(s_ps)

    src_b7 = WORK42 / "src_bundle7"
    ok_ap, ap_msg = apply_patch_to_fresh_v3(BUNDLE7_PATCH, src_b7)
    all_ok = all_ok and ok_ap
    out_lines.append(f"  apply_against_fresh_r15d_v3                 : {ap_msg}")

    b7_exe, b7_sha, b7_cf, b7_lf = build_release_v3(src_b7, WORK42 / "bld_bundle7")
    out_lines.append(f"  bundle7 exe path                            : {b7_exe}")
    out_lines.append(f"  bundle7 exe sha256({b7_exe}) : {b7_sha}")
    out_lines.append(f"  bundle7 id name                             : {get_id_name(b7_exe)}")

    for uopt in ["HindsightDepth", "IdeaB8b", "IdeaS13"]:
        ok_u, u_lines = verify_uci_option_check(b7_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    ok_b7_def, b7_def_lines = verify_all_off_numbers("bundle7_default_off", b7_exe, None)
    ok_b7_exp, b7_exp_lines = verify_all_off_numbers("bundle7_explicit_7_false", b7_exe, ALL_SEVEN_FALSE)
    ok_k7, k7_lines = check_nopc20_hindsight_bench13("bundle7", b7_exe, ALL_SEVEN_FALSE)
    all_ok = all_ok and ok_b7_def and ok_b7_exp and ok_k7
    out_lines.extend(b7_def_lines + b7_exp_lines + k7_lines)

    out_lines.append("")
    out_lines.append("--- 4. bundle_grok7 IdeaB8b Alone ON vs Job 41 P7_bundle7_only_B8b_O_d12.rows.txt ---")
    b8b_only = [(o, "true" if o == "IdeaB8b" else "false") for o in SEVEN_SWITCH_NAMES]
    b8b_rows = run_epd_depth12(
        b7_exe,
        O_FENS_PATH,
        b8b_only,
        JOB42 / "step0_bundle7_only_IdeaB8b_O_d12.rows.txt",
        JOB42 / "step0_bundle7_only_IdeaB8b_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    j41_b8b_rows = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt")
    any_diff_b8b, _ = diff_rows(b8b_rows, j41_b8b_rows)
    b8b_sum = sum(r[1] for r in b8b_rows)
    ok_b8b_1, s_b8b_1 = fmt_cmp("bundle7 IdeaB8b O d12 sum vs J41 P7", b8b_sum, EXP_B8B_O_SUM)
    ok_b8b_2, s_b8b_2 = fmt_cmp("bundle7 IdeaB8b O d12 equal positions vs J41 P7", 200 - any_diff_b8b, 200)
    all_ok = all_ok and ok_b8b_1 and ok_b8b_2
    out_lines.extend([s_b8b_1, s_b8b_2])

    out_lines.append("")
    out_lines.append("--- 5. fastchess, UHO Book & M0 Control Prerequisites ---")
    uho_sha = sha256_file(UHO_BOOK)
    with open(UHO_BOOK, "rb") as bf:
        uho_lines = sum(1 for _ in bf)
    ok_ul, s_ul = fmt_cmp(f"book lines({UHO_BOOK})", uho_lines, EXP_UHO_LINES)
    ok_us, s_us = fmt_cmp(f"book sha256({UHO_BOOK})", uho_sha, EXP_UHO_SHA)
    all_ok = all_ok and ok_ul and ok_us
    out_lines.extend([s_ul, s_us])

    out_lines.append("")
    ok_ov, s_ov = fmt_cmp("STEP 0 OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")

    (JOB42 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    builds_lines = [
        "=== JOB 42 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {EXP_TREE_SHAS[rel]}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Step 0 plain r15d + v3 Release executable: {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name(base_exe)}",
        f"   compile_flags = {base_cf}",
        f"   link_flags    = {base_lf}",
        "",
        f"3. Step 0 fresh 7-switch bundle_grok7 executable (patch {BUNDLE7_PATCH}, sha256 = {b7_patch_sha}):",
        f"   exe path = {b7_exe}",
        f"   exe sha256({b7_exe}) = {b7_sha}",
        f"   id_name = {get_id_name(b7_exe)}",
        f"   compile_flags = {b7_cf}",
        f"   link_flags    = {b7_lf}",
        "",
        f"4. Official fastchess executable: {FASTCHESS_BIN}",
        f"   version = {fc_ver}",
        f"   git_commit(/tmp/carbon2_job40/fastchess_repo) = {fc_commit}",
        f"   exe sha256({FASTCHESS_BIN}) = {sha256_file(FASTCHESS_BIN)}",
        "",
        f"5. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {uho_lines}",
        f"   book sha256({UHO_BOOK}) = {uho_sha}",
    ]
    (JOB42 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
