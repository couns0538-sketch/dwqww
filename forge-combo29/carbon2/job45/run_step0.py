#!/usr/bin/env python3
"""
Job 45 Step 0 (`run_step0.py`):
1. `r15d + v3` source tree verification (`4` file hashes + `0 == 0` CRLF), plain Release build,
   every OFF number (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`, `Set A line L 26,741 / d5b52710...`,
   `n[1..60] line L b6bf7600...`), and non-`PC20` `HindsightDepth` `bench 13` (`862329` false, `840387` true).
2. Fresh `bundle8` build (`r15d + v3 + job 41's bundle_grok7.patch.txt + job 42's P8_S13_hoist.patch.txt`):
   - All 8 switches off = every OFF number + `O` (`8,315,168 == 8,315,168`, `200 == 200`) + `G` (`17,611,204 == 17,611,204`, `353 == 353`).
   - `IdeaB8b` alone = Job 41 `P7` rows position by position on `O` (`8,483,711 == 8,483,711`, `200 == 200`) and `G` (`17,366,116 == 17,366,116`, `353 == 353`).
   - `HindsightDepth=true` non-`PC20` `bench 13` = `840387 == 840387`, `862329 == 862329` with `HindsightDepth=false`.
   - `IdeaS13 + IdeaS13_Hoist` = `O 9,069,588` (`200 == 200`), `G 18,700,461` (`353 == 353`).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j45_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    BUNDLE7_PATCH,
    EIGHT_SWITCH_NAMES,
    EXP_B8B_G_SUM,
    EXP_B8B_O_SUM,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_PC_S13_HOIST_G_FIRST5,
    EXP_PC_S13_HOIST_G_SUM,
    EXP_PC_S13_HOIST_O_FIRST5,
    EXP_PC_S13_HOIST_O_SUM,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    JOB39,
    JOB41,
    JOB43,
    JOB45,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK45,
    apply_bundle8_to_fresh_v3,
    build_release_v3,
    diff_breakdown_with_samples,
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
    WORK45.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 45 STEP 0: r15d + v3 and Bundle8 (r15d + v3 + job41/bundle_grok7.patch.txt + job42/P8_S13_hoist.patch.txt) ===",
        f"start_utc: {utc_now()}",
        "tree_recipe_step0_and_M10: r15d + v3 (/tmp/carbon2_job36/tpl_r15d_v3) + job41/bundle_grok7.patch.txt + job42/P8_S13_hoist.patch.txt",
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
    out_lines.append("--- 2. Plain r15d + v3 Release Build (/tmp/carbon2_job45/bld_base_v3/forge) ---")
    base_exe, base_sha, base_cf, base_lf = build_release_v3(TPL_V3, WORK45 / "bld_base_v3")
    ok_hd0, hd0_lines = verify_uci_option_check(base_exe, "HindsightDepth")
    ok_b0, b0_lines = verify_all_off_numbers("plain_r15d_v3", base_exe, None)
    ok_k0, k0_lines = check_nopc20_hindsight_bench13("plain_r15d_v3", base_exe, [])
    all_ok = all_ok and ok_hd0 and ok_b0 and ok_k0
    out_lines.extend(hd0_lines + b0_lines + k0_lines)

    out_lines.append("")
    out_lines.append("--- 3. Fresh Bundle8 Build (r15d + v3 + bundle_grok7.patch.txt + P8_S13_hoist.patch.txt) ---")
    b7_sha = sha256_file(BUNDLE7_PATCH)
    p8_sha = sha256_file(P8_HOIST_PATCH)
    ok_ps7, s_ps7 = fmt_cmp(f"patch sha256({BUNDLE7_PATCH})", b7_sha, EXP_BUNDLE7_SHA)
    ok_ps8, s_ps8 = fmt_cmp(f"patch sha256({P8_HOIST_PATCH})", p8_sha, EXP_P8_HOIST_SHA)
    all_ok = all_ok and ok_ps7 and ok_ps8
    out_lines.extend([s_ps7, s_ps8])

    src_b8 = WORK45 / "src_bundle8"
    ok_ap, ap_msg = apply_bundle8_to_fresh_v3(src_b8)
    all_ok = all_ok and ok_ap
    out_lines.append(f"  apply_against_fresh_r15d_v3                 : {ap_msg}")

    b8_exe, b8_sha, b8_cf, b8_lf = build_release_v3(src_b8, WORK45 / "bld_bundle8")
    out_lines.append(f"  bundle8 exe path                            : {b8_exe}")
    out_lines.append(f"  bundle8 exe sha256({b8_exe}) : {b8_sha}")
    out_lines.append(f"  bundle8 id name                             : {get_id_name(b8_exe)}")

    for uopt in ["HindsightDepth", "IdeaB8b", "IdeaB8", "IdeaS13", "IdeaS13_Hoist"]:
        ok_u, u_lines = verify_uci_option_check(b8_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    ok_b8_def, b8_def_lines = verify_all_off_numbers("bundle8_default_off", b8_exe, None)
    ok_b8_exp, b8_exp_lines = verify_all_off_numbers("bundle8_explicit_8_false", b8_exe, ALL_EIGHT_IDEA_FALSE)
    ok_k8, k8_lines = check_nopc20_hindsight_bench13("bundle8", b8_exe, ALL_EIGHT_IDEA_FALSE)
    all_ok = all_ok and ok_b8_def and ok_b8_exp and ok_k8
    out_lines.extend(b8_def_lines + b8_exp_lines + k8_lines)

    out_lines.append("")
    out_lines.append("--- 4. Bundle8 All-Switches-OFF on O (8,315,168) and G (17,611,204) vs Job 39 OFF Rows ---")
    ref_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    ref_off_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")
    all_off_8 = ALL_EIGHT_IDEA_FALSE + [("HindsightDepth", "false")]
    off_o_rows = run_epd_depth12(
        b8_exe, O_FENS_PATH, all_off_8,
        JOB45 / "step0_bundle8_all_off_O_d12.rows.txt",
        JOB45 / "step0_bundle8_all_off_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    off_g_rows = run_epd_depth12(
        b8_exe, G_EPD_PATH, all_off_8,
        JOB45 / "step0_bundle8_all_off_G_d12.rows.txt",
        JOB45 / "step0_bundle8_all_off_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    d_off_o, _ = diff_breakdown_with_samples(off_o_rows, ref_off_o, "bundle8_off_O", "J39_OFF_O")
    d_off_g, _ = diff_breakdown_with_samples(off_g_rows, ref_off_g, "bundle8_off_G", "J39_OFF_G")
    for lbl, got, exp in [
        ("bundle8 all_off O d12 sum vs OFF O", sum(r[1] for r in off_o_rows), EXP_OFF_O_SUM),
        ("bundle8 all_off O d12 equal pos vs OFF O", d_off_o["equal"], 200),
        ("bundle8 all_off G d12 sum vs OFF G", sum(r[1] for r in off_g_rows), EXP_OFF_G_SUM),
        ("bundle8 all_off G d12 equal pos vs OFF G", d_off_g["equal"], 353),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)

    out_lines.append("")
    out_lines.append("--- 5. Bundle8 IdeaB8b Alone ON vs Job 41 P7 Rows on O (8,483,711) and G (17,366,116) ---")
    b8b_only = [(o, "true" if o == "IdeaB8b" else "false") for o in EIGHT_SWITCH_NAMES] + [("HindsightDepth", "false")]
    b8b_o_rows = run_epd_depth12(
        b8_exe, O_FENS_PATH, b8b_only,
        JOB45 / "step0_bundle8_only_IdeaB8b_O_d12.rows.txt",
        JOB45 / "step0_bundle8_only_IdeaB8b_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    b8b_g_rows = run_epd_depth12(
        b8_exe, G_EPD_PATH, b8b_only,
        JOB45 / "step0_bundle8_only_IdeaB8b_G_d12.rows.txt",
        JOB45 / "step0_bundle8_only_IdeaB8b_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    j41_b8b_o = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt")
    j41_b8b_g = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_G_d12.rows.txt")
    d_b8b_o, _ = diff_breakdown_with_samples(b8b_o_rows, j41_b8b_o, "bundle8_B8b_O", "J41_P7_B8b_O")
    d_b8b_g, _ = diff_breakdown_with_samples(b8b_g_rows, j41_b8b_g, "bundle8_B8b_G", "J41_P7_B8b_G")
    for lbl, got, exp in [
        ("bundle8 IdeaB8b O d12 sum vs J41 P7 O", sum(r[1] for r in b8b_o_rows), EXP_B8B_O_SUM),
        ("bundle8 IdeaB8b O d12 equal pos vs J41 P7 O", d_b8b_o["equal"], 200),
        ("bundle8 IdeaB8b G d12 sum vs J41 P7 G", sum(r[1] for r in b8b_g_rows), EXP_B8B_G_SUM),
        ("bundle8 IdeaB8b G d12 equal pos vs J41 P7 G", d_b8b_g["equal"], 353),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)

    out_lines.append("")
    out_lines.append("--- 6. IdeaS13 + IdeaS13_Hoist ON vs PC Known Answers (O=9069588, G=18700461) ---")
    s13_hoist_on = [(o, "true" if o in ("IdeaS13", "IdeaS13_Hoist") else "false") for o in EIGHT_SWITCH_NAMES] + [("HindsightDepth", "false")]
    sh_o_rows = run_epd_depth12(
        b8_exe, O_FENS_PATH, s13_hoist_on,
        JOB45 / "step0_bundle8_S13_and_Hoist_O_d12.rows.txt",
        JOB45 / "step0_bundle8_S13_and_Hoist_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    sh_g_rows = run_epd_depth12(
        b8_exe, G_EPD_PATH, s13_hoist_on,
        JOB45 / "step0_bundle8_S13_and_Hoist_G_d12.rows.txt",
        JOB45 / "step0_bundle8_S13_and_Hoist_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    j43_sho = read_j39_rows(JOB43 / "step0_bundle8_S13_and_Hoist_O_d12.rows.txt")
    j43_shg = read_j39_rows(JOB43 / "step0_bundle8_S13_and_Hoist_G_d12.rows.txt")
    d_sho, _ = diff_breakdown_with_samples(sh_o_rows, j43_sho, "b8_sho", "j43_sho")
    d_shg, _ = diff_breakdown_with_samples(sh_g_rows, j43_shg, "b8_shg", "j43_shg")
    for lbl, got, exp in [
        ("bundle8 S13+Hoist O d12 sum vs PC known answer", sum(r[1] for r in sh_o_rows), EXP_PC_S13_HOIST_O_SUM),
        ("bundle8 S13+Hoist O d12 first 5 vs PC known answer", [r[1] for r in sh_o_rows[:5]], EXP_PC_S13_HOIST_O_FIRST5),
        ("bundle8 S13+Hoist O d12 equal pos vs J43 Step 0", d_sho["equal"], 200),
        ("bundle8 S13+Hoist G d12 sum vs PC known answer", sum(r[1] for r in sh_g_rows), EXP_PC_S13_HOIST_G_SUM),
        ("bundle8 S13+Hoist G d12 first 5 vs PC known answer", [r[1] for r in sh_g_rows[:5]], EXP_PC_S13_HOIST_G_FIRST5),
        ("bundle8 S13+Hoist G d12 equal pos vs J43 Step 0", d_shg["equal"], 353),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)

    out_lines.append("")
    out_lines.append("--- 7. fastchess & UHO Book Prerequisites ---")
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

    (JOB45 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    builds_lines = [
        "=== JOB 45 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {EXP_TREE_SHAS[rel]}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Step 0 plain r15d + v3 Release executable: {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name(base_exe)}",
        f"   compile_flags = {base_cf}",
        f"   link_flags    = {base_lf}",
        "",
        f"3. Step 0 + Part M10 bundle8 executable (patches: {BUNDLE7_PATCH} [{b7_sha}] + {P8_HOIST_PATCH} [{p8_sha}]):",
        f"   exe path = {b8_exe}",
        f"   exe sha256({b8_exe}) = {b8_sha}",
        f"   id_name = {get_id_name(b8_exe)}",
        f"   compile_flags = {b8_cf}",
        f"   link_flags    = {b8_lf}",
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
    (JOB45 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
