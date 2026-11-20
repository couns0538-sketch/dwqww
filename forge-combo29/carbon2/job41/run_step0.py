#!/usr/bin/env python3
"""
Job 41 Step 0 (`run_step0.py`):
1. Verifies `r15d + v3` source tree (`src/search.cpp`, `src/uci.cpp`, `src/board.cpp`, `include/forge/board.hpp`
   `sha256` and `0 == 0` CRLF); builds/verifies plain `r15d + v3` (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`,
   `Set A line L 26,741 / 107,124,743 / d5b52710...`, `n[1..60] line L`), and checks `HindsightDepth` in `uci`.
2. Applies `forge-combo29/carbon2/job39/bundle_grok.patch.txt` on a fresh copy (`/tmp/carbon2_job41/src_bundle6`),
   builds `/tmp/carbon2_job41/bld_bundle6/forge`, checks `HindsightDepth` in `uci`, proves all switches OFF =
   every OFF number, and proves `IdeaB8` alone ON = Job 39 `P6_B8_078_on_O_d12.rows.txt` on `200 == 200` positions.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j41_lib import (  # noqa: E402
    BUNDLE6_PATCH,
    EXP_BUNDLE6_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    GROK_028_PATCH,
    EXP_GROK_028_SHA,
    JOB39,
    JOB41,
    O_FENS_PATH,
    SIX_OLD_SWITCHES,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK41,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    get_id_name,
    read_j39_rows,
    run_epd_depth12,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    verify_uci_option_check,
)


def main() -> int:
    WORK41.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 41 STEP 0: r15d + v3, HindsightDepth UCI Check, Fresh bundle_grok.patch.txt OFF & IdeaB8 O Identity ===",
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
    out_lines.append("--- 2. Plain r15d + v3 Release Build (/tmp/carbon2_job41/bld_base_v3/forge) ---")
    base_exe, base_sha, base_cf, base_lf = build_release_v3(TPL_V3, WORK41 / "bld_base_v3")
    ok_hd0, hd0_lines = verify_uci_option_check(base_exe, "HindsightDepth")
    all_ok = all_ok and ok_hd0
    out_lines.extend(hd0_lines)

    ok_base, base_lines = verify_all_off_numbers("plain_r15d_v3", base_exe, None)
    all_ok = all_ok and ok_base
    out_lines.extend(base_lines)

    out_lines.append("")
    out_lines.append("--- 3. Fresh Copy + Job 39 bundle_grok.patch.txt (/tmp/carbon2_job41/bld_bundle6/forge) ---")
    b6_patch_sha = sha256_file(BUNDLE6_PATCH)
    ok_ps, s_ps = fmt_cmp(f"patch sha256({BUNDLE6_PATCH})", b6_patch_sha, EXP_BUNDLE6_SHA)
    all_ok = all_ok and ok_ps
    out_lines.append(s_ps)

    src_b6 = WORK41 / "src_bundle6"
    ok_ap, ap_msg = apply_patch_to_fresh_v3(BUNDLE6_PATCH, src_b6)
    all_ok = all_ok and ok_ap
    out_lines.append(f"  apply_against_fresh_r15d_v3                 : {ap_msg}")

    b6_exe, b6_sha, b6_cf, b6_lf = build_release_v3(src_b6, WORK41 / "bld_bundle6")
    out_lines.append(f"  bundle6 exe path                            : {b6_exe}")
    out_lines.append(f"  bundle6 exe sha256({b6_exe}) : {b6_sha}")
    out_lines.append(f"  bundle6 id name                             : {get_id_name(b6_exe)}")

    ok_hd6, hd6_lines = verify_uci_option_check(b6_exe, "HindsightDepth")
    all_ok = all_ok and ok_hd6
    out_lines.extend(hd6_lines)

    ok_b6_off, b6_off_lines = verify_all_off_numbers("bundle6_all_off", b6_exe, None)
    all_ok = all_ok and ok_b6_off
    out_lines.extend(b6_off_lines)

    out_lines.append("")
    out_lines.append("--- 4. IdeaB8 Alone ON vs Job 39 P6_B8_078_on_O_d12.rows.txt ---")
    b8_only_opts = [(opt, "true" if opt == "IdeaB8" else "false") for _, opt, _, _ in SIX_OLD_SWITCHES]
    b8_rows = run_epd_depth12(
        b6_exe,
        O_FENS_PATH,
        b8_only_opts,
        JOB41 / "step0_bundle6_only_IdeaB8_O_d12.rows.txt",
        JOB41 / "step0_bundle6_only_IdeaB8_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    j39_p6_rows = read_j39_rows(JOB39 / "P6_B8_078_on_O_d12.rows.txt")
    any_diff_b8, _ = diff_rows(b8_rows, j39_p6_rows)
    b8_sum = sum(r[1] for r in b8_rows)
    ok_b8_1, s_b8_1 = fmt_cmp("bundle6 IdeaB8 O d12 sum vs J39 P6", b8_sum, 8262696)
    ok_b8_2, s_b8_2 = fmt_cmp("bundle6 IdeaB8 O d12 equal positions vs P6", 200 - any_diff_b8, 200)
    all_ok = all_ok and ok_b8_1 and ok_b8_2
    out_lines.extend([s_b8_1, s_b8_2])

    out_lines.append("")
    out_lines.append("--- 5. Seat 028 Source Patch, fastchess & UHO Book Verification ---")
    s028_sha = sha256_file(GROK_028_PATCH)
    s028_lines = len(GROK_028_PATCH.read_text(encoding="utf-8").splitlines())
    ok_028_l, s_028_l = fmt_cmp(f"patch lines({GROK_028_PATCH})", s028_lines, 361)
    ok_028_s, s_028_s = fmt_cmp(f"patch sha256({GROK_028_PATCH})", s028_sha, EXP_GROK_028_SHA)
    all_ok = all_ok and ok_028_l and ok_028_s
    out_lines.extend([s_028_l, s_028_s])

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

    (JOB41 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    builds_lines = [
        "=== JOB 41 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {EXP_TREE_SHAS[rel]}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Step 0 plain r15d + v3 Release executable: {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name(base_exe)}",
        f"   compile_flags = {base_cf}",
        f"   link_flags    = {base_lf}",
        "",
        f"3. Step 0 fresh 6-switch bundle executable (patch {BUNDLE6_PATCH}, sha256 = {b6_patch_sha}):",
        f"   exe path = {b6_exe}",
        f"   exe sha256({b6_exe}) = {b6_sha}",
        f"   id_name = {get_id_name(b6_exe)}",
        f"   compile_flags = {b6_cf}",
        f"   link_flags    = {b6_lf}",
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
    (JOB41 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
