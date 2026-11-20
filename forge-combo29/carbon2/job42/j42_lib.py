#!/usr/bin/env python3
"""
Job 42 Shared Library (`j42_lib.py`).
"""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK42 = pathlib.Path("/tmp/carbon2_job42")
WORK41 = pathlib.Path("/tmp/carbon2_job41")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")

BUNDLE7_PATCH = JOB41 / "bundle_grok7.patch.txt"
EXP_BUNDLE7_SHA = "b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146"
EXP_B8B_O_SUM = 8483711
EXP_NOPC20_HD_FALSE_BENCH13 = 862329
EXP_NOPC20_HD_TRUE_BENCH13 = 840387

SEVEN_SWITCH_SPECS = [
    ("K4", "IdeaK4", JOB39 / "P1_K4_093_on_O_d12.rows.txt", 8080229),
    ("S32", "IdeaS32", JOB39 / "P2_S32_074_on_O_d12.rows.txt", 8339315),
    ("B1", "IdeaB1", JOB39 / "P3_B1_030_on_O_d12.rows.txt", 8548042),
    ("S13", "IdeaS13", JOB39 / "P4_S13_016_on_O_d12.rows.txt", 8077984),
    ("S10", "IdeaS10", JOB39 / "P5_S10_081_on_O_d12.rows.txt", 8314153),
    ("B8", "IdeaB8", JOB39 / "P6_B8_078_on_O_d12.rows.txt", 8262696),
    ("B8b", "IdeaB8b", JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt", 8483711),
]

EIGHT_SWITCH_NAMES = [
    "IdeaK4",
    "IdeaS32",
    "IdeaB1",
    "IdeaS13",
    "IdeaS13_Hoist",
    "IdeaS10",
    "IdeaB8",
    "IdeaB8b",
]
ALL_EIGHT_IDEA_FALSE = [(o, "false") for o in EIGHT_SWITCH_NAMES]

sys.path.insert(0, str(JOB41))
sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j41_lib import (  # noqa: E402
    ALL_SEVEN_FALSE,
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
