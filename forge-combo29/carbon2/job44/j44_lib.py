#!/usr/bin/env python3
"""
Job 44 Shared Library (`j44_lib.py`).
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB44 = REPO / "forge-combo29/carbon2/job44"
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK44 = pathlib.Path("/tmp/carbon2_job44")
WORK43 = pathlib.Path("/tmp/carbon2_job43")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")

P9_B8_FAST_PATCH = JOB43 / "P9_B8_fast.patch.txt"
EXP_P9_B8_FAST_SHA = "bc0bb2b7aa2a7a817c3aca6ef7765ff81796feeb825e2670204d0c04e2b24395"

NINE_SWITCH_NAMES = [
    "IdeaK4",
    "IdeaS32",
    "IdeaB1",
    "IdeaS13",
    "IdeaS13_Hoist",
    "IdeaS10",
    "IdeaB8",
    "IdeaB8_Fast",
    "IdeaB8b",
]
ALL_NINE_IDEA_FALSE = [(o, "false") for o in NINE_SWITCH_NAMES]
ALL_TEN_FALSE = ALL_NINE_IDEA_FALSE + [("HindsightDepth", "false")]

sys.path.insert(0, str(JOB43))
sys.path.insert(0, str(JOB42))
sys.path.insert(0, str(JOB41))
sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j43_lib import (  # noqa: E402
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_PC_S13_HOIST_G_EQUAL_S13,
    EXP_PC_S13_HOIST_G_FIRST5,
    EXP_PC_S13_HOIST_G_SUM,
    EXP_PC_S13_HOIST_O_FIRST5,
    EXP_PC_S13_HOIST_O_SUM,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    PC20_OPTIONS,
    UHO_BOOK,
    apply_bundle8_to_fresh_v3,
    build_release_v3,
    diff_breakdown_with_samples,
    fmt_cmp,
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


def apply_bundle9_to_fresh_v3(dst_dir: pathlib.Path) -> tuple[bool, str]:
    """Copy fresh `r15d + v3` to `dst_dir` and apply `bundle_grok7` + `P8_S13_hoist` + `P9_B8_fast`."""
    ok8, msg8 = apply_bundle8_to_fresh_v3(dst_dir)
    if not ok8:
        return False, msg8
    chk = subprocess.run(
        ["git", "apply", "--check", "-p1", str(P9_B8_FAST_PATCH)],
        cwd=str(dst_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if chk.returncode != 0:
        return False, f"P9_B8_fast --check failed ({chk.returncode}): {chk.stderr.strip()}"
    ap = subprocess.run(
        ["git", "apply", "-p1", str(P9_B8_FAST_PATCH)],
        cwd=str(dst_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if ap.returncode != 0:
        return False, f"P9_B8_fast apply failed ({ap.returncode}): {ap.stderr.strip()}"
    return True, "bundle_grok7 + P8_S13_hoist + P9_B8_fast git apply --check -p1 PASS (0 == 0)"
