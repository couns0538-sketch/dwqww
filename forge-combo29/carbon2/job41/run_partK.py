#!/usr/bin/env python3
"""
Job 41 Part K (`run_partK.py`):
- On `/tmp/carbon2_job41/bld_bundle7/forge` (`bundle_grok7`), with all seven `Idea*` switches `false`
  and `HindsightDepth=true` added to `PC20`:
  1. Verifies `HindsightDepth` in `uci` (`True == True`, `0 == 0` bad responses/stderr).
  2. Runs `O` depth-12 rows and checks against the PC's known answer:
     `sum_nodes == 8,732,910`, first three `12,572 / 30,191 / 29,126`, `200 / 200` positions differ from OFF `O`.
  3. Runs `G` depth-12 rows (`sum_nodes`, differing count vs OFF `G`).
  4. Runs `Set A line L` (`records`, `searches`, `nodes`, `sha256`).
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j41_lib import (  # noqa: E402
    ALL_SEVEN_FALSE,
    EXP_HINDSIGHT_O_FIRST3,
    EXP_HINDSIGHT_O_SUM,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    G_EPD_PATH,
    JOB39,
    JOB41,
    O_FENS_PATH,
    WORK41,
    diff_rows,
    fmt_cmp,
    read_j39_rows,
    run_epd_depth12,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_uci_option_check,
    write_seta_meta,
    write_v2_v3_rows,
)


def main() -> int:
    b7_exe = str(WORK41 / "bld_bundle7/forge")
    b7_sha = sha256_file(pathlib.Path(b7_exe))
    hd_opts = ALL_SEVEN_FALSE + [("HindsightDepth", "true")]

    out_lines: list[str] = [
        "=== JOB 41 PART K: HindsightDepth on bundle_grok7 (All 7 Idea* Switches False + PC20) ===",
        f"start_utc: {utc_now()}",
        f"exe_path : {b7_exe}",
        f"exe sha256({b7_exe}) : {b7_sha}",
        "",
    ]
    all_ok = True

    ok_u, u_lines = verify_uci_option_check(b7_exe, "HindsightDepth")
    all_ok = all_ok and ok_u
    out_lines.extend(u_lines)

    j39_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    j39_off_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")

    hd_o = run_epd_depth12(
        b7_exe,
        O_FENS_PATH,
        hd_opts,
        JOB41 / "partK_HindsightDepth_O_d12.rows.txt",
        JOB41 / "partK_HindsightDepth_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    hd_g = run_epd_depth12(
        b7_exe,
        G_EPD_PATH,
        hd_opts,
        JOB41 / "partK_HindsightDepth_G_d12.rows.txt",
        JOB41 / "partK_HindsightDepth_G_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )

    hd_o_sum = sum(r[1] for r in hd_o)
    hd_g_sum = sum(r[1] for r in hd_g)
    hd_o_first3 = [hd_o[0][1], hd_o[1][1], hd_o[2][1]]
    diff_o, nd_o = diff_rows(hd_o, j39_off_o)
    diff_g, nd_g = diff_rows(hd_g, j39_off_g)
    mv_o = sum(1 for a, b in zip(hd_o, j39_off_o) if a[3] != b[3])
    mv_g = sum(1 for a, b in zip(hd_g, j39_off_g) if a[3] != b[3])

    ok1, s1 = fmt_cmp("HindsightDepth O sum_nodes vs PC known answer", hd_o_sum, EXP_HINDSIGHT_O_SUM)
    ok2, s2 = fmt_cmp("HindsightDepth O pos 1 nodes vs PC known answer", hd_o_first3[0], EXP_HINDSIGHT_O_FIRST3[0])
    ok3, s3 = fmt_cmp("HindsightDepth O pos 2 nodes vs PC known answer", hd_o_first3[1], EXP_HINDSIGHT_O_FIRST3[1])
    ok4, s4 = fmt_cmp("HindsightDepth O pos 3 nodes vs PC known answer", hd_o_first3[2], EXP_HINDSIGHT_O_FIRST3[2])
    ok5, s5 = fmt_cmp("HindsightDepth O differing positions vs OFF O", diff_o, 200)
    all_ok = all_ok and ok1 and ok2 and ok3 and ok4 and ok5
    out_lines.extend([s1, s2, s3, s4, s5])

    res_sa = run_selfgame_set_with_options(b7_exe, "carbon2-job33-a", 200, None, hd_opts, cpu_pin=1)
    sa_rows_path = JOB41 / "partK_HindsightDepth_SetA_L.rows.txt"
    sa_meta_path = JOB41 / "partK_HindsightDepth_SetA_L.rows.txt.meta"
    write_v2_v3_rows(sa_rows_path, "Job 41 Part K HindsightDepth Set A line L (built-in eval, PC20)", res_sa)
    write_seta_meta(sa_meta_path, b7_exe, hd_opts, res_sa)

    out_lines.extend(
        [
            f"  HindsightDepth O d12 sum_nodes              : {hd_o_sum} (OFF = {EXP_OFF_O_SUM}, ratio = {hd_o_sum / EXP_OFF_O_SUM:.6f})",
            f"  HindsightDepth O d12 differing vs OFF       : {diff_o} / 200 (node diffs = {nd_o}, bestmove diffs = {mv_o})",
            f"  HindsightDepth G d12 sum_nodes              : {hd_g_sum} (OFF = {EXP_OFF_G_SUM}, ratio = {hd_g_sum / EXP_OFF_G_SUM:.6f})",
            f"  HindsightDepth G d12 first 3 nodes          : {hd_g[0][1]} / {hd_g[1][1]} / {hd_g[2][1]}",
            f"  HindsightDepth G d12 differing vs OFF       : {diff_g} / 353 (node diffs = {nd_g}, bestmove diffs = {mv_g})",
            f"  HindsightDepth Set A line L records/searches: {res_sa.total_records} / {res_sa.total_searches} (OFF = {EXP_SETA_L_RECORDS})",
            f"  HindsightDepth Set A line L sum_nodes       : {res_sa.total_nodes} (OFF = {EXP_SETA_L_NODES}, ratio = {res_sa.total_nodes / EXP_SETA_L_NODES:.6f})",
            f"  HindsightDepth Set A line L sha256          : {res_sa.full_sha256} (OFF = {EXP_SETA_L_SHA})",
        ]
    )

    out_lines.append("")
    ok_ov, s_ov = fmt_cmp("PART K OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")

    (JOB41 / "partK_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
