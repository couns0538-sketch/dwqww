#!/usr/bin/env python3
"""
Job 43 Shared Library (`j43_lib.py`).
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK43 = pathlib.Path("/tmp/carbon2_job43")
WORK42 = pathlib.Path("/tmp/carbon2_job42")
WORK41 = pathlib.Path("/tmp/carbon2_job41")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")

BUNDLE7_PATCH = JOB41 / "bundle_grok7.patch.txt"
EXP_BUNDLE7_SHA = "b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146"

P8_HOIST_PATCH = JOB42 / "P8_S13_hoist.patch.txt"
EXP_P8_HOIST_SHA = "16afbb689ed9ace2494d1ca8ea597e0e1deb9b2109931e6abafaa19c458b8326"

EXP_PC_S13_HOIST_O_SUM = 9069588
EXP_PC_S13_HOIST_O_FIRST5 = [20032, 17387, 38324, 18248, 22728]
EXP_PC_S13_HOIST_G_SUM = 18700461
EXP_PC_S13_HOIST_G_FIRST5 = [69963, 64050, 83616, 47203, 25100]
EXP_PC_S13_HOIST_G_EQUAL_S13 = 11

sys.path.insert(0, str(JOB42))
sys.path.insert(0, str(JOB41))
sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j42_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    ALL_SEVEN_FALSE,
    EIGHT_SWITCH_NAMES,
    EXP_B8B_O_SUM,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    O_FENS_PATH,
    PC20_OPTIONS,
    SEVEN_SWITCH_NAMES,
    SEVEN_SWITCH_SPECS,
    UHO_BOOK,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name,
    load_fens,
    pc20_option_lines,
    pgn_to_games_tsv,
    read_j39_rows,
    recount_games_tsv,
    run_epd_depth12,
    run_fresh_bench,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    verify_uci_option_check,
    write_seta_meta,
    write_v2_v3_rows,
)


def apply_bundle8_to_fresh_v3(dst_dir: pathlib.Path) -> tuple[bool, str]:
    """Copy fresh `r15d + v3` to `dst_dir` and apply `bundle_grok7.patch.txt` + `P8_S13_hoist.patch.txt`."""
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    ok7, msg7 = apply_patch_to_fresh_v3(BUNDLE7_PATCH, dst_dir)
    if not ok7:
        return False, f"bundle_grok7 failed: {msg7}"
    chk = subprocess.run(
        ["git", "apply", "--check", "-p1", str(P8_HOIST_PATCH)],
        cwd=str(dst_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if chk.returncode != 0:
        return False, f"P8_S13_hoist --check failed ({chk.returncode}): {chk.stderr.strip()}"
    ap = subprocess.run(
        ["git", "apply", "-p1", str(P8_HOIST_PATCH)],
        cwd=str(dst_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if ap.returncode != 0:
        return False, f"P8_S13_hoist apply failed ({ap.returncode}): {ap.stderr.strip()}"
    return True, "bundle_grok7 + P8_S13_hoist git apply --check -p1 PASS (0 == 0)"


def diff_breakdown_with_samples(
    rows_a: list[tuple[int, int, str, str]],
    rows_b: list[tuple[int, int, str, str]],
    label_a: str,
    label_b: str,
) -> tuple[dict[str, int], list[str]]:
    """
    Exact column-verified comparison of `(pos, nodes, bestmove, score)` rows:
      index 0 = position (1-based)
      index 1 = nodes
      index 2 = bestmove
      index 3 = score
    Also formats one sample row where `bestmove` (`row[2]`) differs and one sample row
    where `score` (`row[3]`) differs with `bestmove` equal, per File 43 line 41.
    """
    assert len(rows_a) == len(rows_b)
    n_any = 0
    n_nd = 0
    n_bm = 0
    n_sc = 0
    sample_bm: str | None = None
    sample_sc_only: str | None = None
    for a, b in zip(rows_a, rows_b):
        assert a[0] == b[0]
        if a != b:
            n_any += 1
        if a[1] != b[1]:
            n_nd += 1
        if a[2] != b[2]:
            n_bm += 1
            if sample_bm is None:
                sample_bm = (
                    f"    sample bestmove diff (col 2, pos {a[0]}): "
                    f"{label_a}=(nodes={a[1]}, bestmove={a[2]}, score={a[3]}) vs "
                    f"{label_b}=(nodes={b[1]}, bestmove={b[2]}, score={b[3]})"
                )
        if a[3] != b[3]:
            n_sc += 1
            if a[2] == b[2] and sample_sc_only is None:
                sample_sc_only = (
                    f"    sample score-only diff (col 3, pos {a[0]}): "
                    f"{label_a}=(nodes={a[1]}, bestmove={a[2]}, score={a[3]}) vs "
                    f"{label_b}=(nodes={b[1]}, bestmove={b[2]}, score={b[3]})"
                )
    samples = [s for s in (sample_bm, sample_sc_only) if s is not None]
    return {"any": n_any, "nodes": n_nd, "bestmove": n_bm, "score": n_sc, "equal": len(rows_a) - n_any}, samples
