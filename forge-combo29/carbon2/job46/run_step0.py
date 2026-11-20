#!/usr/bin/env python3
"""
Job 46 Step 0 (`run_step0.py`):
- Reuses Job 44's `bundle9` executable (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524d...`;
  nothing new is built in Job 46, rebuilding only if missing) and plain `r15d + v3` Release executable.
- Verifies:
  1. `r15d + v3` 4 source file hashes (`0 == 0` CRLF), plain `r15d + v3` OFF numbers (`312866 / 862329 / 4865609`,
     `PC20 278024 / 587276`, `Set A line L 26,741 / 107,124,743 / d5b52710...`, `n[1..60] 8,449 / 8,482 / 36,688,357 / b6bf7600...`),
     and non-`PC20` `HindsightDepth` `bench 13 = 840387` (`true`) / `862329` (`false`).
  2. `bundle9` (`9441524d...`) with `PC20`:
     - All switches off (default off and explicit 10 `false`) = every OFF number + `O` (`8,315,168`, `200 == 200` vs
       `job39/OFF_O_d12.rows.txt` and `job41/P7_bundle7_all_off_O_d12.rows.txt`) + `G` (`17,611,204`, `353 == 353` vs
       `job39/OFF_G_d12.rows.txt`).
     - Non-`PC20` `HindsightDepth` `bench 13 = 840387` (`true`) / `862329` (`false`).
     - `IdeaB8b` alone = Job 41 `P7_bundle7_only_B8b_O_d12.rows.txt` position by position (`200 == 200`, `8,483,711`).
     - `IdeaS13 + IdeaS13_Hoist` = `O 9,069,588` (`200 == 200`) and `G 18,700,461` (`353 == 353`).
     - NEW known answers on `O` d12 (`PC20`):
       * `IdeaS10` alone = `8,314,153`, `200 == 200` vs `job41/P7_bundle7_only_S10_O_d12.rows.txt`,
         node count differs from all off on `17` of `200`, best move on `2` of `200`.
       * `IdeaS13` alone (`IdeaS13=true, IdeaS13_Hoist=false`) = `8,077,984`, `200 == 200` vs
         `job41/P7_bundle7_only_S13_O_d12.rows.txt`, node count differs from all off on `200` of `200`.
"""
from __future__ import annotations

import concurrent.futures
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j46_lib import (  # noqa: E402
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_BASE_V3_SHA,
    EXP_BUNDLE7_SHA,
    EXP_BUNDLE9_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PC_S13_HOIST_G_FIRST5,
    EXP_PC_S13_HOIST_G_SUM,
    EXP_PC_S13_HOIST_O_FIRST5,
    EXP_PC_S13_HOIST_O_SUM,
    EXP_S10_O_SUM,
    EXP_S10_VS_OFF_BM_DIFF,
    EXP_S10_VS_OFF_ND_DIFF,
    EXP_S13_ALONE_O_SUM,
    EXP_S13_VS_OFF_ND_DIFF,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    JOB39,
    JOB41,
    JOB44,
    JOB46,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK44,
    WORK45,
    WORK46,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    count_row_diffs,
    fmt_cmp,
    get_id_name,
    read_j39_rows,
    run_epd_depth12_custom,
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
    WORK46.mkdir(parents=True, exist_ok=True)
    JOB46.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 46 STEP 0: r15d + v3 and Reused Job 44 Bundle9 (exe 9441524d...) ===",
        f"start_utc: {utc_now()}",
        "tree_recipe: r15d + v3 (/tmp/carbon2_job36/tpl_r15d_v3) + job41/bundle_grok7.patch.txt + job42/P8_S13_hoist.patch.txt + job43/P9_B8_fast.patch.txt",
        "nothing_new_built_policy: Reuse existing Job 44 bundle9 (/tmp/carbon2_job44/bld_bundle9/forge) and existing plain r15d+v3 Release binary without rebuilding.",
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
    out_lines.append("--- 2. Plain r15d + v3 Release Executable Verification ---")
    cand_base_44 = WORK44 / "bld_base_v3/forge"
    cand_base_45 = WORK45 / "bld_base_v3/forge"
    rebuilt_base = False
    if cand_base_44.exists():
        base_exe = str(cand_base_44)
        base_sha = sha256_file(cand_base_44)
    elif cand_base_45.exists():
        base_exe = str(cand_base_45)
        base_sha = sha256_file(cand_base_45)
    else:
        rebuilt_base = True
        base_exe, base_sha, _, _ = build_release_v3(TPL_V3, WORK46 / "bld_base_v3")
    ok_bs, s_bs = fmt_cmp(f"plain r15d+v3 sha256({base_exe})", base_sha, EXP_BASE_V3_SHA)
    ok_hd0, hd0_lines = verify_uci_option_check(base_exe, "HindsightDepth")
    ok_b0, b0_lines = verify_all_off_numbers("plain_r15d_v3", base_exe, None)
    ok_k0, k0_lines = check_nopc20_hindsight_bench13("plain_r15d_v3", base_exe, [])
    all_ok = all_ok and ok_bs and ok_hd0 and ok_b0 and ok_k0
    out_lines.append(f"  reused_without_rebuild                      : {not rebuilt_base} ({base_exe})")
    out_lines.append(s_bs)
    out_lines.extend(hd0_lines + b0_lines + k0_lines)

    out_lines.append("")
    out_lines.append("--- 3. Job 44 Bundle9 Executable & Patch Verification ---")
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

    cand_b9 = WORK44 / "bld_bundle9/forge"
    rebuilt_b9 = False
    if cand_b9.exists():
        b9_exe = str(cand_b9)
        b9_sha = sha256_file(cand_b9)
    else:
        rebuilt_b9 = True
        src_b9 = WORK46 / "src_bundle9"
        ok_ap, ap_msg = apply_bundle9_to_fresh_v3(src_b9)
        all_ok = all_ok and ok_ap
        out_lines.append(f"  rebuild_apply_status                        : {ap_msg}")
        b9_exe, b9_sha, _, _ = build_release_v3(src_b9, WORK46 / "bld_bundle9")

    ok_b9s, s_b9s = fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA)
    all_ok = all_ok and ok_b9s
    out_lines.append(f"  reused_job44_bundle9_without_rebuild        : {not rebuilt_b9} ({b9_exe})")
    out_lines.append(s_b9s)
    out_lines.append(f"  bundle9 id name                             : {get_id_name(b9_exe)}")

    for uopt in ["HindsightDepth", "IdeaB8b", "IdeaB8", "IdeaB8_Fast", "IdeaS13", "IdeaS13_Hoist", "IdeaS10"]:
        ok_u, u_lines = verify_uci_option_check(b9_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    ok_b9_def, b9_def_lines = verify_all_off_numbers("bundle9_default_off", b9_exe, None)
    ok_b9_exp, b9_exp_lines = verify_all_off_numbers("bundle9_explicit_10_false", b9_exe, ALL_TEN_FALSE)
    ok_k9, k9_lines = check_nopc20_hindsight_bench13("bundle9", b9_exe, ALL_NINE_IDEA_FALSE)
    all_ok = all_ok and ok_b9_def and ok_b9_exp and ok_k9
    out_lines.extend(b9_def_lines + b9_exp_lines + k9_lines)

    out_lines.append("")
    out_lines.append("--- 4. O and G Depth-12 Known-Answer Sweeps on bundle9 (PC20) ---")
    b8b_only = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    s10_only = [(o, "true" if o == "IdeaS10" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    s13_only = [(o, "true" if o == "IdeaS13" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    s13_hoist = [(o, "true" if o in ("IdeaS13", "IdeaS13_Hoist") else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]

    tasks = {
        "off_O": (O_FENS_PATH, ALL_TEN_FALSE, JOB46 / "step0_bundle9_all_off_O_d12.rows.txt", 1),
        "off_G": (G_EPD_PATH, ALL_TEN_FALSE, JOB46 / "step0_bundle9_all_off_G_d12.rows.txt", 2),
        "b8b_O": (O_FENS_PATH, b8b_only, JOB46 / "step0_bundle9_only_IdeaB8b_O_d12.rows.txt", 3),
        "s10_O": (O_FENS_PATH, s10_only, JOB46 / "step0_bundle9_only_IdeaS10_O_d12.rows.txt", 1),
        "s13_O": (O_FENS_PATH, s13_only, JOB46 / "step0_bundle9_only_IdeaS13_O_d12.rows.txt", 2),
        "sh_O": (O_FENS_PATH, s13_hoist, JOB46 / "step0_bundle9_S13_and_Hoist_O_d12.rows.txt", 3),
        "sh_G": (G_EPD_PATH, s13_hoist, JOB46 / "step0_bundle9_S13_and_Hoist_G_d12.rows.txt", 1),
    }

    results: dict[str, tuple[list[tuple[int, int, str, str]], list[str]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futs = {
            k: pool.submit(
                run_epd_depth12_custom,
                b9_exe,
                spath,
                PC20_OPTIONS,
                eopts,
                rpath,
                pathlib.Path(str(rpath) + ".meta"),
                12,
                cpin,
            )
            for k, (spath, eopts, rpath, cpin) in tasks.items()
        }
        for k, fut in futs.items():
            results[k] = fut.result()

    for k, (_, bad_lines) in results.items():
        ok_bl, s_bl = fmt_cmp(f"{k} unknown/invalid option lines", len(bad_lines), 0)
        all_ok = all_ok and ok_bl
        out_lines.append(s_bl)

    off_o_rows = results["off_O"][0]
    off_g_rows = results["off_G"][0]
    b8b_o_rows = results["b8b_O"][0]
    s10_o_rows = results["s10_O"][0]
    s13_o_rows = results["s13_O"][0]
    sh_o_rows = results["sh_O"][0]
    sh_g_rows = results["sh_G"][0]

    j39_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    j39_off_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")
    j41_off_o = read_j39_rows(JOB41 / "P7_bundle7_all_off_O_d12.rows.txt")
    j41_b8b_o = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt")
    j41_s10_o = read_j39_rows(JOB41 / "P7_bundle7_only_S10_O_d12.rows.txt")
    j41_s13_o = read_j39_rows(JOB41 / "P7_bundle7_only_S13_O_d12.rows.txt")
    j44_sh_o = read_j39_rows(JOB44 / "step0_bundle9_S13_and_Hoist_O_d12.rows.txt")
    j44_sh_g = read_j39_rows(JOB44 / "step0_bundle9_S13_and_Hoist_G_d12.rows.txt")

    c_off_o_39 = count_row_diffs(off_o_rows, j39_off_o)
    c_off_o_41 = count_row_diffs(off_o_rows, j41_off_o)
    c_off_g_39 = count_row_diffs(off_g_rows, j39_off_g)
    c_b8b_41 = count_row_diffs(b8b_o_rows, j41_b8b_o)
    c_s10_41 = count_row_diffs(s10_o_rows, j41_s10_o)
    c_s10_vs_off = count_row_diffs(s10_o_rows, off_o_rows)
    c_s13_41 = count_row_diffs(s13_o_rows, j41_s13_o)
    c_s13_vs_off = count_row_diffs(s13_o_rows, off_o_rows)
    c_sh_o_44 = count_row_diffs(sh_o_rows, j44_sh_o)
    c_sh_g_44 = count_row_diffs(sh_g_rows, j44_sh_g)

    row_checks = [
        ("bundle9 all_off O d12 sum", c_off_o_39["sum_a"], EXP_OFF_O_SUM),
        ("bundle9 all_off O d12 equal vs J39 OFF_O", c_off_o_39["equal"], 200),
        ("bundle9 all_off O d12 equal vs J41 P7_all_off", c_off_o_41["equal"], 200),
        ("bundle9 all_off G d12 sum", c_off_g_39["sum_a"], EXP_OFF_G_SUM),
        ("bundle9 all_off G d12 equal vs J39 OFF_G", c_off_g_39["equal"], 353),
        ("bundle9 IdeaB8b O d12 sum", c_b8b_41["sum_a"], EXP_B8B_O_SUM),
        ("bundle9 IdeaB8b O d12 equal vs J41 P7_only_B8b", c_b8b_41["equal"], 200),
        ("bundle9 IdeaS10 O d12 sum (NEW known answer)", c_s10_41["sum_a"], EXP_S10_O_SUM),
        ("bundle9 IdeaS10 O d12 equal vs J41 P7_only_S10", c_s10_41["equal"], 200),
        ("bundle9 IdeaS10 vs all_off O d12 node diffs", c_s10_vs_off["nodes_diff"], EXP_S10_VS_OFF_ND_DIFF),
        ("bundle9 IdeaS10 vs all_off O d12 bestmove diffs", c_s10_vs_off["bestmove_diff"], EXP_S10_VS_OFF_BM_DIFF),
        ("bundle9 IdeaS13 (no hoist) O d12 sum (NEW)", c_s13_41["sum_a"], EXP_S13_ALONE_O_SUM),
        ("bundle9 IdeaS13 (no hoist) O equal vs J41 P7_S13", c_s13_41["equal"], 200),
        ("bundle9 IdeaS13 (no hoist) vs all_off node diffs", c_s13_vs_off["nodes_diff"], EXP_S13_VS_OFF_ND_DIFF),
        ("bundle9 S13+Hoist O d12 sum", c_sh_o_44["sum_a"], EXP_PC_S13_HOIST_O_SUM),
        ("bundle9 S13+Hoist O d12 first 5", [r[1] for r in sh_o_rows[:5]], EXP_PC_S13_HOIST_O_FIRST5),
        ("bundle9 S13+Hoist O d12 equal vs J44 Step 0", c_sh_o_44["equal"], 200),
        ("bundle9 S13+Hoist G d12 sum", c_sh_g_44["sum_a"], EXP_PC_S13_HOIST_G_SUM),
        ("bundle9 S13+Hoist G d12 first 5", [r[1] for r in sh_g_rows[:5]], EXP_PC_S13_HOIST_G_FIRST5),
        ("bundle9 S13+Hoist G d12 equal vs J44 Step 0", c_sh_g_44["equal"], 353),
    ]
    for lbl, got, exp in row_checks:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)

    out_lines.append("")
    out_lines.append("--- 5. fastchess & UHO Book Prerequisites ---")
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
    (JOB46 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    builds_lines = [
        "=== JOB 46 BUILDS.TXT ===",
        "note: Nothing new was built in Job 46; reused existing binaries verified below.",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {sha256_file(TPL_V3 / rel)}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Step 0 plain r15d + v3 Release executable (reused={not rebuilt_base}): {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name(base_exe)}",
        "",
        f"3. Step 0 + Part M13 + Part M11 + Part M12 bundle9 executable (reused={not rebuilt_b9}): {b9_exe}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {get_id_name(b9_exe)}",
        f"   patch 1 sha256({BUNDLE7_PATCH}) = {b7_sha}",
        f"   patch 2 sha256({P8_HOIST_PATCH}) = {p8_sha}",
        f"   patch 3 sha256({P9_B8_FAST_PATCH}) = {p9_sha}",
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
    (JOB46 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
