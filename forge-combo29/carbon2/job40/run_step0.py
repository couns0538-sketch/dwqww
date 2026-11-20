#!/usr/bin/env python3
"""
Job 40 Step 0 (`run_step0.py`):
1. Verifies `r15d + v3` source tree (`src/search.cpp`, `src/uci.cpp`, `src/board.cpp`, `include/forge/board.hpp`
   `sha256` and `0 == 0` CRLF), builds clean Release `r15d + v3` (`/tmp/carbon2_job40/bld_base_v3/forge`),
   and checks `312866 / 862329 / 4865609` (no option) + `PC20 278024 / 587276` (+ Set A & n[1..60] line L).
2. Applies `forge-combo29/carbon2/job39/bundle_grok.patch.txt` (`sha256` verified) to a fresh copy of `r15d + v3`
   (`/tmp/carbon2_job40/src_bundle`), builds `/tmp/carbon2_job40/bld_bundle/forge`, and verifies:
   - All switches OFF: every OFF number (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`,
     `Set A line L`, `n[1..60] line L`, and `O` depth-12 `200 == 200` vs `job39/OFF_O_d12.rows.txt`).
   - All switches ON: `O` depth-12 rows position-by-position (`200 == 200`, `sum = 8,035,170`) vs
     `job39/BUNDLE_ALL_ON_O_d12.rows.txt`, and `Set A line L` (`27,991` records, `111,242,459` nodes,
     `c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce`) vs `job39/BUNDLE_ALL_ON_SetA_L.rows.txt`.
3. Verifies `fastchess` and `UHO_Lichess_4852_v1.epd` (`2,632,036` lines, `7a7f6470...`) and writes `builds.txt`
   and `step0_raw.txt`.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j40_lib import (  # noqa: E402
    ALL_SIX_FALSE,
    ALL_SIX_TRUE,
    BUNDLE_PATCH,
    EXP_BUNDLE_PATCH_SHA,
    EXP_J39_ALL_ON_O_SUM,
    EXP_J39_ALL_ON_SETA_NODES,
    EXP_J39_ALL_ON_SETA_RECORDS,
    EXP_J39_ALL_ON_SETA_SEARCHES,
    EXP_J39_ALL_ON_SETA_SHA,
    EXP_J39_OFF_O_SUM,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    JOB39,
    JOB40,
    O_FENS_PATH,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    get_id_name,
    read_j39_rows,
    run_epd_depth12,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    write_seta_meta,
    write_v2_v3_rows,
)


def main() -> int:
    WORK40.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 40 STEP 0: r15d + v3, Fresh Bundle Build, OFF & Job 39 ALL-ON Known Answers, fastchess & UHO Book ===",
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
    out_lines.append("--- 2. Plain r15d + v3 Clean Release Build (/tmp/carbon2_job40/bld_base_v3/forge) ---")
    base_exe, base_sha, base_cf, base_lf = build_release_v3(TPL_V3, WORK40 / "bld_base_v3")
    ok_base, base_lines = verify_all_off_numbers("plain_r15d_v3", base_exe, None)
    all_ok = all_ok and ok_base
    out_lines.extend(base_lines)

    out_lines.append("")
    out_lines.append("--- 3. Fresh Copy of r15d + v3 + Job 39 bundle_grok.patch.txt (/tmp/carbon2_job40/bld_bundle/forge) ---")
    patch_sha = sha256_file(BUNDLE_PATCH)
    ok_psha, s_psha = fmt_cmp(f"patch sha256({BUNDLE_PATCH})", patch_sha, EXP_BUNDLE_PATCH_SHA)
    all_ok = all_ok and ok_psha
    out_lines.append(s_psha)

    src_bundle = WORK40 / "src_bundle"
    ok_ap, ap_msg = apply_patch_to_fresh_v3(BUNDLE_PATCH, src_bundle)
    all_ok = all_ok and ok_ap
    out_lines.append(f"  apply_against_fresh_r15d_v3                 : {ap_msg}")

    bnd_exe, bnd_sha, bnd_cf, bnd_lf = build_release_v3(src_bundle, WORK40 / "bld_bundle")
    out_lines.append(f"  bundle exe path                             : {bnd_exe}")
    out_lines.append(f"  bundle exe sha256({bnd_exe}) : {bnd_sha}")
    out_lines.append(f"  bundle id name                              : {get_id_name(bnd_exe)}")

    out_lines.append("")
    out_lines.append("--- 3a. Bundle All Switches OFF (Default Off & Explicit All-Six-False) ---")
    ok_boff_def, boff_def_lines = verify_all_off_numbers("bundle_default_off", bnd_exe, None)
    all_ok = all_ok and ok_boff_def
    out_lines.extend(boff_def_lines)

    # Also verify explicit all-six-false bench 11 / 13 under PC20 and O d12 vs Job 39 OFF_O_d12.rows.txt
    j39_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    off_o_rows = run_epd_depth12(
        bnd_exe,
        O_FENS_PATH,
        ALL_SIX_FALSE,
        JOB40 / "step0_bundle_all_off_O_d12.rows.txt",
        JOB40 / "step0_bundle_all_off_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    off_o_sum = sum(r[1] for r in off_o_rows)
    any_diff_off, _ = diff_rows(off_o_rows, j39_off_o)
    ok_os1, s_os1 = fmt_cmp("bundle_all_off O d12 sum vs Job 39 OFF", off_o_sum, EXP_J39_OFF_O_SUM)
    ok_os2, s_os2 = fmt_cmp("bundle_all_off O d12 equal positions vs J39", 200 - any_diff_off, 200)
    all_ok = all_ok and ok_os1 and ok_os2
    out_lines.extend([s_os1, s_os2])

    out_lines.append("")
    out_lines.append("--- 3b. Bundle All Six Switches ON vs Job 39 Known Answers ---")
    j39_on_o = read_j39_rows(JOB39 / "BUNDLE_ALL_ON_O_d12.rows.txt")
    on_o_rows = run_epd_depth12(
        bnd_exe,
        O_FENS_PATH,
        ALL_SIX_TRUE,
        JOB40 / "step0_bundle_all_on_O_d12.rows.txt",
        JOB40 / "step0_bundle_all_on_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    on_o_sum = sum(r[1] for r in on_o_rows)
    any_diff_on, _ = diff_rows(on_o_rows, j39_on_o)
    ok_on1, s_on1 = fmt_cmp("bundle_all_on O d12 sum vs Job 39 ALL_ON", on_o_sum, EXP_J39_ALL_ON_O_SUM)
    ok_on2, s_on2 = fmt_cmp("bundle_all_on O d12 equal positions vs J39", 200 - any_diff_on, 200)
    all_ok = all_ok and ok_on1 and ok_on2
    out_lines.extend([s_on1, s_on2])

    res_seta_on = run_selfgame_set_with_options(bnd_exe, "carbon2-job33-a", 200, None, ALL_SIX_TRUE, cpu_pin=2)
    seta_rows_path = JOB40 / "step0_bundle_all_on_SetA_L.rows.txt"
    seta_meta_path = JOB40 / "step0_bundle_all_on_SetA_L.rows.txt.meta"
    write_v2_v3_rows(seta_rows_path, "Job 40 Step 0 BUNDLE ALL ON Set A line L (built-in eval, PC20)", res_seta_on)
    write_seta_meta(seta_meta_path, bnd_exe, ALL_SIX_TRUE, res_seta_on)

    ok_sa1, s_sa1 = fmt_cmp("bundle_all_on Set A line L records vs J39", res_seta_on.total_records, EXP_J39_ALL_ON_SETA_RECORDS)
    ok_sa2, s_sa2 = fmt_cmp("bundle_all_on Set A line L searches vs J39", res_seta_on.total_searches, EXP_J39_ALL_ON_SETA_SEARCHES)
    ok_sa3, s_sa3 = fmt_cmp("bundle_all_on Set A line L nodes vs J39", res_seta_on.total_nodes, EXP_J39_ALL_ON_SETA_NODES)
    ok_sa4, s_sa4 = fmt_cmp("bundle_all_on Set A line L sha256 vs J39", res_seta_on.full_sha256, EXP_J39_ALL_ON_SETA_SHA)
    all_ok = all_ok and ok_sa1 and ok_sa2 and ok_sa3 and ok_sa4
    out_lines.extend([s_sa1, s_sa2, s_sa3, s_sa4])

    out_lines.append("")
    out_lines.append("--- 4. fastchess & Official Book UHO_Lichess_4852_v1.epd Verification ---")
    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    fc_sha = sha256_file(FASTCHESS_BIN)
    uho_sha = sha256_file(UHO_BOOK)
    with open(UHO_BOOK, "rb") as bf:
        uho_lines = sum(1 for _ in bf)
    ok_bl, s_bl = fmt_cmp(f"book lines({UHO_BOOK})", uho_lines, EXP_UHO_LINES)
    ok_bs, s_bs = fmt_cmp(f"book sha256({UHO_BOOK})", uho_sha, EXP_UHO_SHA)
    all_ok = all_ok and ok_bl and ok_bs
    out_lines.extend(
        [
            f"  fastchess version                           : {fc_ver}",
            f"  fastchess git commit(fastchess_repo)        : {fc_commit}",
            f"  fastchess exe sha256({FASTCHESS_BIN}) : {fc_sha}",
            s_bl,
            s_bs,
        ]
    )

    out_lines.append("")
    ok_all, s_all = fmt_cmp("STEP 0 OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_all)
    out_lines.append(f"done_utc: {utc_now()}")

    (JOB40 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    builds_lines = [
        "=== JOB 40 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {EXP_TREE_SHAS[rel]}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Plain r15d + v3 Release executable: {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name(base_exe)}",
        f"   compile_flags = {base_cf}",
        f"   link_flags    = {base_lf}",
        "",
        f"3. Job 39 bundle patch: {BUNDLE_PATCH}",
        f"   patch sha256({BUNDLE_PATCH}) = {patch_sha}",
        f"   Patched r15d + v3 bundle Release executable: {bnd_exe}",
        f"   exe sha256({bnd_exe}) = {bnd_sha}",
        f"   id_name = {get_id_name(bnd_exe)}",
        f"   compile_flags = {bnd_cf}",
        f"   link_flags    = {bnd_lf}",
        "",
        f"4. Official fastchess executable: {FASTCHESS_BIN}",
        f"   version = {fc_ver}",
        f"   git_commit(/tmp/carbon2_job40/fastchess_repo) = {fc_commit}",
        f"   exe sha256({FASTCHESS_BIN}) = {fc_sha}",
        "",
        f"5. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {uho_lines}",
        f"   book sha256({UHO_BOOK}) = {uho_sha}",
    ]
    (JOB40 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
