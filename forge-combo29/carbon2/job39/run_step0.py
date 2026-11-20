#!/usr/bin/env python3
"""
Job 39 Step 0 Runner (`run_step0.py`):
1. Verifies `/tmp/carbon2_job36/tpl_r15d_v3` matches all 4 PC file `sha256`s with LF line endings.
2. Reuses Job 36's recorded `r15d + v3` executable (`/tmp/carbon2_job36/bld_sp_sgr15v/forge`,
   `sha256 = bfabc284...`) AND also builds clean Release `r15d + v3` (`/tmp/carbon2_job39/bld_base_v3/forge`,
   Job 36 Release recipe without profile, matching how Part P ports are built), verifying ALL Step 0
   OFF numbers on both and recording the switch-off `O` (200 FENs, depth 12) and `G` (353 FENs, depth 12)
   reference rows under `PC20` + built-in evaluation.
"""
from __future__ import annotations

import concurrent.futures
import pathlib
import sys

sys.dont_write_bytecode = True

from j39_lib import (
    EXP_TREE_SHAS,
    G_EPD_PATH,
    JOB39,
    O_FENS_PATH,
    REC_R15D_V3_PROF_SHA,
    REC_R15D_V3_SHA,
    REUSED_R15D_V3_EXE,
    REUSED_R15D_V3_PROF,
    TPL_V3,
    WORK39,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    get_id_name,
    run_epd_depth12,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
)


def main() -> None:
    WORK39.mkdir(parents=True, exist_ok=True)
    all_ok = True
    lines: list[str] = [
        "=== JOB 39 STEP 0: r15d + v3 Tree, Reused Job 36 Exe & Clean Release Exe OFF Numbers + Base O/G Rows ===",
        f"start_utc: {utc_now()}",
        "",
        "--- 1. r15d + v3 Source Tree Verification (/tmp/carbon2_job36/tpl_r15d_v3, LF line endings) ---",
    ]
    for rel, exp_sha in EXP_TREE_SHAS.items():
        fp = TPL_V3 / rel
        raw = fp.read_bytes()
        has_crlf = int(b"\r" in raw)
        got_sha = sha256_file(fp)
        ok_lf, s_lf = fmt_cmp(f"{rel} CRLF count", has_crlf, 0)
        ok_sh, s_sh = fmt_cmp(f"{rel} sha256", got_sha, exp_sha)
        all_ok = all_ok and ok_lf and ok_sh
        lines.extend([s_lf, s_sh])
    lines.append("")

    # 2. Verify reused Job 36 SP-PGO exe (`bfabc284...`)
    lines.append("--- 2. Reused Job 36/37 r15d + v3 Executable (/tmp/carbon2_job36/bld_sp_sgr15v/forge) ---")
    ok_rsha, s_rsha = fmt_cmp("reused exe sha256 vs recorded", sha256_file(REUSED_R15D_V3_EXE), REC_R15D_V3_SHA)
    ok_psha, s_psha = fmt_cmp("reused profdata sha256 vs recorded", sha256_file(REUSED_R15D_V3_PROF), REC_R15D_V3_PROF_SHA)
    all_ok = all_ok and ok_rsha and ok_psha
    lines.extend([s_rsha, s_psha])
    ok_reused_off, reused_lines = verify_all_off_numbers("reused_r15d_v3", REUSED_R15D_V3_EXE)
    all_ok = all_ok and ok_reused_off
    lines.extend(reused_lines)
    lines.append("")

    # 3. Also build clean non-profile Release r15d + v3 (exact recipe used in Part P-b) and verify all OFF numbers
    lines.append("--- 3. Clean Release r15d + v3 Build (Job 36 Release recipe, no profile step) ---")
    base_exe, base_sha, cflags, lflags = build_release_v3(TPL_V3, WORK39 / "bld_base_v3")
    ok_base_off, base_lines = verify_all_off_numbers("clean_rel_r15d_v3", base_exe)
    all_ok = all_ok and ok_base_off
    lines.extend(base_lines)
    lines.append("")

    # 4. Run switch-off O (first200.fens, 200 positions, d12) and G (set_G.epd, 353 positions, d12) under PC20 + built-in eval
    lines.append("--- 4. Switch-Off Reference Rows on O (200 FENs, d12) and G (353 FENs, d12) under PC20 ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fut_o = pool.submit(
            run_epd_depth12,
            base_exe,
            O_FENS_PATH,
            None,
            JOB39 / "OFF_O_d12.rows.txt",
            JOB39 / "OFF_O_d12.rows.txt.meta",
            12,
            1,
        )
        fut_g = pool.submit(
            run_epd_depth12,
            base_exe,
            G_EPD_PATH,
            None,
            JOB39 / "OFF_G_d12.rows.txt",
            JOB39 / "OFF_G_d12.rows.txt.meta",
            12,
            2,
        )
        # Also cross-check O on reused SP-PGO exe in /tmp to prove identical 200/200 rows!
        fut_o_sp = pool.submit(
            run_epd_depth12,
            REUSED_R15D_V3_EXE,
            O_FENS_PATH,
            None,
            WORK39 / "sp_OFF_O_d12.rows.txt",
            WORK39 / "sp_OFF_O_d12.rows.txt.meta",
            12,
            3,
        )
        rows_o = fut_o.result()
        rows_g = fut_g.result()
        rows_o_sp = fut_o_sp.result()

    any_diff_sp, nd_diff_sp = diff_rows(rows_o, rows_o_sp)
    ok_ocnt, s_ocnt = fmt_cmp("OFF O position count", len(rows_o), 200)
    ok_gcnt, s_gcnt = fmt_cmp("OFF G position count", len(rows_g), 353)
    ok_osp, s_osp = fmt_cmp("OFF O clean_rel vs reused_sp_pgo diffs", any_diff_sp, 0)
    all_ok = all_ok and ok_ocnt and ok_gcnt and ok_osp
    sum_o = sum(r[1] for r in rows_o)
    sum_g = sum(r[1] for r in rows_g)
    lines.extend([
        s_ocnt,
        s_gcnt,
        s_osp,
        f"  OFF O d12 sum_nodes (PC20, built-in eval)   : {sum_o} (first 3: {rows_o[0][1]}, {rows_o[1][1]}, {rows_o[2][1]})",
        f"  OFF G d12 sum_nodes (PC20, built-in eval)   : {sum_g} (first 3: {rows_g[0][1]}, {rows_g[1][1]}, {rows_g[2][1]})",
        "",
        f"STEP 0 OVERALL: {'PASS' if all_ok else 'FAIL'} ({int(all_ok)} == 1)",
        f"done_utc: {utc_now()}",
    ])

    out_txt = "\n".join(lines) + "\n"
    (JOB39 / "step0_raw.txt").write_text(out_txt, encoding="utf-8")

    builds_lines = [
        "=== JOB 39 BUILDS.TXT ===",
        "Tree: /tmp/carbon2_job36/tpl_r15d_v3 (r15d + selfgame_r15d_v3.patch.txt, matching PC forge/r15dsg)",
        f"  src/search.cpp          sha256={EXP_TREE_SHAS['src/search.cpp']}",
        f"  src/uci.cpp             sha256={EXP_TREE_SHAS['src/uci.cpp']}",
        f"  src/board.cpp           sha256={EXP_TREE_SHAS['src/board.cpp']}",
        f"  include/forge/board.hpp sha256={EXP_TREE_SHAS['include/forge/board.hpp']}",
        f"Release compile flags (template): {cflags}",
        f"Release link flags    (template): {lflags}",
        "",
        f"[Step0 reused_r15d_v3] exe={REUSED_R15D_V3_EXE} sha256={REC_R15D_V3_SHA} profdata_sha256={REC_R15D_V3_PROF_SHA} id='{get_id_name(REUSED_R15D_V3_EXE)}'",
        f"[Step0 clean_rel_r15d_v3] exe={base_exe} sha256={base_sha} id='{get_id_name(base_exe)}'",
    ]
    (JOB39 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")
    print(out_txt, flush=True)
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
