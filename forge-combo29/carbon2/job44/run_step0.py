#!/usr/bin/env python3
"""
Job 44 Step 0 (`run_step0.py`):
1. `r15d + v3` source tree (`4` file hashes + `0 == 0` CRLF), plain Release build (`/tmp/carbon2_job44/bld_base_v3/forge`),
   all OFF numbers (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`, `Set A line L 26,741 / d5b52710...`,
   `n[1..60] line L b6bf7600...`), and non-`PC20` `HindsightDepth` `bench 13 = 840387` (`862329` with it false).
2. Fresh bundle9 build (`r15d + v3 + job41/bundle_grok7.patch.txt + job42/P8_S13_hoist.patch.txt + job43/P9_B8_fast.patch.txt`,
   `/tmp/carbon2_job44/bld_bundle9/forge`; `IdeaB8_Fast` stays `false` throughout unless a part names it):
   - All switches off (default off and explicit 10 `false`) = every OFF number.
   - Non-`PC20` `HindsightDepth=true` `bench 13 = 840387` (`862329` with it false).
   - `IdeaB8b` alone = Job 41 `P7_bundle7_only_B8b_O_d12.rows.txt` position by position (`200 == 200`, `8483711 == 8483711`).
   - `IdeaS13 + IdeaS13_Hoist` = `O 9,069,588` (`200 == 200` vs Job 43 Step 0 rows) and `G 18,700,461` (`353 == 353` vs Job 43 Step 0 rows).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j44_lib import (  # noqa: E402
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PC_S13_HOIST_G_FIRST5,
    EXP_PC_S13_HOIST_G_SUM,
    EXP_PC_S13_HOIST_O_FIRST5,
    EXP_PC_S13_HOIST_O_SUM,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    JOB41,
    JOB43,
    JOB44,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK44,
    apply_bundle9_to_fresh_v3,
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
    WORK44.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 44 STEP 0: r15d + v3 and Bundle9 (bundle_grok7 + P8_S13_hoist + P9_B8_fast; IdeaB8_Fast off) ===",
        f"start_utc: {utc_now()}",
        "tree_recipe: r15d + v3 (/tmp/carbon2_job36/tpl_r15d_v3) + job41/bundle_grok7.patch.txt + job42/P8_S13_hoist.patch.txt + job43/P9_B8_fast.patch.txt",
        "note_on_IdeaB8_Fast: Job 43 placed IdeaB8_Fast (covering IdeaB8 [078] only); per File 44 lines 10-11, it is included in the build and stays false everywhere in Job 44.",
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
    out_lines.append("--- 2. Plain r15d + v3 Release Build (/tmp/carbon2_job44/bld_base_v3/forge) ---")
    base_exe, base_sha, base_cf, base_lf = build_release_v3(TPL_V3, WORK44 / "bld_base_v3")
    ok_hd0, hd0_lines = verify_uci_option_check(base_exe, "HindsightDepth")
    ok_b0, b0_lines = verify_all_off_numbers("plain_r15d_v3", base_exe, None)
    ok_k0, k0_lines = check_nopc20_hindsight_bench13("plain_r15d_v3", base_exe, [])
    all_ok = all_ok and ok_hd0 and ok_b0 and ok_k0
    out_lines.extend(hd0_lines + b0_lines + k0_lines)

    out_lines.append("")
    out_lines.append("--- 3. Fresh Bundle9 Build (bundle_grok7 + P8_S13_hoist + P9_B8_fast) ---")
    b7_sha = sha256_file(BUNDLE7_PATCH)
    p8_sha = sha256_file(P8_HOIST_PATCH)
    p9_sha = sha256_file(P9_B8_FAST_PATCH)
    for p_path, got_sha, exp_sha in [
        (BUNDLE7_PATCH, b7_sha, EXP_BUNDLE7_SHA),
        (P8_HOIST_PATCH, p8_sha, EXP_P8_HOIST_SHA),
        (P9_B8_FAST_PATCH, p9_sha, EXP_P9_B8_FAST_SHA),
    ]:
        ok_p, s_p = fmt_cmp(f"patch sha256({p_path})", got_sha, exp_sha)
        all_ok = all_ok and ok_p
        out_lines.append(s_p)

    src_b9 = WORK44 / "src_bundle9"
    ok_ap, ap_msg = apply_bundle9_to_fresh_v3(src_b9)
    all_ok = all_ok and ok_ap
    out_lines.append(f"  apply_against_fresh_r15d_v3                 : {ap_msg}")

    b9_exe, b9_sha, b9_cf, b9_lf = build_release_v3(src_b9, WORK44 / "bld_bundle9")
    out_lines.append(f"  bundle9 exe path                            : {b9_exe}")
    out_lines.append(f"  bundle9 exe sha256({b9_exe}) : {b9_sha}")
    out_lines.append(f"  bundle9 id name                             : {get_id_name(b9_exe)}")

    for uopt in ["HindsightDepth", "IdeaB8b", "IdeaB8", "IdeaB8_Fast", "IdeaS13", "IdeaS13_Hoist"]:
        ok_u, u_lines = verify_uci_option_check(b9_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    ok_b9_def, b9_def_lines = verify_all_off_numbers("bundle9_default_off", b9_exe, None)
    ok_b9_exp, b9_exp_lines = verify_all_off_numbers("bundle9_explicit_10_false", b9_exe, ALL_TEN_FALSE)
    ok_k9, k9_lines = check_nopc20_hindsight_bench13("bundle9", b9_exe, ALL_NINE_IDEA_FALSE)
    all_ok = all_ok and ok_b9_def and ok_b9_exp and ok_k9
    out_lines.extend(b9_def_lines + b9_exp_lines + k9_lines)

    out_lines.append("")
    out_lines.append("--- 4. IdeaB8b Alone ON vs Job 41 P7_bundle7_only_B8b_O_d12.rows.txt ---")
    b8b_only = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    b8b_rows = run_epd_depth12(
        b9_exe,
        O_FENS_PATH,
        b8b_only,
        JOB44 / "step0_bundle9_only_IdeaB8b_O_d12.rows.txt",
        JOB44 / "step0_bundle9_only_IdeaB8b_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    j41_b8b_rows = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt")
    d_b8b, _ = diff_breakdown_with_samples(b8b_rows, j41_b8b_rows, "bundle9_B8b", "J41_P7_B8b")
    ok_b8b_1, s_b8b_1 = fmt_cmp("bundle9 IdeaB8b O d12 sum vs J41 P7", sum(r[1] for r in b8b_rows), EXP_B8B_O_SUM)
    ok_b8b_2, s_b8b_2 = fmt_cmp("bundle9 IdeaB8b O d12 equal positions vs J41 P7", d_b8b["equal"], 200)
    all_ok = all_ok and ok_b8b_1 and ok_b8b_2
    out_lines.extend([s_b8b_1, s_b8b_2])

    out_lines.append("")
    out_lines.append("--- 5. IdeaS13 + IdeaS13_Hoist ON vs PC Known Answers (O=9069588, G=18700461) ---")
    s13_hoist_on = [(o, "true" if o in ("IdeaS13", "IdeaS13_Hoist") else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    sh_o_rows = run_epd_depth12(
        b9_exe,
        O_FENS_PATH,
        s13_hoist_on,
        JOB44 / "step0_bundle9_S13_and_Hoist_O_d12.rows.txt",
        JOB44 / "step0_bundle9_S13_and_Hoist_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    sh_g_rows = run_epd_depth12(
        b9_exe,
        G_EPD_PATH,
        s13_hoist_on,
        JOB44 / "step0_bundle9_S13_and_Hoist_G_d12.rows.txt",
        JOB44 / "step0_bundle9_S13_and_Hoist_G_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    j43_sh_o = read_j39_rows(JOB43 / "step0_bundle8_S13_and_Hoist_O_d12.rows.txt")
    j43_sh_g = read_j39_rows(JOB43 / "step0_bundle8_S13_and_Hoist_G_d12.rows.txt")
    d_sho, _ = diff_breakdown_with_samples(sh_o_rows, j43_sh_o, "b9_S13+Hoist_O", "J43_S13+Hoist_O")
    d_shg, _ = diff_breakdown_with_samples(sh_g_rows, j43_sh_g, "b9_S13+Hoist_G", "J43_S13+Hoist_G")

    for lbl, got, exp in [
        ("bundle9 S13+Hoist O d12 sum vs PC known answer", sum(r[1] for r in sh_o_rows), EXP_PC_S13_HOIST_O_SUM),
        ("bundle9 S13+Hoist O d12 first 5 vs PC known answer", [r[1] for r in sh_o_rows[:5]], EXP_PC_S13_HOIST_O_FIRST5),
        ("bundle9 S13+Hoist O d12 equal pos vs J43 Step 0", d_sho["equal"], 200),
        ("bundle9 S13+Hoist G d12 sum vs PC known answer", sum(r[1] for r in sh_g_rows), EXP_PC_S13_HOIST_G_SUM),
        ("bundle9 S13+Hoist G d12 first 5 vs PC known answer", [r[1] for r in sh_g_rows[:5]], EXP_PC_S13_HOIST_G_FIRST5),
        ("bundle9 S13+Hoist G d12 equal pos vs J43 Step 0", d_shg["equal"], 353),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)

    out_lines.append("")
    out_lines.append("--- 6. fastchess & UHO Book Prerequisites ---")
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
    (JOB44 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    builds_lines = [
        "=== JOB 44 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {EXP_TREE_SHAS[rel]}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Step 0 plain r15d + v3 Release executable: {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name(base_exe)}",
        f"   compile_flags = {base_cf}",
        f"   link_flags    = {base_lf}",
        "",
        f"3. Step 0 + Part L + Part M9 + Part T2 bundle9 executable (patches: {BUNDLE7_PATCH} [{b7_sha}] + {P8_HOIST_PATCH} [{p8_sha}] + {P9_B8_FAST_PATCH} [{p9_sha}]; IdeaB8_Fast=false throughout):",
        f"   exe path = {b9_exe}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {get_id_name(b9_exe)}",
        f"   compile_flags = {b9_cf}",
        f"   link_flags    = {b9_lf}",
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
    (JOB44 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
