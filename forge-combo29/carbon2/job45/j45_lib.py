#!/usr/bin/env python3
"""
Job 45 Shared Library (`j45_lib.py`).
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB45 = REPO / "forge-combo29/carbon2/job45"
JOB44 = REPO / "forge-combo29/carbon2/job44"
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK45 = pathlib.Path("/tmp/carbon2_job45")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")

EXP_B8B_G_SUM = 17366116
EXP_B8B_SETA_L_RECORDS = 26709
EXP_B8B_SETA_L_SEARCHES = 26829
EXP_B8B_SETA_L_NODES = 106651211
EXP_B8B_SETA_L_SHA = "de20b5698c77baabb8be38bb219829d4265c69f1cfeaf14ebe232a01c53d4f31"

sys.path.insert(0, str(JOB43))
sys.path.insert(0, str(JOB42))
sys.path.insert(0, str(JOB41))
sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j43_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    BUNDLE7_PATCH,
    EIGHT_SWITCH_NAMES,
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
